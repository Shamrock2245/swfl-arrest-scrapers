import sys
import json
import time
import re
import argparse
from datetime import datetime
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

def scrape_sarasota(arrest_date):
    records = []
    
    try:
        co = ChromiumOptions()
        co.set_browser_path('/usr/bin/chromium-browser')
        co.auto_port() # Use a random port
        co.set_argument('--ignore-certificate-errors')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--headless=new')
        
        page = ChromiumPage(co)
        
        # 1. Navigate to the iframe URL directly as it's the app
        url = 'https://cms.revize.com/revize/apps/sarasota/index.php'
        page.get(url)
        
        # Custom CF Handler
        def handle_cloudflare(page):
            sys.stderr.write("Checking for Cloudflare...\n")
            # Wait loop
            for _ in range(10):
                title = page.title.lower()
                sys.stderr.write(f"Page Title: {page.title}\n")
                if "just a moment" not in title and "security challenge" not in title:
                    sys.stderr.write("Cloudflare cleared (title check).\n")
                    return True
                
                # Check for specifics
                if page.ele('@id=turnstile-wrapper', timeout=1):
                    sys.stderr.write("Waiting for Turnstile...\n")
                    time.sleep(2)
                    continue
                    
                time.sleep(2)
            return False

        handle_cloudflare(page)
        
        # Verify we are on the real page
        if not page.wait.ele_displayed('tag:body', timeout=10):
             sys.stderr.write("Body not displayed after CF check.\n")

        # Save HTML for debugging
        with open('sarasota_debug.html', 'w', encoding='utf-8') as f:
            f.write(page.html)
             
        # 2. Search by date
        # Click "Arrest Date" tab to be sure
        tab = page.ele('text:Arrest Date', timeout=5)
        if tab:
            tab.click()
            time.sleep(1)

        # Input: Look for placeholder "mm/dd/yyyy" as seen in screenshot
        date_input = page.ele('@placeholder=mm/dd/yyyy') or \
                     page.ele('css:input[name="arrest_date"]') or \
                     page.ele('@name=arrest_date') or \
                     page.ele('css:input.form-control') # Generic fallback
                     
        if not date_input:
             sys.stderr.write("Could not find arrest_date input. Saved HTML to sarasota_debug.html\n")
             return

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
             return
        
        # Wait for results
        # Look for links to viewInmate.php OR "No records found" message
        if not page.wait.ele_displayed('css:a[href*="viewInmate.php"]', timeout=30):
             sys.stderr.write("No results found after wait.\n")
        
        # 3. Extract URLs
        links = page.eles('css:a[href*="viewInmate.php"]')
        detail_urls = []
        base_url = 'https://cms.revize.com/revize/apps/sarasota/'
        
        for link in links:
            href = link.attr('href')
            if href:
                if href.startswith('http'):
                    detail_urls.append(href)
                else:
                    detail_urls.append(base_url + href)
                    
        detail_urls = list(set(detail_urls))
        # Cap
        detail_urls = detail_urls[:100]
        
        # 4. Visit details
        for detail_url in detail_urls:
            try:
                page.get(detail_url)
                
                # Check CF on detail page too!
                handle_cloudflare(page)
                
                if page.wait.ele_displayed('tag:body', timeout=15):
                    data = {}
                    data['Detail_URL'] = detail_url
                    
                    # Wait for load
                    time.sleep(1) # Give JS a moment to replace elements if needed
                    
                    # 1. NAME Extraction (H1)
                    # Content: "BRADY,PATRICK JOHN                  Print "
                    h1 = page.ele('css:h1.page-title')
                    if h1:
                        raw_name = h1.text.split('Print')[0].strip()
                        data['Full_Name'] = raw_name
                        # Try to split last, first
                        if ',' in raw_name:
                            parts = raw_name.split(',', 1)
                            data['Last_Name'] = parts[0].strip()
                            data['First_Name'] = parts[1].strip()

                    # 2. Personal Info (Div Rows)
                    # Look for divs with "text-right" class which contain labels with ":"
                    label_divs = page.eles('css:div.text-right')
                    for ld in label_divs:
                        key = ld.text.replace(':', '').strip()
                        # Value is in the next sibling col-sm-7
                        # Structure: col-sm-5 (key) -> sibling col-sm-7 (val)
                        # We can try getting the parent row's text or traversing
                        try:
                            parent_row = ld.parent()
                            # The text of the row should be "Key: Value"
                            # Let's try to get specific value div if possible
                            val_div = ld.next()
                            if val_div:
                                val = val_div.text.strip()
                                data[key] = val
                                # Map common variations to standard fields
                                if key.lower() in ['arrest date', 'arrested', 'date arrested']:
                                    data['Arrest_Date'] = val
                        except:
                            pass

                    # 3. Charges (Table #data-table)
                    # Headers: Booking Number, Offense Description, Counts, Arraign Date, Bond Amount...
                    # We want to capture these into a list or specific fields
                    # The schema expects "Charges", "Bond_Amount".
                    # If multiple charges, we join them?
                    
                    charges = []
                    total_bond = 0.0
                    
                    rows = page.eles('css:#data-table tr')
                    for row in rows:
                        cells = row.eles('tag:td')
                        if len(cells) > 4:
                            # 0: Booking Number, 1: Offense, 3: Arraign, 4: Bond
                            # Data Mapping based on HTML
                            if 'Booking_Number' not in data:
                                data['Booking_Number'] = cells[0].text.strip()
                            
                            charge_desc = cells[1].text.strip()
                            if charge_desc:
                                # Clean the charge text to extract only the description
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
                    
                    # Use the search arrest_date as Arrest_Date if not found in personal info
                    if 'Arrest_Date' not in data and arrest_date:
                        data['Arrest_Date'] = arrest_date
                                
                    if charges:
                        data['Charges'] = " | ".join(charges)
                    data['Bond_Amount'] = str(total_bond)

                    # 4. Mugshot (Base64 or URL)
                    img = page.ele('css:.mug img')
                    if img:
                        src = img.attr('src')
                        data['Mugshot_URL'] = src # Will be base64, handled by normalizer?
                        
                    sys.stderr.write(f"Scraped {len(data)} keys from {detail_url}\n") 
                    
                    # Debug print keys found
                    if len(data) > 0:
                         sys.stderr.write(f"Found: {list(data.keys())}\n")

                    if 'Booking_Number' in data or 'Full_Name' in data:
                        records.append(data)
                    else:
                        sys.stderr.write(f"Skipping {detail_url}, missing critical data.\n")
                        
                else:
                    sys.stderr.write(f"Table not found on {detail_url}\n")
                    with open('sarasota_detail_fail.html', 'w', encoding='utf-8') as f:
                        f.write(page.html)

                time.sleep(1)
            except Exception as e:
                sys.stderr.write(f"Error processing {detail_url}: {str(e)}\n")
                continue
                
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")

    print(json.dumps(records))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="Arrest date MM/DD/YYYY")
    args = parser.parse_args()
    
    scrape_sarasota(args.date)
