#!/usr/bin/env python3
"""
Seminole County Scraper Runner with Google Sheets Integration

Runs the Seminole County scraper and writes results to Google Sheets.

Usage:
    python3 run_seminole_to_sheets.py
"""

import subprocess
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_scrapers.writers.simple_sheets_writer import write_to_sheets


def run_seminole_scraper():
    """Run the Seminole County scraper and return parsed records."""
    print("🔵 Running Seminole County Scraper...")
    
    solver_path = os.path.join(
        os.path.dirname(__file__),
        'scrapers',
        'seminole_solver.py'
    )
    
    try:
        result = subprocess.run(
            ['python3', solver_path],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes for Selenium-based scraper
        )
        
        # Print stderr (progress logs)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Scraper failed with exit code {result.returncode}")
            return []
        
        raw_json = result.stdout.strip()
        if not raw_json:
            print("⚠️ No data returned from scraper")
            return []
        
        # Parse JSON
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            # Try to find JSON array in output
            start = raw_json.find('[')
            end = raw_json.rfind(']') + 1
            if start != -1 and end > start:
                data = json.loads(raw_json[start:end])
            else:
                print("❌ Could not parse JSON output")
                return []
        
        print(f"✅ Scraped {len(data)} records")
        return data
        
    except subprocess.TimeoutExpired:
        print("❌ Scraper timed out")
        return []
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return []


def transform_seminole_record(record):
    """
    Transform Seminole record fields to match the standard schema.
    
    Seminole scraper outputs different field names that need mapping.
    """
    # Map Seminole-specific fields to standard schema
    transformed = {
        'Booking_Number': record.get('Booking_Number') or record.get('Inmate_Number', ''),
        'Full_Name': record.get('Full_Name', ''),
        'First_Name': record.get('First_Name', ''),
        'Last_Name': record.get('Last_Name', ''),
        'DOB': record.get('DOB', ''),
        'Sex': record.get('Sex', ''),
        'Race': record.get('Race', ''),
        'Arrest_Date': record.get('Arrest_Date', record.get('Booking_Date', '')),
        'Arrest_Time': record.get('Arrest_Time', ''),
        'Booking_Date': record.get('Booking_Date', ''),
        'Booking_Time': record.get('Booking_Time', ''),
        'Agency': record.get('Arrest_Agency', ''),
        'Address': record.get('Address', ''),
        'City': record.get('City', ''),
        'State': record.get('State', 'FL'),
        'Zipcode': record.get('Zipcode', ''),
        'Charges': record.get('Charges', ''),
        'Bond_Amount': record.get('Bond_Amount', ''),
        'Bond_Type': record.get('Bond_Type', ''),
        'Status': record.get('Status', 'In Custody'),
        'Court_Date': record.get('Court_Date', ''),
        'Case_Number': record.get('Case_Number', ''),
        'Mugshot_URL': record.get('Mugshot_URL', ''),
        'Detail_URL': record.get('Detail_URL', ''),
        'County': 'Seminole'
    }
    
    return transformed


def main():
    """Main entry point."""
    print("=" * 60)
    print("Seminole County Scraper -> Google Sheets")
    print("=" * 60)
    
    # Run scraper
    records = run_seminole_scraper()
    
    if not records:
        print("No records to write")
        return
    
    # Transform records to standard schema
    print(f"\n🔄 Transforming {len(records)} records...")
    transformed_records = [transform_seminole_record(r) for r in records]
    
    # Filter out records without booking numbers
    valid_records = [r for r in transformed_records if r.get('Booking_Number')]
    print(f"   {len(valid_records)} records have booking numbers")
    
    if not valid_records:
        print("⚠️ No valid records with booking numbers")
        return
    
    # Write to Google Sheets
    print(f"\n📊 Writing {len(valid_records)} records to Google Sheets...")
    stats = write_to_sheets(valid_records, 'Seminole')
    
    print(f"\n📈 Results:")
    print(f"   Total records: {stats['total']}")
    print(f"   New records written: {stats['new']}")
    print(f"   Duplicates skipped: {stats['skipped']}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
