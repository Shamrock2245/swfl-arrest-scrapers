#!/usr/bin/env python3
"""
Citrus County Solver — PDF Roster Scraper

Citrus County embeds a daily PDF arrest report in an iframe at:
  https://www.sheriffcitrus.org/public_info/recent_arrest.php

The PDF is generated daily by Nitro Pro 13, contains 20+ pages of arrest records
with mugshots, names, charges, bond amounts, and booking dates.

Strategy:
  1. Fetch the page HTML and extract the PDF URL from the iframe
  2. Download the PDF
  3. Use pdfplumber to extract text from each page
  4. Parse arrest records from the extracted text

Source: https://www.sheriffcitrus.org/public_info/recent_arrest.php
Platform: Embedded PDF (Nitro Pro 13)
"""

import sys
import re
import json
import os
import datetime
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("[CITRUS] Missing requests/bs4\n")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    sys.stderr.write("[CITRUS] Missing pdfplumber — install with: pip install pdfplumber\n")
    pdfplumber = None


BASE_URL = "https://www.sheriffcitrus.org"
PAGE_URL = f"{BASE_URL}/public_info/recent_arrest.php"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_citrus(days_back=7, max_pages=30):
    """Scrape Citrus County arrests from the embedded PDF roster."""
    sys.stderr.write(f"[CITRUS] Starting PDF scrape → {PAGE_URL}\n")

    if not pdfplumber:
        sys.stderr.write("[CITRUS] SKIP — pdfplumber not installed\n")
        return []

    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Get the page and find the PDF URL
    pdf_url = _find_pdf_url(session)
    if not pdf_url:
        sys.stderr.write("[CITRUS] Could not find PDF URL\n")
        return []

    sys.stderr.write(f"[CITRUS] Found PDF: {pdf_url}\n")

    # Step 2: Download the PDF
    try:
        resp = session.get(pdf_url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.stderr.write(f"[CITRUS] FAIL downloading PDF: {e}\n")
        return []

    # Step 3: Parse the PDF
    records = _parse_pdf(resp.content)
    sys.stderr.write(f"[CITRUS] Total extracted: {len(records)} records\n")
    return records


def _find_pdf_url(session):
    """Find the PDF URL from the Citrus County page."""
    try:
        resp = session.get(PAGE_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Look for iframe with PDF
        iframe = soup.find('iframe', src=True)
        if iframe:
            src = iframe['src']
            if src.endswith('.pdf') or 'pdf' in src.lower():
                if not src.startswith('http'):
                    src = f"{BASE_URL}/{src.lstrip('/')}"
                return src

        # Look for object/embed tags
        for tag in soup.find_all(['object', 'embed']):
            src = tag.get('data') or tag.get('src') or ''
            if src and ('.pdf' in src.lower() or 'pdf' in src.lower()):
                if not src.startswith('http'):
                    src = f"{BASE_URL}/{src.lstrip('/')}"
                return src

        # Look for direct PDF links
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True).lower()
            if '.pdf' in href.lower() or 'arrest' in text:
                if not href.startswith('http'):
                    href = f"{BASE_URL}/{href.lstrip('/')}"
                if '.pdf' in href.lower():
                    return href

        # Try the "Click Here For Recent Arrests" link
        for a in soup.find_all('a', href=True):
            if 'recent arrest' in a.get_text(strip=True).lower() or 'click here' in a.get_text(strip=True).lower():
                href = a['href']
                if not href.startswith('http'):
                    href = f"{BASE_URL}/{href.lstrip('/')}"
                # Follow this link to find the PDF
                resp2 = session.get(href, timeout=30)
                if resp2.headers.get('Content-Type', '').startswith('application/pdf'):
                    return href
                # Parse the next page for PDF
                soup2 = BeautifulSoup(resp2.text, 'html.parser')
                iframe2 = soup2.find('iframe', src=True)
                if iframe2:
                    src = iframe2['src']
                    if not src.startswith('http'):
                        src = f"{BASE_URL}/{src.lstrip('/')}"
                    return src

        # Last resort: try common PDF paths
        common_paths = [
            '/public_info/arrests.pdf',
            '/public_info/recent_arrests.pdf',
            '/documents/recent_arrest.pdf',
            '/uploads/recent_arrest.pdf',
        ]
        for path in common_paths:
            url = f"{BASE_URL}{path}"
            try:
                resp = session.head(url, timeout=10)
                if resp.status_code == 200 and 'pdf' in resp.headers.get('Content-Type', ''):
                    return url
            except Exception:
                continue

    except Exception as e:
        sys.stderr.write(f"[CITRUS] Error finding PDF: {e}\n")

    return None


def _parse_pdf(pdf_bytes):
    """Parse arrest records from the PDF content."""
    records = []

    try:
        pdf = pdfplumber.open(io.BytesIO(pdf_bytes))
    except Exception as e:
        sys.stderr.write(f"[CITRUS] Error opening PDF: {e}\n")
        return []

    for page_num, page in enumerate(pdf.pages):
        try:
            text = page.extract_text()
            if not text:
                continue

            # Parse individual records from the page text
            page_records = _extract_records_from_text(text, page_num + 1)
            records.extend(page_records)

        except Exception as e:
            sys.stderr.write(f"[CITRUS] Error parsing page {page_num + 1}: {e}\n")

    pdf.close()
    return records


def _extract_records_from_text(text, page_num):
    """Extract arrest records from a page's text content."""
    records = []
    lines = text.split('\n')

    # Citrus PDF typically has records in blocks with:
    # - Name (LAST, FIRST MIDDLE)
    # - DOB, Race, Sex
    # - Booking number, Date
    # - Charges with bond amounts

    current_record = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect a new record start — typically a name in CAPS with a comma
        name_match = re.match(r'^([A-Z][A-Z\s\'-]+),\s+([A-Z][A-Z\s\'-]+)', line)
        if name_match and len(name_match.group(1)) > 1:
            # Save previous record
            if current_record and (current_record.get('Full_Name') or current_record.get('Booking_Number')):
                records.append(current_record)

            current_record = {
                'County': 'Citrus',
                'State': 'FL',
                'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Recent Arrest',
                'Last_Name': name_match.group(1).strip(),
                'First_Name': name_match.group(2).strip().split()[0] if name_match.group(2).strip() else '',
                'Full_Name': line.split('  ')[0].strip() if '  ' in line else line.strip(),
            }

            # Check if middle name is present
            first_parts = name_match.group(2).strip().split()
            if len(first_parts) > 1:
                current_record['First_Name'] = first_parts[0]
                current_record['Middle_Name'] = ' '.join(first_parts[1:])

            continue

        if not current_record:
            continue

        # DOB
        dob_match = re.search(r'DOB[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})', line, re.I)
        if dob_match:
            current_record['DOB'] = dob_match.group(1)

        # Booking date
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)', line, re.I)
        if date_match and not current_record.get('Booking_Date'):
            current_record['Booking_Date'] = date_match.group(1)
            current_record['Booking_Time'] = date_match.group(2)

        # Booking number
        booking_match = re.search(r'(?:Book|Case|Arrest)\s*#?\s*:?\s*(\d{4,}[-\d]*)', line, re.I)
        if booking_match:
            current_record['Booking_Number'] = booking_match.group(1)

        # Race
        race_match = re.search(r'\b(White|Black|Hispanic|Asian|W|B|H|A)\b', line)
        if race_match and not current_record.get('Race'):
            race_map = {'W': 'White', 'B': 'Black', 'H': 'Hispanic', 'A': 'Asian'}
            val = race_match.group(1)
            current_record['Race'] = race_map.get(val, val)

        # Sex
        sex_match = re.search(r'\b(Male|Female)\b', line, re.I)
        if sex_match and not current_record.get('Sex'):
            current_record['Sex'] = 'M' if sex_match.group(1).upper() == 'MALE' else 'F'

        # Charges
        charge_keywords = ['BATTERY', 'THEFT', 'ASSAULT', 'DUI', 'DRUG', 'POSS',
                          'BURG', 'ROBBERY', 'FRAUD', 'TRESP', 'RESIST', 'DRIVING',
                          'VOP', 'PROBATION', 'WARRANT', 'FLEE', 'FEL', 'MISD',
                          'AGGRAVATED', 'CRIMINAL', 'DOMESTIC', 'DISORDERLY']
        if any(kw in line.upper() for kw in charge_keywords):
            existing = current_record.get('Charges', '')
            if existing:
                current_record['Charges'] = f"{existing} | {line}"
            else:
                current_record['Charges'] = line

        # Bond amount
        bond_match = re.search(r'\$[\d,]+\.?\d*', line)
        if bond_match:
            clean = bond_match.group(0).replace('$', '').replace(',', '')
            try:
                val = float(clean)
                existing = float(current_record.get('Bond_Amount', '0'))
                current_record['Bond_Amount'] = str(existing + val)
            except ValueError:
                pass

    # Save last record
    if current_record and (current_record.get('Full_Name') or current_record.get('Booking_Number')):
        records.append(current_record)

    return records


if __name__ == "__main__":
    records = scrape_citrus()
    print(json.dumps(records, indent=2))
