#!/usr/bin/env python3
"""
Broward County Solver — AngularJS API Scraper

Broward Sheriff (BSO) uses an AngularJS SPA at apps.sheriff.org/arrestsearch.
The `?d=y` param loads yesterday's arrests with reCAPTCHA hidden.
Detail pages at /ArrestSearch/InmateDetail/{JMS_NUMBER} have full booking data.

Strategy:
  1. Hit the search page with ?d=y (bypasses captcha for daily view)
  2. The Angular app calls an internal API — we replicate the same call
  3. For each arrest, fetch the detail page for charges/bond/DOB/mugshot
  4. Parse the detail HTML for the full record

Source: https://apps.sheriff.org/arrestsearch
Platform: ASP.NET MVC + AngularJS
"""

import sys
import re
import json
import os
import datetime
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[BROWARD] Missing requests/bs4 — install with: pip install requests beautifulsoup4\n")
    sys.exit(1)


BASE_URL = "https://apps.sheriff.org"
SEARCH_URL = f"{BASE_URL}/arrestsearch"
DETAIL_URL = f"{BASE_URL}/ArrestSearch/InmateDetail"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': SEARCH_URL,
}


def scrape_broward(days_back=7, max_pages=10):
    """Scrape Broward County arrests via the BSO AngularJS app."""
    sys.stderr.write(f"[BROWARD] Starting scrape via apps.sheriff.org\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Load the search page with ?d=y (yesterday's arrests, captcha bypassed)
    try:
        resp = session.get(f"{SEARCH_URL}?d=y", timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[BROWARD] FAIL loading search page: {e}\n")
        return []

    # The Angular app makes API calls. We need to find the API endpoint.
    # Try the common BSO API patterns
    api_endpoints = [
        f"{BASE_URL}/api/arrests",
        f"{BASE_URL}/ArrestSearch/GetArrestSearchResults",
        f"{BASE_URL}/arrestsearch/api/search",
    ]

    arrests_data = []

    # Try to hit the API directly with yesterday's date
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%m/%d/%Y')
    today = datetime.datetime.now().strftime('%m/%d/%Y')

    for endpoint in api_endpoints:
        try:
            # Try POST with search params
            payload = {
                'lastName': '%',
                'firstName': '',
                'd': 'y',
            }
            resp = session.post(endpoint, json=payload, timeout=30)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        arrests_data = data
                        sys.stderr.write(f"[BROWARD] API hit: {endpoint} → {len(data)} records\n")
                        break
                except json.JSONDecodeError:
                    pass

            # Try GET
            resp = session.get(f"{endpoint}?d=y", timeout=30)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        arrests_data = data
                        sys.stderr.write(f"[BROWARD] API hit: {endpoint}?d=y → {len(data)} records\n")
                        break
                except json.JSONDecodeError:
                    pass
        except Exception:
            continue

    # If API didn't work, fall back to scraping detail pages from the rendered page
    # The ?d=y page shows yesterday's arrests — we need to use DrissionPage for the
    # Angular rendering, OR iterate through known arrest numbers
    if not arrests_data:
        sys.stderr.write("[BROWARD] API endpoints not found. Falling back to detail page scraping.\n")
        # Try fetching a range of recent arrest numbers
        # BSO arrest numbers are sequential like 232600590
        # We'll try to discover the latest one and work backwards
        arrests_data = _discover_recent_arrests(session)

    if not arrests_data:
        sys.stderr.write("[BROWARD] No arrests found via any method.\n")
        return []

    # Step 2: Fetch detail pages for each arrest
    records = []
    for i, arrest in enumerate(arrests_data):
        jms_number = arrest.get('JMS_NUMBER', '') if isinstance(arrest, dict) else str(arrest)
        if not jms_number:
            continue

        record = _fetch_detail(session, jms_number)
        if record:
            records.append(record)

        # Rate limit
        if i > 0 and i % 10 == 0:
            time.sleep(1)

    sys.stderr.write(f"[BROWARD] Total extracted: {len(records)} records\n")
    return records


def _discover_recent_arrests(session):
    """Try to discover recent arrest numbers by probing detail pages."""
    # This is a fallback — try common number patterns
    # BSO uses format like 2326XXXXX (year 23, 26 = 2026)
    year_prefix = datetime.datetime.now().strftime('%y')
    # Try a few hundred recent IDs
    found = []
    # Start from a known-good number and work forward
    # The user found 232600590 — let's probe around that
    base_ids = [232600590]  # Known good

    for base_id in base_ids:
        for offset in range(-5, 20):
            test_id = str(base_id + offset)
            try:
                resp = session.head(f"{DETAIL_URL}/{test_id}", timeout=10)
                if resp.status_code == 200:
                    found.append({'JMS_NUMBER': test_id})
            except Exception:
                continue

    sys.stderr.write(f"[BROWARD] Discovered {len(found)} arrest IDs via probing\n")
    return found


def _fetch_detail(session, jms_number):
    """Fetch and parse a Broward inmate detail page."""
    try:
        resp = session.get(f"{DETAIL_URL}/{jms_number}", timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        record = {
            'County': 'Broward',
            'State': 'FL',
            'Booking_Number': jms_number,
            'Detail_URL': f"{DETAIL_URL}/{jms_number}",
            'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Status': 'In Custody',
        }

        # Parse the detail page
        text = soup.get_text(' ', strip=True)

        # Name is in h3
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

        # Parse structured data from the detail page
        # Format: "JMS_NUMBER DATE\nLOCATION\nRACE SEX DOB\nHEIGHT WEIGHT HAIR EYES\nFACILITY"
        # Look for DOB pattern
        dob_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if dob_match:
            # First date is booking date, second might be DOB
            dates = re.findall(r'(\d{2}/\d{2}/\d{4})', text)
            if len(dates) >= 2:
                record['Booking_Date'] = dates[0]
                record['DOB'] = dates[1]
            elif dates:
                record['Booking_Date'] = dates[0]

        # Race/Sex
        race_sex_match = re.search(r'\b([BWH])\s+([MF])\b', text)
        if race_sex_match:
            race_map = {'W': 'White', 'B': 'Black', 'H': 'Hispanic'}
            record['Race'] = race_map.get(race_sex_match.group(1), race_sex_match.group(1))
            record['Sex'] = race_sex_match.group(2)

        # Height/Weight
        hw_match = re.search(r'(\d{3})\s+(\d{2,3})\s+([A-Z]{3})\s+([A-Z]{3})', text)
        if hw_match:
            h = hw_match.group(1)
            record['Height'] = f"{h[0]}'{h[1:]}\""
            record['Weight'] = hw_match.group(2)

        # Location/Facility
        facility_keywords = ['North Broward', 'Main Jail', 'South Broward', 'Joseph V. Conte',
                             'Paul Rein', 'Bureau', 'Detention']
        for kw in facility_keywords:
            if kw.lower() in text.lower():
                fac_match = re.search(rf'({kw}[^\n]*)', text, re.IGNORECASE)
                if fac_match:
                    record['Facility'] = fac_match.group(1).strip()
                    break

        # Charges
        charges = []
        total_bond = 0.0
        # Look for charge blocks
        charge_blocks = re.findall(r'(\d+\s+\w+[-\w]*\s+.+?(?:\$[\d,.]+))', text)
        if not charge_blocks:
            # Alternative: find lines with $ amounts
            lines = text.split('\n')
            for line in lines:
                if '$' in line and any(kw in line.upper() for kw in ['BOND', 'MISD', 'FEL', 'CHARGE', 'HOLD']):
                    charges.append(line.strip())
                    bond_match = re.search(r'\$([\d,.]+)', line)
                    if bond_match:
                        try:
                            total_bond += float(bond_match.group(1).replace(',', ''))
                        except ValueError:
                            pass

        if charges:
            record['Charges'] = ' | '.join(charges)
        if total_bond > 0:
            record['Bond_Amount'] = str(total_bond)

        # Mugshot
        img = soup.find('img', src=lambda s: s and ('photo' in s.lower() or 'image' in s.lower() or 'mug' in s.lower()))
        if img:
            src = img.get('src', '')
            if not src.startswith('http'):
                src = f"{BASE_URL}{src}"
            record['Mugshot_URL'] = src

        return record

    except Exception as e:
        sys.stderr.write(f"[BROWARD] Error fetching detail {jms_number}: {e}\n")
        return None


if __name__ == "__main__":
    records = scrape_broward()
    print(json.dumps(records, indent=2))
