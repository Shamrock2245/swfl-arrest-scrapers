#!/usr/bin/env python3
"""
Baker County Solver — Inmate Roster Scraper

Baker County (Macclenny) is a small county. The sheriff's office at
bakersherifffl.org may have a jail page or link to VINE.

Source: https://www.bakersherifffl.org
Platform: Unknown — adaptive scraper
"""

import sys, re, json, os, datetime, time, string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[BAKER] Missing requests/bs4\n")
    sys.exit(1)

BASE_URL = "https://www.bakersherifffl.org"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_baker(days_back=7, max_pages=10):
    """Scrape Baker County inmate data."""
    sys.stderr.write(f"[BAKER] Starting → {BASE_URL}\n")
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(BASE_URL, timeout=30, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[BAKER] FAIL: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    records = []

    # Find jail/inmate links
    for a in soup.find_all('a', href=True):
        t = a.get_text(strip=True).lower()
        h = a['href'].lower()
        if any(k in t or k in h for k in ['inmate', 'jail', 'roster', 'arrest', 'booking']):
            url = a['href']
            if not url.startswith('http'):
                url = BASE_URL.rstrip('/') + '/' + url.lstrip('/')
            try:
                r2 = session.get(url, timeout=20)
                if r2.status_code == 200:
                    recs = _parse(BeautifulSoup(r2.text, 'html.parser'))
                    if recs:
                        records.extend(recs)
                        break
            except Exception:
                continue

    if not records:
        records = _parse(soup)

    sys.stderr.write(f"[BAKER] Total: {len(records)}\n")
    return records


def _parse(soup):
    records = []
    for table in soup.find_all('table'):
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 2: continue
            rec = {'County': 'Baker', 'State': 'FL',
                    'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Status': 'In Custody'}
            for c in cells:
                t = c.get_text(strip=True)
                if ',' in t and not rec.get('Full_Name') and len(t) > 3:
                    rec['Full_Name'] = t
                    p = t.split(',', 1)
                    rec['Last_Name'] = p[0].strip()
                    fp = p[1].strip().split()
                    if fp: rec['First_Name'] = fp[0]
                elif re.match(r'^\d{4,}$', t) and not rec.get('Booking_Number'):
                    rec['Booking_Number'] = t
                elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', t) and not rec.get('Booking_Date'):
                    rec['Booking_Date'] = t
            if rec.get('Full_Name') or rec.get('Booking_Number'):
                records.append(rec)
    return records


if __name__ == "__main__":
    print(json.dumps(scrape_baker(), indent=2))
