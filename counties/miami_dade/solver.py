#!/usr/bin/env python3
"""
Miami-Dade County Solver — Inmate Search Scraper

Miami-Dade is the HARDEST county — complex CAPTCHA-protected search at
miamidade.gov. This county represents the largest jail population in FL.

Strategy: Try the corrections department API/search first. If blocked
by CAPTCHA, fall back to any available public data feeds.

Source: https://www.miamidade.gov/global/correctionsandrehabilitation/inmate-search.page
Platform: Complex — CAPTCHA protected
"""

import sys, re, json, os, datetime, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[MIAMI_DADE] Missing requests/bs4\n")
    sys.exit(1)

BASE_URL = "https://www.miamidade.gov"
SEARCH_URL = f"{BASE_URL}/global/correctionsandrehabilitation/inmate-search.page"
# Alternative API endpoints to try
ALT_URLS = [
    "https://www3.miamidade.gov/inmatelookup/",
    "https://mdcr-inmatelookup.miamidade.gov/",
    "https://www8.miamidade.gov/Apps/correction/inmate_search/",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_miami_dade(days_back=7, max_pages=10):
    """Attempt to scrape Miami-Dade County inmates."""
    sys.stderr.write(f"[MIAMI_DADE] Starting scrape (high-difficulty target)\n")
    session = requests.Session()
    session.headers.update(HEADERS)

    # Try alternative endpoints first
    for url in ALT_URLS:
        try:
            resp = session.get(url, timeout=20, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 1000:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Check if we got actual content (not a CAPTCHA page)
                text = soup.get_text(' ', strip=True).lower()
                if 'captcha' in text or 'recaptcha' in text or 'challenge' in text:
                    sys.stderr.write(f"[MIAMI_DADE] CAPTCHA at {url}\n")
                    continue
                records = _parse(soup)
                if records:
                    sys.stderr.write(f"[MIAMI_DADE] Got {len(records)} from {url}\n")
                    return records
        except Exception as e:
            sys.stderr.write(f"[MIAMI_DADE] Error on {url}: {e}\n")
            continue

    # Try main search page
    try:
        resp = session.get(SEARCH_URL, timeout=30)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(' ', strip=True).lower()

            if 'captcha' in text or 'recaptcha' in text:
                sys.stderr.write("[MIAMI_DADE] CAPTCHA detected — cannot proceed without browser\n")
                sys.stderr.write("[MIAMI_DADE] Consider: DrissionPage with CAPTCHA solver or manual extraction\n")
                return []

            # If we got through, look for iframes or forms
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                iframe_url = iframe['src']
                if not iframe_url.startswith('http'):
                    iframe_url = f"{BASE_URL}{iframe_url}"
                try:
                    r2 = session.get(iframe_url, timeout=30)
                    if r2.status_code == 200:
                        records = _parse(BeautifulSoup(r2.text, 'html.parser'))
                        if records:
                            return records
                except Exception:
                    pass

    except requests.RequestException as e:
        sys.stderr.write(f"[MIAMI_DADE] FAIL: {e}\n")

    sys.stderr.write("[MIAMI_DADE] Could not bypass CAPTCHA — 0 records\n")
    return []


def _parse(soup):
    records = []
    for table in soup.find_all('table'):
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 2: continue
            rec = {'County': 'Miami-Dade', 'State': 'FL',
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
            rt = row.get_text(' ', strip=True)
            bm = re.search(r'\$([\d,]+\.?\d*)', rt)
            if bm: rec['Bond_Amount'] = bm.group(1).replace(',', '')
            if rec.get('Full_Name') or rec.get('Booking_Number'):
                records.append(rec)
    return records


if __name__ == "__main__":
    print(json.dumps(scrape_miami_dade(), indent=2))
