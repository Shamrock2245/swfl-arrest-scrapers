#!/usr/bin/env python3
"""
St. Johns County Solver — Inmate Search Scraper

St. Johns County (St. Augustine) uses a search at sjso.org.
NOTE: As of April 2026, the inmate search is reported "temporarily down."
This scraper is written to work when it comes back online.

Source: https://www.sjso.org/detention-center/sj-inmate-search/
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
    sys.stderr.write("[STJOHNS] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://www.sjso.org"
SEARCH_URL = f"{BASE_URL}/detention-center/sj-inmate-search/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_stjohns(days_back=7, max_pages=10):
    """Scrape St. Johns County inmate search."""
    sys.stderr.write(f"[STJOHNS] Starting scrape → {SEARCH_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(SEARCH_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[STJOHNS] FAIL loading page: {e}\n")
        return []

    # Check if site is still down
    if 'temporarily down' in resp.text.lower():
        sys.stderr.write("[STJOHNS] Inmate search is temporarily down\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find and submit search form
    form = soup.find('form')
    if not form:
        sys.stderr.write("[STJOHNS] No search form found\n")
        return []

    form_action = form.get('action', SEARCH_URL)
    if not form_action.startswith('http'):
        form_action = f"{BASE_URL}{form_action}"

    hidden_fields = {}
    for inp in form.find_all('input', type='hidden'):
        name = inp.get('name', '')
        value = inp.get('value', '')
        if name:
            hidden_fields[name] = value

    # Iterate A-Z for full roster
    all_records = {}
    for letter in string.ascii_uppercase:
        payload = {
            **hidden_fields,
            'LastName': letter,
            'FirstName': '',
        }

        try:
            resp = session.post(form_action, data=payload, timeout=30)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            records = _parse_results(soup)
            for rec in records:
                key = rec.get('Booking_Number') or rec.get('Full_Name', '')
                if key and key not in all_records:
                    all_records[key] = rec
        except Exception as e:
            sys.stderr.write(f"[STJOHNS] Error on {letter}: {e}\n")

        time.sleep(0.3)

    records = list(all_records.values())
    sys.stderr.write(f"[STJOHNS] Total extracted: {len(records)} records\n")
    return records


def _parse_results(soup):
    """Parse search results."""
    records = []
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            record = {
                'County': 'St. Johns',
                'State': 'FL',
                'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'In Custody',
            }

            texts = [c.get_text(strip=True) for c in cells]
            for text in texts:
                if ',' in text and not record.get('Full_Name'):
                    record['Full_Name'] = text
                    parts = text.split(',', 1)
                    record['Last_Name'] = parts[0].strip()
                    first_parts = parts[1].strip().split()
                    if first_parts:
                        record['First_Name'] = first_parts[0]
                elif re.match(r'^\d{6,}$', text) and not record.get('Booking_Number'):
                    record['Booking_Number'] = text
                elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', text):
                    if not record.get('Booking_Date'):
                        record['Booking_Date'] = text

            if record.get('Full_Name') or record.get('Booking_Number'):
                records.append(record)

    return records


if __name__ == "__main__":
    records = scrape_stjohns()
    print(json.dumps(records, indent=2))
