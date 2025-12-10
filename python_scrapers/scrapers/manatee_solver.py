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
                
                # DEBUG: Dump HTML and exit
                with open('manatee_debug_detail.html', 'w', encoding='utf-8') as f:
                    f.write(page.html)
                print("🚨 DUMPED HTML to manatee_debug_detail.html - STOPPING FOR DEBUG", file=sys.stderr)
                sys.exit(0)

                record = extract_detail_data(page, booking_number, detail_url)
                
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
    """
    data = {
        'Booking_Number': booking_number,
        'Detail_URL': source_url
    }
    
    try:
        personal_fields = {
            'First Name': 'First_Name',
            'Last Name': 'Last_Name',
            'Middle Name': 'Middle_Name',
            'Date of Birth': 'DOB',
            'Race': 'Race',
            'Gender': 'Sex',
            'Hair': 'Hair_Color',
            'Eye': 'Eye_Color',
            'Height': 'Height',
            'Weight': 'Weight'
        }
        
        for field_label, output_key in personal_fields.items():
            field_elem = page.ele(f'xpath://text()[contains(., "{field_label}")]')
            if field_elem:
                parent = field_elem.parent()
                value_elem = parent.ele('tag:input') or parent.next()
                if value_elem:
                    value = value_elem.attr('value') or value_elem.text
                    if value:
                        data[output_key] = clean_text(value)
        
        if 'First_Name' in data and 'Last_Name' in data:
            data['Full_Name'] = f"{data['Last_Name']}, {data['First_Name']}"
        
        booking_table = page.ele('xpath://table[.//th[contains(text(), "Book #")]]')
        if booking_table:
            rows = booking_table.eles('tag:tr')[1:]
            for row in rows:
                cells = row.eles('tag:td')
                if len(cells) >= 3:
                    book_num = clean_text(cells[0].text)
                    book_date = clean_text(cells[1].text)
                    released = clean_text(cells[2].text)
                    if book_num:
                        data['Booking_Date'] = book_date
                        data['Released_Date'] = released
        
        charges_table = page.ele('xpath://table[.//th[contains(text(), "Arrest Date")] or .//th[contains(text(), "Statute")]]')
        charges_list = []
        bonds_list = []
        statutes_list = []
        arrest_dates = []
        
        if charges_table:
            rows = charges_table.eles('tag:tr')[1:]
            for row in rows:
                cells = row.eles('tag:td')
                if len(cells) >= 6:
                    arrest_date = clean_text(cells[0].text)
                    statute = clean_text(cells[1].text)
                    desc = clean_text(cells[2].text)
                    sec_desc = clean_text(cells[3].text)
                    # obts = clean_text(cells[4].text)
                    bond_amt = clean_text(cells[5].text)
                    
                    if desc:
                        charge_text = desc
                        if statute:
                            charge_text = f"{statute} - {charge_text}"
                        if sec_desc and sec_desc != 'A/W':
                            charge_text = f"{charge_text} ({sec_desc})"
                        
                        charges_list.append(charge_text)
                        
                        if statute:
                            statutes_list.append(statute)
                        if bond_amt:
                            bonds_list.append(bond_amt)
                        if arrest_date:
                            arrest_dates.append(arrest_date)
        
        if charges_list:
            data['Charges'] = ' | '.join(charges_list)
        
        if bonds_list:
            total_bond = sum(float(b.replace(',', '').replace('$', '')) for b in bonds_list if b.replace(',', '').replace('$', '').replace('.', '').isdigit())
            data['Bond_Amount'] = str(total_bond)
        else:
            data['Bond_Amount'] = '0'
        
        if arrest_dates:
            data['Arrest_Date'] = arrest_dates[0]
        
        mugshot = page.ele('xpath://img[contains(@src, "photo") or contains(@src, "mugshot") or contains(@src, "image")]')
        if mugshot:
            mugshot_src = mugshot.attr('src')
            if mugshot_src and not mugshot_src.startswith('data:'):
                if not mugshot_src.startswith('http'):
                    mugshot_src = f"https://www.manateesheriff.com{mugshot_src}"
                data['Mugshot_URL'] = mugshot_src
        
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
