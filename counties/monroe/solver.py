#!/usr/bin/env python3
"""
Monroe County Solver — Current Inmates Scraper (Florida Keys)

Monroe County (Key West) publishes a current inmates list at keysso.net.
The page displays all inmates with basic booking info.

Source: https://keysso.net
Platform: Custom web page
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
    sys.stderr.write("[MONROE] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://keysso.net"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_monroe(days_back=7, max_pages=10):
    """Scrape Monroe County current inmates list."""
    sys.stderr.write(f"[MONROE] Starting scrape → {BASE_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Try common paths for inmate pages
    urls_to_try = [
        f"{BASE_URL}/current-inmates",
        f"{BASE_URL}/current-inmates/",
        f"{BASE_URL}/inmates",
        f"{BASE_URL}/inmates/",
        f"{BASE_URL}/arrests",
        f"{BASE_URL}/arrests/",
        f"{BASE_URL}/jail/current-inmates",
        f"{BASE_URL}/detention/current-inmates",
    ]

    page_content = None
    found_url = None

    for url in urls_to_try:
        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 1000:
                if any(kw in resp.text.lower() for kw in ['inmate', 'booking', 'custody', 'arrest']):
                    page_content = resp.text
                    found_url = url
                    break
        except Exception:
            continue

    if not page_content:
        # Try homepage and find the link
        try:
            resp = session.get(BASE_URL, timeout=30)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    text = a.get_text(strip=True).lower()
                    href = a['href'].lower()
                    if 'current inmate' in text or 'inmate' in href:
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
        sys.stderr.write("[MONROE] Could not find inmates page\n")
        return []

    sys.stderr.write(f"[MONROE] Found page: {found_url}\n")
    soup = BeautifulSoup(page_content, 'html.parser')
    records = _parse_inmates(soup)
    sys.stderr.write(f"[MONROE] Total extracted: {len(records)} records\n")
    return records


def _parse_inmates(soup):
    """Parse inmate records from the page."""
    records = []

    # Try table-based parsing first
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            record = _parse_row(cells)
            if record:
                records.append(record)

    # If no table results, try div-based or list-based
    if not records:
        # Look for repeating patterns — inmate cards
        containers = soup.find_all(['div', 'li', 'article'], class_=re.compile(
            r'inmate|booking|arrest|result|card|row', re.I))
        for container in containers:
            record = _parse_container(container)
            if record:
                records.append(record)

    # Last resort: parse entire page text for patterns
    if not records:
        text = soup.get_text('\n', strip=True)
        records = _parse_text(text)

    return records


def _parse_row(cells):
    """Parse a table row into a record."""
    record = {
        'County': 'Monroe',
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
        elif re.match(r'^\d{6,}$', text) and not record.get('Booking_Number'):
            record['Booking_Number'] = text
        elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', text):
            if not record.get('Booking_Date'):
                record['Booking_Date'] = text

    if record.get('Full_Name') or record.get('Booking_Number'):
        return record
    return None


def _parse_container(container):
    """Parse a div/card container into a record."""
    text = container.get_text(' ', strip=True)
    if len(text) < 10:
        return None

    record = {
        'County': 'Monroe',
        'State': 'FL',
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Status': 'In Custody',
    }

    name_match = re.search(r'([A-Z][A-Za-z\'-]+),\s*([A-Z][A-Za-z\'-]+)', text)
    if name_match:
        record['Last_Name'] = name_match.group(1)
        record['First_Name'] = name_match.group(2)
        record['Full_Name'] = f"{name_match.group(1)}, {name_match.group(2)}"

    booking_match = re.search(r'(?:Booking|Book)\s*#?\s*:?\s*(\d{6,})', text, re.I)
    if booking_match:
        record['Booking_Number'] = booking_match.group(1)

    if record.get('Full_Name') or record.get('Booking_Number'):
        return record
    return None


def _parse_text(text):
    """Parse raw text for name patterns."""
    records = []
    # Find NAME, FIRST patterns
    for match in re.finditer(r'([A-Z]{2,}),\s+([A-Z][A-Za-z]+)', text):
        record = {
            'County': 'Monroe',
            'State': 'FL',
            'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Last_Name': match.group(1).title(),
            'First_Name': match.group(2),
            'Full_Name': f"{match.group(1).title()}, {match.group(2)}",
        }
        records.append(record)
    return records


if __name__ == "__main__":
    records = scrape_monroe()
    print(json.dumps(records, indent=2))
