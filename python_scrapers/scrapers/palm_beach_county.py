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
    co.headless(False) # Must be headed for Cloudflare/Captcha
    
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
            
        
        # Loop for backfill
        for i in range(days_back):
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
                        
            
                # 4. Parse Results List
                # Iterate through divs
                # Selector: div[id^="allresults_"]
                
                # Check if we have results
                if not page.ele('css:div[id^="allresults_"]'):
                    sys.stderr.write(f"No results found for {target_date} or page failed to load.\n")
                    continue

                results = page.eles('css:div[id^="allresults_"]')
                sys.stderr.write(f"Found {len(results)} records on list page for {target_date}.\n")
                
                detail_links = []
                
                for row in results:
                    try:
                        # Basic info from list
                        data = {}
                        
                        # Extract text lines
                        text = row.text
                        
                        # Mugshot
                        img = row.ele('css:img.img-zoom')
                        if img:
                            data['Mugshot_URL'] = img.attr('src')
                            
                        # Booking Number & Detail Link ID
                        # Selector: a[onclick^="loaddetail"]
                        link_ele = row.ele('css:a[onclick^="loaddetail"]')
                        if link_ele:
                            data['Booking_Number'] = link_ele.text.strip()
                            
                            # Extract ID from onclick="loaddetail('ID');"
                            onclick = link_ele.attr('onclick')
                            match = re.search(r"loaddetail\('([^']+)'\)", onclick)
                            if match:
                                book_id = match.group(1)
                                
                                # Find xisi
                                if 'xisi=' not in locals():
                                     # Try to find xisi in any link
                                     any_link = page.ele('css:a[href*="xisi="]')
                                     if any_link:
                                         href = any_link.attr('href')
                                         m_xisi = re.search(r'xisi=([^&]+)', href)
                                         if m_xisi:
                                             xisi = m_xisi.group(1)
                                         else:
                                             xisi = ''
                                     else:
                                         # Try hidden input
                                         hi = page.ele('css:input[name="xisi"]')
                                         if hi:
                                             xisi = hi.attr('value')
                                         else:
                                             xisi = ''
                                if 'xisi' not in locals():
                                    xisi = ''
                                
                                detail_url = f"https://www3.pbso.org/blotter/index.cfm?fa=details&fr=1&f=1&xisi={xisi}&bookdetailsID={book_id}"
                                data['Detail_URL'] = detail_url
                                detail_links.append(data)
                                
                    except Exception as e:
                        sys.stderr.write(f"Error parsing row: {e}\n")
                        continue
                        
                sys.stderr.write(f"Extracted {len(detail_links)} links. Visiting details...\n")
                
                # 5. Visit Details
                for item in detail_links:
                    try:
                        url = item['Detail_URL']
                        sys.stderr.write(f"Visiting {url}\n")
                        page.get(url)
                        
                        # Check for body
                        if not page.wait.ele_displayed('tag:body', timeout=10):
                            sys.stderr.write(f"Failed to load detail: {url}\n")
                            continue

                        # Parse Fields
                        
                        # Helper to get text by label strong tag
                        def get_val(label):
                            try:
                                # Find strong tag with text
                                strong = page.ele(f'xpath://strong[contains(text(), "{label}")]')
                                if strong:
                                    # The text is in the parent div, usually after the strong tag
                                    # Get parent text
                                    parent_text = strong.parent().text
                                    # Remove the label part
                                    val = parent_text.replace(label, '').replace(strong.text, '').strip()
                                    return val
                            except:
                                pass
                            return ''

                        # Name
                        # Label is "Name: " inside a strong tag
                        full_name = get_val("Name:")
                        # Parse Name
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

                        # Demographics
                        race = get_val("Race:")
                        sex = get_val("Gender:")
                        facility = get_val("Facility:")
                        
                        # Booking Date/Time
                        booking_dt_str = get_val("Booking Date/Time:") 
                        # Format: 12/12/2025 17:56
                        booking_date, booking_time = "", ""
                        if booking_dt_str:
                            try:
                                dt = datetime.strptime(booking_dt_str, '%m/%d/%Y %H:%M')
                                booking_date = dt.strftime('%Y-%m-%d')
                                booking_time = dt.strftime('%H:%M:00')
                            except:
                                booking_date = booking_dt_str

                        # IDs
                        jacket_num = get_val("Jacket Number:") # Map to Person_ID
                        booking_num = get_val("Booking Number:")
                        if not booking_num and 'Booking_Number' in item:
                            booking_num = item['Booking_Number']

                        # Release Date
                        release_date_str = get_val("Release Date:")
                        status = "In Custody"
                        if release_date_str and "N/A" not in release_date_str:
                            status = "Released"

                        # Mugshot
                        mug_url = item.get('Mugshot_URL', '')
                        if not mug_url:
                            img = page.ele('#person')
                            if img:
                                mug_url = img.attr('src')

                        # Charges & Bonds
                        charges = []
                        total_bond = 0.0
                        
                        # Let's iterate all rows inside the container
                        # Container ID: blotterdetails
                        container = page.ele('#blotterdetails')
                        if container:
                            rows = container.eles('css:div.row')
                            for i_row, r in enumerate(rows):
                                cols = r.eles('css:div[class*="col-sm-"]')
                                if len(cols) >= 2:
                                    # Possible charge row
                                    c1 = cols[0].text.strip()
                                    c2 = cols[1].text.strip()
                                    
                                    # Check if it looks like a charge (Statute in c1, Desc in c2)
                                    if re.search(r'\d', c1) and not "Booking" in c1:
                                        desc = c2
                                        full_charge = f"{c1} - {desc}"
                                        charges.append(full_charge)

                            # Extract Bonds separately by text search
                            # "Current Bond: $0.0000"
                            bond_texts = container.eles('xpath://div[contains(text(), "Current Bond:")]')
                            for bt in bond_texts:
                                txt = bt.text
                                # Extract amount
                                m = re.search(r'Current Bond:\s*\$([\d\.]+)', txt)
                                if m:
                                    try:
                                        amt = float(m.group(1))
                                        total_bond += amt
                                    except: pass

                        # Clean Bond
                        if total_bond == 0.0:
                            bond_amount_str = "0"
                        else:
                            bond_amount_str = f"{total_bond:.2f}"

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
                            "DOB": "", # Not available
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
                            "Bond_Paid": "NO", # Default
                            "Bond_Type": "",
                            "Court_Type": "",
                            "Case_Number": "", # Not available
                            "Court_Date": "",
                            "Court_Time": "",
                            "Court_Location": "",
                            "Detail_URL": url,
                            "Lead_Score": "0", # To be calculated later
                            "Lead_Status": "Cold"
                        }

                        records.append(record)
                        sys.stderr.write(f"   Parsed: {full_name} | Charges: {len(charges)}\n")
                        
                        time.sleep(0.5) 
                        
                    except Exception as e:
                        sys.stderr.write(f"Error processing detail {url}: {e}\n")
            
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
