#!/usr/bin/env python3
"""
St. Lucie County Solver — Inmate Lookup Scraper

St. Lucie Sheriff uses a search where entering '%' in the last name field
returns ALL current inmates. Also shows releases from the past 5 days.

Source: https://www.stluciesheriff.com/
Platform: Custom web form
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
    sys.stderr.write("[ST_LUCIE] Missing requests/bs4\n")
    sys.exit(1)


BASE_URL = "https://www.stluciesheriff.com"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_stlucie(days_back=7, max_pages=10):
    """Scrape St. Lucie County using '%' wildcard search."""
    sys.stderr.write(f"[ST_LUCIE] Starting scrape → {BASE_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Find the inmate lookup page
    lookup_urls = [
        f"{BASE_URL}/inmate-lookup",
        f"{BASE_URL}/inmate-inquiry",
        f"{BASE_URL}/corrections/inmate-lookup",
        f"{BASE_URL}/divisions/corrections/inmate-lookup",
    ]

    lookup_page = None
    for url in lookup_urls:
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200 and ('inmate' in resp.text.lower() or 'search' in resp.text.lower()):
                lookup_page = url
                break
        except Exception:
            continue

    if not lookup_page:
        # Try homepage and find the link
        try:
            resp = session.get(BASE_URL, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if 'inmate' in a.get_text(strip=True).lower() or 'inmate' in a['href'].lower():
                    href = a['href']
                    if not href.startswith('http'):
                        href = f"{BASE_URL}/{href.lstrip('/')}"
                    lookup_page = href
                    break
        except Exception:
            pass

    if not lookup_page:
        sys.stderr.write("[ST_LUCIE] Could not find inmate lookup page\n")
        return []

    sys.stderr.write(f"[ST_LUCIE] Found lookup: {lookup_page}\n")

    # Load the page
    try:
        resp = session.get(lookup_page, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[ST_LUCIE] FAIL: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find form and submit with '%' wildcard
    form = soup.find('form')
    if not form:
        sys.stderr.write("[ST_LUCIE] No form found\n")
        return []

    form_action = form.get('action', lookup_page)
    if not form_action.startswith('http'):
        form_action = f"{BASE_URL}/{form_action.lstrip('/')}"

    hidden_fields = {}
    for inp in form.find_all('input', type='hidden'):
        name = inp.get('name', '')
        value = inp.get('value', '')
        if name:
            hidden_fields[name] = value

    payload = {
        **hidden_fields,
        'LastName': '%',
        'FirstName': '',
    }

    # Find submit button name
    submit = form.find('input', type='submit') or form.find('button', type='submit')
    if submit and submit.get('name'):
        payload[submit['name']] = submit.get('value', 'Search')

    try:
        resp = session.post(form_action, data=payload, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[ST_LUCIE] Search FAIL: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    records = _parse_results(soup)
    sys.stderr.write(f"[ST_LUCIE] Total extracted: {len(records)} records\n")
    return records


def _parse_results(soup):
    """Parse inmate search results."""
    records = []

    # Look for result rows
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            record = {
                'County': 'St. Lucie',
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
                    href = f"{BASE_URL}/{href.lstrip('/')}"
                record['Detail_URL'] = href

            if record.get('Full_Name') or record.get('Booking_Number'):
                records.append(record)

    # Also check for div-based results
    if not records:
        result_divs = soup.find_all('div', class_=re.compile(r'result|inmate|card', re.I))
        for div in result_divs:
            text = div.get_text(' ', strip=True)
            if len(text) < 10:
                continue
            record = {
                'County': 'St. Lucie',
                'State': 'FL',
                'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            name_match = re.search(r'([A-Z][A-Za-z]+),\s*([A-Z][A-Za-z]+)', text)
            if name_match:
                record['Last_Name'] = name_match.group(1)
                record['First_Name'] = name_match.group(2)
                record['Full_Name'] = f"{name_match.group(1)}, {name_match.group(2)}"
                records.append(record)

    return records


if __name__ == "__main__":
    records = scrape_stlucie()
    print(json.dumps(records, indent=2))
