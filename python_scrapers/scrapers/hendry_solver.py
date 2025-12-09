import sys
import json
import time
import re
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stderr.write("=== Hendry Solver Starting ===\n")
sys.stderr.flush()

def clean_charge_text(raw_charge):
    """
    Clean charge text to extract only the human-readable description.
    """
    if not raw_charge:
        return ''
    
    # Remove common prefixes
    text = re.sub(r'^(New Charge:|Weekender:|Charge Description:)\s*', '', raw_charge, flags=re.IGNORECASE)
    
    # Extract the description part (between statute and parentheses)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        return description
    
    # Fallback: if no statute pattern, try to get text before first parenthesis
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    
    return text.strip()

def scrape_hendry(days_back=30):
    records = []
    
    try:
        co = ChromiumOptions()
        co.set_browser_path('/usr/bin/chromium-browser')
        co.headless(True)
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        
        # Cloudflare handler
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
        
        # Navigate to roster page
        url = 'https://www.hendrysheriff.org/inmateSearch'
        sys.stderr.write(f"Navigating to {url}\n")
        sys.stderr.flush()
        
        try:
            page.get(url, timeout=30)
            sys.stderr.write("Page loaded successfully\n")
            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"Error loading page: {e}\n")
            sys.stderr.flush()
            return
        
        sys.stderr.write("Checking Cloudflare...\n")
        sys.stderr.flush()
        handle_cloudflare(page)
        sys.stderr.write("Cloudflare check complete\n")
        sys.stderr.flush()
        
        # Wait for page to be ready
        sys.stderr.write("Waiting for page content...\n")
        sys.stderr.flush()
        time.sleep(3)
        
        # Set sort to newest first (optional - may not always be available)
        sys.stderr.write("Attempting to set sort order...\n")
        sys.stderr.flush()
        try:
            sort_select = page.ele('css:select#sort', timeout=5)
            if sort_select:
                # Try to select by value
                try:
                    sort_select.select.by_value('dateDesc')
                    sys.stderr.write("Sort order set successfully\n")
                except:
                    # Fallback: try by index (usually index 1 or 2 for date desc)
                    try:
                        sort_select.select.by_index(1)
                        sys.stderr.write("Sort order set by index\n")
                    except:
                        sys.stderr.write("Could not set sort order, continuing anyway...\n")
                time.sleep(2)
        except Exception as e:
            sys.stderr.write(f"Sort dropdown not found or error: {e}, continuing...\n")
        
        sys.stderr.flush()
        
        # Extract detail URLs - but actually we'll click "Read More" on each card
        sys.stderr.write("Finding inmate cards...\n")
        
        # Save HTML for debugging
        with open('hendry_debug.html', 'w', encoding='utf-8') as f:
            f.write(page.html)
        sys.stderr.write("Saved hendry_debug.html for inspection\n")
        
        # Find all "Read More" buttons
        read_more_buttons = page.eles('text:Read More')
        sys.stderr.write(f"Found {len(read_more_buttons)} Read More buttons\n")
        
        # Limit to first 3 for testing to avoid timeouts
        buttons_to_process = read_more_buttons[:3]
        
        # Process each inmate card
        for i, button in enumerate(buttons_to_process):
            try:
                sys.stderr.write(f"Processing inmate {i+1}/{len(buttons_to_process)}...\n")
                
                # Scroll button into view before clicking
                try:
                    button.run_js('this.scrollIntoView({block: "center"})')
                    time.sleep(0.5)
                except:
                    pass
                
                # Click Read More to expand details with timeout protection
                try:
                    # Use JS click directly - more reliable
                    button.run_js('this.click()')
                    time.sleep(1)  # Reduced wait time
                except Exception as click_err:
                    sys.stderr.write(f"  Click failed: {click_err}, skipping...\n")
                    continue
                
                # Get the parent card element - go up to find the card container
                # Try different levels to find the card
                card = None
                current = button
                for level in range(1, 8):
                    try:
                        current = current.parent()
                        if current:
                            # Check if this looks like a card (has multiple child elements)
                            if len(current.eles('tag:*')) > 5:
                                card = current
                                break
                    except:
                        break
                
                if not card:
                    sys.stderr.write("  Could not find parent card, trying body text...\n")
                    # Fallback: use entire page
                    card = page.ele('tag:body')
                
                card_text = card.text
                data = {}
                
                # Extract name from h3 or h4 in the card
                name_elem = card.ele('tag:h3') or card.ele('tag:h4') or card.ele('tag:h2')
                if name_elem:
                    full_name = name_elem.text.strip()
                    data['Full_Name'] = full_name
                    # Try to split name
                    if ',' in full_name:
                        parts = full_name.split(',', 1)
                        data['Last_Name'] = parts[0].strip()
                        data['First_Name'] = parts[1].strip()
                
                # Extract Inmate ID / Booking Number
                inmate_match = re.search(r'Inmate ID:\s*([A-Z0-9]+)', card_text)
                if inmate_match:
                    data['Booking_Number'] = inmate_match.group(1)
                
                # Booked Date
                booked_match = re.search(r'Booked Date:\s*([^\n]+)', card_text)
                if booked_match:
                    data['Booking_Date'] = booked_match.group(1).strip()
                
                # Gender
                gender_match = re.search(r'Gender:\s*([MF])', card_text)
                if gender_match:
                    data['Sex'] = gender_match.group(1)
                
                # Race
                race_match = re.search(r'Race:\s*([A-Z])', card_text)
                if race_match:
                    data['Race'] = race_match.group(1)
                
                # Height
                height_match = re.search(r'Height:\s*([^\n]+)', card_text)
                if height_match:
                    data['Height'] = height_match.group(1).strip()
                
                # Weight
                weight_match = re.search(r'Weight:\s*([^\n]+)', card_text)
                if weight_match:
                    data['Weight'] = weight_match.group(1).strip()
                
                # Address
                address_match = re.search(r'Main Address:\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|Height:|Weight:|$)', card_text, re.DOTALL)
                if address_match:
                    data['Address'] = address_match.group(1).strip().replace('\n', ' ')
                
                # Extract charges
                charges = []
                total_bond = 0.0
                
                # Find all charge blocks in the card text
                charge_pattern = r'Charge Code:\s*([^\n]+)\s*Charge Description:\s*([^\n]+)(?:\s*Bond Amount:\s*\$?([\d.,]+))?'
                charge_matches = re.finditer(charge_pattern, card_text)
                
                for match in charge_matches:
                    code = match.group(1).strip()
                    desc = match.group(2).strip()
                    bond_str = match.group(3)
                    
                    # Clean the charge description
                    clean_desc = clean_charge_text(desc)
                    if clean_desc:
                        charges.append(clean_desc)
                    
                    if bond_str:
                        try:
                            bond_val = float(bond_str.replace(',', '').replace('$', ''))
                            total_bond += bond_val
                        except:
                            pass
                
                if charges:
                    data['Charges'] = ' | '.join(charges)
                data['Bond_Amount'] = str(total_bond)
                
                # Mugshot - look for img in the card
                img = card.ele('tag:img')
                if img:
                    src = img.attr('src')
                    if src and ('mug' in src.lower() or 'photo' in src.lower() or 'inmate' in src.lower()):
                        if not src.startswith('http'):
                            src = 'https://www.hendrysheriff.org' + (src if src.startswith('/') else '/' + src)
                        data['Mugshot_URL'] = src
                
                # Add detail URL (the main page URL since we're not navigating away)
                data['Detail_URL'] = url
                
                sys.stderr.write(f"  Scraped {len(data)} keys\n")
                sys.stderr.write(f"  Keys: {list(data.keys())}\n")
                
                if len(data) > 2:
                    records.append(data)
                    sys.stderr.write("  - Added to records.\n")
                
                # Click "Read Less" or collapse to prepare for next one
                read_less = card.ele('text:Read Less')
                if read_less:
                    read_less.click()
                    time.sleep(0.5)
                
            except Exception as e:
                sys.stderr.write(f"  Error processing card {i+1}: {str(e)}\n")
                continue
        
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")
    
    print(json.dumps(records))

if __name__ == "__main__":
    scrape_hendry()
