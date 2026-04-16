#!/usr/bin/env python3
"""
Okeechobee County Solver — Inmate Search Scraper

Okeechobee County SO uses a Wix-hosted site at okeesheriff.org.
The inmate search page may embed an external search widget.

Source: https://www.okeesheriff.org/inmate-search
Platform: Wix (may embed external widget)
"""

import sys
import re
import json
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[OKEECHOBEE] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://www.okeesheriff.org"
SEARCH_URL = f"{BASE_URL}/inmate-search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_okeechobee(days_back=7, max_pages=10):
    """Scrape Okeechobee County inmate search."""
    sys.stderr.write(f"[OKEECHOBEE] Starting scrape → {SEARCH_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(SEARCH_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[OKEECHOBEE] FAIL loading page: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Wix sites often use iframes to embed external content
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        iframe_url = iframe['src']
        sys.stderr.write(f"[OKEECHOBEE] Found iframe: {iframe_url}\n")
        return _scrape_iframe(session, iframe_url)

    # Check for embedded widget or external link
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True).lower()
        if 'inmate' in text or 'roster' in text or 'jail' in text:
            if href.startswith('http') and 'okeesheriff' not in href:
                sys.stderr.write(f"[OKEECHOBEE] External link: {href}\n")
                return _scrape_external(session, href)

    # Try common external platforms
    external_urls = [
        'https://kologik.com/roster/FL0930000',  # Okeechobee FIPS
    ]
    for url in external_urls:
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200 and 'inmate' in resp.text.lower():
                return _parse_roster(BeautifulSoup(resp.text, 'html.parser'))
        except Exception:
            continue

    sys.stderr.write("[OKEECHOBEE] No searchable content found (Wix shell only)\n")
    return []


def _scrape_iframe(session, url):
    """Scrape content from embedded iframe."""
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        return _parse_roster(soup)
    except Exception as e:
        sys.stderr.write(f"[OKEECHOBEE] iframe error: {e}\n")
        return []


def _scrape_external(session, url):
    """Scrape an external linked page."""
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        return _parse_roster(soup)
    except Exception as e:
        sys.stderr.write(f"[OKEECHOBEE] external error: {e}\n")
        return []


def _parse_roster(soup):
    """Parse a roster page."""
    records = []
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            record = {
                'County': 'Okeechobee',
                'State': 'FL',
                'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'In Custody',
            }

            texts = [c.get_text(strip=True) for c in cells]
            for text in texts:
                if ',' in text and not record.get('Full_Name') and len(text) > 3:
                    record['Full_Name'] = text
                    parts = text.split(',', 1)
                    record['Last_Name'] = parts[0].strip()
                    first_parts = parts[1].strip().split()
                    if first_parts:
                        record['First_Name'] = first_parts[0]
                elif re.match(r'^\d{4,}$', text) and not record.get('Booking_Number'):
                    record['Booking_Number'] = text
                elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', text):
                    if not record.get('Booking_Date'):
                        record['Booking_Date'] = text

            row_text = row.get_text(' ', strip=True)
            bond_match = re.search(r'\$([\d,]+\.?\d*)', row_text)
            if bond_match:
                record['Bond_Amount'] = bond_match.group(1).replace(',', '')

            if record.get('Full_Name') or record.get('Booking_Number'):
                records.append(record)

    return records


if __name__ == "__main__":
    records = scrape_okeechobee()
    print(json.dumps(records, indent=2))
