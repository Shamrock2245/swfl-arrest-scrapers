#!/usr/bin/env python3
"""
Broward County Solver — Multi-Agency Sequential ID Probing Scraper

BSO's ArrestSearch system at apps.sheriff.org uses SEQUENTIAL booking IDs
with agency-specific prefixes. Each detail page at /ArrestSearch/InmateDetail/{ID}
is publicly accessible with full booking data.

ID Format: PP26SSSSS
  - PP = 2-digit agency prefix
  - 26 = year (2026)
  - SSSSS = 5-digit sequence number

Known Agency Prefixes (discovered 04/16/2026):
  23 = Pompano Beach PD        (ACTIVE — frontier ~232601027)
  25 = Sunrise PD              (stalled 03/23/2026)
  50 = Broward Sheriff's Office (stalled 03/27/2026)
  57 = Fort Lauderdale PD      (stalled 03/11/2026)
  80 = Main Jail               (stalled 02/17/2026)
  90 = U.S. Marshals Service   (ACTIVE — frontier ~902600268)

Each detail page contains: Name, DOB, Race, Sex, Height, Weight, Hair, Eyes,
Booking Date, Arresting Agency, Facility, Charges (statute + description),
Bond Type/Amount per charge, Case Number, Mugshot URL.

NOTE: BSO does NOT publish defendant addresses on detail pages.

Source: https://apps.sheriff.org/ArrestSearch/InmateDetail/{ID}
"""

import sys
import re
import json
import os
import datetime
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

BASE_URL = "https://apps.sheriff.org"
DETAIL_URL = f"{BASE_URL}/ArrestSearch/InmateDetail"

# Agency prefixes and their known frontiers (calibrated 04/16/2026)
AGENCY_PREFIXES = {
    23: {'name': 'Pompano Beach PD',        'active': True,  'frontier': 232601027, 'rate': 13},
    25: {'name': 'Sunrise PD',              'active': True,  'frontier': 252600276, 'rate': 5},
    50: {'name': 'BSO Direct',              'active': True,  'frontier': 502601127, 'rate': 23},
    57: {'name': 'Fort Lauderdale PD',      'active': True,  'frontier': 572601255, 'rate': 15},
    80: {'name': 'Main Jail',               'active': False, 'frontier': 802600100, 'rate': 2},
    90: {'name': 'U.S. Marshals Service',   'active': True,  'frontier': 902600270, 'rate': 9},
}

ID_DENSITY = 0.45  # ~45% of sequential IDs have records (calibrated 04/16/2026)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

STATE_FILE = os.path.join(os.path.dirname(__file__), '.last_known_ids')


