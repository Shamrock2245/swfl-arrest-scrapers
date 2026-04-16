#!/usr/bin/env python3
"""
Broward County Solver — Sequential ID Probing Scraper

Broward Sheriff (BSO) uses an AngularJS SPA at apps.sheriff.org/arrestsearch.
The Angular app renders via a hidden API we can't easily replicate.

**Strategy**: Detail pages at /ArrestSearch/InmateDetail/{JMS_NUMBER} are
publicly accessible and contain full booking data. BSO arrest numbers are
sequential (e.g., 232600590, 232600591...). We probe forward from a known
recent ID to discover today's arrests.

Each detail page contains: Name, DOB, Race, Sex, Height, Weight,
Booking Date/Time, Facility, Charges with bond amounts, and mugshot.

Source: https://apps.sheriff.org/ArrestSearch/InmateDetail/{ID}
Platform: ASP.NET MVC + AngularJS
"""

import sys
import re
import json
import os
import datetime
import time
import concurrent.futures

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[BROWARD] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://apps.sheriff.org"
DETAIL_URL = f"{BASE_URL}/ArrestSearch/InmateDetail"

# Known good ID from April 2026: 232600590
# BSO format: YY26XXXXX where YY seems to be a prefix identifier
KNOWN_RECENT_ID = 232600590

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# State file to track the last known ID between runs
STATE_FILE = os.path.join(os.path.dirname(__file__), '.last_known_id')


