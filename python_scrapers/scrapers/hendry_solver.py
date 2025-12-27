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
from DrissionPage import ChromiumPage, ChromiumOptions

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
    records = []
    progress_file = 'hendry_progress.jsonl'
    
    # Load previously processed IDs for resume support
    processed_ids = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            rec = json.loads(line)
                            if rec.get('Booking_Number'):
                                processed_ids.add(rec['Booking_Number'])
                        except:
                            pass
        except:
            pass
    
    if processed_ids:
        sys.stderr.write(f"ℹ️  Found {len(processed_ids)} previously scraped records. Resuming...\n")
    
    # Browser Setup
    co = ChromiumOptions()
    co.set_browser_path('/usr/bin/chromium-browser')
    co.auto_port()
    # Check environment variable for headless mode (default to False for dev)
    is_headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    co.headless(is_headless)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--ignore-certificate-errors')
    co.set_argument('--disable-blink-features=AutomationControlled')
    
    # Headless mode configurable via HEADLESS environment variable
    co.headless(HEADLESS_MODE)
    
    page = ChromiumPage(co)
    
    try:
        url = 'https://www.hendrysheriff.org/inmateSearch'
        sys.stderr.write(f"🚦 Starting Hendry County Scraper\n")
        sys.stderr.write(f"📡 Loading {url}...\n")
        page.get(url)
        
        # Cloudflare Check
        for attempt in range(10):
            title = page.title.lower()
            if "just a moment" in title or "security" in title:
                sys.stderr.write(f"⏳ [{attempt+1}/10] Waiting for Cloudflare...\n")
                time.sleep(2)
            else:
                sys.stderr.write("✅ Page loaded successfully\n")
                break
        
        # Sort by Newest First (CRITICAL REQUIREMENT)
        try:
            sys.stderr.write("📋 Setting sort order to Newest...\n")
            sort_select = page.ele('css:select.form-select') or page.ele('css:select#sort')
            if sort_select:
                # Try by value first (most reliable)
                try:
                    sort_select.select.by_value('dateDesc')
                    time.sleep(3)
                    sys.stderr.write("✅ Sorted by Date (Newest First) - by value\n")
                except:
                    # Fallback: Try by text
                    try:
                        sort_select.select.by_text('Newest')
                        time.sleep(3)
                        sys.stderr.write("✅ Sorted by Date (Newest First) - by text\n")
                    except:
                        # Fallback: Try by index (assuming newest is first option)
                        sort_select.select.by_index(0)
                        time.sleep(3)
                        sys.stderr.write("⚠️  Sorted by index 0 (verify this is newest!)\n")
            else:
                sys.stderr.write("⚠️  WARNING: Could not find sort dropdown! Results may not be sorted by newest.\n")
        except Exception as e:
            sys.stderr.write(f"⚠️  Sort error: {e}\n")
            sys.stderr.write("⚠️  CRITICAL: Sorting failed! Recent arrests may be missed.\n")
        
        # Find Inmate Cards via "Read More" buttons
        read_more_buttons = page.eles('text:Read More')
        sys.stderr.write(f"📊 Found {len(read_more_buttons)} inmates on page\n\n")
        
        # Track session duplicates
        session_scraped_ids = set()
        
        for i, btn in enumerate(read_more_buttons):
            try:
                sys.stderr.write(f"🔍 [{i+1}/{len(read_more_buttons)}] Processing inmate...\n")
                
                # Scroll into view and click
                btn.run_js('this.scrollIntoView({block: "center"})')
                time.sleep(0.3)
                btn.click()
                time.sleep(1)
                
                # Find the card container (go up through parent elements)
                card = btn.parent(4)  # Jump to main card container
                if not card:
                    card = btn.parent(3)
                if not card:
                    card = page.ele('tag:body')
                
                data = {
                    "County": "Hendry",
                    "State": "FL",
                    "Facility": "Hendry County Jail"
                }
                
                # --- 1. NAME ---
                name_ele = card.ele('tag:h3') or card.ele('tag:h4') or card.ele('tag:h2')
                if name_ele:
                    full_name = name_ele.text.strip()
                    data['Full_Name'] = full_name
                    if ',' in full_name:
                        parts = full_name.split(',', 1)
                        data['Last_Name'] = parts[0].strip()
                        data['First_Name'] = parts[1].strip()
                    else:
                        data['Last_Name'] = full_name
                        data['First_Name'] = ''
                
                # --- 2. BOOKING INFO ---
                booking_number = get_text_by_label(card, "Inmate ID:")
                if booking_number:
                    data['Booking_Number'] = booking_number
                    
                    # Check for duplicates
                    if booking_number in processed_ids:
                        sys.stderr.write(f"   ⏭️  Skipping {booking_number} (already scraped)\n")
                        try:
                            read_less = card.ele('text:Read Less')
                            if read_less:
                                read_less.click()
                        except:
                            pass
                        continue
                    
                    if booking_number in session_scraped_ids:
                        sys.stderr.write(f"   ⏭️  Skipping {booking_number} (duplicate on page)\n")
                        continue
                
                booking_date = get_text_by_label(card, "Booked Date:")
                if booking_date:
                    data['Booking_Date'] = booking_date
                
                # --- 3. DEMOGRAPHICS ---
                data['Sex'] = get_text_by_label(card, "Gender:")
                data['Race'] = get_text_by_label(card, "Race:")
                data['Height'] = get_text_by_label(card, "Height:")
                data['Weight'] = get_text_by_label(card, "Weight:")
                
                raw_address = get_text_by_label(card, "Main Address:")
                if raw_address:
                    data['Address'] = raw_address.replace('\n', ' ').strip()
                
                # --- 4. MUGSHOT ---
                img = card.ele('tag:img')
                if img:
                    src = img.attr('src')
                    if src and 'placeholder' not in src.lower():
                        if src.startswith('/'):
                            src = 'https://www.hendrysheriff.org' + src
                        data['Mugshot_URL'] = src
                
                # --- 5. CHARGES ---
                charges_list = []
                total_bond = 0.0
                
                # Find all charge description labels
                charge_labels = card.eles('text:Charge Description:')
                
                for label in charge_labels:
                    try:
                        desc_text = label.parent().text.replace("Charge Description:", "").strip()
                        clean_desc = clean_charge_text(desc_text)
                        if clean_desc:
                            charges_list.append(clean_desc)
                        
                        # Find Bond Amount in same row
                        charge_row = label.parent(2)
                        if charge_row:
                            bond_label = charge_row.ele('text:Bond Amount:')
                            if bond_label:
                                bond_text = bond_label.parent().text
                                bond_text = bond_text.replace("Bond Amount:", "").replace('$', '').replace(',', '').strip()
                                try:
                                    total_bond += float(bond_text)
                                except:
                                    pass
                    except:
                        continue
                
                if charges_list:
                    data['Charges'] = ' | '.join(charges_list)
                data['Bond_Amount'] = str(total_bond)
                
                data['Detail_URL'] = url
                
                # Remove None values
                data = {k: v for k, v in data.items() if v is not None}
                
                # Sanitize and validate record before saving
                if VALIDATION_AVAILABLE:
                    data = sanitize_record(data)
                    is_valid, issues = validate_record(data, 'Hendry', strict=False)
                    
                    if not is_valid:
                        sys.stderr.write(f"   ❌ Validation failed:\n")
                        for issue in issues:
                            if issue.startswith('CRITICAL'):
                                sys.stderr.write(f"      {issue}\n")
                        sys.stderr.write(f"   ⚠️  Skipping invalid record\n")
                        continue
                    
                    warnings = [i for i in issues if i.startswith('WARNING')]
                    if warnings:
                        sys.stderr.write(f"   ⚠️  {len(warnings)} validation warnings (record will still be saved)\n")
                
                # Validate and save
                if data.get('Booking_Number') and data.get('Full_Name'):
                    records.append(data)
                    session_scraped_ids.add(data['Booking_Number'])
                    
                    # Auto-save for resume
                    with open(progress_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(data) + '\n')
                    
                    sys.stderr.write(f"   ✅ Saved {data.get('Full_Name')} ({data.get('Booking_Number')}) - Total: {len(records)}\n")
                else:
                    sys.stderr.write(f"   ⚠️  Skipping - missing name or booking number\n")
                
                # Collapse card
                try:
                    read_less = card.ele('text:Read Less')
                    if read_less:
                        read_less.click()
                        time.sleep(0.3)
                except:
                    pass
                
            except Exception as e:
                sys.stderr.write(f"   ❌ Error: {e}\n")
                continue
        
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
        try:
            page.quit()
        except:
            pass
    
    # Combine with previously saved records for final output
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
    
    # Summary Statistics
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
