#!/usr/bin/env python3
"""
Washington County Solver — Inmate Roster Scraper

Washington County (Chipley, FL) publishes an inmate roster at wcso.us.

Source: https://wcso.us/inmateRoster
Platform: Simple HTML roster
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
    sys.stderr.write("[WASHINGTON] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://wcso.us"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_washington(days_back=7, max_pages=10):
    """Scrape Washington County inmate roster."""
    sys.stderr.write(f"[WASHINGTON] Starting scrape → {BASE_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    urls_to_try = [
        f"{BASE_URL}/inmateRoster",
        f"{BASE_URL}/inmates",
        f"{BASE_URL}/inmate-roster",
        f"{BASE_URL}/jail-roster",
        f"{BASE_URL}/jail/roster",
    ]

    page_content = None
    found_url = None

    for url in urls_to_try:
        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 500:
                page_content = resp.text
                found_url = url
                break
        except Exception:
            continue

    if not page_content:
        # Try homepage and find link
        try:
            resp = session.get(BASE_URL, timeout=30)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    text = a.get_text(strip=True).lower()
                    if 'inmate' in text or 'roster' in text or 'jail' in text:
                        url = a['href']
                        if not url.startswith('http'):
                            url = f"{BASE_URL}/{url.lstrip('/')}"
                        resp2 = session.get(url, timeout=20)
                        if resp2.status_code == 200:
                            page_content = resp2.text
                            found_url = url
                            break
        except Exception:
            pass

    if not page_content:
        sys.stderr.write("[WASHINGTON] Could not find any roster page\n")
        return []

    sys.stderr.write(f"[WASHINGTON] Found page: {found_url}\n")
    soup = BeautifulSoup(page_content, 'html.parser')
    records = _parse_roster(soup)
    sys.stderr.write(f"[WASHINGTON] Total extracted: {len(records)} records\n")
    return records


def _parse_roster(soup):
    """Parse the inmate roster page."""
    records = []

    # Table parsing
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            record = {
                'County': 'Washington',
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

            # Charges
            charge_keywords = ['BATTERY', 'THEFT', 'ASSAULT', 'DUI', 'POSS',
                              'VOP', 'WARRANT', 'DRIVING', 'DRUG']
            for text in texts:
                if any(kw in text.upper() for kw in charge_keywords):
                    record['Charges'] = text

            link = row.find('a', href=True)
            if link:
                href = link['href']
                if not href.startswith('http'):
                    href = f"{BASE_URL}/{href.lstrip('/')}"
                record['Detail_URL'] = href

            img = row.find('img')
            if img and img.get('src'):
                src = img['src']
                if not src.startswith('http'):
                    src = f"{BASE_URL}/{src.lstrip('/')}"
                record['Mugshot_URL'] = src

            if record.get('Full_Name') or record.get('Booking_Number'):
                records.append(record)

    # Div/card fallback
    if not records:
        containers = soup.find_all(['div', 'article'], class_=re.compile(
            r'inmate|roster|card|entry', re.I))
        for container in containers:
            text = container.get_text(' ', strip=True)
            if len(text) < 10:
                continue
            name_match = re.search(r'([A-Z][A-Za-z\'-]+),\s*([A-Z][A-Za-z\'-]+)', text)
            if name_match:
                record = {
                    'County': 'Washington',
                    'State': 'FL',
                    'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Last_Name': name_match.group(1),
                    'First_Name': name_match.group(2),
                    'Full_Name': f"{name_match.group(1)}, {name_match.group(2)}",
                }
                records.append(record)

    return records


if __name__ == "__main__":
    records = scrape_washington()
    print(json.dumps(records, indent=2))
