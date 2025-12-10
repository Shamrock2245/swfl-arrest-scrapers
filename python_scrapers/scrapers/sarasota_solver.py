import sys
import json
import time
import re
import os
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

def clean_charge_text(raw_charge):
    """
    Clean charge text to extract only the human-readable description.
    Input: "New Charge: 843.02 - Resisting Officer Without Violence (LEV:M DEG:F 3143) (Principal - P)"
    Output: "Resisting Officer Without Violence"
    """
    if not raw_charge:
        return ''
    
    # Remove "New Charge:" or "Weekender:" prefix
    text = re.sub(r'^(New Charge:|Weekender:)\s*', '', raw_charge, flags=re.IGNORECASE)
    
    # Extract the description part (between statute and parentheses)
    # Pattern: [statute] - [Description] (LEV:...)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        return description
    
    # Fallback: if no statute pattern, try to get text before first parenthesis
    if '(' in text:
        description = text.split('(')[0].strip()
        # Remove leading statute if present
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    
    return text.strip()

def scrape_sarasota(days_back=21):
    """
    Scrape Sarasota County with date range support and RESUME capability
    """
    records = []
    progress_file = 'sarasota_progress.jsonl'
    
    # Load existing progress to skip duplicates
    processed_ids = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            if 'Detail_URL' in rec:
                                processed_ids.add(rec['Detail_URL'])
                        except: pass
        except Exception as e:
            sys.stderr.write(f"Warning: Could not read progress file: {e}\n")
            
    sys.stderr.write(f"ℹ️  Found {len(processed_ids)} previously scraped records. Resuming...\n")
    
    try:
        co = ChromiumOptions()
        # co.set_browser_path('/usr/bin/chromium-browser')
        
        # HEADFUL mode for Cloudflare
        co.headless(False)
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        # co.set_argument('--disable-gpu') 
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        
        # Custom CF Handler
        def handle_cloudflare(page):
            sys.stderr.write("Checking for Cloudflare...\n")
            # Wait loop
            for i in range(15):
                title = page.title.lower()
                sys.stderr.write(f"[{i+1}/15] Page Title: {page.title}\n")
                
                if "just a moment" not in title and "security challenge" not in title and "attention" not in title:
                    sys.stderr.write("Cloudflare cleared (title check).\n")
                    return True
                
                # Check for specifics
                if page.ele('@id=turnstile-wrapper', timeout=1):
                    sys.stderr.write("Waiting for Turnstile...\n")
                
                time.sleep(2)
            return False

        # Generate date range (today back to days_back)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        sys.stderr.write(f"🚀 Starting Sarasota County scraper\n")
        sys.stderr.write(f"📅 Date range: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}\n\n")
        
        # We'll search by date, one day at a time
        current_date = start_date
        all_detail_urls = set()
        
        while current_date <= end_date:
            arrest_date = current_date.strftime('%m/%d/%Y')
            sys.stderr.write(f"\n📅 Searching for arrests on {arrest_date}...\n")
            
            # 1. Navigate to the iframe URL directly
            url = 'https://cms.revize.com/revize/apps/sarasota/index.php'
            page.get(url)
            
            handle_cloudflare(page)
            
            # Verify we are on the real page
            if not page.wait.ele_displayed('tag:body', timeout=10):
                sys.stderr.write("Body not displayed after CF check.\n")
                current_date += timedelta(days=1)
                continue

            # 2. Search by date
            # Click "Arrest Date" tab to be sure
            try:
                tab = page.ele('text:Arrest Date', timeout=5)
                if tab:
                    tab.click()
                    time.sleep(1)
            except:
                pass

            # Input: Look for placeholder "mm/dd/yyyy"
            date_input = page.ele('@placeholder=mm/dd/yyyy') or \
                         page.ele('css:input[name="arrest_date"]') or \
                         page.ele('@name=arrest_date') or \
                         page.ele('css:input.form-control')
                         
            if not date_input:
                sys.stderr.write("Could not find arrest_date input. Saved HTML to sarasota_debug.html\n")
                current_date += timedelta(days=1)
                continue

            # Clear and type
            date_input.clear()
            date_input.input(arrest_date)
            time.sleep(1)
            
            # Click Search - Green button saying "SEARCH"
            search_btn = page.ele('text:SEARCH') or page.ele('css:button.btn-success') or page.ele('@type=submit')
            if search_btn:
                search_btn.click()
            else:
                sys.stderr.write("Could not find SEARCH button.\n")
                current_date += timedelta(days=1)
                continue
            
            # Wait for results
            time.sleep(3)
            
            # 3. Extract URLs
            links = page.eles('css:a[href*="viewInmate.php"]')
            base_url = 'https://cms.revize.com/revize/apps/sarasota/'
            
            date_urls = []
            for link in links:
                href = link.attr('href')
                if href:
                    if href.startswith('http'):
                        date_urls.append(href)
                    else:
                        date_urls.append(base_url + href)
            
            date_urls = list(set(date_urls))
            sys.stderr.write(f"   📋 Found {len(date_urls)} inmates for {arrest_date}\n")
            all_detail_urls.update(date_urls)
            
            # Move to next date
            current_date += timedelta(days=1)
            time.sleep(2)  # Be nice to the server
        
        sys.stderr.write(f"\n📊 Total unique inmates found: {len(all_detail_urls)}\n")
        
        # Convert set to list for processing
        detail_urls = list(all_detail_urls)
        
        # FILTER: Removed processed
        original_count = len(detail_urls)
        detail_urls = [u for u in detail_urls if u not in processed_ids]
        skipped_count = original_count - len(detail_urls)
        
        if skipped_count > 0:
             sys.stderr.write(f"📉 Skipping {skipped_count} already scraped records. {len(detail_urls)} remaining.\n")
        
        # 4. Visit details
        for i, detail_url in enumerate(detail_urls):
            try:
                sys.stderr.write(f"\n🔍 [{i+1}/{len(detail_urls)}] Processing {detail_url}\n")
                page.get(detail_url)
                
                # Check CF on detail page too!
                handle_cloudflare(page)
                
                if page.wait.ele_displayed('tag:body', timeout=15):
                    data = {}
                    data['Detail_URL'] = detail_url
                    
                    # Wait for load
                    time.sleep(1)
                    
                    # 1. NAME Extraction (H1)
                    h1 = page.ele('css:h1.page-title')
                    if h1:
                        raw_name = h1.text.split('Print')[0].strip()
                        data['Full_Name'] = raw_name
                        # Try to split last, first
                        if ',' in raw_name:
                            parts = raw_name.split(',', 1)
                            data['Last_Name'] = parts[0].strip()
                            data['First_Name'] = parts[1].strip()
                    else:
                         # Fallback for name
                         pass

                    # 2. Personal Info (Div Rows)
                    label_divs = page.eles('css:div.text-right')
                    for ld in label_divs:
                        key = ld.text.replace(':', '').strip()
                        try:
                            val_div = ld.next()
                            if val_div:
                                val = val_div.text.strip()
                                # Normalize Keys
                                if key == 'DOB': data['DOB'] = val
                                elif key == 'Race': data['Race'] = val
                                elif key == 'Sex': data['Sex'] = val
                                elif key == 'Height': data['Height'] = val
                                elif key == 'Weight': data['Weight'] = val
                                elif key == 'Address': data['Address'] = val
                                elif key == 'City': data['City'] = val
                                elif key == 'State': data['State'] = val
                                elif key == 'Zip Code': data['ZIP'] = val
                                # Map common variations to standard fields
                                if key.lower() in ['arrest date', 'arrested', 'date arrested']:
                                    data['Arrest_Date'] = val
                        except:
                            pass

                    # 3. Charges (Table #data-table)
                    charges = []
                    total_bond = 0.0
                    
                    rows = page.eles('css:#data-table tr')
                    for row in rows:
                        cells = row.eles('tag:td')
                        if len(cells) > 4:
                            # 0: Booking Number, 1: Offense, 3: Arraign, 4: Bond
                            if 'Booking_Number' not in data:
                                data['Booking_Number'] = cells[0].text.strip()
                            
                            charge_desc = cells[1].text.strip()
                            if charge_desc:
                                clean_desc = clean_charge_text(charge_desc)
                                if clean_desc:
                                    charges.append(clean_desc)
                            
                            bond_str = cells[4].text.replace('$','').replace(',','').strip()
                            try:
                                if bond_str:
                                    total_bond += float(bond_str)
                            except:
                                pass
                            
                            # Intake Date (Booking Date) - Index 6
                            if len(cells) > 6 and 'Booking_Date' not in data:
                                intake_dt = cells[6].text.strip()
                                if intake_dt:
                                    data['Booking_Date'] = intake_dt
                                
                    if charges:
                        data['Charges'] = " | ".join(charges)
                    data['Bond_Amount'] = str(total_bond)

                    # 4. Mugshot (Base64 or URL)
                    img = page.ele('css:.mug img')
                    if img:
                        src = img.attr('src')
                        data['Mugshot_URL'] = src
                        
                    sys.stderr.write(f"Scraped {len(data)} keys from {detail_url}\n") 
                    
                    # Log Name
                    name = data.get('Full_Name', 'Unknown')
                    sys.stderr.write(f"   👤 Name: {name}\n")

                    if 'Booking_Number' in data or 'Full_Name' in data:
                        records.append(data)
                        
                        # IMMEDIATE SAVE to JSONL
                        with open(progress_file, 'a') as f:
                            f.write(json.dumps(data) + '\n')
                            
                        sys.stderr.write(f"   ✅ Added & Saved record (Total New: {len(records)})\n")
                    else:
                        sys.stderr.write(f"Skipping {detail_url}, missing critical data.\n")
                        
                else:
                    sys.stderr.write(f"Body not found on {detail_url}\n")
                    with open('sarasota_detail_fail.html', 'w', encoding='utf-8') as f:
                        f.write(page.html)

                time.sleep(1)
            except Exception as e:
                sys.stderr.write(f"Error processing {detail_url}: {str(e)}\n")
                continue
        
        sys.stderr.write(f"\n📊 Total new records collected: {len(records)}\n")
                
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")

    # Combine all records for final output
    final_records = []
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        final_records.append(json.loads(line))
                    except: pass
    else:
        final_records = records

    print(json.dumps(final_records))

if __name__ == "__main__":
    # Parse command line arguments
    days_back = 21  # Default 3 weeks
    
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except:
            pass
    
    sys.stderr.write(f"🚀 Starting Sarasota County scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n\n")
    
    scrape_sarasota(days_back)
