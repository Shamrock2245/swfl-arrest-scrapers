#!/usr/bin/env python3
"""
Simple Google Sheets Writer for County Scrapers

Writes normalized arrest data directly to county-specific tabs in the master spreadsheet.
Uses the 34-column schema defined in the project.

Author: SWFL Arrest Scrapers Team
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

# Google Sheets configuration
SPREADSHEET_ID = '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E'
CREDENTIALS_PATH = '/home/ubuntu/swfl-arrest-scrapers/creds/service-account-key.json'

# County sheet GIDs (for reference)
COUNTY_GIDS = {
    'Orange': 9307263,
    'Seminole': 840815333,
    'Polk': 277129360,
    'Pinellas': 1392727770,
    'Lee': 0,
    'Charlotte': 172130241,
    'Collier': 944555709,
    'Sarasota': 1695156637,
    'Hendry': 1669874962,
    'DeSoto': 1563909734,
    'Manatee': 517748079,
    'Palm Beach': 2073655185,
    'Broward': 1291101941,
    'Hillsborough': 1317140542,
    'Osceola': 82714931,
}

# 34-column header schema (as specified by user)
HEADER_COLUMNS = [
    'Booking_Number', 'Full_Name', 'First_Name', 'Last_Name', 'DOB', 'Sex', 'Race',
    'Arrest_Date', 'Arrest_Time', 'Booking_Date', 'Booking_Time', 'Agency',
    'Address', 'City', 'State', 'Zipcode', 'Charges',
    'Charge_1', 'Charge_1_Statute', 'Charge_1_Bond',
    'Charge_2', 'Charge_2_Statute', 'Charge_2_Bond',
    'Bond_Amount', 'Bond_Type', 'Status', 'Court_Date', 'Case_Number',
    'Mugshot_URL', 'County', 'Court_Location', 'Detail_URL',
    'Lead_Score', 'Lead_Status', 'LastChecked', 'LastCheckedMode'
]

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class SimpleSheetsWriter:
    """Simple writer for appending arrest records to Google Sheets."""
    
    def __init__(self, credentials_path: str = CREDENTIALS_PATH):
        """Initialize the sheets writer with credentials."""
        self.credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES
        )
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
    
    def normalize_record(self, raw_record: Dict[str, Any], county: str) -> List[str]:
        """
        Normalize a raw scraper record to the 34-column schema.
        
        Args:
            raw_record: Dictionary from scraper output
            county: County name
        
        Returns:
            List of values matching HEADER_COLUMNS order
        """
        # Parse charges into individual charge fields
        charges_str = raw_record.get('Charges', '')
        charges_list = [c.strip() for c in charges_str.split('|') if c.strip()] if charges_str else []
        
        charge_1 = charges_list[0] if len(charges_list) > 0 else ''
        charge_2 = charges_list[1] if len(charges_list) > 1 else ''
        
        # Build the normalized row
        row = [
            str(raw_record.get('Booking_Number', '') or ''),
            str(raw_record.get('Full_Name', '') or ''),
            str(raw_record.get('First_Name', '') or ''),
            str(raw_record.get('Last_Name', '') or ''),
            str(raw_record.get('DOB', '') or ''),
            str(raw_record.get('Sex', '') or ''),
            str(raw_record.get('Race', '') or ''),
            str(raw_record.get('Arrest_Date', '') or ''),
            str(raw_record.get('Arrest_Time', '') or ''),
            str(raw_record.get('Booking_Date', '') or ''),
            str(raw_record.get('Booking_Time', '') or ''),
            str(raw_record.get('Agency', raw_record.get('Arrest_Agency', '')) or ''),
            str(raw_record.get('Address', '') or ''),
            str(raw_record.get('City', '') or ''),
            str(raw_record.get('State', 'FL') or 'FL'),
            str(raw_record.get('Zipcode', raw_record.get('ZIP', '')) or ''),
            charges_str,
            charge_1,
            '',  # Charge_1_Statute
            '',  # Charge_1_Bond
            charge_2,
            '',  # Charge_2_Statute
            '',  # Charge_2_Bond
            str(raw_record.get('Bond_Amount', '') or ''),
            str(raw_record.get('Bond_Type', '') or ''),
            str(raw_record.get('Status', 'In Custody') or 'In Custody'),
            str(raw_record.get('Court_Date', '') or ''),
            str(raw_record.get('Case_Number', '') or ''),
            str(raw_record.get('Mugshot_URL', '') or ''),
            county,
            str(raw_record.get('Court_Location', '') or ''),
            str(raw_record.get('Detail_URL', '') or ''),
            '',  # Lead_Score (calculated later)
            '',  # Lead_Status (calculated later)
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # LastChecked
            'Scraper'  # LastCheckedMode
        ]
        
        return row
    
    def get_existing_booking_numbers(self, sheet_name: str) -> set:
        """Get all existing booking numbers and full names from a sheet for deduplication."""
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            all_values = sheet.get_all_values()
            
            if len(all_values) <= 1:
                return set()
            
            # Booking_Number is column 0, Full_Name is column 1
            identifiers = set()
            for row in all_values[1:]:
                # Add booking number if present
                if row and row[0]:
                    identifiers.add(str(row[0]).strip())
                # Also add full name for records without booking numbers
                if row and len(row) > 1 and row[1]:
                    identifiers.add(str(row[1]).strip())
            
            return identifiers
        except Exception as e:
            print(f"Warning: Could not get existing identifiers: {e}")
            return set()
    
    def write_records(
        self,
        records: List[Dict[str, Any]],
        county: str,
        deduplicate: bool = True
    ) -> Dict[str, int]:
        """
        Write records to the county-specific sheet.
        
        Args:
            records: List of raw record dictionaries from scraper
            county: County name (must match sheet tab name)
            deduplicate: Skip records with existing booking numbers
        
        Returns:
            Statistics dictionary
        """
        if not records:
            return {'total': 0, 'new': 0, 'skipped': 0}
        
        # Get the sheet
        try:
            sheet = self.spreadsheet.worksheet(county)
        except gspread.WorksheetNotFound:
            print(f"Error: Sheet '{county}' not found")
            return {'total': 0, 'new': 0, 'skipped': 0, 'error': 'Sheet not found'}
        
        # Get existing booking numbers for deduplication
        existing_bookings = set()
        if deduplicate:
            existing_bookings = self.get_existing_booking_numbers(county)
            print(f"Found {len(existing_bookings)} existing records in {county}")
        
        # Normalize and filter records
        new_rows = []
        skipped = 0
        
        for record in records:
            booking_num = str(record.get('Booking_Number', '') or '').strip()
            full_name = str(record.get('Full_Name', '') or '').strip()
            
            # Use booking number if available, otherwise use full name for dedupe
            dedupe_key = booking_num if booking_num else full_name
            
            # Skip if no identifier at all
            if not dedupe_key:
                skipped += 1
                continue
            
            # Skip duplicates
            if deduplicate and dedupe_key in existing_bookings:
                skipped += 1
                continue
            
            # Normalize the record
            row = self.normalize_record(record, county)
            new_rows.append(row)
        
        # Write new records
        if new_rows:
            sheet.append_rows(new_rows, value_input_option='USER_ENTERED')
            print(f"✅ Wrote {len(new_rows)} new records to {county}")
        
        return {
            'total': len(records),
            'new': len(new_rows),
            'skipped': skipped
        }


def write_to_sheets(records: List[Dict[str, Any]], county: str) -> Dict[str, int]:
    """
    Convenience function to write records to Google Sheets.
    
    Args:
        records: List of record dictionaries from scraper
        county: County name
    
    Returns:
        Statistics dictionary
    """
    writer = SimpleSheetsWriter()
    return writer.write_records(records, county)


if __name__ == "__main__":
    # Test the writer
    print("Testing SimpleSheetsWriter...")
    writer = SimpleSheetsWriter()
    
    # Test record
    test_record = {
        'Booking_Number': 'TEST123',
        'Full_Name': 'DOE, JOHN',
        'First_Name': 'JOHN',
        'Last_Name': 'DOE',
        'DOB': '01/01/1990',
        'Sex': 'M',
        'Race': 'W',
        'Charges': 'TEST CHARGE 1 | TEST CHARGE 2',
        'Status': 'In Custody',
        'County': 'Orange'
    }
    
    # Normalize and print
    normalized = writer.normalize_record(test_record, 'Orange')
    print(f"Normalized record has {len(normalized)} columns")
    print(f"Headers: {len(HEADER_COLUMNS)} columns")
    
    for i, (h, v) in enumerate(zip(HEADER_COLUMNS, normalized)):
        if v:
            print(f"  {i}: {h} = {v}")
