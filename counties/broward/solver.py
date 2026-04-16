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

# Calibrated 04/16/2026:
#   232600590 = 03/05/2026, 232601027 = 04/15/2026
#   437 IDs across 42 days → ~10.4 arrests/day
#   ~38% of sequential IDs are valid (gaps of 1-3 between records)
#   Format: 2326XXXXX (23 = prefix, 26 = year, XXXXX = sequence)
KNOWN_RECENT_ID = 232601027
ARRESTS_PER_DAY = 11  # Conservative estimate
ID_DENSITY = 0.38     # ~38% of IDs have records

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

    # Phase 2: Scrape detail pages from start_id to frontier + buffer
    # At ~10 arrests/day with 38% density, 1 day ≈ ~29 IDs to scan
    # We scan from start_id to frontier + small buffer for late-arriving IDs
    ids_per_day = int(ARRESTS_PER_DAY / ID_DENSITY)  # ~29 IDs to scan per day
    scan_range = ids_per_day * days_back
    scan_start = max(frontier - scan_range, start_id)

    records = []
    consecutive_misses = 0
    max_consecutive_misses = 10  # At 38% density, 10 misses = very likely past frontier

    for jms_id in range(scan_start, frontier + 50):
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
    """Quick check if an arrest ID exists."""
    try:
        # Use GET since BSO may not support HEAD properly
        resp = session.get(f"{DETAIL_URL}/{jms_id}", timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return False
        # Check for actual inmate content (h3 with name)
        return '<h3' in resp.text and len(resp.text) > 1000
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
        h3 = soup.find('h3')
        if not h3 or len(text) < 200:
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

        # Name — in the h3 element (already found above)
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

        # Dates — BSO format: "232601026 04/16/2026" then "W M 09/29/1986"
        # First date after booking number is booking date, date after race/sex is DOB
        dates = re.findall(r'(\d{2}/\d{2}/\d{4})', text)
        if len(dates) >= 2:
            record['Booking_Date'] = dates[0]
            record['DOB'] = dates[1]
        elif len(dates) == 1:
            record['Booking_Date'] = dates[0]

        # Arrest location — appears right after booking date on BSO pages
        # Format: "232601026 04/16/2026\nPOMPANO BEACH"
        loc_match = re.search(r'\d{2}/\d{2}/\d{4}\s+([A-Z][A-Z\s]+?)\s+[BWHAI]\s+[MF]', text)
        if loc_match:
            record['Arrest_Location'] = loc_match.group(1).strip()

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

        # Charges — BSO format: "893.13-6a(Fent) POSSESSION OF FENTANYL"
        # Bond format: "PENDING TRIAL BD $1,000.00" or "BOND DECR BD $5.00"
        charges = []
        total_bond = 0.0

        # Match BSO charge pattern: statute + description
        charge_matches = re.findall(
            r'(\d{2,3}\.\d{2,3}[^\n]*?(?:POSSESSION|BATTERY|ASSAULT|THEFT|DUI|DRUG|'
            r'BURG|ROBBERY|FRAUD|RESIST|DRIVING|FLEE|VOP|PROBATION|WARRANT|'
            r'FELONY|MISDEMEANOR|VIOLATION|CAPIAS|HOLD|TRESPASS|CARRY|WEAPON|'
            r'MURDER|HOMICIDE|SEXUAL|LEWD|CHILD|DOMESTIC|STALKING|FLEE|'
            r'IMMIGRATION|CONTEMPT|FAIL)[^\n]*)',
            text, re.I
        )
        for cm in charge_matches:
            charges.append(cm.strip())

        # Also catch non-statute charges (immigration holds, capias, etc)
        hold_matches = re.findall(
            r'((?:HLD|CAP|FTA|VOP|HOLD)[A-Z-]*\s+[A-Z][A-Z\s-]+)',
            text
        )
        for hm in hold_matches:
            if hm.strip() not in charges:
                charges.append(hm.strip())

        # Extract all bond amounts
        bond_matches = re.findall(r'\$([\d,]+\.\d{2})', text)
        for bm in bond_matches:
            try:
                total_bond += float(bm.replace(',', ''))
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