def _http_get(url):
    """Fetch a URL using urllib (no external deps)."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        return None


def scrape_broward(days_back=2, max_pages=10):
    """Scrape Broward County arrests across all agency prefixes."""
    sys.stderr.write(f"[BROWARD] Starting multi-agency probe (days_back={days_back})\n")

    saved_frontiers = _load_frontiers()
    all_records = []

    for prefix, info in AGENCY_PREFIXES.items():
        if not info['active']:
            sys.stderr.write(f"[BROWARD] Skipping inactive prefix {prefix} ({info['name']})\n")
            continue

        # Use saved frontier if available, otherwise use calibrated default
        start_frontier = saved_frontiers.get(str(prefix), info['frontier'])
        sys.stderr.write(f"[BROWARD] === Prefix {prefix} ({info['name']}) — start={start_frontier} ===\n")

        # Find current frontier
        frontier = _find_frontier(start_frontier)
        sys.stderr.write(f"[BROWARD]   Frontier: {frontier}\n")

        # Scan backwards from frontier
        rate = info['rate']
        ids_per_day = int(rate / ID_DENSITY) if ID_DENSITY > 0 else 30
        scan_range = ids_per_day * days_back
        scan_start = frontier - scan_range

        records = []
        consecutive_misses = 0

        sys.stderr.write(f"[BROWARD]   Scanning {scan_start} → {frontier + 30}\n")

        for jms_id in range(scan_start, frontier + 30):
            record = _fetch_and_parse(jms_id)
            if record:
                records.append(record)
                consecutive_misses = 0
            else:
                consecutive_misses += 1
                if jms_id > frontier and consecutive_misses > 8:
                    break
            time.sleep(0.15)

        sys.stderr.write(f"[BROWARD]   Found {len(records)} records for {info['name']}\n")
        all_records.extend(records)

        # Update frontier
        if records:
            max_id = max(int(r.get('Booking_Number', '0')) for r in records)
            saved_frontiers[str(prefix)] = max_id

    # Save all frontiers
    _save_frontiers(saved_frontiers)

    sys.stderr.write(f"[BROWARD] Total across all agencies: {len(all_records)} records\n")

    # Stats
    by_date = {}
    by_agency = {}
    for r in all_records:
        d = r.get('Booking_Date', '?')
        a = r.get('Arrest_Location', '?')
        by_date[d] = by_date.get(d, 0) + 1
        by_agency[a] = by_agency.get(a, 0) + 1
    for d in sorted(by_date.keys()):
        sys.stderr.write(f"[BROWARD]   {d}: {by_date[d]} arrests\n")
    for a in sorted(by_agency.keys()):
        sys.stderr.write(f"[BROWARD]   {a}: {by_agency[a]} records\n")

    return all_records


def _find_frontier(start_id):
    """Find the latest valid ID from a starting point."""
    step = 100
    current = start_id

    while step > 0:
        test_id = current + step
        html = _http_get(f"{DETAIL_URL}/{test_id}")
        if html and '<h3' in html and len(html) > 1000:
            current = test_id
            step = min(step * 2, 500)
        else:
            if step <= 1:
                break
            step = step // 2
        time.sleep(0.1)

    return current


def _fetch_and_parse(jms_id):
    """Fetch and parse a BSO inmate detail page."""
    html = _http_get(f"{DETAIL_URL}/{jms_id}")
    if not html or '<h3' not in html or len(html) < 1000:
        return None

    h3 = re.search(r'<h3>(.*?)</h3>', html)
    if not h3:
        return None

    name = h3.group(1).strip()
    record = {
        'County': 'Broward',
        'State': 'FL',
        'Booking_Number': str(jms_id),
        'Detail_URL': f"{DETAIL_URL}/{jms_id}",
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Status': 'In Custody',
    }

    # === NAME ===
    record['Full_Name'] = name
    if ',' in name:
        parts = name.split(',', 1)
        record['Last_Name'] = parts[0].strip()
        first_parts = parts[1].strip().split()
        if first_parts:
            record['First_Name'] = first_parts[0]
            if len(first_parts) > 1:
                record['Middle_Name'] = ' '.join(first_parts[1:])

    # === LABELED FIELDS ===
    fields = _extract_labeled_fields(html)
    race_map = {'W': 'White', 'B': 'Black', 'H': 'Hispanic', 'A': 'Asian', 'I': 'Indian'}

    if 'Arrest Date' in fields: record['Booking_Date'] = fields['Arrest Date']
    if 'DOB' in fields: record['DOB'] = fields['DOB']
    if 'Race' in fields: record['Race'] = race_map.get(fields['Race'], fields['Race'])
    if 'Sex' in fields: record['Sex'] = fields['Sex']
    if 'Height' in fields:
        h = fields['Height'].strip()
        record['Height'] = f"{h[0]}'{h[1:]}\"" if len(h) == 3 and h.isdigit() else h
    if 'Weight' in fields: record['Weight'] = fields['Weight']
    if 'Hair' in fields: record['Hair'] = fields['Hair']
    if 'Eyes' in fields: record['Eyes'] = fields['Eyes']
    if fields.get('Arresting Agency'): record['Arrest_Location'] = fields['Arresting Agency']
    if fields.get('Location'): record['Facility'] = fields['Location']
    if fields.get('Expected Release Date', '').strip():
        record['Release_Date'] = fields['Expected Release Date']

    # === MUGSHOT ===
    photo = re.search(r"vm\.photo='(/photos/[^']+)'", html)
    if photo:
        record['Mugshot_URL'] = f"{BASE_URL}{photo.group(1)}"

    # === CHARGES ===
    charges = _extract_charges(html)
    if charges:
        descs, total_bond, cases = [], 0.0, []
        for c in charges:
            d = []
            if c.get('statute'): d.append(c['statute'])
            if c.get('description'): d.append(c['description'])
            if d: descs.append(' '.join(d))
            if c.get('bond_amount'):
                try: total_bond += float(c['bond_amount'].replace('$', '').replace(',', ''))
                except: pass
            if c.get('case_number'): cases.append(c['case_number'])

        if descs: record['Charges'] = ' | '.join(descs)
        if total_bond > 0: record['Bond_Amount'] = f"{total_bond:.2f}"
        if cases: record['Case_Number'] = ', '.join(cases)

    return record


def _extract_labeled_fields(html):
    """Extract label→value pairs from BSO Bootstrap panels."""
    fields = {}
    pattern = r'<label[^>]*>([^<]+)</label>\s*(?:<br\s*/?>)?\s*<span[^>]*>\s*(?:<span[^>]*>)?\s*([^<]*?)(?:</span>)?\s*</span>'
    for m in re.finditer(pattern, html, re.S):
        l, v = m.group(1).strip(), m.group(2).strip()
        if l and v:
            fields[l] = v
    return fields


def _extract_charges(html):
    """Extract all charge panels from BSO detail page."""
    charges = []

    # Charge panels
    panels = re.split(r'<div class="panel-heading">Charge</div>', html)
    for panel in panels[1:]:
        end = panel.find('<div class="container">')
        if end > 0: panel = panel[:end]
        f = _extract_labeled_fields(panel)
        chg = {}
        for src, dst in [('Statute', 'statute'), ('Description', 'description'),
                         ('Charge Status', 'status'), ('Bond Type', 'bond_type'),
                         ('Bond Amount', 'bond_amount'), ('Case Number', 'case_number'),
                         ('Charge Comments', 'comments'), ('Disposition', 'disposition')]:
            if f.get(src, '').strip():
                chg[dst] = f[src].strip()
        if chg.get('statute') or chg.get('description'):
            charges.append(chg)

    # Holder panels
    hpanels = re.split(r'<div class="panel-heading">Holder</div>', html)
    for hp in hpanels[1:]:
        end = hp.find('<div class="container">')
        if end > 0: hp = hp[:end]
        f = _extract_labeled_fields(hp)
        desc = f.get('Description', '').strip()
        if desc:
            charges.append({'description': f'HOLDER - {desc}'})

    return charges


def _load_frontiers():
    """Load saved frontier IDs per agency prefix."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_frontiers(frontiers):
    """Save frontier IDs for all agency prefixes."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(frontiers, f)
    except Exception:
        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days-back', type=int, default=2)
    args = parser.parse_args()
    records = scrape_broward(days_back=args.days_back)
    print(json.dumps(records, indent=2))
