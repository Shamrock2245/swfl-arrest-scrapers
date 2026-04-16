#!/usr/bin/env python3
"""
Marion County Solver — Jail Inmate Search Scraper

Marion County (Ocala) uses a simple HTML form at jail.marionso.com.
The "Recent" button shows recently booked inmates without requiring a name search.

Strategy:
  1. POST to the search form with empty name fields to get recent bookings
  2. Parse the results table for booking data
  3. Follow detail links for charges/bond

Source: https://jail.marionso.com/
Platform: Custom ASP/HTML
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
    sys.stderr.write("[MARION] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://jail.marionso.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_marion(days_back=7, max_pages=10):
    """Scrape Marion County jail roster via Recent button."""
    sys.stderr.write(f"[MARION] Starting scrape → {BASE_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Load the search page to get any hidden form fields
    try:
        resp = session.get(BASE_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[MARION] FAIL loading page: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Step 2: Submit "Recent" search (empty last/first name)
    # Find the form and its action
    form = soup.find('form')
    form_action = form.get('action', '/') if form else '/'
    if not form_action.startswith('http'):
        form_action = f"{BASE_URL}{form_action}"

    # Extract hidden fields
    hidden_fields = {}
    if form:
        for inp in form.find_all('input', type='hidden'):
            name = inp.get('name', '')
            value = inp.get('value', '')
            if name:
                hidden_fields[name] = value

    # Submit with Recent button
    payload = {
        **hidden_fields,
        'LastName': '',
        'FirstName': '',
        'cmdRecent': 'Recent',
    }

    try:
        resp = session.post(form_action, data=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[MARION] FAIL submitting Recent: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Step 3: Parse results table
    records = []
    table = soup.find('table')
    if not table:
        # Try finding result rows by class/id
        results = soup.find_all('tr')
        if len(results) <= 1:
            sys.stderr.write("[MARION] No results table found\n")
            return []

    rows = soup.find_all('tr')
    for row in rows[1:]:  # Skip header
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        record = {
            'County': 'Marion',
            'State': 'FL',
            'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Status': 'In Custody',
        }

        # Try to parse cells — typical order varies
        texts = [c.get_text(strip=True) for c in cells]

        # Look for links to detail pages
        link = row.find('a')
        if link and link.get('href'):
            href = link['href']
            if not href.startswith('http'):
                href = f"{BASE_URL}/{href.lstrip('/')}"
            record['Detail_URL'] = href

        # Parse the row data
        for i, text in enumerate(texts):
            # Name detection (contains comma)
            if ',' in text and not record.get('Full_Name'):
                record['Full_Name'] = text
                parts = text.split(',', 1)
                record['Last_Name'] = parts[0].strip()
                first_parts = parts[1].strip().split()
                if first_parts:
                    record['First_Name'] = first_parts[0]

            # Booking number (numeric, 6+ digits)
            elif re.match(r'^\d{6,}$', text) and not record.get('Booking_Number'):
                record['Booking_Number'] = text

            # Date pattern
            elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', text):
                if not record.get('Booking_Date'):
                    record['Booking_Date'] = text

            # Race/Sex (single letters)
            elif len(text) == 1 and text in 'BWHAM':
                race_map = {'W': 'White', 'B': 'Black', 'H': 'Hispanic', 'A': 'Asian', 'M': 'Mixed'}
                record['Race'] = race_map.get(text, text)
            elif len(text) == 1 and text in 'MF':
                record['Sex'] = text

        if record.get('Full_Name') or record.get('Booking_Number'):
            records.append(record)

    # Step 4: Fetch detail pages for charges/bond if available
    for i, record in enumerate(records):
        detail_url = record.get('Detail_URL')
        if detail_url:
            _enrich_from_detail(session, record, detail_url)
            if i > 0 and i % 5 == 0:
                time.sleep(0.5)

    sys.stderr.write(f"[MARION] Total extracted: {len(records)} records\n")
    return records


def _enrich_from_detail(session, record, url):
    """Fetch a detail page and enrich the record with charges/bond."""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True)

        # DOB
        dob_match = re.search(r'DOB[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
        if dob_match:
            record['DOB'] = dob_match.group(1)

        # Charges
        charges = []
        charge_rows = soup.find_all('tr')
        for row in charge_rows:
            cells = row.find_all('td')
            cell_texts = [c.get_text(strip=True) for c in cells]
            # Look for rows with charge-like content
            for ct in cell_texts:
                if any(kw in ct.upper() for kw in ['BATTERY', 'THEFT', 'ASSAULT', 'DUI',
                       'DRUG', 'POSS', 'BURG', 'ROBBERY', 'FRAUD', 'TRESP', 'RESIST',
                       'DRIVING', 'FLEE', 'VOP', 'PROBATION', 'WARRANT']):
                    if ct not in charges and len(ct) > 5:
                        charges.append(ct)

        if charges:
            record['Charges'] = ' | '.join(charges[:10])

        # Bond amounts
        bond_matches = re.findall(r'\$[\d,]+\.?\d*', text)
        if bond_matches:
            total = 0
            for bm in bond_matches:
                try:
                    total += float(bm.replace('$', '').replace(',', ''))
                except ValueError:
                    pass
            if total > 0:
                record['Bond_Amount'] = str(total)

        # Mugshot
        img = soup.find('img', src=lambda s: s and ('photo' in s.lower() or 'mug' in s.lower() or 'image' in s.lower()))
        if img and img.get('src'):
            src = img['src']
            if not src.startswith('http'):
                src = f"{BASE_URL}/{src.lstrip('/')}"
            record['Mugshot_URL'] = src

    except Exception as e:
        sys.stderr.write(f"[MARION] Detail error: {e}\n")


if __name__ == "__main__":
    records = scrape_marion()
    print(json.dumps(records, indent=2))
