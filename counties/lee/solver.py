#!/usr/bin/env python3
"""
Lee County Solver — REST API Scraper
Lee County Sheriff's Office exposes a public JSON API at:
  https://www.sheriffleefl.org/public-api/bookings

Endpoints:
  GET /public-api/bookings?limit=N&offset=N  → paginated booking list
  GET /public-api/bookings/{bookingNumber}/charges → charges for a booking

API fields: id, permId, bookingNumber, bookingDate, releaseDate, surName,
givenName, middleName, suffixName, birthDate, birthCountry, race, sex,
weight, height, hair, image (base64 JPEG), address, inCustody,
inCustodyText, housing

Source: https://www.sheriffleefl.org/booking-search/
Platform: Custom WordPress REST API (Odyssey-style)
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
except ImportError:
    sys.stderr.write("[LEE] Missing requests library\n")
    sys.exit(1)

BASE_URL = "https://www.sheriffleefl.org"
BOOKINGS_URL = f"{BASE_URL}/public-api/bookings"
CHARGES_URL = f"{BASE_URL}/public-api/bookings/{{booking_number}}/charges"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': f'{BASE_URL}/booking-search/',
}

PAGE_SIZE = 100  # API supports up to 100 per page


def _parse_date(raw: str) -> str:
    """Parse API date string to MM/DD/YYYY format."""
    if not raw:
        return ''
    try:
        # Format: "2026-04-23 15:19:00.000"
        dt = datetime.datetime.strptime(raw[:10], '%Y-%m-%d')
        return dt.strftime('%m/%d/%Y')
    except (ValueError, TypeError):
        return raw[:10] if raw else ''


def _parse_time(raw: str) -> str:
    """Parse API datetime string to HH:MM format."""
    if not raw:
        return ''
    try:
        # Format: "2026-04-23 15:19:00.000"
        dt = datetime.datetime.strptime(raw[:16], '%Y-%m-%d %H:%M')
        return dt.strftime('%H:%M')
    except (ValueError, TypeError):
        return ''


def _parse_height(raw: str) -> str:
    """Convert height from inches string (e.g. '510') to feet/inches (e.g. "5'10\"")."""
    if not raw:
        return ''
    try:
        h = int(raw)
        feet = h // 100
        inches = h % 100
        return f"{feet}'{inches}\""
    except (ValueError, TypeError):
        return raw


def _fetch_charges(session: requests.Session, booking_number: str) -> dict:
    """Fetch charges for a booking and return parsed data."""
    url = CHARGES_URL.format(booking_number=booking_number)
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        charges_data = resp.json()
    except Exception as e:
        sys.stderr.write(f"[LEE] Charges fetch failed for {booking_number}: {e}\n")
        return {'charges_text': '', 'total_bond': 0.0, 'bond_type': '',
                'case_number': '', 'agency': '', 'court_date': '', 'court_location': ''}

    charges = []
    total_bond = 0.0
    bond_type = ''
    case_number = ''
    agency = ''
    court_date = ''
    court_location = ''

    for charge in charges_data:
        desc = charge.get('offenseDescription', '').strip()
        statute = charge.get('offenseCode', '').strip()
        if desc:
            if statute:
                charges.append(f"{desc} ({statute})")
            else:
                charges.append(desc)

        # Bond amount
        bond_raw = charge.get('bondAmount', '')
        if bond_raw and bond_raw not in ('Not Set', '', 'N/A', 'None'):
            clean = bond_raw.replace('$', '').replace(',', '').strip()
            try:
                total_bond += float(clean)
            except ValueError:
                pass

        # Bond type
        if not bond_type and charge.get('bondTypeName'):
            bond_type = charge['bondTypeName'].strip()

        # Case number (use first one found)
        if not case_number and charge.get('caseNumber'):
            case_number = charge['caseNumber'].strip()

        # Arresting agency
        if not agency and charge.get('arrestingAgencyName'):
            agency = charge['arrestingAgencyName'].strip()

        # Court date
        if not court_date and charge.get('hearingDate'):
            court_date = _parse_date(charge['hearingDate'])

        # Court location
        if not court_location and charge.get('courtLocation'):
            court_location = charge['courtLocation'].strip()

    return {
        'charges_text': ' | '.join(charges) if charges else '',
        'total_bond': total_bond,
        'bond_type': bond_type,
        'case_number': case_number,
        'agency': agency,
        'court_date': court_date,
        'court_location': court_location,
    }


def _normalize_race(raw: str) -> str:
    """Normalize race code to standard single-char."""
    mapping = {
        'W': 'W', 'WHITE': 'W',
        'B': 'B', 'BLACK': 'B',
        'H': 'H', 'HISPANIC': 'H',
        'A': 'A', 'ASIAN': 'A',
        'I': 'I', 'NATIVE': 'I',
        'O': 'O', 'OTHER': 'O',
    }
    return mapping.get((raw or '').upper(), 'U')


def _build_record(raw: dict, charges_info: dict) -> dict:
    """Convert raw API booking to our 34-column schema dict."""
    booking_date = _parse_date(raw.get('bookingDate', ''))
    booking_time = _parse_time(raw.get('bookingDate', ''))

    # Name parsing
    last_name = (raw.get('surName') or '').strip().upper()
    first_name = (raw.get('givenName') or '').strip().upper()
    middle_name = (raw.get('middleName') or '').strip().upper()
    suffix = (raw.get('suffixName') or '').strip().upper()

    full_name_parts = [last_name]
    if first_name:
        name_part = first_name
        if middle_name:
            name_part += f' {middle_name}'
        if suffix:
            name_part += f' {suffix}'
        full_name_parts.append(name_part)
    full_name = ', '.join(full_name_parts) if len(full_name_parts) > 1 else last_name

    # Status
    in_custody = raw.get('inCustody', True)
    status = 'In Custody' if in_custody else 'Released'

    # Address parsing
    address_raw = (raw.get('address') or '').strip()
    address = address_raw
    city = ''
    state = 'FL'
    zip_code = ''
    if address_raw:
        # Format: "15326 CRICKET LN CYPRESS LAKE FL 33919"
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\s*$', address_raw)
        if zip_match:
            zip_code = zip_match.group(1)
        state_match = re.search(r'\b([A-Z]{2})\s+\d{5}', address_raw)
        if state_match:
            state = state_match.group(1)
            # City is everything between last comma/space and state
            city_match = re.search(r'(?:,\s*)?([A-Z][A-Z\s]+?)\s+' + state_match.group(1) + r'\b', address_raw)
            if city_match:
                city = city_match.group(1).strip()

    # DOB
    dob = _parse_date(raw.get('birthDate', ''))

    # Mugshot — image is base64 JPEG; we construct a URL instead
    booking_number = str(raw.get('bookingNumber', '')).strip()
    mugshot_url = f"{BASE_URL}/public-api/bookings/{booking_number}/image" if booking_number else ''

    # Bond amount as string
    bond_amount = str(int(charges_info['total_bond'])) if charges_info['total_bond'] > 0 else '0'

    record = {
        'Scrape_Timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'County': 'Lee',
        'Booking_Number': booking_number,
        'Person_ID': str(raw.get('permId', '')).strip(),
        'Full_Name': full_name,
        'First_Name': first_name,
        'Middle_Name': middle_name,
        'Last_Name': last_name,
        'DOB': dob,
        'Booking_Date': booking_date,
        'Booking_Time': booking_time,
        'Status': status,
        'Facility': (raw.get('housing') or '').strip(),
        'Agency': charges_info.get('agency', 'LEE COUNTY SHERIFFS OFFICE'),
        'Race': _normalize_race(raw.get('race', '')),
        'Sex': (raw.get('sex') or 'U').upper()[:1],
        'Height': _parse_height(raw.get('height', '')),
        'Weight': str(raw.get('weight', '')).strip(),
        'Address': address,
        'City': city,
        'State': state,
        'ZIP': zip_code,
        'Mugshot_URL': mugshot_url,
        'Charges': charges_info.get('charges_text', ''),
        'Bond_Amount': bond_amount,
        'Bond_Paid': 'No',
        'Bond_Type': charges_info.get('bond_type', ''),
        'Court_Type': '',
        'Case_Number': charges_info.get('case_number', ''),
        'Court_Date': charges_info.get('court_date', ''),
        'Court_Time': '',
        'Court_Location': charges_info.get('court_location', ''),
        'Detail_URL': f"{BASE_URL}/booking-search/?bookingNum={booking_number}",
        'Lead_Score': 0,
        'Lead_Status': 'Cold',
    }

    return record


def scrape_lee(days_back: int = 7, max_pages: int = 20) -> list:
    """
    Scrape Lee County jail bookings via the public REST API.

    Args:
        days_back: Not used directly (API returns current inmates); kept for interface compatibility
        max_pages: Maximum number of pages to fetch (PAGE_SIZE=100 per page)

    Returns:
        list[dict] — arrest records matching the 34-column schema
    """
    sys.stderr.write(f"[LEE] Starting REST API scraper → {BOOKINGS_URL}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    all_records = []
    offset = 0
    page = 0

    while page < max_pages:
        url = f"{BOOKINGS_URL}?limit={PAGE_SIZE}&offset={offset}"
        sys.stderr.write(f"[LEE] Fetching page {page + 1} (offset={offset})\n")

        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            bookings = resp.json()
        except requests.RequestException as e:
            sys.stderr.write(f"[LEE] FAIL fetching bookings: {e}\n")
            break
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[LEE] JSON parse error: {e}\n")
            break

        if not bookings:
            sys.stderr.write(f"[LEE] No more records at offset {offset}\n")
            break

        sys.stderr.write(f"[LEE] Got {len(bookings)} bookings on page {page + 1}\n")

        for booking in bookings:
            booking_number = str(booking.get('bookingNumber', '')).strip()
            if not booking_number:
                continue

            # Fetch charges (with rate limiting)
            charges_info = _fetch_charges(session, booking_number)
            time.sleep(0.3)  # Respectful rate limiting

            record = _build_record(booking, charges_info)
            if record.get('Full_Name') or record.get('Booking_Number'):
                all_records.append(record)

        # Check if we got a full page (more records may exist)
        if len(bookings) < PAGE_SIZE:
            break

        offset += PAGE_SIZE
        page += 1
        time.sleep(1.0)  # Pause between pages

    sys.stderr.write(f"[LEE] Total extracted: {len(all_records)} records\n")
    return all_records


if __name__ == "__main__":
    records = scrape_lee()
    print(json.dumps(records, indent=2))
