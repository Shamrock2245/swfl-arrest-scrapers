import sys
import json
import time
import re
import os
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

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

def scrape_sarasota(days_back=7):
    """
    Scrape Sarasota County with date range support and RESUME capability
    Default days_back=7 (covers last week for safety margin)
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
        co.set_browser_path('/usr/bin/chromium-browser')
        
        # Headless mode configurable via HEADLESS environment variable
        co.auto_port() # Use a free port to avoid conflicts
        co.headless(HEADLESS_MODE)
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        # co.set_argument('--disable-gpu') 
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        
        # Custom CF Handler
        def handle_cloudflare(page):
            sys.stderr.write("Checking for Cloudflare... (Please solve CAPTCHA manually if it appears)\n")
            
            # Wait up to 60 seconds
            for i in range(30):
                title = page.title.lower()
                sys.stderr.write(f"[{i*2}s] Page Title: {page.title}\n")
                
                # Success condition
                if "just a moment" not in title and "security" not in title and "attention" not in title:
                    # Double check we have body content
                    if page.ele('tag:body'):
                        sys.stderr.write("✅ Cloudflare cleared!\n")
                        return True
                
                # Attempt to find and click Turnstile (Cloudflare checkbox)
                try:
                    # Strategy 1: Look for the specific Cloudflare checkbox in Shadow DOM
                    # This often appears within a shadow root under #turnstile-wrapper or similar
                    cb = page.ele('css:input[type=checkbox]')
                    if cb and 'turnstile' in str(cb.html).lower():
                         sys.stderr.write("   🖱️ Found generic Turnstile checkbox, clicking...\n")
                         cb.click()
                         time.sleep(2)

                    # Strategy 2: Look for the iframe and click coordinates (DrissionPage handles this well usually)
                    # or look for text 'Verify you are human' and click it
                    verify_text = page.ele('text:Verify you are human')
                    if verify_text:
                         sys.stderr.write("   �️ Found 'Verify you are human' text, clicking...\n")
                         verify_text.click()
                         time.sleep(2)
                except Exception as cf_error:
                    # sys.stderr.write(f"   (CF interaction error: {cf_error})\n")
                    pass

                # If we are stuck for a while, ask user
                if i == 5:
                     sys.stderr.write("⚠️  STUCK? Please click the Cloudflare checkbox manually in the browser window!\n")
                
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
            
            if not handle_cloudflare(page):
                 sys.stderr.write("❌ Could not clear Cloudflare. Stopping.\n")
                 break
            
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
            # Based on diagnosis: name="date", id="date"
            date_input = page.ele('css:input[name="date"]') or \
                         page.ele('#date') or \
                         page.ele('@placeholder=mm/dd/yyyy') or \
                         page.ele('css:input[name="arrest_date"]')
                         
            if not date_input:
                sys.stderr.write("Could not find arrest_date input. Saved HTML to sarasota_debug.html\n")
                current_date += timedelta(days=1)
                continue

            # Clear and type
            try:
                date_input.click()
                date_input.clear()
                time.sleep(0.5)
                date_input.input(arrest_date)
                page.actions.type('\n') # Press Enter
                time.sleep(1)
            except Exception as e:
                sys.stderr.write(f"Error typing date: {e}\n")
            
            # Click Search - Green button saying "SEARCH"
            search_btn = page.ele('text:SEARCH') or page.ele('css:button.btn-success') or page.ele('@type=submit')
            if search_btn:
                # Scroll to ensure visible
                try: search_btn.run_js('this.scrollIntoView()')
                except: pass
                
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
                                if key.lower() in ['arrest date', 'arrested', 'date arrested', 'intake date']:
                                    data['Booking_Date'] = val
                        except:
                            pass
                    
                    # Force set Booking_Date from search context if missing
                    if 'Booking_Date' not in data and 'arrest_date' in locals():
                        data['Booking_Date'] = arrest_date

                    # 3. Charges (Table #data-table)
                    charges = []
                    total_bond = 0.0
                    
                    rows = page.eles('css:#data-table tr')
                    for row in rows:
                        cells = row.eles('tag:td')
                        if len(cells) > 0:
                             # DEBUG: Print columns for the first row to verify mappings
                             if i == 0 and rows.index(row) == 0:
                                 cell_values = [f"[{idx}] {c.text}" for idx, c in enumerate(cells)]
                                 sys.stderr.write(f"   📊 TABLE COLUMNS: { ' | '.join(cell_values) }\n")

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
                            # This is critical for spreadsheet
                            if len(cells) > 6 and 'Booking_Date' not in data:
                                intake_dt = cells[6].text.strip()
                                if intake_dt:
                                    # Fix for Time-Only Booking Dates
                                    # If it looks like a time (e.g. "14:30") and short, prepend the search date
                                    if ':' in intake_dt and len(intake_dt) < 12 and 'arrest_date' in locals():
                                        data['Booking_Date'] = f"{arrest_date} {intake_dt}"
                                    else:
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
                    
                    # NORMALIZE DATA FOR SHEETS
                    data['County'] = 'Sarasota'
                    data['State'] = 'FL'
                    if 'ZIP' in data:
                        data['Zipcode'] = data.pop('ZIP')
                    
                    
                    # CRITICAL: Do NOT use fallback date - skip record if no booking date
                    if not data.get('Booking_Date'):
                        sys.stderr.write("   ⚠️  Missing Booking_Date, skipping record to avoid data corruption\n")
                        continue
                            
                    # Clean up Booking Date format if needed
                    # Scraper output: 2025-11-26 00:29:52.000
                    if 'Booking_Date' in data:
                        # Make sure we have just the date part for the main Booking_Date field 
                        # if the schema expects YYYY-MM-DD. 
                        # But wait, schema says: Booking_Date: str (Fields 10)
                        # The user provided JSON shows full datetime.
                        # Let's clean it to be safe, or leave it if Sheets handles it.
                        # For now, let's leave it, but ensure we populate Arrest_Date
                        pass

                    bdate = data.get('Arrest_Date', data.get('Booking_Date', 'N/A'))
                    sys.stderr.write(f"   👤 Name: {name} | Date: {bdate}\n")

                    # Sanitize and validate record before saving
                    if VALIDATION_AVAILABLE:
                        data = sanitize_record(data)
                        is_valid, issues = validate_record(data, 'Sarasota', strict=False)
                        
                        if not is_valid:
                            sys.stderr.write(f"   ❌ Validation failed:\n")
                            for issue in issues:
                                if issue.startswith('CRITICAL'):
                                    sys.stderr.write(f"      {issue}\n")
                            sys.stderr.write("   ⚠️  Skipping invalid record\n")
                            continue
                        
                        warnings = [i for i in issues if i.startswith('WARNING')]
                        if warnings:
                            sys.stderr.write(f"   ⚠️  {len(warnings)} validation warnings (record will still be saved)\n")

                    if 'Booking_Number' in data or 'Full_Name' in data:
                        records.append(data)
                        
                        # IMMEDIATE SAVE to JSONL
                        with open(progress_file, 'a') as f:
                            f.write(json.dumps(data) + '\n')
                        
                        sys.stderr.write(f"   ✅ Added & Saved record (Total New: {len(records)})\n")
                    else:
                        sys.stderr.write("   ⚠️  Skipping - no booking number or name\n")ta.\n")
                        
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

    # Summary Statistics
    sys.stderr.write(f"\n🎯 Final Summary:\n")
    sys.stderr.write(f"   Records scraped this session: {len(records)}\n")
    sys.stderr.write(f"   Total records in output: {len(final_records)}\n")
    sys.stderr.write(f"   Previously scraped (skipped): {len(processed_ids)}\n")
    sys.stderr.write(f"   Dates searched: {days_back} days\n")
    
    if VALIDATION_AVAILABLE and records:
        from validation import get_data_completeness_score
        completeness_scores = [get_data_completeness_score(r) for r in records]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        sys.stderr.write(f"   Average data completeness: {avg_completeness:.1f}%\n")
    
    sys.stderr.write(f"\n✅ Sarasota County scraping complete!\n")

    print(json.dumps(final_records))

if __name__ == "__main__":
    # Parse command line arguments
    days_back = 7  # Default: Last 7 days for safety margin
    
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except:
            pass
    
    sys.stderr.write(f"🚀 Starting Sarasota County scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n\n")
    
    scrape_sarasota(days_back)
