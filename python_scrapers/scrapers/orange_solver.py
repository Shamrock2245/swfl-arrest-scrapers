#!/usr/bin/env python3
"""
Orange County Arrest Scraper
Source: https://netapps.ocfl.net/BestJail/PDF/bookings.pdf
System: PDF Document (daily booking report)

This scraper downloads the daily booking PDF from Orange County Jail
and extracts arrest records using pdfplumber text extraction.

Known Limitations:
- PDF is regenerated daily with 24-hour booking window
- Some charge descriptions may be truncated at page boundaries
- Bond amounts are not included in the PDF (would require web scraping)
"""

import sys
import json
import re
import requests
import pdfplumber
import io
from datetime import datetime


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return " ".join(text.strip().split())


def parse_orange_pdf(pdf_bytes):
    """
    Parse the Orange County Jail booking PDF and extract arrest records.
    
    The PDF format is:
    - Header with date: "BOOKINGS DURING THE 24-HOUR PERIOD BEGINNING AT MIDNIGHT MM/DD/YYYY"
    - Records with format:
      NAME, FIRSTNAME MIDDLE   BOOKING#   RACE/SEX   AGE   CELL
      CITY, FL ZIPCODE   ETHNICITY
      CASE: CASENUMBER   ARRESTING_AGENCY
      STATUTE   FELONY/MISDEMEANOR   DEGREE   CHARGE_DESCRIPTION
      (multiple charge lines possible)
    """
    records = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        sys.stderr.write(f"   PDF has {len(pdf.pages)} pages\n")
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text(layout=True)
            if not text:
                continue
            
            # Extract booking date from header
            date_match = re.search(r'BEGINNING AT MIDNIGHT (\d{1,2}/\d{1,2}/\d{4})', text)
            booking_date = date_match.group(1) if date_match else datetime.now().strftime('%m/%d/%Y')
            
            lines = text.split('\n')
            current_record = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip header lines
                if any(skip in line for skip in [
                    'ORANGE COUNTY JAIL', 'BOOKINGS DURING', 'BEGINNING AT',
                    'Race/', 'Gender/', 'Booking #', 'Ethnicity', 'Release Date'
                ]):
                    continue
                
                # Skip page footer lines
                if 'IMS061' in line or 'Page:' in line or 'Total Inmates' in line:
                    continue
                
                # Record start pattern: NAME, FIRSTNAME   8-digit-booking#   RACE/SEX   AGE   CELL
                # Examples:
                #   ADAMS, REGINALD LEE 25040426 B / M 56 BRC-MBF-NA
                #   WILLIAMS, GEORGE WASHINGTON 4 25040451 B / M 26 BRC-MBF-NA
                record_match = re.match(
                    r'^([A-Z][A-Z\s,\-\'\.0-9]+?)\s+(\d{8})\s+([BWHUA]\s*/\s*[MFU])\s+(\d+)\s+(.+)$',
                    line
                )
                
                if record_match:
                    # Save previous record
                    if current_record:
                        records.append(current_record)
                    
                    full_name = clean_text(record_match.group(1))
                    booking_number = record_match.group(2)
                    race_sex = record_match.group(3).replace(' ', '')
                    age = record_match.group(4)
                    facility = clean_text(record_match.group(5))
                    
                    # Parse name (Last, First Middle)
                    last_name = ""
                    first_name = ""
                    if ',' in full_name:
                        parts = full_name.split(',', 1)
                        last_name = parts[0].strip()
                        first_name = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        last_name = full_name
                    
                    # Parse race/sex
                    race = ""
                    sex = ""
                    if '/' in race_sex:
                        rs_parts = race_sex.split('/')
                        race = rs_parts[0].strip()
                        sex = rs_parts[1].strip()
                    
                    current_record = {
                        'Booking_Number': booking_number,
                        'Full_Name': full_name,
                        'Last_Name': last_name,
                        'First_Name': first_name,
                        'Race': race,
                        'Sex': sex,
                        'Age': age,
                        'Facility': facility,
                        'Booking_Date': booking_date,
                        'Booking_Time': '',
                        'County': 'Orange',
                        'State': 'FL',
                        'Address': '',
                        'City': '',
                        'ZIP': '',
                        'Ethnicity': '',
                        'Case_Number': '',
                        'Charges': [],
                        'Arrest_Agency': '',
                        'Bond_Amount': '',
                        'Status': 'In Custody',
                        'Mugshot_URL': '',
                        'Detail_URL': 'https://netapps.ocfl.net/BestJail/PDF/bookings.pdf'
                    }
                    continue
                
                # If we have a current record, parse additional lines
                if current_record:
                    # Address line: CITY, FL ZIPCODE   ETHNICITY
                    # Examples:
                    #   ORLANDO, FL 32810 NON-HISPANIC
                    #   LEHIGH ACRES, FL 33974 HISPANIC
                    address_match = re.match(r'^([A-Z][A-Z\s]+),\s*FL\s+(\d{5})\s*(.*)$', line)
                    if address_match:
                        city = address_match.group(1).strip()
                        zip_code = address_match.group(2)
                        ethnicity = address_match.group(3).strip()
                        current_record['Address'] = f"{city}, FL {zip_code}"
                        current_record['City'] = city
                        current_record['ZIP'] = zip_code
                        if ethnicity:
                            current_record['Ethnicity'] = ethnicity
                        continue
                    
                    # Case line: CASE: CASENUMBER   AGENCY
                    # Examples:
                    #   CASE: 2025CF014469O ORANGE COUNTY SHERIFF OFFICE
                    #   CASE: 0134905 ORLANDO PD
                    case_match = re.match(r'^CASE:\s*(\S+)\s+(.+)$', line)
                    if case_match:
                        current_record['Case_Number'] = case_match.group(1)
                        current_record['Arrest_Agency'] = clean_text(case_match.group(2))
                        continue
                    
                    # Charge line patterns:
                    # STATUTE   FELONY/MISDEMEANOR / DEGREE   DESCRIPTION
                    # Examples:
                    #   784.041(2)(A)-1 FELONY / THIRD DEGREE BATTERY BY STRANGULATION
                    #   901.15(4) MISDEMEANOR / DEGREE OUT-OF-COUNTY WARRANT
                    #   CITY33.06 MISDEMEANOR / DEGREE ALCOHOLIC BEVERAGES
                    charge_match = re.match(
                        r'^(\d+\.\d+[^\s]*|CITY\d+\.\d+[^\s]*)\s+'
                        r'(FELONY|MISDEMEANOR)\s*/?\s*'
                        r'(FIRST|SECOND|THIRD)?\s*DEGREE\s*'
                        r'(.+)$',
                        line, re.IGNORECASE
                    )
                    if charge_match:
                        statute = charge_match.group(1).strip()
                        severity = charge_match.group(2).upper()
                        degree = charge_match.group(3).upper() if charge_match.group(3) else ""
                        description = clean_text(charge_match.group(4))
                        
                        if degree:
                            charge_str = f"{statute} {severity}/{degree} DEGREE {description}"
                        else:
                            charge_str = f"{statute} {severity} {description}"
                        
                        current_record['Charges'].append(charge_str)
                        continue
                    
                    # Catch simpler charge patterns or continuation lines
                    if re.match(r'^\d+\.\d+', line):
                        current_record['Charges'].append(clean_text(line))
            
            # Don't forget the last record on the page
            if current_record:
                records.append(current_record)
                current_record = None
    
    # Post-process records
    final_records = []
    for rec in records:
        # Join charges with pipe separator
        if rec['Charges']:
            rec['Charges'] = ' | '.join(rec['Charges'])
        else:
            rec['Charges'] = ''
        
        final_records.append(rec)
    
    return final_records


def scrape_orange():
    """Main scraper function for Orange County"""
    sys.stderr.write("🍊 Starting Orange County PDF Scraper\n")
    
    url = "https://netapps.ocfl.net/BestJail/PDF/bookings.pdf"
    
    try:
        sys.stderr.write(f"📡 Downloading PDF from {url}...\n")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        sys.stderr.write(f"   PDF Size: {len(response.content)} bytes\n")
        
        records = parse_orange_pdf(response.content)
        
        sys.stderr.write(f"📊 Extracted {len(records)} records from PDF\n")
        
        # Output JSON to stdout
        print(json.dumps(records))
        
    except requests.RequestException as e:
        sys.stderr.write(f"❌ Network Error: {e}\n")
        print("[]")
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
        print("[]")


if __name__ == "__main__":
    scrape_orange()
