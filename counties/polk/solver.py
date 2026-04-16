#!/usr/bin/env python3
"""
Polk County Solver — Jail Inquiry Scraper (Lakeland/Winter Haven)

Polk County uses a Sitefinity CMS with a jail inquiry search widget at:
  https://www.polksheriff.org/detention/jail-inquiry

The search supports Name, Booking Date, and AKA lookups.
Strategy: Use A-Z name iteration to get all current inmates.

Source: https://www.polksheriff.org/detention/jail-inquiry
Platform: Sitefinity CMS (ASP.NET) — JS-rendered search widget
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
    sys.stderr.write("[POLK] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://www.polksheriff.org"
JAIL_URL = f"{BASE_URL}/detention/jail-inquiry"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_polk(days_back=7, max_pages=10):
    """Scrape Polk County jail by iterating A-Z last name searches."""
    sys.stderr.write(f"[POLK] Starting scrape → {JAIL_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(JAIL_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[POLK] FAIL loading page: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find iframe or embedded search widget
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        search_url = iframe['src']
        if not search_url.startswith('http'):
            search_url = f"{BASE_URL}{search_url}"
        sys.stderr.write(f"[POLK] Found iframe: {search_url}\n")
        return _scrape_iframe(session, search_url)

    # Fall back to A-Z letter iteration
    all_records = {}
    for letter in string.ascii_uppercase:
        sys.stderr.write(f"[POLK] Searching: {letter}...\n")
        records = _search_name(session, letter)
        for rec in records:
            key = rec.get('Booking_Number') or rec.get('Full_Name', '')
            if key and key not in all_records:
                all_records[key] = rec
        time.sleep(0.5)

    records = list(all_records.values())
    sys.stderr.write(f"[POLK] Total extracted: {len(records)} records\n")
    return records


def _scrape_iframe(session, url):
    """Scrape the iframe-embedded search."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        return _parse_results(soup, url)
    except Exception as e:
        sys.stderr.write(f"[POLK] iframe error: {e}\n")
        return []


def _search_name(session, last_name):
    """Submit a name search."""
    try:
        payload = {'LastName': last_name, 'FirstName': ''}
        resp = session.post(JAIL_URL, data=payload, timeout=30)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        return _parse_results(soup, JAIL_URL)
    except Exception as e:
        sys.stderr.write(f"[POLK] Search error: {e}\n")
        return []


def _parse_results(soup, base_url):
    """Parse inmate results from page."""
    records = []
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue

            record = {
                'County': 'Polk',
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

            row_text = row.get_text(' ', strip=True)
            bond_match = re.search(r'\$([\d,]+\.?\d*)', row_text)
            if bond_match:
                record['Bond_Amount'] = bond_match.group(1).replace(',', '')

            link = row.find('a', href=True)
            if link:
                href = link['href']
                if not href.startswith('http'):
                    href = f"{BASE_URL}{href}"
                record['Detail_URL'] = href

            if record.get('Full_Name') or record.get('Booking_Number'):
                records.append(record)

    return records


if __name__ == "__main__":
    records = scrape_polk()
    print(json.dumps(records, indent=2))
