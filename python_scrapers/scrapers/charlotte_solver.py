import sys
import json
import time
import re
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

def scrape_charlotte():
    records = []
    
    try:
        # Configure DrissionPage
        co = ChromiumOptions()
        co.set_browser_path('/usr/bin/chromium-browser')
        co.auto_port() # Use a random port to avoid conflicts
        co.set_argument('--ignore-certificate-errors')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--headless=new')
        
        # Try to find a valid browser path if needed, but auto usually works.
        # mac_browser_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        # if os.path.exists(mac_browser_path):
        #     co.set_browser_path(mac_browser_path)

        page = ChromiumPage(co)
        
        # 1. Navigate to list page
        url = 'https://inmates.charlottecountyfl.revize.com/bookings'
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

        # Wait for table or links
        if not page.wait.ele_displayed('tag:table', timeout=30):
             sys.stderr.write("Table not found after wait.\n")
        
        # 2. Extract detail URLs
        links = page.eles('tag:a')
        detail_urls = []
        base_url = 'https://inmates.charlottecountyfl.revize.com'
        
        for link in links:
            href = link.attr('href')
            if href and '/bookings/' in href and not href.endswith('/bookings/') and not href.endswith('/bookings'):
                if href.startswith('http'):
                    detail_urls.append(href)
                else:
                    detail_urls.append(base_url + href)
        
        detail_urls = list(set(detail_urls))
        detail_urls = detail_urls[:50]
        
        # 3. Visit each detail page
        for i, detail_url in enumerate(detail_urls):
            try:
                page.get(detail_url)
                
                # Check CF on detail page too!
                handle_cloudflare(page)
                # Save HTML for debugging
                if i == 0: # Only save the first one
                    with open('charlotte_debug.html', 'w', encoding='utf-8') as f:
                        f.write(page.html)
                
                # Wait for main content area to ensure page load
                sys.stderr.write(f"Loading detail page {i+1}/{len(detail_urls)}...\n")
                page.wait.load_start()
                if page.wait.ele_displayed('#bookings-table', timeout=5):
                    sys.stderr.write(" - Bookings table found.\n")
                else:
                    sys.stderr.write(" - Bookings table NOT found immediately.\n")
                
                # Try to extract data
                data = {}
                data['Detail_URL'] = detail_url
                
                # Extract ID from URL
                if '/bookings/' in detail_url:
                    parts = detail_url.split('/bookings/')
                    if len(parts) > 1:
                        data['Booking_Number'] = parts[1].split('?')[0].strip()
                
                # Strategy 1: Look for specific labels "First Name", "Last Name" (seen in screenshot)
                # They appear to be headers or labels above the value.
                # using DrissionPage's relative location
                
                # Helper to get value below a label
                def get_val_below(label_text):
                    try:
                        # Find the label element: text exactly matching or containing
                        label = page.ele(f'text:{label_text}')
                        if label:
                            # Try next sibling
                            nxt = label.next()
                            if nxt:
                                # If it's an input, get value
                                if nxt.tag == 'input':
                                    return nxt.value
                                return nxt.text.strip()
                    except Exception as e:
                        sys.stderr.write(f"Error getting value below {label_text}: {e}\n")
                    return None

                # Specific fields from screenshot
                fn = get_val_below('First Name')
                ln = get_val_below('Last Name')
                if fn: data['First_Name'] = fn
                if ln: data['Last_Name'] = ln
                
                if fn and ln:
                    data['Full_Name'] = f"{ln}, {fn}"

                # Strategy 2: Header Name (fallback)
                if 'Full_Name' not in data:
                    name_ele = page.ele('css:h3.name') or page.ele('css:h1') or page.ele('css:h2') or page.ele('css:.name')
                    if name_ele:
                        data['Full_Name'] = name_ele.text.strip()

                # Strategy 3: Generic DL/DT/DD
                dts = page.eles('tag:dt')
                for dt in dts:
                    key = dt.text.strip().replace(':', '')
                    dd = dt.next('tag:dd')
                    if dd:
                        val = dd.text.strip()
                        data[key] = val
                        
                # Strategy 4: Specific Bookings Table (Desktop)
                # This table contains Booking #, Date, and nested Charges table
                booking_table = page.ele('#bookings-table')
                if booking_table:
                    # 4a. Booking Info (Row 1)
                    # The first row in tbody usually has data-booking="0"
                    booking_row = booking_table.ele('css:tbody tr[data-booking]')
                    if booking_row:
                        tds = booking_row.eles('tag:td')
                        if len(tds) > 4:
                            data['Booking_Number'] = tds[1].text.strip()
                            data['Booking_Date'] = tds[3].text.strip()
                    
                    # 4b. Charges & Bond (Nested Table)
                    # Limit search to the bookings table to avoid mobile duplicates
                    charge_rows = booking_table.eles('css:.arrest-table tbody tr')
                    charges = []
                    total_bond = 0.0
                    
                    for row in charge_rows:
                        cols = row.eles('tag:td')
                        if len(cols) >= 5:
                            desc = cols[0].text.strip().replace('\n', ' ')
                            bond_text = cols[4].text.strip().replace('$','').replace(',','')
                            
                            if desc:
                                # Clean the charge text to extract only the description
                                clean_desc = clean_charge_text(desc)
                                if clean_desc:
                                    charges.append(clean_desc)
                            try:
                                total_bond += float(bond_text)
                            except:
                                pass
                    
                    if charges:
                        data['Charges'] = " | ".join(charges)
                    data['Bond_Amount'] = str(total_bond)

                else:
                    # Fallback Strategy: Generic Table Rows (if desktop table hidden/renamed)
                    sys.stderr.write("Desktop table not found, using generic fallback.\n")
                    trs = page.eles('tag:tr')
                    for tr in trs:
                        tds = tr.eles('tag:td')
                        if len(tds) >= 2:
                            key = tds[0].text.strip().replace(':', '')
                            val = tds[1].text.strip()
                            if key and val and 'Desc' not in key and 'Bond' not in key:
                                # Avoid capturing header rows as data
                                data[key] = val
                
                # Capture Mugshot
                imgs = page.eles('tag:img')
                for img in imgs:
                    src = img.attr('src')
                    if src and ('mug' in src or 'photo' in src or 'base64' in src[:30]):
                            # Handle relative URLs
                            if not src.startswith('http') and not src.startswith('data:'):
                                src = base_url + src
                            
                            # Check for Sheet limits (50k chars)
                            if len(src) > 49000:
                                sys.stderr.write(" - Mugshot too large for Sheets (Base64), skipping.\n")
                                data['Mugshot_URL'] = ''
                            else:
                                data['Mugshot_URL'] = src
                            break
                
                sys.stderr.write(f"Scraped {len(data)} keys from {detail_url}\n")
                if len(data) > 0:
                    sys.stderr.write(f"Keys: {list(data.keys())}\n")

                if len(data) > 2:
                    records.append(data)
                    sys.stderr.write(" - Added to records.\n")
                else:
                    sys.stderr.write(f" - Skipping {detail_url}, insufficient data.\n")
                        
                sys.stderr.write(" - Sleeping...\n")
                time.sleep(1)
                
            except Exception as e:
                sys.stderr.write(f"Error scraping {detail_url}: {str(e)}\n")
                continue
                
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")
    
    print(json.dumps(records))

if __name__ == "__main__":
    scrape_charlotte()
