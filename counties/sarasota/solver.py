#!/usr/bin/env python3
"""
Sarasota County Arrest Scraper — DrissionPage
Targets: https://cms.revize.com/revize/apps/sarasota/
Platform: Revize CMS (same family as Charlotte, Manatee)
Anti-bot: Cloudflare Managed Challenge (requires JS execution)

3-Phase Approach:
  Phase 1: Date search URL → collect PIN links (paginated)
  Phase 2: PIN pages → resolve to booking detail URLs
  Phase 3: Booking detail pages → extract structured data → JSON output

Usage:
  python sarasota_solver.py              # Scrape today only (days_back=1)
  python sarasota_solver.py 3            # Scrape last 3 days
  python sarasota_solver.py 7 --headed   # 7 days, visible browser

Author: SWFL Arrest Scrapers
Last Updated: 2026-04-03
"""

import sys
import os
import json
import time
import re
import datetime
import argparse
from DrissionPage import ChromiumPage, ChromiumOptions


# ─── Helpers ────────────────────────────────────────────────────────────────

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def clean_charge_text(raw_charge):
    """
    Clean charge text to extract human-readable description.
    Input:  "New Charge: 843.02 - Resisting Officer Without Violence (LEV:M DEG:F 3143) (Principal - P)"
    Output: "Resisting Officer Without Violence"
    """
    if not raw_charge:
        return ''
    text = re.sub(r'^(New Charge:|Weekender:)\s*', '', raw_charge, flags=re.IGNORECASE)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    return text.strip()


# ─── Browser Setup ──────────────────────────────────────────────────────────

def setup_browser(headed=False):
    """Configure and launch DrissionPage browser with anti-detection."""
    co = ChromiumOptions()
    co.auto_port()

    # Docker / CI: use CHROME_PATH if set
    chrome_path = os.getenv("CHROME_PATH")
    if chrome_path:
        co.set_browser_path(chrome_path)

    # Headless mode (default unless --headed or HEADLESS=false)
    headless = not headed and os.getenv("HEADLESS", "true").lower() != "false"
    if headless:
        co.headless(True)
        co.set_argument('--headless=new')

    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--window-size=1920,1080')
    co.set_argument('--ignore-certificate-errors')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    sys.stderr.write(f"🌐 Browser: headless={headless}, chrome={chrome_path or 'default'}\n")
    return ChromiumPage(addr_or_opts=co)


def wait_for_cloudflare(page, max_wait=30):
    """Wait for Cloudflare challenge to clear, if present."""
    waited = 0
    while waited < max_wait:
        title = page.title.lower() if page.title else ''
        if 'just a moment' not in title and 'checking' not in title and 'security challenge' not in title:
            return True
        sys.stderr.write(f"   ⏳ Cloudflare challenge... ({waited}/{max_wait}s)\n")
        time.sleep(1)
        waited += 1
    return False


# ─── Phase 1: Date Search → Collect PINs ────────────────────────────────────

BASE_URL = "https://cms.revize.com/revize/apps/sarasota/"


def collect_pins_for_date(page, date_str):
    """
    Navigate to date search page and collect all unique PINs.
    Returns set of PIN strings.

    Args:
        page: DrissionPage browser instance
        date_str: Date in MM/DD/YYYY format
    """
    pins = set()
    page_num = 1

    while True:
        search_url = f"{BASE_URL}personSearch.php?type=date&date={date_str}"
        if page_num > 1:
            search_url += f"&page={page_num}"

        sys.stderr.write(f"   📄 Page {page_num}: {search_url}\n")
        page.get(search_url)
        time.sleep(2)

        if not wait_for_cloudflare(page):
            sys.stderr.write("   ❌ Cloudflare did not clear on search page\n")
            break

        # Extract PIN links: <a href="pinSearch.php?pin=XXXXX">
        pin_links = page.eles('css:a[href*="pinSearch.php"]')

        if not pin_links:
            if page_num == 1:
                sys.stderr.write(f"   📋 No inmates found for {date_str}\n")
            break

        new_count = 0
        for link in pin_links:
            href = link.attr('href') or ''
            if 'pin=' in href:
                pin = href.split('pin=')[1].split('&')[0].strip().replace('%20', '')
                if pin and pin not in pins:
                    pins.add(pin)
                    new_count += 1

        sys.stderr.write(f"   📋 Page {page_num}: {new_count} new PINs (total: {len(pins)})\n")

        if new_count == 0:
            break

        # Check for next page — look for page links
        next_page_links = page.eles(f'css:a[href*="page={page_num + 1}"]')
        if not next_page_links:
            break

        page_num += 1
        time.sleep(1)

    return pins


