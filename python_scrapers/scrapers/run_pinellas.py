#!/usr/bin/env python3
"""
Pinellas County Scraper Runner - Production Ready

Integrates pinellas_solver.py with the Python scraper infrastructure:
- Calls the solver to scrape raw data
- Converts to ArrestRecord objects
- Scores records with LeadScorer
- Writes to Google Sheets via SheetsWriter

Author: SWFL Arrest Scrapers Team
Date: December 27, 2025
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
    
    # Flatten charges list if needed
    charges = raw_data.get('charges', [])
    if isinstance(charges, list):
        charges_str = ' | '.join(charges)
    else:
        charges_str = str(charges)
    
    # Map raw fields to ArrestRecord schema v3.0 (39 columns)
    record = ArrestRecord(
        County="Pinellas",
        Booking_Number=raw_data.get('booking_number', ''),
        Person_ID=raw_data.get('booking_number', ''), # Reuse if needed
        Full_Name=raw_data.get('full_name', ''),
        First_Name=raw_data.get('first_name', ''),
        Middle_Name=raw_data.get('middle_name', ''),
        Last_Name=raw_data.get('last_name', ''),
        DOB=raw_data.get('dob', ''),
        Arrest_Date=raw_data.get('booking_date', ''), # Pinellas provides booking date usually
        Arrest_Time=raw_data.get('booking_time', ''),
        Booking_Date=raw_data.get('booking_date', ''),
        Booking_Time=raw_data.get('booking_time', ''),
        Status=raw_data.get('status', 'IN CUSTODY'),
        Facility=raw_data.get('facility', 'Pinellas County Jail'),
        Agency=raw_data.get('agency', ''),
        Race=raw_data.get('race', ''),
        Sex=raw_data.get('sex', ''),
        Height=raw_data.get('height', ''),
        Weight=raw_data.get('weight', ''),
        Address=raw_data.get('address', ''),
        City=raw_data.get('city', ''),
        State=raw_data.get('state', 'FL'),
        ZIP=raw_data.get('zip', ''),
        Mugshot_URL=raw_data.get('mugshot_url', ''),
        Charges=charges_str,
        Bond_Amount=raw_data.get('bond_amount', '0'),
        Bond_Paid=raw_data.get('bond_paid', 'NO'),
        Bond_Type=raw_data.get('bond_type', ''),
        Court_Type=raw_data.get('court_type', ''),
        Case_Number=raw_data.get('case_number', ''),
        Court_Date=raw_data.get('court_date', ''),
        Court_Time=raw_data.get('court_time', ''),
        Court_Location=raw_data.get('court_location', ''),
        Detail_URL=raw_data.get('detail_url', ''),
        Lead_Score=0,
        Lead_Status="WARM",
        LastChecked=datetime.utcnow().isoformat(),
        LastCheckedMode="INITIAL"
    )
    
    # Chronological Fallback Logic
    if not record.Booking_Date and record.Arrest_Date:
        record.Booking_Date = record.Arrest_Date
    if not record.Booking_Time and record.Arrest_Time:
        record.Booking_Time = record.Arrest_Time
        
    return record


def main():
    """Main execution function."""
    
    print(f"\n{'='*80}")
    print(f"🔵 Pinellas County Scraper - Production Runner")
    print(f"{'='*80}\n")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solver_path = os.path.join(script_dir, 'pinellas_solver.py')
    
    # Run the solver
    print(f"📡 Running Pinellas solver (days_back={args.days_back})...")
    try:
        # Stream logs directly to console (stderr) while capturing JSON output (stdout)
        result = subprocess.run(
            ['python3', solver_path, str(args.days_back)],
            stdout=subprocess.PIPE,
            stderr=sys.stderr,  # Stream logs directly to console
            text=True,
            timeout=3600  # 60 minute timeout
        )
        
        if result.returncode != 0:
            print(f"❌ Solver failed with return code {result.returncode}")
            return
        
        # Parse JSON output
        try:
            raw_records = json.loads(result.stdout)
            print(f"✅ Solver extracted {len(raw_records)} raw records")
        except json.JSONDecodeError:
                raise
            
        print(f"✅ Solver extracted {len(raw_records)} raw records")
        
    except subprocess.TimeoutExpired:
        print("❌ Solver timed out after 20 minutes")
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
        
        # Check standard credential locations
        possible_creds = [
            os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH'),
            os.path.join(os.path.dirname(__file__), '../../creds/service-account-key.json'),
            os.path.join(os.path.dirname(__file__), '../../../creds/service-account-key.json')
        ]
        
        creds_path = None
        for path in possible_creds:
            if path and os.path.exists(path):
                creds_path = path
                break
        
        writer = SheetsWriter(
            spreadsheet_id=sheets_id,
            credentials_path=creds_path
        )
        
        # Write to Pinellas tab
        stats = writer.write_records(scored_records, county="Pinellas")
        
        # Also log to ingestion log
        writer.log_ingestion("Pinellas", stats)
        
        print(f"\n{'='*80}")
        print(f"✅ Pinellas County Scraper Complete!")
        print(f"{'='*80}")
        print(f"   New records: {stats['new_records']}")
        print(f"   Updated: {stats.get('updated_records', 0)}")
        print(f"   Qualified: {stats['qualified_records']}")
        print(f"   Duplicates skipped: {stats['duplicates_skipped']}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error writing to sheets: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
