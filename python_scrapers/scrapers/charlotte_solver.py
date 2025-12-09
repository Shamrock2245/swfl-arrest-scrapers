import sys
import json
import time
import re
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

def scrape_charlotte(days_back=21, max_pages=10):
    """
    Scrape Charlotte County with pagination support
    
    Args:
        days_back: Number of days to go back (default: 21 for 3 weeks)
        max_pages: Maximum number of pages to scrape (default: 10)
    """
    records = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        # Configure DrissionPage
        co = ChromiumOptions()
        # Try to use system Chrome/Chromium
        # co.set_browser_path('/usr/bin/chromium-browser')  # Uncomment for Linux
        
        # Run in headful mode for better Cloudflare bypass
        co.headless(False)  # Changed to False - headful mode works better
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        # co.set_argument('--disable-gpu')  # Removed - can interfere with CF
        co.set_argument('--ignore-certificate-errors')
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        # Custom CF Handler - Improved
        def handle_cloudflare(page):
            sys.stderr.write("Checking for Cloudflare...\n")
            # Wait loop - increased to 30 seconds
            for i in range(15):
                time.sleep(2)  # Wait first
                
                title = page.title.lower()
                sys.stderr.write(f"[{i+1}/15] Page Title: {page.title}\n")
                
                # Check if we're past Cloudflare
                if "just a moment" not in title and "security challenge" not in title and "attention required" not in title:
                    # Additional check - look for actual content
                    if page.ele('tag:table', timeout=2) or page.ele('tag:a', timeout=2):
                        sys.stderr.write("✅ Cloudflare cleared - content found!\n")
                        return True
                    else:
                        sys.stderr.write("⏳ Title OK but waiting for content...\n")
                        continue
                
                # Check for Turnstile
                if page.ele('@id=turnstile-wrapper', timeout=1) or page.ele('css:.cf-turnstile', timeout=1):
                    sys.stderr.write("⏳ Waiting for Turnstile challenge...\n")
                    continue
                
                sys.stderr.write(f"⏳ Still on Cloudflare page, waiting...\n")
            
            sys.stderr.write("⚠️  Cloudflare may still be blocking\n")
            return False

        # Base URL
        base_url = 'https://inmates.charlottecountyfl.revize.com'
        
        # Pagination loop
        current_page = 1
        all_detail_urls = []
        
        while current_page <= max_pages:
            sys.stderr.write(f"\n📄 Processing page {current_page}...\n")
            
            # Navigate to list page (with page parameter if not first page)
            if current_page == 1:
                url = f'{base_url}/bookings'
            else:
                url = f'{base_url}/bookings?page={current_page}'
            
            page.get(url)
            if not handle_cloudflare(page):
                sys.stderr.write("⚠️  Cloudflare bypass may have failed, trying anyway...\n")
            
            # Give extra time for page to fully load
            time.sleep(3)
            
            # Wait for table or links
            if not page.wait.ele_displayed('tag:table', timeout=30):
                sys.stderr.write("⚠️  Table not found after wait - page may not have loaded\n")
                # Save HTML for debugging
                with open('charlotte_list_page_fail.html', 'w', encoding='utf-8') as f:
                    f.write(page.html)
                sys.stderr.write("💾 Saved HTML to charlotte_list_page_fail.html for debugging\n")
                break
            
            # Extract detail URLs from current page
            links = page.eles('tag:a')
            page_detail_urls = []
            
            for link in links:
                href = link.attr('href')
                if href and '/bookings/' in href and not href.endswith('/bookings/') and not href.endswith('/bookings'):
                    if href.startswith('http'):
                        page_detail_urls.append(href)
                    else:
                        page_detail_urls.append(base_url + href)
            
            page_detail_urls = list(set(page_detail_urls))
            sys.stderr.write(f"   📋 Found {len(page_detail_urls)} inmates on page {current_page}\n")
            
            if len(page_detail_urls) == 0:
                sys.stderr.write("   ⚠️  No inmates found on this page, stopping pagination\n")
                break
            
            all_detail_urls.extend(page_detail_urls)
            
            # Check if there's a next page button
            next_button = page.ele('text:Next') or page.ele('css:.pagination .next') or page.ele('css:a[rel="next"]')
            if not next_button or current_page >= max_pages:
                if current_page >= max_pages:
                    sys.stderr.write(f"   ℹ️  Reached maximum pages ({max_pages})\n")
                else:
                    sys.stderr.write("   ℹ️  No more pages available\n")
                break
            
            current_page += 1
            time.sleep(2)  # Be nice to the server
        
        sys.stderr.write(f"\n📊 Total inmates found across {current_page} page(s): {len(all_detail_urls)}\n")
        
        # Remove duplicates
        all_detail_urls = list(set(all_detail_urls))
        
        # Visit each detail page
        stopped_early = False
        for i, detail_url in enumerate(all_detail_urls):
            try:
                sys.stderr.write(f"\n🔍 [{i+1}/{len(all_detail_urls)}] Processing {detail_url}\n")
                page.get(detail_url)
                
                # Check CF on detail page too!
                handle_cloudflare(page)
                
                # Save HTML for debugging (first one only)
                if i == 0:
                    with open('charlotte_debug.html', 'w', encoding='utf-8') as f:
                        f.write(page.html)
                
                # Wait for main content area to ensure page load
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
                
                # Helper to get value below a label
                def get_val_below(label_text):
                    try:
                        label = page.ele(f'text:{label_text}')
                        if label:
                            nxt = label.next()
                            if nxt:
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
                booking_table = page.ele('#bookings-table')
                if booking_table:
                    # 4a. Booking Info (Row 1)
                    booking_row = booking_table.ele('css:tbody tr[data-booking]')
                    if booking_row:
                        tds = booking_row.eles('tag:td')
                        if len(tds) > 4:
                            data['Booking_Number'] = tds[1].text.strip()
                            data['Booking_Date'] = tds[3].text.strip()
                    
                    # 4b. Charges & Bond (Nested Table)
                    charge_rows = booking_table.eles('css:.arrest-table tbody tr')
                    charges = []
                    total_bond = 0.0
                    
                    for row in charge_rows:
                        cols = row.eles('tag:td')
                        if len(cols) >= 5:
                            desc = cols[0].text.strip().replace('\n', ' ')
                            bond_text = cols[4].text.strip().replace('$','').replace(',','')
                            
                            if desc:
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
                    # Fallback Strategy: Generic Table Rows
                    sys.stderr.write("Desktop table not found, using generic fallback.\n")
                    trs = page.eles('tag:tr')
                    for tr in trs:
                        tds = tr.eles('tag:td')
                        if len(tds) >= 2:
                            key = tds[0].text.strip().replace(':', '')
                            val = tds[1].text.strip()
                            if key and val and 'Desc' not in key and 'Bond' not in key:
                                data[key] = val
                
                # Check date cutoff
                if 'Booking_Date' in data:
                    try:
                        booking_date = datetime.strptime(data['Booking_Date'], '%m/%d/%Y')
                        if booking_date < cutoff_date:
                            sys.stderr.write(f"   ⏸️  Reached cutoff date ({booking_date.strftime('%Y-%m-%d')}), stopping...\n")
                            stopped_early = True
                            break
                    except:
                        pass  # Continue if date parsing fails
                
                # Capture Mugshot
                imgs = page.eles('tag:img')
                for img in imgs:
                    src = img.attr('src')
                    if src and ('mug' in src or 'photo' in src or 'base64' in src[:30]):
                        if not src.startswith('http') and not src.startswith('data:'):
                            src = base_url + src
                        
                        if len(src) > 49000:
                            sys.stderr.write(" - Mugshot too large for Sheets (Base64), skipping.\n")
                            data['Mugshot_URL'] = ''
                        else:
                            data['Mugshot_URL'] = src
                        break
                
                sys.stderr.write(f"Scraped {len(data)} keys from {detail_url}\n")

                if len(data) > 2:
                    records.append(data)
                    sys.stderr.write(f"   ✅ Added record (Total: {len(records)})\n")
                else:
                    sys.stderr.write(f" - Skipping {detail_url}, insufficient data.\n")
                        
                time.sleep(1)
                
            except Exception as e:
                sys.stderr.write(f"Error scraping {detail_url}: {str(e)}\n")
                continue
        
        sys.stderr.write(f"\n📊 Total records collected: {len(records)}\n")
        if stopped_early:
            sys.stderr.write("ℹ️  Stopped early due to date cutoff\n")
                
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")
    
    print(json.dumps(records))

if __name__ == "__main__":
    # Parse command line arguments
    days_back = 21  # Default 3 weeks
    max_pages = 10  # Default 10 pages
    
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except:
            pass
    
    sys.stderr.write(f"🚀 Starting Charlotte County scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n")
    sys.stderr.write(f"📄 Max pages: {max_pages}\n\n")
    
    scrape_charlotte(days_back, max_pages)
