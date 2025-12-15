import sys
import json
import time
import re
import os
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stderr.write("=== Hendry Solver Starting ===\n")
sys.stderr.flush()


def clean_charge_text(raw_charge):
    """Clean charge text to extract only the human-readable description."""
    if not raw_charge:
        return ''
    
    text = re.sub(r'^(New Charge:|Weekender:|Charge Description:)\s*', '', raw_charge, flags=re.IGNORECASE)
    
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    
    return text.strip()


def extract_detail_data(page):
    """Extract all data from an inmate detail page (after SPA navigation)."""
    data = {}
    body_text = page.ele('tag:body').text if page.ele('tag:body') else ''
    
    # Get name from h2 in mainCard
    main_card = page.ele('css:#mainCard')
    if main_card:
        h2 = main_card.ele('tag:h2')
        if h2:
            full_name = h2.text.strip()
            data['Full_Name'] = full_name
            if ',' in full_name:
                parts = full_name.split(',', 1)
                data['Last_Name'] = parts[0].strip()
                data['First_Name'] = parts[1].strip()
    
    # Extract posted date
    posted_match = re.search(r'Posted on\s+([^<\n]+(?:AM|PM)\s+[A-Z]+)', body_text)
    if posted_match:
        data['Booking_Date'] = posted_match.group(1).strip()
    
    # Extract from body text
    inmate_id_match = re.search(r'Inmate ID:\s*([A-Z0-9]+)', body_text)
    if inmate_id_match:
        data['Booking_Number'] = inmate_id_match.group(1)
    
    height_match = re.search(r'Height:\s*([^\n]+)', body_text)
    if height_match:
        val = height_match.group(1).strip()
        if 'Weight' not in val:
            data['Height'] = val
    
    weight_match = re.search(r'Weight:\s*(\d+\s*lbs)', body_text)
    if weight_match:
        data['Weight'] = weight_match.group(1)
    
    gender_match = re.search(r'Gender:\s*([MF])', body_text)
    if gender_match:
        data['Sex'] = gender_match.group(1)
    
    race_match = re.search(r'Race:\s*([A-Z])', body_text)
    if race_match:
        data['Race'] = race_match.group(1)
    
    age_match = re.search(r'Age:\s*(\d+)', body_text)
    if age_match:
        data['Age'] = age_match.group(1)
    
    # Address
    addr_match = re.search(r'Main Address:\s*\n?([^\n]+)', body_text)
    if addr_match:
        addr_val = addr_match.group(1).strip()
        if 'Currently Unavailable' not in addr_val and len(addr_val) > 3:
            data['Address'] = addr_val
    
    # Custody status
    custody_match = re.search(r'Custody Status:\s*([A-Z]+)', body_text)
    if custody_match:
        data['Status'] = custody_match.group(1)
    
    # Booked date
    booked_match = re.search(r'Booked Date:\s*([\d/]+\s+[\d:]+\s+[A-Z]+)', body_text)
    if booked_match:
        data['Arrest_Date'] = booked_match.group(1).strip()
    
    # Get mugshot
    img = page.ele('css:#mainCard img.chakra-image')
    if img:
        src = img.attr('src')
        if src and 'missing-image' not in src:
            data['Mugshot_URL'] = src
    
    # Extract charges - look for pattern after "Charges:" section
    charges = []
    total_bond = 0.0
    
    # Find all Charge Code entries
    charge_codes = re.findall(r'Charge Code:\s*([^\n]+)', body_text)
    bond_amounts = re.findall(r'Bond Amount:\s*\$?([\d,.]+)', body_text)
    
    for i, code in enumerate(charge_codes):
        code = code.strip()
        if code:
            # Use the charge code as the charge (description not always present)
            charges.append(code)
        
        # Get corresponding bond
        if i < len(bond_amounts):
            try:
                bond_val = float(bond_amounts[i].replace(',', ''))
                total_bond += bond_val
            except:
                pass
    
    if charges:
        data['Charges'] = ' | '.join(charges)
    
    data['Bond_Amount'] = str(total_bond) if total_bond > 0 else '0'
    data['Detail_URL'] = page.url
    
    return data


