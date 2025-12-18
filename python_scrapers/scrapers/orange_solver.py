import sys
import json
import time
import requests
import pdfplumber
import io
import re
from datetime import datetime

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.strip().split())

def parse_pdf_text_mode(pdf_bytes):
    records = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text(layout=True) + "\n"
            
    # The text layout is fixed-width-ish but best parsed by looking for the Booking # pattern
    # Booking # looks like 8 digits, matches regex `\d{8}`
    # Name is to the left of it.
    
    # Text snippet shows:
    # ALLENPIERRE, ZYANNAH NYZADAAZAR 25040081 B / F 20 BRC-IA HOLD-IA07
    
    lines = full_text.split('\n')
    current_record = None
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Header skip
        if "ORANGE COUNTY JAIL" in line or "BOOKINGS DURING" in line or "Race/" in line:
            continue
            
        # START OF RECORD PATTERN: Name + Booking # (8 digits)
        # Regex: ^(.*?) (\d{8}) ([BWU] / [MF]) (\d+) (.*)$
        # Note: Race/Sex might be variable. 
        # Example: 25040081 B / F 20
        
        match = re.search(r'^(.*?) (\d{8}) ([A-Z] ?/ ?[A-Z]) (\d+) (.*)$', line)
        if match:
            # Save previous record if exists
            if current_record:
                records.append(current_record)
            
            # Start New Record
            current_record = {
                "County": "Orange",
                "State": "FL",
                "Details_PDF": "https://netapps.ocfl.net/BestJail/PDF/bookings.pdf",
                "Charges": [], 
                "Bond_Total": 0.0
            }
            
            current_record['Full_Name'] = clean_text(match.group(1))
            current_record['Booking_Number'] = match.group(2)
            
            rs = match.group(3).replace(' ', '')
            if '/' in rs:
                parts = rs.split('/')
                current_record['Race'] = parts[0]
                current_record['Sex'] = parts[1]
                
            current_record['Age'] = match.group(4)
            current_record['Facility'] = clean_text(match.group(5))
            
            # Parse Name to Last/First
            if ',' in current_record['Full_Name']:
                parts = current_record['Full_Name'].split(',', 1)
                current_record['Last_Name'] = parts[0].strip()
                current_record['First_Name'] = parts[1].strip()
            
            continue
            
        # If we are in a record, parse details
        if current_record:
            # Address line? "APOPKA, FL 32703 NON-HISPANIC"
            # It usually contains FL + Zip
            if ', FL' in line:
                # Extract address
                # Might be mixed with Ethnicity
                # Strategy: Split by "  " or take everything before Ethnicity
                # Simple heuristic: Take whole line as Address for now, clean later
                current_record['Address'] = line
            
            # Case Line? "CASE: 2024CF..."
            elif line.startswith('CASE:'):
                current_record['Case_Number'] = line.replace('CASE:', '').strip()
                
            # Charge Line? 
            # Starts with statute often: "843.15(1)(A) FELONY..."
            # Or just text.
            # We treat other lines as charges if they aren't metadata
            elif 'ORANGE COUNTY SHERIFF' in line or 'ORLANDO PD' in line:
                current_record['Arrest_Agency'] = line
            
            # Charge/Detail Line
            else:
                # Noise Filtering
                if "IMS061" in line or "Page:" in line or "ORANGE   COUNTY" in line:
                    continue
                if "BOOKINGS  DURING" in line or "BEGINNING AT" in line:
                    continue
                if "Total Inmates" in line or "TOTAL INMATES" in line:
                    continue
                    
                # Ensure we don't capture the table header again if it repeats
                if "Gender/" in line or "Name" in line and "Booking #" in line:
                    continue

                # Likely a charge or address continuation
                # If we already have address, append to charges
                # If line is short and looks like a city/state, might be address correction
                # But safer to just dump to charges if unsure, or detail
                
                # Check for bond amount at end of line?
                # Regex for "Bond: $..." or just number at end?
                # In text mode, columns are less strict.
                # If line contains "FELONY" or "MISDEMEANOR", it is definitely a charge.
                current_record['Charges'].append(line)

    # Append last record
    if current_record:
        records.append(current_record)
        
    # Post-process records
    final_records = []
    for rec in records:
        # Join charges
        if rec['Charges']:
            rec['Charges'] = ' | '.join(rec['Charges'])
        else:
            rec['Charges'] = ''
            
        # Generate timestamps if missing (PDF doesn't seem to have booking time in that top line?)
        # Header says "BOOKINGS DURING THE 24-HOUR PERIOD BEGINNING AT MIDNIGHT 12/16/2025"
        # We can use that date as default
        # But wait, snippet didn't show the date in the record line. 
        # The header has the date.
        
        # Search for date in full text header
        date_match = re.search(r'BEGINNING AT MIDNIGHT (\d{1,2}/\d{1,2}/\d{4})', full_text)
        if date_match and 'Booking_Date' not in rec:
            rec['Booking_Date'] = date_match.group(1)
        
        # Use scraping time as fallback
        if 'Booking_Date' not in rec:
             rec['Booking_Date'] = datetime.now().strftime('%m/%d/%Y')
             
        # Normalize fields
        if 'Bond_Total' in rec:
             rec['Bond_Amount'] = str(rec['Bond_Total'])
             del rec['Bond_Total']
             
        final_records.append(rec)

    return final_records

def scrape_orange():
    sys.stderr.write("🚀 Starting Orange County PDF Scraper (Text Mode)\n")
    url = "https://netapps.ocfl.net/BestJail/PDF/bookings.pdf"
    
    try:
        sys.stderr.write(f"📡 Downloading PDF from {url}...\n")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        sys.stderr.write(f"   PDF Size: {len(response.content)} bytes\n")
        
        records = parse_pdf_text_mode(response.content)
        
        sys.stderr.write(f"📊 Extracted {len(records)} records from PDF\n")
        
        print(json.dumps(records))
        
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
        print("[]")

if __name__ == "__main__":
    scrape_orange()
