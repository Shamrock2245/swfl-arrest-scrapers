import sys
import json
import time
import re
import os
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stderr.write("=== Hendry Solver Starting ===\n")
sys.stderr.flush()

def clean_charge_text(raw_charge):
    """
    Clean charge text to extract only the human-readable description.
    """
    if not raw_charge:
        return ''
    
    text = re.sub(r'^(New Charge:|Weekender:|Charge Description:)\s*', '', raw_charge, flags=re.IGNORECASE)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        return description
    
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    
    return text.strip()

def scrape_hendry(days_back=30):
    records = []
    progress_file = 'hendry_progress.jsonl'
    
    processed_ids = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            if 'Booking_Number' in rec:
                                processed_ids.add(rec['Booking_Number'])
                        except: pass
        except: pass
        
    sys.stderr.write(f"ℹ️  Found {len(processed_ids)} previously scraped records. Resuming...\n")
    
    try:
        co = ChromiumOptions()
        # co.set_browser_path('/usr/bin/chromium-browser')
        co.headless(False) # HEADFUL for Cloudflare
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        
        def handle_cloudflare(page):
            sys.stderr.write("Checking for Cloudflare...\n")
            for _ in range(10):
                title = page.title.lower()
                sys.stderr.write(f"Page Title: {page.title}\n")
                if "just a moment" not in title and "security challenge" not in title:
                    sys.stderr.write("Cloudflare cleared (title check).\n")
                    return True
                
                if page.ele('@id=turnstile-wrapper', timeout=1):
                    sys.stderr.write("Waiting for Turnstile...\n")
                    time.sleep(2)
                    continue
                    
                time.sleep(2)
            return False
        
        url = 'https://www.hendrysheriff.org/inmateSearch'
        sys.stderr.write(f"Navigating to {url}\n")
        page.get(url, timeout=30)
        handle_cloudflare(page)
        
        # Sort by Date Desc if possible
        try:
            sort_select = page.ele('css:select#sort', timeout=5)
            if sort_select:
                try: sort_select.select.by_value('dateDesc')
                except: sort_select.select.by_index(1)
                time.sleep(2)
        except: pass
        
        # Load all "Read More" buttons to find cards
        read_more_buttons = page.eles('text:Read More')
        sys.stderr.write(f"Found {len(read_more_buttons)} Read More buttons\n")
        
        # Track IDs seen in THIS session to avoid duplicates on the page itself
        session_scraped_ids = set()

        for i, button in enumerate(read_more_buttons):
            try:
                sys.stderr.write(f"Processing button {i+1}/{len(read_more_buttons)}...\n")
                
                try:
                    button.run_js('this.scrollIntoView({block: "center"})')
                    time.sleep(0.5)
                    button.run_js('this.click()')
                    time.sleep(1)
                except Exception as click_err:
                    sys.stderr.write(f"  Click failed: {click_err}, skipping...\n")
                    continue
                
                # Find parent card
                card = None
                current = button
                for level in range(1, 8):
                    try:
                        current = current.parent()
                        if len(current.eles('tag:*')) > 5:
                            card = current
                            break
                    except: break
                
                if not card: card = page.ele('tag:body')
                
                card_text = card.text
                data = {}
                
                # Booking Number
                inmate_match = re.search(r'Inmate ID:\s*([A-Z0-9]+)', card_text)
                booking_number = None
                if inmate_match:
                    booking_number = inmate_match.group(1)
                    data['Booking_Number'] = booking_number
                
                # CHECK DUPLICATES (Processed previously OR in this session)
                if booking_number:
                    if booking_number in processed_ids:
                        sys.stderr.write(f"  ⚠️  Skipping {booking_number} (Already scraped previously)\n")
                        # Collapse
                        try:
                            read_less = card.ele('text:Read Less')
                            if read_less: read_less.click()
                        except: pass
                        continue
                    
                    if booking_number in session_scraped_ids:
                        sys.stderr.write(f"  ⚠️  Skipping {booking_number} (Duplicate on page)\n")
                        try:
                            read_less = card.ele('text:Read Less')
                            if read_less: read_less.click()
                        except: pass
                        continue
                        
                name_elem = card.ele('tag:h3') or card.ele('tag:h4') or card.ele('tag:h2')
                if name_elem:
                    full_name = name_elem.text.strip()
                    data['Full_Name'] = full_name
                    if ',' in full_name:
                        parts = full_name.split(',', 1)
                        data['Last_Name'] = parts[0].strip()
                        data['First_Name'] = parts[1].strip()
                
                booked_match = re.search(r'Booked Date:\s*([^\n]+)', card_text)
                if booked_match: data['Booking_Date'] = booked_match.group(1).strip()
                
                gender_match = re.search(r'Gender:\s*([MF])', card_text)
                if gender_match: data['Sex'] = gender_match.group(1)
                
                race_match = re.search(r'Race:\s*([A-Z])', card_text)
                if race_match: data['Race'] = race_match.group(1)
                
                height_match = re.search(r'Height:\s*([^\n]+)', card_text)
                if height_match: data['Height'] = height_match.group(1).strip()
                
                weight_match = re.search(r'Weight:\s*([^\n]+)', card_text)
                if weight_match: data['Weight'] = weight_match.group(1).strip()
                
                address_match = re.search(r'Main Address:\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|Height:|Weight:|$)', card_text, re.DOTALL)
                if address_match: data['Address'] = address_match.group(1).strip().replace('\n', ' ')
                
                multiplier_charges = []
                total_bond = 0.0
                charge_pattern = r'Charge Code:\s*([^\n]+)\s*Charge Description:\s*([^\n]+)(?:\s*Bond Amount:\s*\$?([\d.,]+))?'
                charge_matches = re.finditer(charge_pattern, card_text)
                
                for match in charge_matches:
                    desc = match.group(2).strip()
                    bond_str = match.group(3)
                    clean_desc = clean_charge_text(desc)
                    if clean_desc: multiplier_charges.append(clean_desc)
                    if bond_str:
                        try: total_bond += float(bond_str.replace(',', '').replace('$', ''))
                        except: pass
                
                if multiplier_charges: data['Charges'] = ' | '.join(multiplier_charges)
                data['Bond_Amount'] = str(total_bond)
                
                img = card.ele('tag:img')
                if img:
                    src = img.attr('src')
                    if src and ('mug' in src.lower() or 'photo' in src.lower() or 'inmate' in src.lower()):
                        if not src.startswith('http'):
                            src = 'https://www.hendrysheriff.org' + (src if src.startswith('/') else '/' + src)
                        data['Mugshot_URL'] = src
                
                data['Detail_URL'] = url # One page app
                
                if len(data) > 2:
                    records.append(data)
                    # Mark as seen
                    if booking_number:
                        session_scraped_ids.add(booking_number)
                        
                    # AUTO SAVE
                    with open(progress_file, 'a') as f:
                        f.write(json.dumps(data) + '\n')
                    sys.stderr.write(f"   ✅ Saved {data.get('Full_Name')} (Total New: {len(records)})\n")
                
                # Collapse
                try:
                    read_less = card.ele('text:Read Less')
                    if read_less: 
                        read_less.click()
                        time.sleep(0.5)
                except: pass
                
            except Exception as e:
                sys.stderr.write(f"  Error processing card {i+1}: {str(e)}\n")
                continue
        
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")
    
    # Final Output
    final_records = []
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            # We also deduplicate final output just in case
            seen_final = set()
            for line in f:
                if line.strip():
                    try: 
                        r = json.loads(line)
                        bn = r.get('Booking_Number')
                        if bn and bn not in seen_final:
                            final_records.append(r)
                            seen_final.add(bn)
                    except: pass
    else:
        final_records = records
        
    print(json.dumps(final_records))

if __name__ == "__main__":
    scrape_hendry()