def scrape_hendry(max_pages=5, max_records=50):
    """Scrape Hendry County inmate roster with SPA navigation for charges."""
    records = []
    
    max_pages = int(os.getenv('HENDRY_MAX_PAGES', max_pages))
    max_records = int(os.getenv('HENDRY_MAX_RECORDS', max_records))
    
    try:
        co = ChromiumOptions()
        co.auto_port()
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        
        def handle_cloudflare(page, max_wait=20):
            sys.stderr.write("Checking for Cloudflare...\n")
            start = time.time()
            while time.time() - start < max_wait:
                title = page.title.lower()
                if "just a moment" not in title and "security challenge" not in title:
                    sys.stderr.write("Cloudflare cleared.\n")
                    return True
                time.sleep(1)
            return False
        
        roster_url = 'https://www.hendrysheriff.org/inmateSearch'
        sys.stderr.write(f"Navigating to {roster_url}\n")
        
        try:
            page.get(roster_url, timeout=30)
            sys.stderr.write("Page loaded successfully\n")
        except Exception as e:
            sys.stderr.write(f"Error loading page: {e}\n")
            print(json.dumps([]))
            return
        
        handle_cloudflare(page)
        time.sleep(2)
        
        # Set sort order to newest first
        sys.stderr.write("Setting sort order to newest first...\n")
        try:
            sort_select = page.ele('css:select#sort', timeout=5)
            if sort_select:
                sort_select.select.by_value('dateDesc')
                sys.stderr.write("Sort order set to Date (Newest - Oldest)\n")
                time.sleep(2)
        except Exception as e:
            sys.stderr.write(f"Could not set sort order: {e}\n")
        
        current_page = 1
        
        while True:
            sys.stderr.write(f"\n--- Processing page {current_page} ---\n")
            time.sleep(1.5)
            
            # Find all inmate cards and their detail links
            cards = page.eles('css:.chakra-card')
            sys.stderr.write(f"Found {len(cards)} inmate cards\n")
            
            if len(cards) == 0:
                break
            
            # Collect detail URLs first (before navigating away)
            detail_urls = []
            for card in cards:
                link = card.ele('css:a[href*="/inmateSearch/"]')
                if link:
                    href = link.attr('href')
                    if href and re.search(r'/inmateSearch/\d+', href):
                        if not href.startswith('http'):
                            href = 'https://www.hendrysheriff.org' + href
                        detail_urls.append(href)
            
            sys.stderr.write(f"Collected {len(detail_urls)} detail URLs\n")
            
            # Visit each detail page by clicking the link (SPA navigation)
            for i, card in enumerate(cards):
                if max_records > 0 and len(records) >= max_records:
                    sys.stderr.write(f"Reached max_records limit ({max_records})\n")
                    break
                
                try:
                    # Get the detail link
                    link = card.ele('css:a[href*="/inmateSearch/"]')
                    if not link:
                        continue
                    
                    detail_url = link.attr('href')
                    if not detail_url or not re.search(r'/inmateSearch/\d+', detail_url):
                        continue
                    
                    sys.stderr.write(f"  [{len(records)+1}] Clicking link for detail page\n")
                    
                    # Click the link (triggers SPA navigation)
                    link.click()
                    time.sleep(2)  # Wait for SPA to update
                    
                    # Extract data from detail page
                    data = extract_detail_data(page)
                    
                    if data.get('Full_Name') and data.get('Booking_Number'):
                        records.append(data)
                        charges_preview = (data.get('Charges', 'No charges'))[:40]
                        bond = data.get('Bond_Amount', '0')
                        sys.stderr.write(f"      ✅ {data['Full_Name']} | ${bond} | {charges_preview}\n")
                    else:
                        sys.stderr.write(f"      ⚠️ Incomplete data\n")
                    
                    # Navigate back to roster
                    page.get(roster_url, timeout=30)
                    time.sleep(2)
                    
                    # Re-apply sort order
                    try:
                        sort_select = page.ele('css:select#sort', timeout=3)
                        if sort_select:
                            sort_select.select.by_value('dateDesc')
                            time.sleep(1)
                    except:
                        pass
                    
                except Exception as e:
                    sys.stderr.write(f"      Error: {str(e)}\n")
                    # Try to get back to roster
                    try:
                        page.get(roster_url, timeout=30)
                        time.sleep(2)
                    except:
                        pass
                    continue
            
            if max_records > 0 and len(records) >= max_records:
                break
            
            if max_pages > 0 and current_page >= max_pages:
                sys.stderr.write(f"Reached max_pages limit ({max_pages})\n")
                break
            
            # Navigate back to roster for next page
            sys.stderr.write(f"  Returning to roster...\n")
            page.get(roster_url, timeout=30)
            time.sleep(2)
            
            # Re-set sort order (SPA might reset it)
            try:
                sort_select = page.ele('css:select#sort', timeout=5)
                if sort_select:
                    sort_select.select.by_value('dateDesc')
                    time.sleep(1)
            except:
                pass
            
            # Navigate to next page
            try:
                # Find current page info
                page_info = page.ele('css:button[aria-label*="Page"]')
                if page_info:
                    page_text = page_info.text
                    match = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', page_text)
                    if match:
                        curr = int(match.group(1))
                        total = int(match.group(2))
                        if curr >= total:
                            break
                
                # Click to desired page
                for _ in range(current_page):
                    next_button = page.ele('css:button[aria-label="Page Right"]')
                    if next_button:
                        next_button.click()
                        time.sleep(1.5)
                    else:
                        break
                
                current_page += 1
                
            except Exception as e:
                sys.stderr.write(f"Pagination error: {e}\n")
                break
        
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")
    
    sys.stderr.write(f"\nTotal records scraped: {len(records)}\n")
    print(json.dumps(records))


if __name__ == "__main__":
    scrape_hendry()
