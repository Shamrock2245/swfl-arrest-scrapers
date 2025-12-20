"""
Pinellas County Scraper Runner - Writes to Google Sheets
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_scrapers.scrapers.pinellas_solver import scrape_pinellas
from python_scrapers.writers.simple_sheets_writer import SimpleSheetsWriter


def main():
    """Run Pinellas scraper and write to Google Sheets."""
    print("=" * 60)
    print("Pinellas County Arrest Scraper -> Google Sheets")
    print("=" * 60)
    
    # Scrape data
    print("\n📡 Scraping Pinellas County arrests...")
    inmates = scrape_pinellas(days_back=7, fetch_details=False)
    
    if not inmates:
        print("❌ No inmates found")
        return
    
    print(f"✅ Found {len(inmates)} inmates")
    
    # Transform to sheets format
    print("\n📝 Transforming data for Google Sheets...")
    rows = []
    for inmate in inmates:
        # Combine charges
        charges_list = inmate.get('charges', [])
        all_charges = '; '.join(charges_list) if charges_list else ''
        
        # Get individual charges
        charge_1 = charges_list[0] if len(charges_list) > 0 else ''
        charge_2 = charges_list[1] if len(charges_list) > 1 else ''
        
        row = {
            'Booking_Number': inmate.get('booking_number', ''),
            'Full_Name': inmate.get('full_name', ''),
            'First_Name': inmate.get('first_name', ''),
            'Last_Name': inmate.get('last_name', ''),
            'DOB': inmate.get('dob', ''),
            'Sex': inmate.get('sex', ''),
            'Race': inmate.get('race', ''),
            'Arrest_Date': inmate.get('booking_date', ''),
            'Arrest_Time': inmate.get('booking_time', ''),
            'Booking_Date': inmate.get('booking_date', ''),
            'Booking_Time': inmate.get('booking_time', ''),
            'Agency': '',
            'Address': '',
            'City': '',
            'State': 'FL',
            'Zipcode': '',
            'Charges': all_charges,
            'Charge_1': charge_1,
            'Charge_1_Statute': '',
            'Charge_1_Bond': '',
            'Charge_2': charge_2,
            'Charge_2_Statute': '',
            'Charge_2_Bond': '',
            'Bond_Amount': inmate.get('bond_amount', ''),
            'Bond_Type': '',
            'Status': inmate.get('status', ''),
            'Court_Date': '',
            'Case_Number': '',
            'Mugshot_URL': '',
            'County': 'Pinellas',
            'Court_Location': '',
            'Detail_URL': inmate.get('detail_url', ''),
            'Lead_Score': '',
            'Lead_Status': '',
            'LastChecked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'LastCheckedMode': 'scraper'
        }
        rows.append(row)
    
    # Write to Google Sheets
    print("\n📊 Writing to Google Sheets...")
    
    # Initialize writer (uses default credentials path)
    writer = SimpleSheetsWriter()
    
    # Write to Pinellas sheet using the correct method
    result = writer.write_records(
        records=rows,
        county='Pinellas',
        deduplicate=True
    )
    
    print(f"\n✅ Complete!")
    print(f"   Total records: {result.get('total', 0)}")
    print(f"   New records written: {result.get('new', 0)}")
    print(f"   Duplicates skipped: {result.get('skipped', 0)}")


if __name__ == "__main__":
    main()