def scrape_broward(days_back=7, max_pages=10):
    """Scrape Broward County arrests by probing sequential detail page IDs."""
    sys.stderr.write(f"[BROWARD] Starting sequential ID probe scraper\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Load last known ID from state file, or use the known baseline
    start_id = _load_last_id()
    sys.stderr.write(f"[BROWARD] Starting from ID: {start_id}\n")

    # Phase 1: Find the current frontier — probe forward to find latest valid ID
    frontier = _find_frontier(session, start_id)
    sys.stderr.write(f"[BROWARD] Frontier ID: {frontier}\n")

    # Phase 2: Scrape detail pages from (frontier - range) to frontier
    # For daily runs, scan last ~200 IDs (covers a busy day)
    # For catchup (days_back > 1), scan more
    scan_range = min(200 * days_back, 2000)
    scan_start = max(frontier - scan_range, start_id - 50)

    records = []
    consecutive_misses = 0
    max_consecutive_misses = 20

    for jms_id in range(scan_start, frontier + 100):
        record = _fetch_detail(session, str(jms_id))
        if record:
            records.append(record)
            consecutive_misses = 0
        else:
            consecutive_misses += 1
            if jms_id > frontier and consecutive_misses > max_consecutive_misses:
                break

        # Rate limit: ~5 req/sec
        if len(records) % 10 == 0 and len(records) > 0:
            time.sleep(0.5)

    # Save the highest found ID for next run
    if records:
        max_id = max(int(r.get('Booking_Number', '0')) for r in records)
        _save_last_id(max_id)
        sys.stderr.write(f"[BROWARD] Saved frontier: {max_id}\n")

    sys.stderr.write(f"[BROWARD] Total extracted: {len(records)} records\n")
    return records


def _find_frontier(session, start_id):
    """Binary-search forward to find the approximate latest valid ID."""
    # First, jump forward in big steps to find the boundary
    step = 100
    current = start_id

    # Jump forward until we hit a miss
    while step > 0:
        test_id = current + step
        if _id_exists(session, test_id):
            current = test_id
            step = min(step * 2, 500)  # Accelerate
        else:
            if step <= 1:
                break
            step = step // 2  # Decelerate — binary search

    return current


def _id_exists(session, jms_id):
    """Quick check if an arrest ID exists (HEAD request)."""
    try:
        resp = session.head(f"{DETAIL_URL}/{jms_id}", timeout=8, allow_redirects=False)
        # 200 = exists, 302/404 = doesn't
        return resp.status_code == 200
    except Exception:
        return False


def _fetch_detail(session, jms_number):
    """Fetch and parse a Broward inmate detail page."""
    try:
        resp = session.get(f"{DETAIL_URL}/{jms_number}", timeout=12)
        if resp.status_code != 200:
            return None

        # Quick check — if it redirected to search page, the ID doesn't exist
        if 'arrestsearch' in resp.url.lower() and 'inmatedetail' not in resp.url.lower():
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True)

        # Verify this is actually an inmate detail page
        if 'Arrest Search' in text and 'ARREST NO' not in text and len(text) < 500:
            return None

        record = {
            'County': 'Broward',
            'State': 'FL',
            'Booking_Number': jms_number,
            'Detail_URL': f"{DETAIL_URL}/{jms_number}",
            'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Status': 'In Custody',
        }

        # ---- Parse structured fields ----

        # Name — typically in an h3 or prominent element
        h3 = soup.find('h3')
        if h3:
            name = h3.get_text(strip=True)
            record['Full_Name'] = name
            if ',' in name:
                parts = name.split(',', 1)
                record['Last_Name'] = parts[0].strip()
                first_parts = parts[1].strip().split()
                if first_parts:
                    record['First_Name'] = first_parts[0]
                    if len(first_parts) > 1:
                        record['Middle_Name'] = ' '.join(first_parts[1:])

        # All dates on page
        dates = re.findall(r'(\d{2}/\d{2}/\d{4})', text)
        if len(dates) >= 2:
            record['Booking_Date'] = dates[0]
            record['DOB'] = dates[1]
        elif len(dates) == 1:
            record['Booking_Date'] = dates[0]

        # Race/Sex — typically single letters like "W M" or "B F"
        race_sex = re.search(r'\b([BWHAI])\s+([MF])\b', text)
        if race_sex:
            race_map = {'W': 'White', 'B': 'Black', 'H': 'Hispanic', 'A': 'Asian', 'I': 'Indian'}
            record['Race'] = race_map.get(race_sex.group(1), race_sex.group(1))
            record['Sex'] = race_sex.group(2)

        # Height (3 digits like 510 = 5'10") / Weight
        hw = re.search(r'\b(\d{3})\s+(\d{2,3})\b', text)
        if hw:
            h = hw.group(1)
            if 400 <= int(h) <= 699:  # Valid height range
                record['Height'] = f"{h[0]}'{h[1:]}\""
                record['Weight'] = hw.group(2)

        # Facility
        facilities = ['North Broward', 'Main Jail', 'South Broward',
                      'Joseph V. Conte', 'Paul Rein', 'BSO Main',
                      'Stockade', 'North Detention', 'South Regional']
        for fac in facilities:
            if fac.lower() in text.lower():
                record['Facility'] = fac
                break

        # Charges — look for table rows or lines with charge descriptions
        charges = []
        total_bond = 0.0

        # Try parsing charge table
        charge_tables = soup.find_all('table')
        for ct in charge_tables:
            for row in ct.find_all('tr'):
                row_text = row.get_text(' ', strip=True)
                # Charge rows typically have statute numbers or descriptions
                if re.search(r'\d{3}\.\d{2,3}', row_text) or \
                   any(kw in row_text.upper() for kw in ['BATTERY', 'THEFT', 'ASSAULT', 'DUI',
                       'DRUG', 'POSS', 'BURG', 'ROBBERY', 'FRAUD', 'TRESP', 'RESIST',
                       'DRIVING', 'FLEE', 'VOP', 'PROBATION', 'WARRANT', 'FELONY',
                       'MISDEMEANOR', 'HOLD']):
                    charges.append(row_text.strip())
                    # Extract bond from this row
                    bond_match = re.search(r'\$([\d,]+\.?\d*)', row_text)
                    if bond_match:
                        try:
                            total_bond += float(bond_match.group(1).replace(',', ''))
                        except ValueError:
                            pass

        if charges:
            record['Charges'] = ' | '.join(charges[:15])  # Cap at 15 charges
        if total_bond > 0:
            record['Bond_Amount'] = str(total_bond)

        # Mugshot
        img = soup.find('img', src=lambda s: s and any(
            kw in s.lower() for kw in ['photo', 'image', 'mug', 'inmate', 'booking']))
        if img:
            src = img.get('src', '')
            if not src.startswith('http'):
                src = f"{BASE_URL}{src}"
            record['Mugshot_URL'] = src

        return record

    except Exception as e:
        sys.stderr.write(f"[BROWARD] Error on {jms_number}: {e}\n")
        return None


def _load_last_id():
    """Load the last known arrest ID from state file."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception:
        pass
    return KNOWN_RECENT_ID


def _save_last_id(jms_id):
    """Save the latest arrest ID for the next run."""
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(str(jms_id))
    except Exception:
        pass


if __name__ == "__main__":
    records = scrape_broward()
    print(json.dumps(records, indent=2))