# ─── Phase 2: PIN Resolution → Booking URLs ─────────────────────────────────

def resolve_bookings_for_pin(page, pin, target_dates):
    """
    Visit a PIN search page and find booking links matching target dates.
    Returns list of (booking_id, detail_url) tuples.

    Args:
        page: DrissionPage browser instance
        pin: PIN string
        target_dates: Set of date strings (MM/DD/YYYY) we're interested in
    """
    bookings = []
    pin_url = f"{BASE_URL}pinSearch.php?pin={pin}"

    try:
        page.get(pin_url)
        time.sleep(2)

        if not wait_for_cloudflare(page):
            sys.stderr.write(f"   ⚠️ Cloudflare on PIN page for {pin}\n")
            return bookings

        # Look for booking links in search result rows
        # Try table rows first
        rows = page.eles('css:tr.search-row') or page.eles('css:tr')

        for row in rows:
            cells = row.eles('tag:td')
            if len(cells) >= 3:
                arrest_date = clean_text(cells[0].text)
                # Check if this arrest matches one of our target dates
                if arrest_date in target_dates:
                    # Find booking link in this row
                    booking_link = row.ele('css:a[href*="booking.php"]') or \
                                   row.ele('css:a[href*="viewInmate.php"]')
                    if booking_link:
                        href = booking_link.attr('href') or ''
                        href = href.replace('%20', '').strip()
                        if not href.startswith('http'):
                            href = BASE_URL + href
                        # Extract booking ID
                        booking_id = ''
                        if 'id=' in href:
                            booking_id = href.split('id=')[1].split('&')[0]
                        elif 'pin=' in href:
                            booking_id = href.split('pin=')[1].split('&')[0]
                        bookings.append((booking_id or pin, href))

        # If no table rows, look for any booking/viewInmate links on the page
        if not bookings:
            all_links = page.eles('css:a[href*="booking.php"]') or \
                        page.eles('css:a[href*="viewInmate.php"]')
            for link in all_links:
                href = link.attr('href') or ''
                href = href.replace('%20', '').strip()
                if not href.startswith('http'):
                    href = BASE_URL + href
                booking_id = ''
                if 'id=' in href:
                    booking_id = href.split('id=')[1].split('&')[0]
                bookings.append((booking_id or pin, href))

    except Exception as e:
        sys.stderr.write(f"   ⚠️ Error resolving PIN {pin}: {e}\n")

    return bookings


# ─── Phase 3: Detail Extraction ─────────────────────────────────────────────

