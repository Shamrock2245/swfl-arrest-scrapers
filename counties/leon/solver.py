#!/usr/bin/env python3
"""
Leon County Solver — Inmate Search Scraper (Tallahassee)

Leon County SO uses a search form at leoncountyso.com.
Strategy: Submit search with wildcard/empty name to get roster,
or iterate A-Z last name searches to get all inmates.

Source: https://www.leoncountyso.com/resources/inmate-search
Platform: Custom web form
"""

import sys
import re
import json
import os
import datetime
import time
import string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[LEON] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://www.leoncountyso.com"
SEARCH_URL = f"{BASE_URL}/resources/inmate-search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_leon(days_back=7, max_pages=10):
    """Scrape Leon County inmates by iterating A-Z last name prefix."""
    sys.stderr.write(f"[LEON] Starting scrape → {SEARCH_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    all_records = {}  # Dedup by booking number

    # Try submitting with each letter of the alphabet
    for letter in string.ascii_uppercase:
        sys.stderr.write(f"[LEON] Searching last name: {letter}...\n")

        try:
            # POST the search form
            payload = {
                'FirstName': '',
                'LastName': letter,
                'submit': 'Search Poster',
            }
            resp = session.post(SEARCH_URL, data=payload, timeout=30)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            records = _parse_results(soup)

            for rec in records:
                key = rec.get('Booking_Number') or rec.get('Full_Name', '')
                if key and key not in all_records:
                    all_records[key] = rec

            sys.stderr.write(f"[LEON] Letter {letter}: {len(records)} results\n")

        except Exception as e:
            sys.stderr.write(f"[LEON] Error on letter {letter}: {e}\n")

        time.sleep(0.5)  # Rate limit

    records = list(all_records.values())
    sys.stderr.write(f"[LEON] Total extracted: {len(records)} records\n")
    return records


def _parse_results(soup):
    """Parse inmate search results page."""
    records = []

    # Look for inmate cards/rows in the results
    # Leon County might use divs, tables, or cards
    # Try finding result containers
    result_containers = soup.find_all('div', class_=re.compile(r'result|inmate|card|poster', re.I))
    if not result_containers:
        result_containers = soup.find_all('tr')

    for container in result_containers:
        record = {
            'County': 'Leon',
            'State': 'FL',
            'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Status': 'In Custody',
        }

        text = container.get_text(' ', strip=True)
        if len(text) < 10:
            continue

        # Name
        name_match = re.search(r'([A-Z][A-Za-z]+),\s*([A-Z][A-Za-z]+)', text)
        if name_match:
            record['Last_Name'] = name_match.group(1)
            record['First_Name'] = name_match.group(2)
            record['Full_Name'] = f"{name_match.group(1)}, {name_match.group(2)}"

        # Booking number
        booking_match = re.search(r'(?:Booking|Book)\s*#?\s*:?\s*(\d{6,})', text, re.I)
        if booking_match:
            record['Booking_Number'] = booking_match.group(1)

        # DOB
        dob_match = re.search(r'DOB[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.I)
        if dob_match:
            record['DOB'] = dob_match.group(1)

        # Race / Sex
        race_match = re.search(r'(?:Race|Ethnicity)[:\s]*(\w+)', text, re.I)
        if race_match:
            record['Race'] = race_match.group(1)
        sex_match = re.search(r'(?:Gender|Sex)[:\s]*(Male|Female|M|F)', text, re.I)
        if sex_match:
            val = sex_match.group(1)
            record['Sex'] = 'M' if val.upper().startswith('M') else 'F'

        # Charges
        charge_match = re.search(r'(?:Charge|Offense)[:\s]*(.+?)(?:\n|$)', text, re.I)
        if charge_match:
            record['Charges'] = charge_match.group(1).strip()

        # Bond
        bond_match = re.search(r'\$[\d,]+\.?\d*', text)
        if bond_match:
            clean = bond_match.group(0).replace('$', '').replace(',', '')
            try:
                record['Bond_Amount'] = str(float(clean))
            except ValueError:
                pass

        # Mugshot
        img = container.find('img')
        if img and img.get('src'):
            src = img['src']
            if not src.startswith('http'):
                src = f"{BASE_URL}{src}"
            record['Mugshot_URL'] = src

        # Detail link
        link = container.find('a', href=True)
        if link:
            href = link['href']
            if not href.startswith('http'):
                href = f"{BASE_URL}{href}"
            record['Detail_URL'] = href

        if record.get('Full_Name') or record.get('Booking_Number'):
            records.append(record)

    return records


if __name__ == "__main__":
    records = scrape_leon()
    print(json.dumps(records, indent=2))
