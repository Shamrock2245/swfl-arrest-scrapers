#!/usr/bin/env python3
"""
Orange County Arrest Scraper
Source: https://netapps.ocfl.net/BestJail/PDF/bookings.pdf
System: PDF Document (daily booking report) + Web Enrichment (DrissionPage)

This scraper:
1. Downloads the daily booking PDF from Orange County Jail.
2. Extracts base arrest records using pdfplumber.
3. Enriches records with Bond Amount and Court Date by scraping the web portal
   (https://netapps.ocfl.net/BestJail/Home/Inmates).

Known Limitations:
- PDF is regenerated daily with 24-hour booking window
- Web enrichment requires a headless browser (DrissionPage)
- Search is performed by Name because Booking Number search is unreliable.
"""

import sys
import json
import re
import requests
import pdfplumber
import io
import time
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

# Headless mode configuration
HEADLESS = True

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return " ".join(text.strip().split())


def parse_orange_pdf(pdf_bytes):
    """
    Parse the Orange County Jail booking PDF and extract arrest records.
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
                record_match = re.match(
                    r'^([A-Z][A-Z\s,\-\'\.0-9]+?)\s+(\d{8})\s+([BWHUA]\s*/\s*[MFU])\s+(\d+)\s+(.+)$',
                    line
                )
                
                if record_match:
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
                        'Bond_Amount': '0', # Default, will be enriched
                        'Court_Date': '',   # Default, will be enriched
                        'Court_Time': '',   # Default, will be enriched
                        'Status': 'In Custody',
                        'Mugshot_URL': '',
                        'Detail_URL': 'https://netapps.ocfl.net/BestJail/Home/Inmates' 
                    }
                    continue
                
                # Parse additional lines
                if current_record:
                    # Address line
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
                    
                    # Case line
                    case_match = re.match(r'^CASE:\s*(\S+)\s+(.+)$', line)
                    if case_match:
                        current_record['Case_Number'] = case_match.group(1)
                        current_record['Arrest_Agency'] = clean_text(case_match.group(2))
                        continue
                    
                    # Charge line
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
                    
                    if re.match(r'^\d+\.\d+', line):
                        current_record['Charges'].append(clean_text(line))
            
            if current_record:
                records.append(current_record)
                current_record = None
    
    # Post-process records
    final_records = []
    for rec in records:
        if rec['Charges']:
            rec['Charges'] = ' | '.join(rec['Charges'])
        else:
            rec['Charges'] = ''
        final_records.append(rec)
    
    return final_records


def enrich_records_with_web(records):
    """
    Enrich records with Bond Amount and Court Date using DrissionPage.
    Searches by name and matches Booking Number.
    """
    if not records:
        return records

    sys.stderr.write(f"🌐 Starting Web Enrichment for {len(records)} records...\n")

    page = None
    try:
        co = ChromiumOptions()
        if HEADLESS:
            co.headless()
        
        # Initialize browser
        page = ChromiumPage(co)
        
        # Iterate records
        for i, rec in enumerate(records):
            try:
                # Refresh session periodically or on first run
                if i % 10 == 0:
                    page.get("https://netapps.ocfl.net/BestJail/Home/Inmates")
                    time.sleep(2)

                # Ensure we are on search page
                if "Inmates" not in page.url:
                    page.get("https://netapps.ocfl.net/BestJail/Home/Inmates")
                    time.sleep(1)

                # Try search strategies: Full Name first, then Last, First
                search_candidates = [
                    f"{rec['Last_Name']}, {rec['First_Name']}", # Full name as parsed
                ]
                # If First Name has spaces, add a version with just the first part
                if ' ' in rec['First_Name']:
                     search_candidates.append(f"{rec['Last_Name']}, {rec['First_Name'].split(' ')[0]}")
                
                target_row = None
                
                for search_name in search_candidates:
                    sys.stderr.write(f"   Searching for: {search_name} (Booking #{rec['Booking_Number']})\n")

                    # Clear and input search
                    page.ele('#inmate').clear()
                    page.ele('#inmate').input(search_name)
                    page.ele('#btnSearch').click()
                    
                    # Wait for result content
                    start_time = time.time()
                    found = False
                    no_records = False
                    
                    while time.time() - start_time < 5:
                        if page.ele(f'text:{rec["Booking_Number"]}', timeout=0.1):
                            found = True
                            break
                        if page.ele('text:No records found found matching criteria', timeout=0.1):
                            no_records = True
                            break
                        time.sleep(0.5)

                    if found:
                        # Find the link with the booking number in the onclick
                        link = page.ele(f'css:a.inmateLink[onclick*="{rec["Booking_Number"]}"]')
                        if link:
                            target_row = link
                            break # Success, stop trying names
                    
                    if no_records:
                        sys.stderr.write(f"      No results for '{search_name}'\n")
                    
                if target_row:
                    link = target_row
                    if link:
                        link.click()
                        time.sleep(1.5) # Wait for detail view
                        
                        # Extract details from the page text
                        # The detail view likely replaces the content or is a modal
                        detail_text = page.ele('body').text
                        
                        # Court Date
                        court_match = re.search(r'Court Date:?\s*(\d{1,2}/\d{1,2}/\d{4})', detail_text, re.IGNORECASE)
                        if court_match:
                            rec['Court_Date'] = court_match.group(1)
                        
                        # Court Time
                        time_match = re.search(r'Court Time:?\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)', detail_text, re.IGNORECASE)
                        if time_match:
                            rec['Court_Time'] = time_match.group(1)

                        # Bond Amount extraction
                        # Look for "Bond Amount: $100.00" or similar
                        # Strategy: Sum all amounts in the 'Charges' section if possible, or look for specific Bond lines
                        # The page usually lists charges. We can look for "$X,XXX.XX" 
                        # Be careful not to sum unrelated money.
                        
                        # Finding the charges table in detail view
                        # It often has "Charge Description" or "Bond Amount" headers
                        total_bond = 0.0
                        
                        # Parse lines looking for bond amounts
                        # Pattern often: ... Bond Amount: $1,000.00 ...
                        # Or it's in a table column.
                        
                        # Let's try to find specific bond amounts associated with charges
                        # A simple regex describing the bond amount label might work best if table parsing is tricky
                        
                        # Case 1: "Bond Amount: $500.00"
                        bond_matches = re.findall(r'Bond Amount[:\s]*\$([\d,]+\.?\d{2})', detail_text, re.IGNORECASE)
                        if bond_matches:
                            for b in bond_matches:
                                try:
                                    total_bond += float(b.replace(',', ''))
                                except: pass
                        else:
                            # Fallback: Check for just "$500.00" in a Bond column if header exists
                            pass
                        
                        if total_bond > 0:
                            rec['Bond_Amount'] = f"{total_bond:.2f}"
                        
                        sys.stderr.write(f"      Enriched: Bond=${rec['Bond_Amount']}, Court={rec['Court_Date']}\n")
                        
                        # Back to search list? Or just continue loop which reloads/searches
                        # Continuing loop reloads search page anyway.
                        
                    else:
                         sys.stderr.write(f"      Link for {rec['Booking_Number']} not clickable.\n")
                
                else:
                    sys.stderr.write(f"      Booking #{rec['Booking_Number']} not found in search results.\n")

            except Exception as e:
                sys.stderr.write(f"      ⚠️ Error enriching record {rec['Booking_Number']}: {e}\n")
                continue
                
    except Exception as e:
        sys.stderr.write(f"❌ Web Scraping Error: {e}\n")
    finally:
        if page:
            page.quit()

    return records


def scrape_orange():
    """Main scraper function for Orange County"""
    sys.stderr.write("🍊 Starting Orange County PDF+Web Scraper\n")
    
    url = "https://netapps.ocfl.net/BestJail/PDF/bookings.pdf"
    
    try:
        sys.stderr.write(f"📡 Downloading PDF from {url}...\n")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        sys.stderr.write(f"   PDF Size: {len(response.content)} bytes\n")
        
        # 1. Parse PDF
        records = parse_orange_pdf(response.content)
        sys.stderr.write(f"📊 Extracted {len(records)} records from PDF\n")
        
        # 2. Enrich with Web Data
        if records:
            records = enrich_records_with_web(records)
        
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
