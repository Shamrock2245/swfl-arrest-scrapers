#!/usr/bin/env python3
"""
Hillsborough County Scraper Runner - Production Ready

Integrates hillsborough_solver.py with the Python scraper infrastructure:
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
    
    # Map raw fields to ArrestRecord schema v3.0 (39 columns)
    record = ArrestRecord(
        County="Hillsborough",
        Booking_Number=raw_data.get('Booking_Number', ''),
        Person_ID=raw_data.get('Person_ID', ''),
        Full_Name=raw_data.get('Full_Name', ''),
        First_Name=raw_data.get('First_Name', ''),
        Middle_Name=raw_data.get('Middle_Name', ''),
        Last_Name=raw_data.get('Last_Name', ''),
        DOB=raw_data.get('DOB', ''),
        Arrest_Date=raw_data.get('Arrest_Date', ''),
        Arrest_Time=raw_data.get('Arrest_Time', ''),
        Booking_Date=raw_data.get('Booking_Date', ''),
        Booking_Time=raw_data.get('Booking_Time', ''),
        Status=raw_data.get('Status', 'IN CUSTODY'),
        Facility=raw_data.get('Facility', ''),
        Agency=raw_data.get('Agency', ''),
        Race=raw_data.get('Race', ''),
        Sex=raw_data.get('Sex', ''),
        Height=raw_data.get('Height', ''),
        Weight=raw_data.get('Weight', ''),
        Address=raw_data.get('Address', ''),
        City=raw_data.get('City', ''),
        State=raw_data.get('State', 'FL'),
        ZIP=raw_data.get('ZIP', ''),
        Mugshot_URL=raw_data.get('Mugshot_URL', ''),
        Charges=raw_data.get('Charges', ''),
        Bond_Amount=raw_data.get('Bond_Amount', '0'),
        Bond_Paid=raw_data.get('Bond_Paid', 'NO'),
        Bond_Type=raw_data.get('Bond_Type', ''),
        Court_Type=raw_data.get('Court_Type', ''),
        Case_Number=raw_data.get('Case_Number', ''),
        Court_Date=raw_data.get('Court_Date', ''),
        Court_Time=raw_data.get('Court_Time', ''),
        Court_Location=raw_data.get('Court_Location', ''),
        Detail_URL=raw_data.get('Detail_URL', ''),
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
    print(f"🏙️ Hillsborough County Scraper - Production Runner")
    print(f"{'='*80}\n")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solver_path = os.path.join(script_dir, 'hillsborough_solver.py')
    
    # Run the solver
    print(f"📡 Running Hillsborough solver (days_back={args.days_back})...")
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
        print("❌ Solver timed out after 10 minutes")
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
        
        # Write to Hillsborough tab
        stats = writer.write_records(scored_records, county="Hillsborough")
        
        # Also log to ingestion log
        writer.log_ingestion("Hillsborough", stats)
        
        print(f"\n{'='*80}")
        print(f"✅ Hillsborough County Scraper Complete!")
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
