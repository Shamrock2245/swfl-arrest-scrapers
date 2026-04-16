#!/usr/bin/env python3
"""
SmartCOP Parser — Shared parser for all SmartCOP/SmartWEB jail roster sites.

SmartCOP systems use a consistent ASP.NET layout:
  - Single listing page at /smartwebclient/Jail.aspx (or /SmartWEBClient/Jail.aspx)
  - Default view: "BOOKED Last 24 Hours" (current inmates)
  - All data rendered in inmate cards on one page (no detail pages needed)
  - Cards contain: name, race/gender, DOB, status, booking number, booking date,
    bond amount, address, charges table with statute/degree/level/bond per charge
  - Mugshot via ViewImage.aspx?bookno={booking_number}
  - "Load More Results" button for additional records (AJAX pagination)

Usage from county solver:
    from core.smartcop_parser import scrape_smartcop

    def scrape_bradford(days_back=7, max_pages=10):
        return scrape_smartcop(
            base_url="http://smartweb.bradfordsheriff.org",
            county="Bradford",
        )
"""

import sys
import re
import datetime
import requests
from bs4 import BeautifulSoup


def scrape_smartcop(base_url: str, county: str, jail_path: str = "/smartwebclient/Jail.aspx",
                    timeout: int = 30, load_all: bool = True) -> list:
    """
    Scrape a SmartCOP jail roster site.

    Args:
        base_url: Site root, e.g. "http://smartweb.bradfordsheriff.org"
        county: County name for records, e.g. "Bradford"
        jail_path: Path to jail page (varies slightly between sites)
        timeout: HTTP request timeout in seconds
        load_all: If True, attempt to load all pages via AJAX pagination

    Returns:
        list[dict] — arrest records matching the 34-column schema
    """
    url = f"{base_url.rstrip('/')}{jail_path}"
    sys.stderr.write(f"[{county.upper()}] SmartCOP scraper → {url}\n")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })

    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[{county.upper()}] FAIL: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Check for results count
    results_span = soup.find('span', id='ResultsReturned')
    if results_span:
        count = results_span.get_text(strip=True)
        sys.stderr.write(f"[{county.upper()}] Initial results: {count}\n")

    # Load additional results via AJAX if available
    all_html = resp.text
    if load_all:
        all_html = _load_all_results(session, url, soup, all_html, county)

    # Re-parse with all results
    soup = BeautifulSoup(all_html, 'html.parser')

    # Parse inmate cards
    records = _parse_inmate_cards(soup, base_url, county)

    sys.stderr.write(f"[{county.upper()}] Total extracted: {len(records)} records\n")
    return records


