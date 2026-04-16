#!/usr/bin/env python3
"""
Lafayette County Solver

Very small county. May not have online roster.

Source: https://www.lafayetteso.org
Platform: unknown
"""

import sys, re, json, os, datetime, time, string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[LAFAYETTE] Missing requests/bs4\n")
    sys.exit(1)

BASE_URL = "https://www.lafayetteso.org"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_lafayette(days_back=7, max_pages=10):
    """Scrape Lafayette County inmate data."""
    sys.stderr.write(f"[LAFAYETTE] Starting → {BASE_URL}\n")
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(BASE_URL, timeout=30, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[LAFAYETTE] FAIL: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    records = []

    # Try iframe
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        iurl = iframe['src']
        if not iurl.startswith('http'):
            iurl = BASE_URL.rstrip('/') + '/' + iurl.lstrip('/')
        try:
            r2 = session.get(iurl, timeout=30)
            if r2.status_code == 200:
                soup = BeautifulSoup(r2.text, 'html.parser')
        except Exception:
            pass

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

    if not records:
        form = soup.find('form')
        if form:
            records = _az(session, form)

    sys.stderr.write(f"[LAFAYETTE] Total: {len(records)}\n")
    return records


def _az(session, form):
    action = form.get('action', BASE_URL)
    if not action.startswith('http'):
        action = BASE_URL.rstrip('/') + '/' + action.lstrip('/')
    hf = {}
    for inp in form.find_all('input', type='hidden'):
        n, v = inp.get('name',''), inp.get('value','')
        if n: hf[n] = v
    all_r = {}
    for letter in string.ascii_uppercase:
        try:
            r = session.post(action, data={**hf, 'LastName': letter, 'FirstName': ''}, timeout=30)
            if r.status_code == 200:
                for rec in _parse(BeautifulSoup(r.text, 'html.parser')):
                    k = rec.get('Booking_Number') or rec.get('Full_Name','')
                    if k: all_r[k] = rec
        except Exception: pass
        time.sleep(0.3)
    return list(all_r.values())


def _parse(soup):
    records = []
    for table in soup.find_all('table'):
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 2: continue
            rec = {'County': 'Lafayette', 'State': 'FL',
                    'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Status': 'In Custody'}
            for c in cells:
                t = c.get_text(strip=True)
                if ',' in t and not rec.get('Full_Name') and len(t)>3:
                    rec['Full_Name'] = t
                    p = t.split(',',1)
                    rec['Last_Name'] = p[0].strip()
                    fp = p[1].strip().split()
                    if fp: rec['First_Name'] = fp[0]
                elif re.match(r'^\d{4,}$', t) and not rec.get('Booking_Number'):
                    rec['Booking_Number'] = t
                elif re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', t) and not rec.get('Booking_Date'):
                    rec['Booking_Date'] = t
            rt = row.get_text(' ', strip=True)
            bm = re.search(r'\$([\d,]+\.?\d*)', rt)
            if bm: rec['Bond_Amount'] = bm.group(1).replace(',','')
            lnk = row.find('a', href=True)
            if lnk:
                h = lnk['href']
                if not h.startswith('http'): h = BASE_URL.rstrip('/')+'/'+h.lstrip('/')
                rec['Detail_URL'] = h
            if rec.get('Full_Name') or rec.get('Booking_Number'):
                records.append(rec)
    if not records:
        for c in soup.find_all(['div','article','li'], class_=re.compile(r'inmate|roster|card|entry|booking|arrest', re.I)):
            t = c.get_text(' ', strip=True)
            if len(t)<10: continue
            m = re.search(r"([A-Z][A-Za-z\'-]+),\s*([A-Z][A-Za-z\'-]+)", t)
            if m:
                records.append({'County':'Lafayette','State':'FL','Scrape_Timestamp':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Last_Name':m.group(1),'First_Name':m.group(2),'Full_Name':f"{m.group(1)}, {m.group(2)}"})
    return records


if __name__ == "__main__":
    print(json.dumps(scrape_lafayette(), indent=2))
