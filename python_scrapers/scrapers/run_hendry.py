#!/usr/bin/env python3
"""
Hendry County Scraper Runner - Production Ready

Integrates hendry_solver.py with the Python scraper infrastructure:
- Calls the solver to scrape raw data
- Converts to ArrestRecord objects
- Scores records with LeadScorer
- Writes to Google Sheets via SheetsWriter

Author: SWFL Arrest Scrapers Team
Date: December 9, 2025
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import score_and_update
from python_scrapers.writers.sheets_writer import SheetsWriter


def convert_to_arrest_record(raw_data: dict) -> ArrestRecord:
    """Convert raw scraper data to ArrestRecord object."""
    
    # Map raw fields to ArrestRecord schema
    record = ArrestRecord(
        County="Hendry",
        Booking_Number=raw_data.get('Booking_Number', ''),
        Full_Name=raw_data.get('Full_Name', ''),
        First_Name=raw_data.get('First_Name', ''),
        Last_Name=raw_data.get('Last_Name', ''),
        DOB=raw_data.get('DOB', raw_data.get('Date of Birth', '')),
        Sex=raw_data.get('Sex', raw_data.get('Gender', '')),
        Race=raw_data.get('Race', ''),
        Arrest_Date=raw_data.get('Arrest_Date', ''),
        Booking_Date=raw_data.get('Booking_Date', ''),
        Address=raw_data.get('Address', ''),
        City=raw_data.get('City', ''),
        State=raw_data.get('State', 'FL'),
        Zipcode=raw_data.get('Zipcode', ''),
        Charges=raw_data.get('Charges', ''),
        Bond_Amount=raw_data.get('Bond_Amount', ''),
        Bond_Type=raw_data.get('Bond_Type', ''),
        Status=raw_data.get('Status', 'IN CUSTODY'),
        Mugshot_URL=raw_data.get('Mugshot_URL', ''),
        source_url=raw_data.get('Detail_URL', '')
    )
    
    return record


def main():
    """Main execution function."""
    
    print(f"\n{'='*80}")
    print(f"🚦 Hendry County Scraper - Production Runner")
    print(f"{'='*80}\n")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solver_path = os.path.join(script_dir, 'hendry_solver.py')
    
    # Run the solver
    print("📡 Running Hendry solver...")
    try:
        result = subprocess.run(
            ['python3', solver_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print stderr (debug info) to stderr
        if result.stderr:
            sys.stderr.write(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Solver failed with return code {result.returncode}")
            return
        
        # Parse JSON output
        raw_records = json.loads(result.stdout)
        print(f"✅ Solver extracted {len(raw_records)} raw records")
        
    except subprocess.TimeoutExpired:
        print("❌ Solver timed out after 5 minutes")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse solver output: {e}")
        print(f"Output was: {result.stdout[:500]}")
        return
    except Exception as e:
        print(f"❌ Error running solver: {e}")
        return
    
    if not raw_records:
        print("⚠️  No records scraped")
        return
    
    # Convert to ArrestRecord objects
    print(f"\n📊 Converting to ArrestRecord objects...")
    records = []
    for raw in raw_records:
        try:
            record = convert_to_arrest_record(raw)
            records.append(record)
            print(f"   ✅ {record.Full_Name} ({record.Booking_Number})")
        except Exception as e:
            print(f"   ⚠️  Failed to convert record: {e}")
            continue
    
    print(f"\n✅ Converted {len(records)} records")
    
    # Score records
    print(f"\n📊 Scoring records...")
    scored_records = []
    for record in records:
        try:
            scored = score_and_update(record)
            scored_records.append(scored)
        except Exception as e:
            print(f"   ⚠️  Failed to score {record.Booking_Number}: {e}")
            scored_records.append(record)  # Add unscored
    
    # Write to Google Sheets
    print(f"\n📝 Writing to Google Sheets...")
    
    try:
        # Get credentials from environment or use defaults
        sheets_id = os.getenv('GOOGLE_SHEETS_ID', '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E')
        creds_path = '/Users/brendan/Desktop/swfl-arrest-scrapers/creds/service-account-key.json'
        
        writer = SheetsWriter(
            spreadsheet_id=sheets_id,
            credentials_path=creds_path
        )
        
        stats = writer.write_records(scored_records, county="Hendry")
        
        print(f"\n{'='*80}")
        print(f"✅ Hendry County Scraper Complete!")
        print(f"{'='*80}")
        print(f"   New records: {stats['new_records']}")
        print(f"   Updated: {stats['updated_records']}")
        print(f"   Qualified: {stats['qualified_records']}")
        print(f"   Duplicates skipped: {stats['duplicates_skipped']}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error writing to sheets: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
