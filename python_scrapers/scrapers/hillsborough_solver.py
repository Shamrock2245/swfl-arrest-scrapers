import sys
import json
import time
import re
from DrissionPage import ChromiumPage, ChromiumOptions

def clean_charge_text(raw_charge):
    if not raw_charge:
        return ''
    return raw_charge.strip()

def scrape_hillsborough(days_back=3):
    """
    Scrape Hillsborough County (HCSO) with DrissionPage & Captcha Handling
    """
    records = []
    
    end_date = time.strftime("%m/%d/%Y")
    # For now, let's just do a small range or what the user asked
    # Calculate start date
    import datetime
    start_dt = datetime.datetime.now() - datetime.timedelta(days=days_back)
    start_date = start_dt.strftime("%m/%d/%Y")

    sys.stderr.write(f"ℹ️  Scraping HCSO from {start_date} to {end_date}\n")
    
    try:
        co = ChromiumOptions()
        co.headless(False) # Visible to help with captcha interactions
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        url = 'https://webapps.hcso.tampa.fl.us/arrestinquiry/'
        page.get(url)
        
        # 1. Fill Form
        sys.stderr.write("🔍 Handling search form...\n")
        
        # Booking Date From
        if page.ele('#SearchBookingDate'):
            page.ele('#SearchBookingDate').input(start_date)
        
        # Booking Date Thru
        if page.ele('#SearchReleaseDate'):
             page.ele('#SearchReleaseDate').input(end_date) # It's labeled Release Date but often used as "Date Range Thru" or we should check if there is a 'SearchBookingDateThru'
             # Looking at screenshot: "Release Date" is distinct. 
             # Screenshot shows "Booking Date" single input? OR "Booking Date" and "Release Date".
             # Actually screenshot shows:
             # Booking Date: 12/12/2025
             # Release Date: 12/15/2025
             # HCSO allows searching by booking date range separately usually, but here it looks like strict fields.
             # If I want "Arrests from X to Y", usually I'd put range in "Booking Date".
             # But the input is typically just one field or two.
             # Debug output showed: SearchBookingDate (index 3) and SearchReleaseDate (index 5)
             # Let's hope SearchBookingDate accepts a range or just a start date implies "on or after".
             # Wait, screenshot shows "Booking Date" with value "12/12/2025". It seems to be a single date or start.
             # Let's try putting the start date there.
             pass

        # Include Arrest Details
        if page.ele('#SearchIncludeDetails'):
            page.ele('#SearchIncludeDetails').click()

        time.sleep(5)

        # 2. CAPTCHA HANDLING
        sys.stderr.write("🤖 Detecting reCAPTCHA...\n")
        
        # Find the iframe with retry
        captcha_iframe = None
        for i in range(5):
            # Try looser selector
            captcha_iframe = page.ele('tag:iframe@src:recaptcha')
            if captcha_iframe:
                break
            time.sleep(1)

        if captcha_iframe:
            sys.stderr.write("   ✅ Found reCAPTCHA iframe. Attempting to click...\n")
            
            # Use strict mode off or specific wait
            time.sleep(1)
            
            # Try identifying the checkbox inside
            # "I'm not a robot" checkbox usually has id "recaptcha-anchor"
            # It might be in shadow root or just inside frame
            
            btn_box = None
            try:
                # DrissionPage: access element inside iframe
                btn_box = captcha_iframe.ele('#recaptcha-anchor', timeout=2)
                if not btn_box:
                    btn_box = captcha_iframe.ele('.recaptcha-checkbox-border', timeout=2)
            except: pass

            if btn_box:
                btn_box.click()
                sys.stderr.write("   🖱️  Clicked reCAPTCHA checkbox\n")
            else:
                sys.stderr.write("   ⚠️  Could not find checkbox inside iframe (tried #recaptcha-anchor and .recaptcha-checkbox-border)\n")
            
            # Wait for solved
            for i in range(10):
                time.sleep(1)
                try:
                    # Check aria-checked on the anchor or check if checkmark is visible
                    if btn_box and btn_box.attr('aria-checked') == 'true':
                        sys.stderr.write("   ✅ reCAPTCHA Solved!\n")
                        break
                except: pass
                sys.stderr.write(f"   ⏳ Waiting for captcha... {i+1}/10\n")
        else:
             sys.stderr.write("⚠️  No reCAPTCHA iframe found (unexpected) - check screenshot if visible\n")

        time.sleep(1)
        
        # 3. Search
        sys.stderr.write("🚀 Submitting Search...\n")
        page.ele('#button_submit').click()
        
        time.sleep(5)
        
        # DEBUG: Snapshot
        page.get_screenshot(path='hcso_results_debug.png', full_page=True)
        with open('hcso_results_debug.html', 'w') as f:
            f.write(page.html)
        sys.stderr.write("📸 Saved debug screenshot and HTML\n")

        # 4. Extract Detail URLs
        detail_urls = []
        rows = page.eles('css:table.table tbody tr') 
        if not rows:
             sys.stderr.write("   ℹ️  No table rows found.\n")
             
        for row in rows:
            cols = row.eles('tag:td')
            if len(cols) > 0:
                link = cols[0].ele('tag:a')
                if link:
                    href = link.attr('href')
                    if href:
                        if href.startswith('http'):
                            full_url = href
                        else:
                            # Handle potential leading slash
                            if not href.startswith('/'):
                                href = '/' + href
                            full_url = 'https://webapps.hcso.tampa.fl.us' + href
                        detail_urls.append(full_url)

        sys.stderr.write(f"✅ Found {len(detail_urls)} records. Processing...\n")
        
        records = []
        for url in detail_urls:
            try:
                sys.stderr.write(f"   Processing {url}...\n")
                page.get(url)
                
                # Helper to get field by label
                def get_val(label_text):
                    try:
                        # Find label with title or text
                        lbl = page.ele(f'css:label[title="{label_text}"]') or page.ele(f'text:^{label_text}:?$')
                        if lbl:
                            # The value is usually the text node following the label or in the parent text
                            # In this HTML, it's typically: <div class="col"><label>...</label> VALUE </div>
                            # So get parent text and strip label text
                            parent = lbl.parent()
                            full_text = parent.text
                            val = full_text.replace(lbl.text, '').strip()
                            return val
                    except:
                        pass
                    return ''

                record = {}
                record['Detail_URL'] = url
                record['County'] = 'Hillsborough'
                record['Scrape_Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Mugshot
                try:
                    mug_img = page.ele('css:#mugShot img')
                    if mug_img:
                        src = mug_img.attr('src')
                        if src:
                            if not src.startswith('http'):
                                src = 'https://webapps.hcso.tampa.fl.us' + src
                            record['Mugshot_URL'] = src
                except: pass

                # Demographics
                record['Booking_Number'] = get_val('Booking Number')
                record['Arrest_Date'] = get_val('Arrest Date') # Fallback if booking date missing
                
                # Name
                # Name is in h2.title but mixed with "Inmate" span
                try:
                    name_h2 = page.ele('css:h2.title')
                    if name_h2:
                        raw_name = name_h2.text.replace('Inmate', '').strip()
                        # Format: LAST, FIRST MIDDLE
                        if ',' in raw_name:
                            parts = raw_name.split(',', 1)
                            record['Last_Name'] = parts[0].strip()
                            rest = parts[1].strip().split()
                            if rest:
                                record['First_Name'] = rest[0]
                                if len(rest) > 1:
                                    record['Middle_Name'] = ' '.join(rest[1:])
                        record['Full_Name'] = raw_name
                except: pass

                record['DOB'] = get_val('Date of Birth')
                record['Sex'] = get_val('Sex / Gender')
                record['Race'] = get_val('Race')
                record['Height'] = get_val('Height')
                record['Weight'] = get_val('Weight')
                
                # Address
                addr = get_val('Street Address')
                city = get_val('City')
                state = get_val('State')
                zip_code = get_val('Zip Code')
                record['Address'] = addr
                record['City'] = city
                record['State'] = state
                record['ZIP'] = zip_code
                
                # Booking Info
                record['Booking_Date'] = get_val('Booking Date')
                record['Booking_Time'] = get_val('Booking Time')
                
                # Status
                status_raw = get_val('Booking Status') # "STATUS - *RELEASED*"
                record['Status'] = status_raw.replace('STATUS -', '').replace('*', '').strip()

                # Charges & Bond
                charges = []
                total_bond = 0.0
                
                # Find all charge blocks
                # They are inside .default-hcso-bg.bordered
                # Strategy: Look for "Charge Description" labels and traverse up
                charge_labels = page.eles('css:label[title="Charge Description"]')
                
                for cl in charge_labels:
                    try:
                        # Get the row containing the label
                        row_div = cl.parent().parent() # label -> col -> row
                        # Get description value
                        container = row_div.parent() # The charge container div
                        
                        desc = row_div.text.replace(cl.text, '').strip()
                        
                        # Find bond in this container
                        bond_lbl = container.ele('css:label[title="Bond Amount"]')
                        bond_val = 0
                        if bond_lbl:
                            bond_text = bond_lbl.parent().parent().text.replace(bond_lbl.text, '').strip()
                            # $2,500.00
                            bond_clean = bond_text.replace('$', '').replace(',', '')
                            try:
                                bond_val = float(bond_clean)
                            except: pass
                        
                        total_bond += bond_val
                        charges.append(desc)
                        
                        # Find Case Number
                        case_lbl = container.ele('css:label[title="Court Docket Case Number"]')
                        if case_lbl and 'Case_Number' not in record:
                             case_text = case_lbl.parent().parent().text.replace(case_lbl.text, '').strip()
                             record['Case_Number'] = case_text
                             
                    except: pass
                
                record['Charges'] = ' | '.join(charges)
                record['Bond_Amount'] = str(total_bond)
                
                records.append(record)
                
                # Be polie
                time.sleep(1)
                
            except Exception as e:
                sys.stderr.write(f"   ⚠️ Error processing {url}: {e}\n")

        if records:
            print(json.dumps(records, indent=2))
        else:
            sys.stderr.write("⚠️  No records extracted.\n")

    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    scrape_hillsborough()
