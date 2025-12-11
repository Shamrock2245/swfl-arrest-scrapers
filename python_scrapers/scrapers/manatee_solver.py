#!/usr/bin/env python3
"""
Manatee County Arrest Scraper using DrissionPage
Bypasses Cloudflare/iframe security and extracts detailed arrest information
Now with pagination support for historical data collection
"""

import json
import sys
import time
import os
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return " ".join(text.strip().split())

def scrape_manatee_arrests(days_back=21, max_pages=10):
    """
    Scrape Manatee County arrests with RESUME support
    """
    print(f"🚦 Starting Manatee County Scraper", file=sys.stderr)
    print(f"📅 Days back: {days_back}", file=sys.stderr)
    print(f"📄 Max pages: {max_pages}", file=sys.stderr)
    
    progress_file = 'manatee_progress.jsonl'
    
    # Load processed IDs
    processed_ids = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            # Booking_Number or Detail_URL
                            if 'Booking_Number' in rec:
                                processed_ids.add(rec['Booking_Number'])
                            if 'Detail_URL' in rec:
                                processed_ids.add(rec['Detail_URL'])    
                        except: pass
        except: pass
        
    print(f"ℹ️  Found {len(processed_ids)} previously scraped records. Resuming...", file=sys.stderr)

    co = ChromiumOptions()
    co.auto_port()  # Avoid port conflicts
    co.headless(False) # Headful for CF
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        page = ChromiumPage(addr_or_opts=co)
    except Exception as e:
        print(f"❌ Failed to start browser: {e}", file=sys.stderr)
        raise e
    arrests = [] # New records only
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        base_url = "https://manatee-sheriff.revize.com/bookings"
        
        current_page = 1
        all_booking_links = []
        
        # Phase 1: Collect Links
        while current_page <= max_pages:
            print(f"\n📄 Processing page {current_page}...", file=sys.stderr)
            
            if current_page == 1:
                url = base_url
            else:
                url = f"{base_url}?page={current_page}"
            
            print(f"📡 Loading: {url}", file=sys.stderr)
            try:
                page.get(url)
            except Exception as nav_err:
                 print(f"⚠️ Page {current_page} nav error: {nav_err}. Restarting page...", file=sys.stderr)
                 try: page.quit() 
                 except: pass
                 page = ChromiumPage(addr_or_opts=co)
                 page.get(url)

            if "just a moment" in page.title.lower():
                 print("   ⚠️  Encountered Cloudflare, waiting...", file=sys.stderr)
                 time.sleep(5)
            
            time.sleep(3)
            
            booking_links = page.eles('xpath://a[contains(@href, "/bookings/")]')
            
            valid_links = []
            for link in booking_links:
                href = link.attr('href')
                if href and not href.endswith('/bookings') and not href.endswith('/bookings/'):
                    # Check duplication early if possible? No, safer to dedup later
                    valid_links.append(link)
            
            booking_links = valid_links
            print(f"   📋 Found {len(booking_links)} inmates on page {current_page}", file=sys.stderr)
            
            if len(booking_links) == 0:
                print("   ⚠️  No inmates found on this page, stopping pagination", file=sys.stderr)
                break
            
            # Store tuple (text, href)
            for link in booking_links:
                all_booking_links.append((link.text.strip(), link.attr('href')))
            
            next_button = page.ele('text:Next') or page.ele('css:.pagination .next') or page.ele('css:a[rel="next"]') or page.ele('xpath://a[contains(text(), "›")]')
            
            if not next_button:
                next_page_num = current_page + 1
                if not page.ele(f'text:{next_page_num}'):
                    if current_page >= max_pages:
                        print(f"   ℹ️  Reached maximum pages ({max_pages})", file=sys.stderr)
                    else:
                        print("   ℹ️  No more pages available", file=sys.stderr)
                    break
            
            if current_page >= max_pages:
                break

            current_page += 1
            time.sleep(2)
        
        # Dedup Links
        all_booking_links = list(set(all_booking_links))
        print(f"\n📊 Total inmates found: {len(all_booking_links)}", file=sys.stderr)

        # Filter Processed
        original_len = len(all_booking_links)
        filtered_links = []
        for bnum, url in all_booking_links:
            # Check ID logic
            is_processed = False
            # Check URL
            if not url.startswith('http'):
                full_url = f"https://www.manateesheriff.com{url}"
            else:
                full_url = url
            
            if full_url in processed_ids or bnum in processed_ids:
                is_processed = True
            
            if not is_processed:
                filtered_links.append((bnum, url))
        
        all_booking_links = filtered_links
        print(f"📉 Remaining to scrape: {len(all_booking_links)} (skipped {original_len - len(all_booking_links)})", file=sys.stderr)
        
        stopped_early = False
        for idx, (booking_number, detail_url) in enumerate(all_booking_links, 1):
            try:
                if not detail_url.startswith('http'):
                    detail_url = f"https://www.manateesheriff.com{detail_url}"
                
                print(f"\n🔍 [{idx}/{len(all_booking_links)}] Processing: {booking_number}", file=sys.stderr)
                
                page.get(detail_url)
                time.sleep(2)
                
                if "just a moment" in page.title.lower():
                    time.sleep(3)
                
                # record = extract_detail_data(page, booking_number, detail_url)
                # MOVED: Logic to extract data is now robust.
                
                record = extract_detail_data(page, booking_number, detail_url)
                
                # Sanity Check: Booking Date vs Statute
                # User reported Statute (e.g. 948.06) appearing in Booking Date
                if record and 'Booking_Date' in record:
                    bd = record['Booking_Date']
                    # detailed check: if it looks like a float (statute) or doesn't have separators
                    if '.' in bd or ('-' not in bd and '/' not in bd):
                        print(f"   ⚠️  Suspicious Booking Date '{bd}' detected (looks like statute?). Clearing.", file=sys.stderr)
                        del record['Booking_Date']


                
                if record and 'Booking_Date' in record:
                    try:
                        book_date = datetime.strptime(record['Booking_Date'], '%m/%d/%Y')
                        if book_date < cutoff_date:
                            print(f"   ⏸️  Reached cutoff date ({book_date.strftime('%Y-%m-%d')}), stopping...", file=sys.stderr)
                            stopped_early = True
                            break
                    except: pass
                
                if record:
                    arrests.append(record)
                    # AUTO SAVE
                    with open(progress_file, 'a') as f:
                        f.write(json.dumps(record) + '\n')
                    print(f"   ✅ Saved {record.get('Full_Name', 'Unknown')} (Total New: {len(arrests)})", file=sys.stderr)
                
                time.sleep(1)
                
            except Exception as e:
                err_msg = str(e)
                print(f"   ⚠️  Error processing {booking_number}: {err_msg}", file=sys.stderr)
                
                # RECOVERY LOGIC
                if "disconnected" in err_msg.lower() or "connection" in err_msg.lower():
                    print("   🔄 Browser disconnected! Restarting...", file=sys.stderr)
                    try:
                        page.quit()
                    except: pass
                    
                    # Restart Browser
                    time.sleep(2)
                    page = ChromiumPage(addr_or_opts=co)
                    
                    # Retry this one
                    try:
                         print(f"   🔄 Retrying {booking_number}...", file=sys.stderr)
                         page.get(detail_url)
                         time.sleep(2)
                         
                         record = extract_detail_data(page, booking_number, detail_url)
                         if record:
                             arrests.append(record)
                             with open(progress_file, 'a') as f:
                                 f.write(json.dumps(record) + '\n')
                             print(f"   ✅ Saved {record.get('Full_Name', 'Unknown')} (Recovered)", file=sys.stderr)
                    except Exception as retry_err:
                         print(f"   ❌ Retry failed for {booking_number}: {retry_err}", file=sys.stderr)
                
                continue
        
        print(f"\n📊 Total new records collected: {len(arrests)}", file=sys.stderr)
        if stopped_early:
            print("ℹ️  Stopped early due to date cutoff", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        pass
    
    finally:
        try: page.quit()
        except: pass
    
    # OUTPUT ALL
    final_records = []
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            for line in f:
                if line.strip():
                    try: final_records.append(json.loads(line))
                    except: pass
    else:
        final_records = arrests
        
    return final_records

def extract_detail_data(page, booking_number, source_url):
    """
    Extract detailed arrest information from booking detail page
    Uses JavaScript execution for more robust DOM traversal (ported from V2)
    """
    data = {
        'Booking_Number': booking_number,
        'Detail_URL': source_url
    }
    
    try:
        # Use JavaScript to extract all data in one go
        # This is more robust against minor layout changes
        js_data = page.run_js("""
            const result = {};
            
            // 1. Personal Info - Iterate labels
            const labels = document.querySelectorAll('label, th, td, dt');
            labels.forEach(label => {
                const text = label.textContent.trim().replace(/:$/, '');
                let value = null;
                
                // Try parent input (Bootstrap style)
                const parent = label.parentElement;
                const input = parent ? parent.querySelector('input') : null;
                
                // Try next sibling
                const nextSibling = label.nextElementSibling;
                
                if (input) value = input.value || input.textContent;
                else if (nextSibling) value = nextSibling.textContent || nextSibling.value;
                
                if (value) result[text] = value.trim();
            });
            
            // 2. Booking Info from Main Table (#bookings-table)
            const bookTable = document.querySelector('#bookings-table');
            if (bookTable) {
                // Must explicitly target the booking row
                const row = bookTable.querySelector('tr[data-booking]');
                if (row) {
                    const cells = row.querySelectorAll('td');
                    // cells[0]=button, cells[1]=Book#, cells[2]=BookDate, cells[3]=Status
                    if (cells.length >= 3) {
                        result['__Booking_Date'] = cells[2].textContent.trim();
                        if (cells.length > 3) result['__Status'] = cells[3].textContent.trim();
                    }
                }
            }
            
            // 3. Charges from .arrest-table (Exclude mobile duplicate)
            const charges = [];
            document.querySelectorAll('table.arrest-table:not(.table-mobile)').forEach(table => {
                // Ensure we are in a valid table (has headers)
                const headers = Array.from(table.querySelectorAll('th')).map(h => h.textContent.trim());
                if (headers.some(h => h.includes('Statute') || h.includes('Desc'))) {
                    table.querySelectorAll('tbody tr').forEach(row => {
                        const cells = row.querySelectorAll('td');
                        // 0:Date, 1:Statute, 2:Desc, 3:SecDesc, 5:Bond
                        if (cells.length >= 6) {
                            charges.push({
                                date: cells[0].textContent.trim(),
                                statute: cells[1].textContent.trim(),
                                desc: cells[2].textContent.trim(),
                                sec_desc: cells[3].textContent.trim(),
                                bond: cells[5].textContent.trim()
                            });
                        }
                    });
                }
            });
            result['__CHARGES_ARR'] = charges;
            
            // 4. Mugshot
            const img = document.querySelector('img[src*="photo"], img[src*="mugshot"], img[src*="image"]');
            if (img && !img.src.startsWith('data:')) result['__Mugshot'] = img.src;
            if (img && img.src.startsWith('data:')) result['__Mugshot_Base64'] = img.src;

            return result;
        """)
        
        # --- Map JS Result to Schema ---
        
        # Personal Info Mapping
        field_map = {
            'First Name': 'First_Name',
            'Last Name': 'Last_Name',
            'Middle Name': 'Middle_Name',
            'Date of Birth': 'DOB',
            'Race': 'Race',
            'Gender': 'Sex',
            'Address': 'Address',
            'City': 'City',
            'State': 'State',
            'Zip Code': 'Zipcode',
            'Height': 'Height',
            'Weight': 'Weight',
            'Hair': 'Hair_Color',
            'Eye': 'Eye_Color'
        }
        
        for js_key, py_key in field_map.items():
            if js_key in js_data:
                data[py_key] = clean_text(js_data[js_key])
                
        # Full Name Construction
        if 'First_Name' in data and 'Last_Name' in data:
            data['Full_Name'] = f"{data['Last_Name']}, {data['First_Name']}"
            if 'Middle_Name' in data and data['Middle_Name']:
                data['Full_Name'] += f" {data['Middle_Name']}"

        # Booking Info
        if '__Booking_Date' in js_data:
            bd = clean_text(js_data['__Booking_Date'])
            # 2nd Validation Check for Date
            if len(bd) > 5 and ('-' in bd or '/' in bd) and not any(c.isalpha() for c in bd):
                data['Booking_Date'] = bd
        
        if '__Status' in js_data:
            data['Status'] = clean_text(js_data['__Status'])
            
        # Charges & Bond
        charges_list = []
        total_bond = 0.0
        seen_charges = set()
        
        charge_entries = js_data.get('__CHARGES_ARR', [])
        for entry in charge_entries:
            desc = clean_text(entry.get('desc', ''))
            statute = clean_text(entry.get('statute', ''))
            sec_desc = clean_text(entry.get('sec_desc', ''))
            bond_str = clean_text(entry.get('bond', '0'))
            arr_date = clean_text(entry.get('date', ''))
            
            # Use first charge date as Arrest Date if missing
            if 'Arrest_Date' not in data and arr_date:
                data['Arrest_Date'] = arr_date
                
            # Build charge string
            # Format: Statute - Desc (Sec Desc)
            c_str = desc
            if sec_desc and sec_desc != 'A/W':
                c_str += f" ({sec_desc})"
            if statute:
                c_str = f"{statute} - {c_str}"
            
            if c_str:
                charges_list.append(c_str)
                
            # Bond
            try:
                b_val = float(bond_str.replace('$', '').replace(',', ''))
                total_bond += b_val
            except: pass

            
        if charges_list:
            data['Charges'] = " | ".join(charges_list)
        
        data['Bond_Amount'] = str(total_bond)
        
        # Mugshot
        if '__Mugshot' in js_data:
            data['Mugshot_URL'] = js_data['__Mugshot']
        elif '__Mugshot_Base64' in js_data:
            data['Mugshot_URL'] = js_data['__Mugshot_Base64']
        else:
            # Fallback
            data['Mugshot_URL'] = f"https://manatee-sheriff.revize.com/photo?bookingNumber={booking_number}"

    except Exception as e:
        print(f"   ⚠️  Error extracting data: {e}", file=sys.stderr)
    
    return data

def main():
    days_back = 21
    max_pages = 1
    if len(sys.argv) > 1:
        try: days_back = int(sys.argv[1])
        except: pass
    if len(sys.argv) > 2:
        try: max_pages = int(sys.argv[2])
        except: pass
    
    try:
        arrests = scrape_manatee_arrests(days_back, max_pages)
        print(json.dumps(arrests, indent=2))
        return 0 if arrests else 1
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
