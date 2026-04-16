#!/usr/bin/env python3
"""
Union County Solver — Inmate Roster Scraper

Union County (Lake Butler) is the 2nd smallest FL county by population.
The sheriff's office may have a minimal web presence.

Source: https://www.unioncountysheriff.us
Platform: Unknown — adaptive scraper
"""

import sys, re, json, os, datetime, time, string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[UNION] Missing requests/bs4\n")
    sys.exit(1)

BASE_URL = "https://www.unioncountysheriff.us"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_union(days_back=7, max_pages=10):
    """Scrape Union County inmate data."""
    sys.stderr.write(f"[UNION] Starting → {BASE_URL}\n")
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(BASE_URL, timeout=30, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[UNION] FAIL: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    records = []

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

    sys.stderr.write(f"[UNION] Total: {len(records)}\n")
    return records


def _parse(soup):
    records = []
    for table in soup.find_all('table'):
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 2: continue
            rec = {'County': 'Union', 'State': 'FL',
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
    print(json.dumps(scrape_union(), indent=2))
