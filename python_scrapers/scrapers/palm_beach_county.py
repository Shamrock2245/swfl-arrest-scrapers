import sys
import json
import time
import re
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

def scrape_palm_beach(days_back=1):
    records = []
    
    # 1. Initialize Browser
    co = ChromiumOptions()
    co.auto_port()
    co.headless(True)  # Run headless for GitHub Actions
    
    # Add Linux-specific options for GitHub Actions
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-software-rasterizer')
    co.set_argument('--disable-extensions')
    
    # Optional: set user agent or other headers if needed
    
    page = ChromiumPage(co)
    
    try:
        # Initial navigation to check for captcha
        sys.stderr.write("Navigating to PBSO Blotter for initial check...\n")
        page.get('https://www3.pbso.org/blotter/index.cfm')
        
        # 2. Handle Entry & Captcha
        if not page.wait.ele_displayed('tag:body', timeout=15):
             sys.stderr.write("Error: Page did not load.\n")
             return []

        # Check for hCaptcha
        if page.ele('tag:iframe[src*="hcaptcha.com"]'):
            sys.stderr.write("⚠️  hCaptcha detected. Please solve it manually in the browser window.\n")
            sys.stderr.write("Waiting 30 seconds for manual solution...\n")
            # We wait for the user to solve it. 
            # Usually solving it enables the form or submits it?
            # Let's wait until the 'Search' button is interactable or the iframe is gone?
            time.sleep(30)
            
        
        # Loop for backfill (Oldest to Newest)
        # range(days_back) gives 0..4 (if 5). 0 is today, 4 is 4 days ago.
        # We want to start at 4 days ago (oldest) and go to 0 (today).
        for i in range(days_back - 1, -1, -1):
            try:
                # Calculate date: Today minus i days
                target_date_obj = datetime.now() - timedelta(days=i)
                target_date = target_date_obj.strftime('%m/%d/%Y')
                
                sys.stderr.write(f"\n--- Starting Search for {target_date} (Day {i+1}/{days_back}) ---\n")
                
                # Navigate specifically to search page each time to reset
                # Only if we aren't already there? 
                # Better to just go there to be safe.
                if i > 0 or page.url != 'https://www3.pbso.org/blotter/index.cfm':
                    page.get('https://www3.pbso.org/blotter/index.cfm')
                    time.sleep(2)

                # 3. Perform Search
                sys.stderr.write(f"Setting search date: {target_date}\n")
                
                # Wait for inputs
                if page.wait.ele_displayed('#start_date', timeout=10):
                    # Clear and input
                    page.ele('#start_date').clear()
                    page.ele('#start_date').input(target_date)
                    
                    # page.ele('#end_date').input(target_date) # Assuming end date defaults correctly or is single day
                    
                    # Click Search
                    # Finding the button - Reusing logic from POC
                    btns = page.eles('tag:button')
                    submit_btn = None
                    for b in btns:
                        if 'search' in b.text.lower():
                            submit_btn = b
                            break
                    
                    if not submit_btn:
                        submit_btn = page.ele('css:input[type=submit]')
                    
                    if submit_btn:
                        sys.stderr.write("Clicking Search...\n")
                        submit_btn.click()
                        
                        # Wait for navigation
                        time.sleep(5)
                        
            
                # Loop for pagination
                page_num = 1
                while True:
                    sys.stderr.write(f"Scraping {target_date} - Page {page_num}\n")
                    
                    # 4. Parse Results List
                    # Logic: Extract everything from the list items without visiting details
                    
                    # Wait for results to be visible
                    if not page.wait.ele_displayed('css:div[id^="allresults_"]', timeout=10):
                        sys.stderr.write(f"No results found for {target_date} (Page {page_num}).\n")
                        break # Stop pagination for this date

                    results = page.eles('css:div[id^="allresults_"]')
                    sys.stderr.write(f"Found {len(results)} records on Page {page_num}.\n")
                    
                    for row in results:
                        try:
                            # Helper to get value from strong label relative to this row
                            def get_row_val(r_ele, label):
                                try:
                                    # Use relative xpath from the row element
                                    # .//strong[contains(text(), "Label")]
                                    strong = r_ele.ele(f'xpath:.//strong[contains(text(), "{label}")]')
                                    if strong:
                                        parent = strong.parent()
                                        # Text is "Label: Value"
                                        # Remove label and strong text
                                        val = parent.text.replace(label, '').replace(strong.text, '').strip()
                                        return val
                                except:
                                    pass
                                return ''

                            # Extract Fields
                            full_name = get_row_val(row, "Name:")
                            race = get_row_val(row, "Race:")
                            sex = get_row_val(row, "Gender:")
                            facility = get_row_val(row, "Facility:")
                            jacket_num = get_row_val(row, "Jacket Number:")
                            booking_dt_str = get_row_val(row, "Booking Date/Time:")
                            release_date_str = get_row_val(row, "Release Date:")
                            
                            # Booking Number is usually a link
                            booking_num = ""
                            link_ele = row.ele('css:a[onclick^="loaddetail"]')
                            if link_ele:
                                booking_num = link_ele.text.strip()
                            else:
                                # Fallback
                                booking_num = get_row_val(row, "Booking Number:")
                            
                            # Mugshot
                            mug_url = ""
                            img = row.ele('css:img.img-zoom')
                            if img:
                                mug_url = img.attr('src')
                                
                            # Parsing Name
                            first_name, middle_name, last_name = "", "", ""
                            if full_name:
                                if ',' in full_name:
                                    parts = full_name.split(',', 1)
                                    last_name = parts[0].strip()
                                    remainder = parts[1].strip()
                                    if ' ' in remainder:
                                         r_parts = remainder.split(' ', 1)
                                         first_name = r_parts[0].strip()
                                         middle_name = r_parts[1].strip()
                                    else:
                                         first_name = remainder
                                else:
                                    last_name = full_name
                                    
                            # Parsing Dates
                            booking_date, booking_time = "", ""
                            if booking_dt_str:
                                try:
                                    dt = datetime.strptime(booking_dt_str, '%m/%d/%Y %H:%M')
                                    booking_date = dt.strftime('%Y-%m-%d')
                                    booking_time = dt.strftime('%H:%M:00')
                                except:
                                    booking_date = booking_dt_str
                                    
                            status = "In Custody"
                            if release_date_str and "N/A" not in release_date_str and release_date_str.strip() != "":
                                status = "Released"
                                
                            # Address - Not usually on list view? 
                            # Screenshot doesn't show address. Leave empty.
                            
                            # Charges & Bond
                            charges = []
                            total_bond = 0.0
                            
                            # Charges are often in a sub-table or rows below the main info
                            # Within 'row', look for the charge rows.
                            # Based on HTML structure, there's usually a container "blotterdetails"? 
                            # No, "blotterdetails" ID is likely unique or repeated? 
                            # Actually IDs must be unique. The detailed view injects #blotterdetails.
                            # The LIST view might have different structure.
                            # Screenshot shows: "Charges" header, then rows.
                            # Let's simple-parse text lines that look like statutes?
                            # Or look for the structure "Statute (Level) ... Description ... Bond"
                            
                            # iterate div.row inside this result
                            inner_rows = row.eles('css:div.row')
                            for ir in inner_rows:
                                txt = ir.text.strip().replace('\n', ' ')
                                # Check for charge pattern (Statute number)
                                if re.search(r'\d+\.\d+', txt) and "Booking" not in txt:
                                    # Clean up Charge String
                                    cleaned = txt
                                    
                                    # 1. Remove Bond Info
                                    # Split on "Original Bond", "Current Bond", "Bond Information", or pipe
                                    splitters = ["Original Bond", "Current Bond", "Bond Information", "|"]
                                    for s in splitters:
                                        if s in cleaned:
                                            cleaned = cleaned.split(s)[0]
                                            
                                    cleaned = cleaned.strip()
                                    
                                    # 2. Remove Statute Number (e.g. "843.15 ")
                                    cleaned = re.sub(r'^\d+(\.\d+)?\s+', '', cleaned)
                                    
                                    # 3. Remove Degree/Level (e.g. "1B (MF)", "1 (MS)", "(F)")
                                    # Matches: Optional Alphanumeric prefix + (Letters)
                                    cleaned = re.sub(r'^([0-9A-Za-z]+\s+)?\([A-Za-z]+\)\s+', '', cleaned)
                                    
                                    # 4. Remove secondary numeric codes (e.g. "8888" in "888.8888 8888")
                                    cleaned = re.sub(r'^\d+\s+', '', cleaned)
                                    
                                    # 5. Remove trailing dash/hyphen
                                    cleaned = cleaned.strip(' -')
                                    
                                    if cleaned:
                                        charges.append(cleaned)
                                    
                            # Bond
                            # Look for text "Current Bond: $..."
                            # It might be in the text of the row or inner divs
                            row_text = row.text
                            bond_matches = re.findall(r'Current Bond:\s*\$([\d\.]+)', row_text)
                            for amt in bond_matches:
                                try:
                                    total_bond += float(amt)
                                except: pass
                                
                            if total_bond == 0.0:
                                bond_amount_str = "0"
                            else:
                                bond_amount_str = f"{total_bond:.2f}"
                                
                            # URL - use the page URL as fallback since we aren't visiting details
                            detail_url = page.url 

                            # Construct Record
                            record = {
                                "Scrape_Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "County": "Palm Beach",
                                "Booking_Number": booking_num,
                                "Person_ID": jacket_num,
                                "Full_Name": full_name,
                                "First_Name": first_name,
                                "Middle_Name": middle_name,
                                "Last_Name": last_name,
                                "DOB": "", # Not in list view
                                "Booking_Date": booking_date,
                                "Booking_Time": booking_time,
                                "Status": status,
                                "Facility": facility,
                                "Race": race,
                                "Sex": sex,
                                "Height": "",
                                "Weight": "",
                                "Address": "",
                                "City": "",
                                "State": "",
                                "ZIP": "",
                                "Mugshot_URL": mug_url,
                                "Charges": " | ".join(charges),
                                "Bond_Amount": bond_amount_str,
                                "Bond_Paid": "NO",
                                "Bond_Type": "",
                                "Court_Type": "",
                                "Case_Number": "", 
                                "Court_Date": "",
                                "Court_Time": "",
                                "Court_Location": "",
                                "Detail_URL": detail_url,
                                "Lead_Score": "0",
                                "Lead_Status": "Cold"
                            }
                            
                            records.append(record)
                            # print(f"Parsed {booking_num}") # Debug
                            
                        except Exception as e:
                            sys.stderr.write(f"Error parsing row: {e}\n")
                            continue
                            
                    # Pagination Check
                    # Look for "Next" button?
                    # Common paginators: "Next >>" or just ">>"
                    # Screenshot showed: "Page 1 of 14 1 2 3 4 ... Last >>"
                    # We want the 'Next' link specifically, or the page_num + 1
                    
                    # Try to find link with text "Next" or "Next >"
                    # Often it's an 'a' tag.
                    next_btn = None
                    
                    # Strategy 1: 'Next' text or variations
                    next_selectors = [
                        'xpath://a[contains(text(), "Next")]',
                        'xpath://a[contains(text(), "next")]',
                        'xpath://a[contains(text(), ">>")]',
                        'xpath://a[contains(text(), "»")]',
                        'xpath://a[contains(text(), ">")]' 
                    ]
                    
                    for sel in next_selectors:
                        try:
                            btn = page.ele(sel)
                            if btn and btn.ele_displayed:
                                # Start with a check: is it the "Last" button?
                                if "last" in btn.text.lower():
                                    continue
                                
                                next_btn = btn
                                sys.stderr.write(f"Found Next button via selector: {sel}\n")
                                break
                        except: pass
                    
                    # Strategy 2: Click the Page Number directly (e.g. "2", "3")
                    if not next_btn:
                        next_page_num = page_num + 1
                        try:
                            # Look for 'a' tag with exact text equal to next_page_num
                            # using xpath for exact match or close to it
                            # //a[text()="2"] or //a[contains(text(), " 2 ")]
                            
                            # DrissionPage css: a@@text=2 ?
                            # Let's try xpath
                            page_link = page.ele(f'xpath://a[normalize-space(text())="{next_page_num}"]')
                            if page_link and page_link.ele_displayed:
                                next_btn = page_link
                                sys.stderr.write(f"Found specific page link: {next_page_num}\n")
                        except: pass
                        
                    # Strategy 3: Relative to "Last" button
                    if not next_btn:
                        try:
                            # Find "Last" link
                            # usually text "Last" or "Last >>"
                            last_btn = page.ele('xpath://a[contains(text(), "Last")]')
                            if last_btn:
                                # Get the preceding sibling 'a' tag
                                # xpath: preceding-sibling::a[1]
                                # But we need to be careful if there are spacers.
                                # Let's try getting the parent and finding the index of Last
                                parent = last_btn.parent()
                                links = parent.eles('tag:a')
                                # Find index of last_btn
                                last_idx = -1
                                for idx, l in enumerate(links):
                                    if l.html == last_btn.html: # basic comparison
                                        last_idx = idx
                                        break
                                
                                if last_idx > 0:
                                    potential_next = links[last_idx - 1]
                                    
                                    # Logic: The Next button is strictly between the page numbers and "Last".
                                    # It might be an arrow character (>) or an icon (empty text).
                                    # It should NOT be a number (which would be a page link).
                                    
                                    txt = potential_next.text.strip()
                                    
                                    # Check if it's likely the Next button
                                    # 1. Matches arrow symbols
                                    # 2. Or is empty/short and NOT a digit (to avoid clicking page "5" when we want ">")
                                    is_next_candidate = False
                                    
                                    
                                    if any(x in txt for x in [">", "»", "Next"]):
                                        is_next_candidate = True
                                    elif not txt.isdigit(): 
                                        # If it's not a digit (page number), it's likely the navigation control
                                        is_next_candidate = True
                                        
                                    if is_next_candidate:
                                         next_btn = potential_next
                                         sys.stderr.write(f"Found likely Next button (text='{txt}') before Last button.\n")
                        except: pass
                    
                    # Debug: Print all links in pagination for user visibility
                    try:
                        sys.stderr.write("DEBUG: Scanning pagination links to help identify 'Next' button...\n")
                        
                        # Try standard bootstrap pagination
                        pagination_container = page.ele('css:ul.pagination')
                        if not pagination_container:
                             pagination_container = page.ele('css:div.pagination')
                        if not pagination_container:
                             pagination_container = page.ele('css:.pagination')
                             
                        # Fallback to finding "Page 1 of..." text parent
                        if not pagination_container:
                            try:
                                page_info = page.ele('xpath://*[contains(text(), "Page 1 of")]') # or similar
                                if page_info:
                                    pagination_container = page_info.parent()
                            except: pass

                        if pagination_container:
                            dlinks = pagination_container.eles('tag:a')
                            link_texts = [f"'{l.text.strip()}'" for l in dlinks]
                            sys.stderr.write(f"DEBUG LINKS FOUND: {', '.join(link_texts)}\n")
                        else:
                            sys.stderr.write("DEBUG: Could not locate pagination container.\n")
                            
                    except Exception as e:
                        sys.stderr.write(f"DEBUG Error: {e}\n")

                    if next_btn:
                        sys.stderr.write(f"Clicking Next Page (Target: {page_num + 1})...\n")
                        next_btn.click()
                        page_num += 1
                        time.sleep(3) # Wait for reload
                        continue
                    else:
                        sys.stderr.write("No Next button or next page link found. End of results for this date.\n")
                        break
            
            except Exception as e:
                   sys.stderr.write(f"Error scraping date {target_date}: {e}\n")
                   continue # Continue to next day
                
        page.quit()
        return records

    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
        try:
            page.quit()
        except: pass
        return []

if __name__ == "__main__":
    days = 1
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    
    results = scrape_palm_beach(days_back=days)
    print(json.dumps(results, indent=2))