def _load_all_results(session, url, soup, html, county, max_iterations=20):
    """Load all pages via AJAX AddMoreResults endpoint."""
    # Extract ASP.NET form data for AJAX calls
    load_more = soup.find(id='LoadMoreRow')
    if not load_more:
        return html

    # Count initial results
    results_span = soup.find('span', id='ResultsReturned')
    records_loaded = int(results_span.get_text(strip=True)) if results_span else 0

    if records_loaded == 0:
        return html

    for i in range(max_iterations):
        try:
            payload = {
                'FirstName': '', 'MiddleName': '', 'LastName': '',
                'BeginBookDate': '', 'EndBookDate': '',
                'BeginReleaseDate': '', 'EndReleaseDate': '',
                'TypeJailSearch': 0, 'RecordsLoaded': records_loaded,
                'SortOption': 0, 'SortOrder': 0, 'IsDefault': True
            }

            resp = session.post(
                f"{url}/AddMoreResults",
                json=payload,
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()

            result_data = data.get('d', {}).get('Data', {})
            new_html = result_data.get('data', '')
            results_returned = result_data.get('resultsReturned', 0)
            results_attempted = result_data.get('resultsAttempted', 0)

            if results_returned == 0:
                break

            # Inject new HTML into the JailInfo div
            html = html.replace('</table></div>', f'{new_html}</table></div>')
            records_loaded += results_returned
            sys.stderr.write(f"[{county.upper()}] Loaded {records_loaded} total records (batch {i+1})\n")

            if results_attempted > results_returned:
                break  # No more results

        except Exception as e:
            sys.stderr.write(f"[{county.upper()}] AJAX pagination stopped: {e}\n")
            break

    return html


def _parse_inmate_cards(soup, base_url, county):
    """Parse all inmate cards from the SmartCOP JailView table."""
    records = []

    # Find the main jail info table
    jail_table = soup.find('table', class_='JailView')
    if not jail_table:
        # Fallback: look in JailInfo div
        jail_div = soup.find('div', id='JailInfo')
        if jail_div:
            jail_table = jail_div.find('table')
        if not jail_table:
            sys.stderr.write(f"[{county.upper()}] WARN: No JailView table found\n")
            return []

    # Each inmate record starts with a <tr style="InmateRecordRow">
    # followed by their info table, separator rows, then charges table
    inmate_rows = jail_table.find_all('tr', style=lambda s: s and 'InmateRecordRow' in str(s))
    charge_tables = jail_table.find_all('table', class_='JailViewCharges')

    sys.stderr.write(f"[{county.upper()}] Found {len(inmate_rows)} inmate cards\n")

    for idx, row in enumerate(inmate_rows):
        try:
            record = _parse_single_inmate(row, base_url, county)

            # Match charges table (same index)
            if idx < len(charge_tables):
                charges_data = _parse_charges_table(charge_tables[idx])
                record['Charges'] = charges_data['charges_text']
                if charges_data['total_bond'] > 0:
                    record['Bond_Amount'] = str(charges_data['total_bond'])
                if charges_data['bond_type']:
                    record['Bond_Type'] = charges_data['bond_type']

            if record.get('Booking_Number') or record.get('Full_Name'):
                records.append(record)

        except Exception as e:
            sys.stderr.write(f"[{county.upper()}] WARN: Error parsing card {idx}: {e}\n")

    return records


def _parse_single_inmate(row, base_url, county):
    """Parse a single inmate card row."""
    record = {
        'County': county,
        'State': 'FL',
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # --- Mugshot URL ---
    img = row.find('img')
    if img and img.get('src'):
        src = img['src']
        if 'ViewImage' in src:
            record['Mugshot_URL'] = f"{base_url.rstrip('/')}/smartwebclient/{src}"
            # Extract booking number from mugshot URL
            bookno_match = re.search(r'bookno=([^&"\']+)', src)
            if bookno_match:
                record['Booking_Number'] = bookno_match.group(1)

    # --- Info table (nested inside the card row) ---
    info_table = row.find('table')
    if not info_table:
        return record

    # Header: name, race, gender, DOB
    header = info_table.find('td', class_='SearchHeader')
    if header:
        header_text = header.get_text(' ', strip=True)
        _parse_header(header_text, record)

    # Detail rows: label-value pairs in InmateInfoGridTd cells
    detail_rows = info_table.find('tbody')
    if detail_rows:
        rows = detail_rows.find_all('tr')
        for tr in rows:
            cells = tr.find_all('td', class_='InmateInfoGridTd')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).rstrip(':')
                value = cells[1].get_text(strip=True)
                _map_field(label, value, record)

            # Check for 4-cell rows (e.g., Booking No / MniNo)
            if len(cells) >= 4:
                label2 = cells[2].get_text(strip=True).rstrip(':')
                value2 = cells[3].get_text(strip=True)
                if label2 and value2:
                    _map_field(label2, value2, record)

    # Default status
    if 'Status' not in record:
        record['Status'] = 'In Custody'

    return record


def _parse_header(header_text, record):
    """Parse the header line: 'LAST, FIRST MIDDLE  (R/ GENDER / DOB: 1/1/2000 )'"""
    # Remove extra whitespace
    header_text = re.sub(r'\s+', ' ', header_text).strip()

    # Extract name (everything before the first parenthesis)
    name_match = re.match(r'^(.+?)\s*\(', header_text)
    if name_match:
        full_name = name_match.group(1).strip()
    else:
        full_name = header_text.strip()

    record['Full_Name'] = full_name

    # Parse Last, First Middle
    if ',' in full_name:
        parts = full_name.split(',', 1)
        record['Last_Name'] = parts[0].strip()
        first_parts = parts[1].strip().split()
        if first_parts:
            record['First_Name'] = first_parts[0]
            if len(first_parts) > 1:
                record['Middle_Name'] = ' '.join(first_parts[1:])

    # Extract race from (R/ pattern
    race_match = re.search(r'\((\w)/', header_text)
    if race_match:
        race_code = race_match.group(1)
        race_map = {'W': 'White', 'B': 'Black', 'H': 'Hispanic', 'A': 'Asian',
                     'I': 'Native American', 'O': 'Other', 'U': 'Unknown'}
        record['Race'] = race_map.get(race_code, race_code)

    # Extract gender
    gender_match = re.search(r'/\s*(MALE|FEMALE)\s*/', header_text, re.IGNORECASE)
    if gender_match:
        record['Sex'] = gender_match.group(1)[0].upper()  # M or F

    # Extract DOB
    dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', header_text)
    if dob_match:
        record['DOB'] = dob_match.group(1)


def _map_field(label, value, record):
    """Map a SmartCOP label to our schema field."""
    if not label or not value:
        return

    label_lower = label.lower().strip()

    if 'status' in label_lower:
        status_text = value.strip()
        if 'released' in status_text.lower() or 'out' in status_text.lower():
            record['Status'] = 'Released'
        elif 'jail' in status_text.lower() or 'custody' in status_text.lower():
            record['Status'] = 'In Custody'
        else:
            record['Status'] = status_text

    elif 'booking no' in label_lower or 'book no' in label_lower:
        record['Booking_Number'] = value

    elif 'booking date' in label_lower or 'book date' in label_lower:
        record['Booking_Date'] = value

    elif 'age on booking' in label_lower or 'age at booking' in label_lower:
        pass  # We already have DOB from header

    elif 'bond amount' in label_lower:
        # Parse "$1,234.00" → "1234.00"
        clean = value.replace('$', '').replace(',', '').strip()
        try:
            amt = float(clean)
            record['Bond_Amount'] = str(amt)
        except ValueError:
            record['Bond_Amount'] = '0'

    elif 'address' in label_lower:
        record['Address'] = value
        # Try to parse city/state/zip
        addr_match = re.search(r',?\s+([A-Z][A-Za-z\s]+?)\s*,?\s+FL\s+(\d{5})', value)
        if addr_match:
            record['City'] = addr_match.group(1).strip()
            record['ZIP'] = addr_match.group(2)
        elif 'FL' in value:
            fl_match = re.search(r'([A-Z][A-Za-z\s]+?)\s*,?\s+FL\s*(\d{5})?', value)
            if fl_match:
                record['City'] = fl_match.group(1).strip()
                if fl_match.group(2):
                    record['ZIP'] = fl_match.group(2)

    elif 'facility' in label_lower or 'housing' in label_lower:
        record['Facility'] = value

    elif label_lower == 'mnino' or 'mni' in label_lower:
        pass  # Internal SmartCOP ID, not in our schema


def _parse_charges_table(charge_table):
    """Parse a SmartCOP charges table."""
    result = {
        'charges_text': '',
        'total_bond': 0.0,
        'bond_type': '',
    }

    charges = []
    total_bond = 0.0

    # Skip header rows (class="SearchHeader"), parse data rows
    rows = charge_table.find_all('tr')
    for row in rows:
        cells = row.find_all('td', attrs={'nowrap': 'nowrap'})
        if len(cells) >= 4:
            # Typical order: [expander], STATUTE, COURT CASE, CHARGE, DEGREE, LEVEL, BOND
            # But expander may or may not be present
            texts = [c.get_text(strip=True) for c in cells]

            # Find the charge text (usually the longest descriptive field)
            charge_text = ''
            statute = ''
            degree = ''
            bond_text = ''

            for i, t in enumerate(texts):
                # Skip [+] expander
                if t in ('[+]', '[-]'):
                    continue
                # Statute is usually first real field (e.g., "784.03.1a1")
                if re.match(r'^\d+\.', t) and not statute:
                    statute = t
                # Bond amount has $ sign
                elif '$' in t:
                    bond_text = t
                # Degree is short like "F", "M", "1"
                elif len(t) <= 3 and t in ('F', 'M', '1', '2', '3', 'L', 'C'):
                    degree = t
                # Level keywords
                elif t.upper() in ('FELONY', 'MISDEMEANOR', 'INFRACTION', 'ORDINANCE', 'VIOLATION'):
                    pass  # Level info, not charge text
                # Court case number (contains dashes and letters)
                elif re.match(r'^\d{2}[-]', t) or '(' in t:
                    pass  # Court case number
                # Remaining text is likely the charge
                elif len(t) > 3 and not charge_text:
                    charge_text = t

            if charge_text:
                if statute:
                    charges.append(f"{charge_text} ({statute})")
                else:
                    charges.append(charge_text)

            if bond_text:
                clean = bond_text.replace('$', '').replace(',', '').strip()
                try:
                    total_bond += float(clean)
                except ValueError:
                    pass

    result['charges_text'] = ' | '.join(charges) if charges else ''
    result['total_bond'] = total_bond
    return result
