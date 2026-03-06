#!/usr/bin/env python3
"""
Hendry County Solver - Robust DrissionPage Scraper

Scrapes inmate data from hendrysheriff.org with:
- Reliable label-based field extraction
- Cloudflare/Turnstile handling
- Sorting by newest first
- Clean charge parsing
- Resume support via progress file

Author: SWFL Arrest Scrapers Team
Date: December 13, 2025
"""

import sys
import json
import time
import re
import os
from datetime import datetime

# Force UTF-8 for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Import validation module
try:
    from validation import validate_record, sanitize_record
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    sys.stderr.write("⚠️  Validation module not found, skipping validation\n")

# Configuration: Allow headless mode via environment variable
# Set HEADLESS=false for local debugging, true for automation
HEADLESS_MODE = os.getenv('HEADLESS', 'true').lower() == 'true'


def get_text_by_label(card_ele, label_text):
    """
    Finds an element containing specific label text and returns the value following it.
    Example: Finds 'Gender:', returns 'M'.
    """
    try:
        label_ele = card_ele.ele(f'text:{label_text}', timeout=0.5)
        if label_ele:
            # Get parent's full text (usually "Gender: M")
            full_text = label_ele.parent().text
            # Remove the label to get the value
            clean_value = full_text.replace(label_text, '').strip()
            # If empty, try next sibling
            if not clean_value:
                next_ele = label_ele.next()
                if next_ele:
                    clean_value = next_ele.text.strip()
            return clean_value if clean_value else None
    except:
        pass
    return None


