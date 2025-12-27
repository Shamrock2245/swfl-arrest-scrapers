import sys
import json
import time
import re
import os
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

# Import validation module
try:
    from validation import validate_record, sanitize_record, format_validation_report
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    sys.stderr.write("⚠️  Validation module not found, skipping validation\n")

# Configuration: Allow headless mode via environment variable
# Set HEADLESS=false for local debugging, true for automation
HEADLESS_MODE = os.getenv('HEADLESS', 'true').lower() == 'true'

def clean_charge_text(raw_charge):
    """
    Clean charge text to extract only the human-readable description.
    """
    if not raw_charge:
        return ''
    
    text = re.sub(r'^(New Charge:|Weekender:)\s*', '', raw_charge, flags=re.IGNORECASE)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        description = match.group(1).strip()
        return description
    
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    
    return text.strip()

def scrape_charlotte(days_back=21, max_pages=10):
    """
    Scrape Charlotte County with pagination and RESUME support
    """
    records = []
    progress_file = 'charlotte_progress.jsonl'
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Load processed IDs (Booking Numbers)
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
                            elif 'Detail_URL' in rec: # Fallback
                                processed_ids.add(rec['Detail_URL'])
                        except: pass
        except Exception as e:
            sys.stderr.write(f"Warning: Could not read progress file: {e}\n")
            
    sys.stderr.write(f"ℹ️  Found {len(processed_ids)} previously scraped records. Resuming...\n")
    
    try:
        co = ChromiumOptions()
        # Check environment variable for headless mode
        is_headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        co.headless(is_headless)
        co.auto_port()
        
        # Support CI paths if they exist
        if os.path.exists('/usr/bin/chromium-browser'):
            co.set_browser_path('/usr/bin/chromium-browser')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--ignore-certificate-errors')
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        def handle_cloudflare(page):
            sys.stderr.write("Checking for Cloudflare...\n")
            for i in range(15):
                time.sleep(2)
                title = page.title.lower()
                sys.stderr.write(f"[{i+1}/15] Page Title: {page.title}\n")
                if "just a moment" not in title and "security" not in title and "attention" not in title:
                    if page.ele('tag:table', timeout=1) or page.ele('tag:a', timeout=1):
                         sys.stderr.write("✅ Cloudflare cleared - content found!\n")
                         return True
                if page.ele('@id=turnstile-wrapper', timeout=1):
                    sys.stderr.write("⏳ Waiting for Turnstile challenge...\n")
            return False

        base_url = 'https://inmates.charlottecountyfl.revize.com'
        
        current_page = 1
        all_detail_urls = []
        
        # Phase 1: Collect ALL Links first
        # This is slightly less resumable if we crash during link collection, but standard for pagination
        while current_page <= max_pages:
            sys.stderr.write(f"\n📄 Processing page {current_page}...\n")
            
            if current_page == 1:
                url = f'{base_url}/bookings'
            else:
                url = f'{base_url}/bookings?page={current_page}'
            
            page.get(url)
            
            if not handle_cloudflare(page):
                sys.stderr.write("⚠️  Cloudflare bypass may have failed, trying anyway...\n")
            
            time.sleep(5)
            
            links = page.eles('tag:a')
            page_detail_urls = []
            for link in links:
                href = link.attr('href')
                if href and '/bookings/' in href:
                    if href.endswith('/bookings') or href.endswith('/bookings/'):
                        continue
                    if not href.startswith('http'):
                        full_url = base_url + href
                    else:
                        full_url = href
                    page_detail_urls.append(full_url)
            
            page_detail_urls = list(set(page_detail_urls))
            
            if len(page_detail_urls) == 0:
                sys.stderr.write("⚠️  No booking links found - stopping pagination\n")
                break
            else:
                sys.stderr.write(f"✅ Found {len(page_detail_urls)} unique inmates on page {current_page}\n")
            
            all_detail_urls.extend(page_detail_urls)
            
            next_link = page.ele('text:Next') or page.ele('css:a[rel="next"]') or page.ele('xpath://a[contains(text(), "Next")]') or page.ele('xpath://a[contains(text(), "›")]')
            
            if not next_link:
                next_page_num = current_page + 1
                if page.ele(f'text:{next_page_num}'):
                    sys.stderr.write(f"   ℹ️  Found link to page {next_page_num}, continuing\n")
                    pass
                else:
                    if current_page >= max_pages:
                        sys.stderr.write(f"   ℹ️  Reached maximum pages ({max_pages})\n")
                    else:
                        sys.stderr.write("   ℹ️  No Next button found, stopping\n")
                    break
            
            if current_page >= max_pages:
                break
                
            current_page += 1
            time.sleep(2)
        
        all_detail_urls = list(set(all_detail_urls))
        sys.stderr.write(f"\n📊 Total inmates found: {len(all_detail_urls)}\n")
        
        # Filter Skipped
        original_count = len(all_detail_urls)
        # Extract ID from URL to match
        filtered_urls = []
        for u in all_detail_urls:
            # Extract ID: /bookings/12345
            parts = u.split('/bookings/')
            if len(parts) > 1:
                bid = parts[1].split('?')[0].strip()
                if bid not in processed_ids:
                    filtered_urls.append(u)
            else:
                filtered_urls.append(u)
        
        all_detail_urls = filtered_urls
        sys.stderr.write(f"📉 Remaining to scrape: {len(all_detail_urls)} (skipped {original_count - len(all_detail_urls)})\n")
        
        # Phase 2: Visit Details
        stopped_early = False
        for i, detail_url in enumerate(all_detail_urls):
            try:
                sys.stderr.write(f"\n🔍 [{i+1}/{len(all_detail_urls)}] Processing {detail_url}\n")
                page.get(detail_url)
                handle_cloudflare(page)
                
                is_loaded = False
                for _ in range(5):
                    if page.ele('#bookings-table') or page.ele('text:Charges'):
                        is_loaded = True
                        break
                    time.sleep(1)
                
                if not is_loaded:
                     sys.stderr.write("⚠️  Content not loaded, skipping\n")
                     continue

                data = {}
                data['Detail_URL'] = detail_url
                data['County'] = 'Charlotte'
                data['State'] = 'FL'
                
                if '/bookings/' in detail_url:
                    parts = detail_url.split('/bookings/')
                    if len(parts) > 1:
                        data['Booking_Number'] = parts[1].split('?')[0].strip()
                
                # Helper to get value from input next to label
                def get_input_val(label_text):
                    try:
                        # Try exact match first
                        label = page.ele(f'text:^{label_text}$')
                        if not label:
                            # Try contains match
                            label = page.ele(f'text:{label_text}')
                        
                        if label:
                            # Get the next element which should be the input
                            inp = label.next()
                            if inp and inp.tag == 'input':
                                return inp.value
                            elif inp:
                                return inp.text.strip()
                    except:
                        pass
                    return None

                # Strategy 1: Label/Input pairs (New Site Structure)
                # Personal Info
                fn = get_input_val('First Name')
                ln = get_input_val('Last Name')
                if fn: data['First_Name'] = fn
                if ln: data['Last_Name'] = ln
                
                if fn and ln:
                    data['Full_Name'] = f"{ln}, {fn}"
                
                dob = get_input_val('Date of Birth')
                if dob: data['DOB'] = dob
                
                race = get_input_val('Race')
                if race: data['Race'] = race
                
                sex = get_input_val('Gender')
                if sex: data['Sex'] = sex
                
                height = get_input_val('Height')
                if height: data['Height'] = height
                
                weight = get_input_val('Weight')
                if weight: data['Weight'] = weight
                
                # Address Info
                addr = get_input_val('Address')
                if addr: data['Address'] = addr
                
                city = get_input_val('City')
                if city: data['City'] = city
                
                state = get_input_val('State')
                if state: data['State'] = state
                
                zip_code = get_input_val('Zip Code')
                if zip_code: data['ZIP'] = zip_code

                # Strategy 2: Header Name (Fallback if Strategy 1 fails)
                if 'Full_Name' not in data:
                    name_ele = page.ele('css:h3.name') or page.ele('css:.inmate-name') or page.ele('css:div.name') or page.ele('css:h1')
                    if name_ele:
                        data['Full_Name'] = name_ele.text.strip()
                        if ',' in data['Full_Name']:
                            parts = data['Full_Name'].split(',', 1)
                            data['Last_Name'] = parts[0].strip()
                            data['First_Name'] = parts[1].strip()

                # Strategy 3: Generic DL/DT/DD (Old Site Structure Fallback)
                if 'First_Name' not in data: 
                    dts = page.eles('tag:dt')
                    for dt in dts:
                        key = dt.text.strip().replace(':', '')
                        dd = dt.next('tag:dd')
                        if dd:
                            val = dd.text.strip()
                            if key == 'First Name': data['First_Name'] = val
                            elif key == 'Last Name': data['Last_Name'] = val
                            elif key == 'DOB' or key == 'Date of Birth': data['DOB'] = val
                            elif key == 'Race': data['Race'] = val
                            elif key == 'Sex' or key == 'Gender': data['Sex'] = val
                            elif key == 'Height': data['Height'] = val
                            elif key == 'Weight': data['Weight'] = val
                            elif key == 'Address': data['Address'] = val
                            elif key == 'City': data['City'] = val
                            elif key == 'State': data['State'] = val
                            elif key == 'Zip Code': data['ZIP'] = val
                
                booking_table = page.ele('#bookings-table') or page.ele('css:table.bookings')
                charges = []
                total_bond = 0.0
                
                if booking_table:
                    booking_row = booking_table.ele('css:tbody tr')
                    if booking_row:
                        tds = booking_row.eles('tag:td')
                        for td in tds:
                            txt = td.text.strip()
                            match = re.search(r'\d{2}/\d{2}/\d{4}', txt)
                            if match:
                                data['Booking_Date'] = match.group(0)
                    
                    charge_rows = booking_table.eles('css:tr')
                    for row in charge_rows:
                        cols = row.eles('tag:td', timeout=0.1) # Fast lookup
                        if len(cols) >= 3:
                            col_texts = [c.text.strip() for c in cols]
                            
                            bond_val = 0
                            for t in col_texts:
                                if '$' in t:
                                    try:
                                        b = float(t.replace('$','').replace(',',''))
                                        if b > 0 and b < 10000000:
                                            bond_val = b
                                    except: pass
                            
                            if bond_val > 0:
                                total_bond += bond_val
                            
                            desc_cand = ""
                            for t in col_texts:
                                if len(t) > 10 and not '$' in t and not '/' in t:
                                    clean = clean_charge_text(t)
                                    if clean and len(clean) > 3:
                                        desc_cand = clean
                                        break
                            
                            if desc_cand:
                                charges.append(desc_cand)

                if charges:
                    data['Charges'] = " | ".join(list(set(charges)))
                if total_bond > 0:
                    data['Bond_Amount'] = str(total_bond)
                else:
                    data['Bond_Amount'] = '0'

                imgs = page.eles('tag:img')
                for img in imgs:
                    src = img.attr('src')
                    if src and ('mug' in src.lower() or 'photo' in src.lower() or 'base64' in src[:30]):
                        if not src.startswith('http') and not src.startswith('data:'):
                            src = base_url + src
                        if len(src) < 50000:
                            data['Mugshot_URL'] = src
                        if 'revize' not in src:
                             break

                if 'Booking_Date' in data:
                    try:
                        dt_str = data['Booking_Date'].split()[0]
                        booking_date = datetime.strptime(dt_str, '%m/%d/%Y')
                        if booking_date < cutoff_date:
                            sys.stderr.write(f"   ⏸️  Reached cutoff date ({booking_date.strftime('%Y-%m-%d')}), stopping...\n")
                            stopped_early = True
                            break 
                    except Exception as e:
                        pass

                sys.stderr.write(f"   Scraped {len(data)} fields. Name: {data.get('Full_Name', 'Unknown')}\n")

                # Sanitize and validate record before saving
                if VALIDATION_AVAILABLE:
                    data = sanitize_record(data)
                    is_valid, issues = validate_record(data, 'Charlotte', strict=False)
                    
                    if not is_valid:
                        sys.stderr.write(f"   ❌ Validation failed for {detail_url}:\n")
                        for issue in issues:
                            if issue.startswith('CRITICAL'):
                                sys.stderr.write(f"      {issue}\n")
                        sys.stderr.write(f"   ⚠️  Skipping invalid record\n")
                        continue
                    
                    # Log warnings but still save
                    warnings = [i for i in issues if i.startswith('WARNING')]
                    if warnings:
                        sys.stderr.write(f"   ⚠️  {len(warnings)} validation warnings (record will still be saved)\n")
                
                # Final check: must have minimum required data
                if len(data) > 2 and 'Booking_Number' in data and 'Full_Name' in data:
                    records.append(data)
                    # AUTO SAVE
                    with open(progress_file, 'a') as f:
                        f.write(json.dumps(data) + '\n')
                    sys.stderr.write(f"   ✅ Added & Saved record (Total New: {len(records)})\n")
                else:
                    sys.stderr.write(f"   ⚠️  Skipping {detail_url}, insufficient data (need Booking_Number and Full_Name)\n")
                
                if stopped_early:
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                sys.stderr.write(f"   ⚠️  Error processing {detail_url}: {e}\n")
                continue
        
        sys.stderr.write(f"\n📊 Total new records collected: {len(records)}\n")
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {str(e)}\n")
    
    # Final Output Combine
    final_records = []
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:final_records.append(json.loads(line))
                    except:pass
    else:
        final_records = records

    # Summary Statistics
    sys.stderr.write(f"\n🎯 Final Summary:\n")
    sys.stderr.write(f"   Records scraped this session: {len(records)}\n")
    sys.stderr.write(f"   Total records in output: {len(final_records)}\n")
    sys.stderr.write(f"   Previously scraped (skipped): {len(processed_ids)}\n")
    
    if VALIDATION_AVAILABLE and records:
        from validation import get_data_completeness_score
        completeness_scores = [get_data_completeness_score(r) for r in records]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        sys.stderr.write(f"   Average data completeness: {avg_completeness:.1f}%\n")
    
    sys.stderr.write(f"\n✅ Charlotte County scraping complete!\n")

    print(json.dumps(final_records))

if __name__ == "__main__":
    days_back = 21
    max_pages = 10  # Increased from 1 to capture more arrests
    if len(sys.argv) > 1:
        try: days_back = int(sys.argv[1])
        except: pass
    if len(sys.argv) > 2:
        try: max_pages = int(sys.argv[2])
        except: pass
    
    sys.stderr.write(f"🚀 Starting Charlotte County scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n")
    sys.stderr.write(f"📄 Max pages: {max_pages}\n\n")
    
    scrape_charlotte(days_back, max_pages)