def extract_detail(page, booking_id, detail_url):
    """
    Extract structured data from a booking detail page.
    Uses both DrissionPage element selectors and JS extraction.
    """
    data = {
        'Booking_Number': booking_id,
        'Detail_URL': detail_url,
        'County': 'Sarasota',
        'State': 'FL',
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    try:
        page.get(detail_url)
        time.sleep(2)

        if not wait_for_cloudflare(page):
            sys.stderr.write("   ⚠️ Cloudflare on detail page\n")
            return data

        # --- Name from h1.page-title ---
        h1 = page.ele('css:h1.page-title')
        if h1:
            raw_name = h1.text.split('Print')[0].strip()
            data['Full_Name'] = raw_name
            if ',' in raw_name:
                parts = raw_name.split(',', 1)
                data['Last_Name'] = parts[0].strip()
                data['First_Name'] = parts[1].strip()

        # --- Personal Info from div.text-right labels ---
        field_map = {
            'dob': 'DOB',
            'date of birth': 'DOB',
            'race': 'Race',
            'sex': 'Sex',
            'gender': 'Sex',
            'height': 'Height',
            'weight': 'Weight',
            'address': 'Address',
            'city': 'City',
            'state': 'State',
            'zip code': 'Zipcode',
            'zip': 'Zipcode',
            'facility': 'Facility',
            'agency': 'Agency',
            'arrest date': 'Booking_Date',
            'arrested': 'Booking_Date',
            'date arrested': 'Booking_Date',
            'booking date': 'Booking_Date',
            'intake date': 'Booking_Date',
        }

        label_divs = page.eles('css:div.text-right')
        for ld in label_divs:
            key = ld.text.replace(':', '').strip()
            key_lower = key.lower()
            try:
                val_div = ld.next()
                if val_div:
                    val = clean_text(val_div.text)
                    if val and key_lower in field_map:
                        schema_key = field_map[key_lower]
                        if schema_key not in data or not data[schema_key]:
                            data[schema_key] = val
            except Exception:
                pass

        # --- Charges from #data-table ---
        charges = []
        total_bond = 0.0

        charge_rows = page.eles('css:#data-table tr')
        for row in charge_rows:
            cells = row.eles('tag:td')
            if len(cells) > 4:
                # Column layout: 0=Booking#, 1=Offense, 2=Counts?, 3=Arraign?, 4=Bond, ...6=Intake
                if not data.get('Booking_Number') or data['Booking_Number'] == booking_id:
                    bn = clean_text(cells[0].text)
                    if bn:
                        data['Booking_Number'] = bn

                charge_desc = clean_text(cells[1].text)
                if charge_desc:
                    clean_desc = clean_charge_text(charge_desc)
                    if clean_desc:
                        charges.append(clean_desc)

                bond_str = cells[4].text.replace('$', '').replace(',', '').strip()
                try:
                    if bond_str:
                        total_bond += float(bond_str)
                except ValueError:
                    pass

                # Intake date from column 6 as fallback
                if len(cells) > 6 and not data.get('Booking_Date'):
                    intake = clean_text(cells[6].text)
                    if intake and ('/' in intake or '-' in intake):
                        data['Booking_Date'] = intake

        # --- Also try div.offense blocks (alternate booking.php layout) ---
        if not charges:
            offense_divs = page.eles('css:div.offense')
            for off_div in offense_divs:
                charge_data = {}
                label_pairs = off_div.eles('css:div.text-right')
                for lp in label_pairs:
                    lbl = lp.text.replace(':', '').strip()
                    try:
                        vp = lp.next()
                        if vp:
                            charge_data[lbl] = clean_text(vp.text)
                    except Exception:
                        pass

                desc = charge_data.get('Charge Description', '') or charge_data.get('Offense', '')
                if desc:
                    charges.append(clean_charge_text(desc))

                bond_val = charge_data.get('Bond Amount', '0').replace('$', '').replace(',', '')
                try:
                    total_bond += float(bond_val)
                except ValueError:
                    pass

                if not data.get('Booking_Date'):
                    for dk in ['Arrest Date', 'Date Arrested', 'Booking Date', 'Intake Date']:
                        if charge_data.get(dk):
                            data['Booking_Date'] = charge_data[dk]
                            break

        if charges:
            data['Charges'] = " | ".join(charges)
        data['Bond_Amount'] = str(total_bond)

        # --- Mugshot ---
        mug = page.ele('css:.mug img') or page.ele('css:img[alt*="mugshot"]')
        if mug:
            src = mug.attr('src')
            if src and not src.startswith('data:'):
                if not src.startswith('http'):
                    src = BASE_URL + src
                data['Mugshot_URL'] = src

    except Exception as e:
        sys.stderr.write(f"   ⚠️ Error extracting detail: {e}\n")

    return data


# ─── Main Scraper ────────────────────────────────────────────────────────────

def scrape_sarasota(days_back=1, max_pages=30, headed=False):
    """
    Main scraper entry point.

    Args:
        days_back: Number of days to scrape (1 = today only)
        max_pages: Max pagination pages per date search (safety limit)
        headed: If True, show the browser window

    Returns:
        List of arrest record dicts
    """
    sys.stderr.write(f"🏖️  Sarasota County Scraper (DrissionPage)\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    # Build list of target dates
    today = datetime.datetime.now()
    target_dates = set()
    date_list = []
    for i in range(days_back):
        d = today - datetime.timedelta(days=i)
        date_str = d.strftime('%m/%d/%Y')
        target_dates.add(date_str)
        date_list.append(date_str)

    sys.stderr.write(f"📅 Target dates: {', '.join(date_list)}\n\n")

    page = setup_browser(headed=headed)

    try:
        # ─── Phase 1: Collect PINs across all target dates ───
        sys.stderr.write("═══ Phase 1: Collecting PINs from date searches ═══\n")
        all_pins = {}  # pin → set of dates it appeared on

        for date_str in date_list:
            sys.stderr.write(f"\n🔍 Searching: {date_str}\n")
            pins = collect_pins_for_date(page, date_str)
            for pin in pins:
                if pin not in all_pins:
                    all_pins[pin] = set()
                all_pins[pin].add(date_str)
            time.sleep(1)

        sys.stderr.write(f"\n📊 Phase 1 complete: {len(all_pins)} unique PINs\n")

        if not all_pins:
            sys.stderr.write("⚠️ No inmates found for any target date.\n")
            return []

        # ─── Phase 2: Resolve PINs → Booking URLs ───
        sys.stderr.write("\n═══ Phase 2: Resolving PINs to booking URLs ═══\n")
        booking_set = set()  # (booking_id, url) — deduped
        booking_list = []

        for idx, (pin, pin_dates) in enumerate(all_pins.items(), 1):
            sys.stderr.write(f"📝 [{idx}/{len(all_pins)}] PIN: {pin}\n")
            bookings = resolve_bookings_for_pin(page, pin, pin_dates)
            for b in bookings:
                if b[1] not in booking_set:
                    booking_set.add(b[1])
                    booking_list.append(b)
            time.sleep(1)

        sys.stderr.write(f"\n📊 Phase 2 complete: {len(booking_list)} booking URLs\n")

        if not booking_list:
            # Fallback: if PIN resolution found no bookings, try direct viewInmate links
            sys.stderr.write("⚠️ No bookings from PIN resolution. Trying direct links...\n")
            for date_str in date_list:
                search_url = f"{BASE_URL}personSearch.php?type=date&date={date_str}"
                page.get(search_url)
                time.sleep(2)
                if wait_for_cloudflare(page):
                    direct_links = page.eles('css:a[href*="viewInmate.php"]') or \
                                   page.eles('css:a[href*="booking.php"]')
                    for link in direct_links:
                        href = link.attr('href') or ''
                        href = href.replace('%20', '').strip()
                        if not href.startswith('http'):
                            href = BASE_URL + href
                        if href not in booking_set:
                            booking_set.add(href)
                            bid = href.split('=')[-1] if '=' in href else ''
                            booking_list.append((bid, href))

            sys.stderr.write(f"📊 Fallback found: {len(booking_list)} direct links\n")

        if not booking_list:
            sys.stderr.write("⚠️ No booking links found at all.\n")
            return []

        # ─── Phase 3: Extract Details ───
        sys.stderr.write(f"\n═══ Phase 3: Extracting details from {len(booking_list)} bookings ═══\n")
        arrests = []

        for idx, (booking_id, detail_url) in enumerate(booking_list, 1):
            sys.stderr.write(f"\n🔍 [{idx}/{len(booking_list)}] {booking_id}\n")

            try:
                record = extract_detail(page, booking_id, detail_url)

                if record.get('Full_Name'):
                    arrests.append(record)
                    bond = record.get('Bond_Amount', '0')
                    sys.stderr.write(f"   ✅ {record['Full_Name']} — Bond: ${bond}\n")
                else:
                    sys.stderr.write(f"   ⚠️ No name extracted, skipping\n")

            except Exception as e:
                sys.stderr.write(f"   ⚠️ Error: {e}\n")
                continue

            time.sleep(1)  # Polite delay

        sys.stderr.write(f"\n{'═' * 60}\n")
        sys.stderr.write(f"📊 Sarasota scraper complete: {len(arrests)} records\n")
        sys.stderr.write(f"{'═' * 60}\n")
        return arrests

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return []

    finally:
        try:
            page.quit()
        except Exception:
            pass


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Sarasota County Arrest Scraper')
    parser.add_argument('days_back', nargs='?', type=int, default=1,
                        help='Number of days back to scrape (default: 1 = today)')
    parser.add_argument('--max-pages', type=int, default=30,
                        help='Max pagination pages per date (default: 30)')
    parser.add_argument('--headed', action='store_true',
                        help='Show browser window (default: headless)')
    args = parser.parse_args()

    sys.stderr.write(f"🚀 Starting Sarasota County scraper\n")
    sys.stderr.write(f"📅 Days back: {args.days_back}\n")
    sys.stderr.write(f"📄 Max pages: {args.max_pages}\n\n")

    arrests = scrape_sarasota(
        days_back=args.days_back,
        max_pages=args.max_pages,
        headed=args.headed
    )

    # JSON to stdout (records or empty array)
    print(json.dumps(arrests))
    return 0 if arrests else 1


if __name__ == "__main__":
    sys.exit(main())