def clean_charge_text(raw_charge):
    """
    Clean charge text to extract only the human-readable description.
    Examples:
        "893.135 - TRAFFICKING IN COCAINE" -> "TRAFFICKING IN COCAINE"
        "316.193(1) - DUI" -> "DUI"
    """
    if not raw_charge:
        return ''
    
    # Remove common prefixes
    text = re.sub(r'^(New Charge:|Weekender:|Charge Description:)\s*', '', raw_charge, flags=re.IGNORECASE)
    
    # Extract text after statute number and dash
    match = re.search(r'[\d.]+[a-z]*\s*-\s*(.+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # If no dash pattern, try removing leading statute
    text = re.sub(r'^[\d.]+[a-z]*\s*', '', text)
    
    # Remove degree indicators like (F1), (M1), etc.
    text = re.sub(r'\s*\([A-Z]\d?\)\s*$', '', text)
    
    return text.strip()


def scrape_hendry(days_back=30):
    """
    Scrape Hendry County inmate roster.
    
    Args:
        days_back: Not currently used for filtering (site shows current inmates only)
    
    Returns:
        List of inmate records as JSON (printed to stdout)
    """
    import os
    import sys
    import json
    
    progress_file = os.path.join(os.path.dirname(__file__), 'hendry_progress.jsonl')
    
    records = []
    processed_ids = set()
    
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            if 'Booking_Number' in rec:
                                processed_ids.add(rec['Booking_Number'])
                        except:
                            pass
        except:
            pass
    
    if processed_ids:
        sys.stderr.write(f"ℹ️  Found {len(processed_ids)} previously scraped records. Resuming...\n")
    
    from playwright.sync_api import sync_playwright
    import re
    from bs4 import BeautifulSoup
    import os
    
    records = []
    
    # Set Playwright temp and browser path to bypass EPERM errors
    os.environ['TMPDIR'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp_userdata_mac_hendry'))
    os.makedirs(os.environ['TMPDIR'], exist_ok=True)
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.playwright-browsers'))
    
    with sync_playwright() as p:
        sys.stderr.write(f"🚦 Starting Hendry County Scraper (Playwright browser)\n")
        
        # Configure the browser profile to avoid basic detection
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--window-size=1920,1080'
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
        )
        page = context.new_page()
        
        # Override navigator.webdriver
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        api_responses = []
        def on_response(response):
            if response.request.resource_type in ["fetch", "xhr"]:
                if "json" in response.headers.get("content-type", "") and "paginatedBlog" in response.url:
                    try:
                        api_responses.append(response.json())
                    except:
                        pass
                        
        page.on("response", on_response)
        
        url = 'https://www.hendrysheriff.org/inmateSearch'
        sys.stderr.write(f"📡 Loading {url}...\n")
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            # --- Wait for Cloudflare Check ---
            for attempt in range(10):
                title = page.title()
                if "just a moment" in title.lower() or "security" in title.lower():
                    sys.stderr.write(f"⏳ [{attempt+1}/10] Waiting for Cloudflare...\n")
                    time.sleep(3)
                else:
                    sys.stderr.write("✅ Page loaded successfully\n")
                    break
                    
            # Handle possible intro disclaimer
            try:
                disclaimer_btn = page.locator("text='I Agree'")
                if disclaimer_btn.is_visible(timeout=2000):
                    disclaimer_btn.click()
                    sys.stderr.write("   👆 Clicked Disclaimer\n")
                    time.sleep(1)
            except:
                pass
                
            # Set newest first - this triggers a new API request if not already sorted
            try:
                sys.stderr.write("📋 Setting sort order to Newest...\n")
                sort_select = page.locator("select.form-select, select#sort")
                if sort_select.count() > 0:
                    try:
                        sort_select.select_option(value="dateDesc")
                        sys.stderr.write("✅ Sorted by Date (Newest First) - by value\n")
                    except:
                        try:
                            sort_select.select_option(label="Newest")
                            sys.stderr.write("✅ Sorted by Date (Newest First) - by text\n")
                        except:
                            sort_select.select_option(index=0)
                            sys.stderr.write("⚠️  Sorted by index 0\n")
                    time.sleep(3)
            except Exception as e:
                sys.stderr.write(f"⚠️  Sort error: {e}\n")
                
            sys.stderr.write("📜 Processing inmates via API interception...\n")
            session_scraped_ids = set()
            page_num = 1
            max_pages = 50 # Safety limit
            
            while page_num <= max_pages:
                sys.stderr.write(f"📄 Processing Page {page_num}...\n")
                
                # Wait for API response for this page
                wait_time = 0
                while len(api_responses) == 0 and wait_time < 15:
                    time.sleep(1)
                    wait_time += 1
                    
                if len(api_responses) == 0:
                    sys.stderr.write(f"⚠️  No API response captured for page {page_num}, stopping.\n")
                    break
                    
                data = api_responses.pop(-1)
                entries = data.get("entries", [])
                
                if not entries:
                    sys.stderr.write(f"⚠️  No entries found in API response on page {page_num}, stopping.\n")
                    break
                    
                sys.stderr.write(f"📊 Found {len(entries)} records in API response on page {page_num}...\n")
                
                for i, entry in enumerate(entries):
                    try:
                        sys.stderr.write(f"🔍 [{i+1}/{len(entries)}] Processing inmate...\n")
                        
                        html_content = entry.get("content", "")
                        if not html_content:
                            sys.stderr.write(f"   ⚠️ No HTML content in API entry.\n")
                            continue
                            
                        soup = BeautifulSoup(html_content, "html.parser")
                        
                        data_obj = {
                            "County": "Hendry",
                            "State": "FL",
                            "Facility": "Hendry County Jail",
                            "Detail_URL": url,
                        }
                        
                        full_name = entry.get("title", entry.get("titleWithFirst", ""))
                        if full_name:
                            data_obj['Full_Name'] = full_name.strip()
                            data_obj['First_Name'] = entry.get("firstName", "").strip()
                            data_obj['Last_Name'] = entry.get("lastName", "").strip()
                            # If empty, try splitting
                            if not data_obj['Last_Name'] and ',' in full_name:
                                parts = full_name.split(',', 1)
                                data_obj['Last_Name'] = parts[0].strip()
                                data_obj['First_Name'] = parts[1].strip()
                                
                        def extract_label_value(label_text):
                            strong_tag = soup.find('b', string=re.compile(label_text, re.IGNORECASE))
                            if not strong_tag:
                                strong_tag = soup.find('strong', string=re.compile(label_text, re.IGNORECASE))
                                
                            if strong_tag and strong_tag.next_sibling:
                                return str(strong_tag.next_sibling).strip().replace(':', '').strip()
                                
                            for node in soup.find_all(string=True):
                                if label_text.lower() in node.lower():
                                    val = str(node).split(label_text, 1)[-1].strip().replace(':', '', 1).strip()
                                    if val:
                                        return val
                            return None
                            
                        booking_number = entry.get("inmateID", extract_label_value("Inmate ID"))
                        if booking_number:
                            data_obj['Booking_Number'] = booking_number
                            if booking_number in processed_ids or booking_number in session_scraped_ids:
                                sys.stderr.write(f"   ⏭️  Skipping {booking_number} (already scraped)\n")
                                continue
                                
                        data_obj['Booking_Date'] = extract_label_value("Booked Date")
                        
                        raw_address = extract_label_value("Address")
                        if raw_address:
                            # Handle <br> tags in address correctly BEFORE replacing newlines
                            for br in soup.find_all("br"):
                                br.replace_with(" ")
                            raw_address = extract_label_value("Address") # re-extract with spaces
                            if raw_address:
                                clean_addr = re.sub(r'\s+', ' ', raw_address).strip()
                                data_obj['Address'] = clean_addr
                                try:
                                    zip_match = re.search(r'\b\d{5}\b$', clean_addr)
                                    if zip_match:
                                        data_obj['ZIP'] = zip_match.group(0)
                                        clean_addr = clean_addr[:zip_match.start()].strip()
                                    state_match = re.search(r'\b[A-Z]{2}\b$', clean_addr)
                                    if state_match:
                                        data_obj['State'] = state_match.group(0)
                                        clean_addr = clean_addr[:state_match.start()].strip().rstrip(',')
                                    if ',' in clean_addr:
                                        parts = clean_addr.rsplit(',', 1)
                                        data_obj['City'] = parts[1].strip()
                                        data_obj['Address'] = parts[0].strip()
                                except:
                                    pass
                                
                        data_obj['Sex'] = extract_label_value("Gender")
                        data_obj['Race'] = extract_label_value("Race")
                        data_obj['Height'] = extract_label_value("Height")
                        data_obj['Weight'] = extract_label_value("Weight")
                        
                        images = entry.get("images", [])
                        if images and isinstance(images, list) and len(images) > 0:
                            img = images[0]
                            if isinstance(img, dict) and img.get("large"):
                                src = img.get("large")
                                data_obj['Mugshot_URL'] = src
                            elif isinstance(img, dict) and img.get("small"):
                                src = img.get("small")
                                data_obj['Mugshot_URL'] = src
                                
                        charges_list = []
                        total_bond = 0.0
                        
                        charge_tags = soup.find_all(string=re.compile("Charge Description:", re.IGNORECASE))
                        for ctag in charge_tags:
                            try:
                                desc_text = str(ctag).split("Charge Description:", 1)[-1].strip()
                                clean_desc = clean_charge_text(desc_text)
                                if clean_desc:
                                    charges_list.append(clean_desc)
                            except:
                                pass
                                
                        bond_tags = soup.find_all(string=re.compile("Bond Amount:", re.IGNORECASE))
                        for btag in bond_tags:
                            try:
                                bond_text = str(btag).split("Bond Amount:", 1)[-1].strip().replace('$', '').replace(',', '').strip()
                                total_bond += float(bond_text)
                            except:
                                pass
                                
                        if charges_list:
                            data_obj['Charges'] = ' | '.join(charges_list)
                        data_obj['Bond_Amount'] = str(total_bond)
                        
                        data_obj = {k: v for k, v in data_obj.items() if v is not None}
                        
                        if VALIDATION_AVAILABLE:
                            data_obj = sanitize_record(data_obj)
                            is_valid, issues = validate_record(data_obj, 'Hendry', strict=False)
                            if not is_valid:
                                continue
                                
                        if data_obj.get('Booking_Number') and data_obj.get('Full_Name'):
                            records.append(data_obj)
                            session_scraped_ids.add(data_obj['Booking_Number'])
                            with open(progress_file, 'a', encoding='utf-8') as f:
                                f.write(json.dumps(data_obj) + '\n')
                            sys.stderr.write(f"   ✅ Saved {data_obj.get('Full_Name')} ({data_obj.get('Booking_Number')})\n")
                            
                    except Exception as e:
                        sys.stderr.write(f"   ❌ Error processing API entry: {e}\n")

                # Pagination
                pagination = data.get("pagination", {})
                if pagination.get("next") == True:
                    try:
                        next_btn = page.locator('button[aria-label="Page Right"]')
                        if next_btn.count() > 0 and next_btn.first.is_visible() and not next_btn.first.is_disabled():
                            sys.stderr.write("➡️  Clicking next page...\n")
                            api_responses.clear() # Clear before clicking
                            next_btn.first.click(timeout=5000)
                            page_num += 1
                        else:
                            sys.stderr.write("🏁 No more pages or next button disabled in UI.\n")
                            break
                    except Exception as e:
                        sys.stderr.write(f"🏁 Next page click failed: {e}\n")
                        break
                else:
                    sys.stderr.write("🏁 API indicates no more pages.\n")
                    break
                    
        except Exception as e:
            sys.stderr.write(f"❌ Playwright execution error: {e}\n")
        finally:
            browser.close()
    
    final_records = []
    seen_ids = set()
    
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        bid = rec.get('Booking_Number')
                        if bid and bid not in seen_ids:
                            final_records.append(rec)
                            seen_ids.add(bid)
                    except:
                        pass
    else:
        final_records = records
    
    sys.stderr.write(f"\n🎯 Final Summary:\n")
    sys.stderr.write(f"   Records scraped this session: {len(records)}\n")
    sys.stderr.write(f"   Total unique records in output: {len(final_records)}\n")
    sys.stderr.write(f"   Previously scraped (skipped): {len(processed_ids)}\n")
    
    if VALIDATION_AVAILABLE and records:
        from validation import get_data_completeness_score
        completeness_scores = [get_data_completeness_score(r) for r in records]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        sys.stderr.write(f"   Average data completeness: {avg_completeness:.1f}%\n")
    
    sys.stderr.write(f"\n✅ Hendry County scraping complete!\n")
    
    print(json.dumps(final_records))
    
if __name__ == "__main__":
    days_back = 30
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except:
            pass
    
    scrape_hendry(days_back)
