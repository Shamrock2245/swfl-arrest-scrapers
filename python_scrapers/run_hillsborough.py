
import subprocess
import json
import sys
import os
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.arrest_record import ArrestRecord
from scoring.lead_scorer import LeadScorer
from writers.sheets_writer import SheetsWriter

def run_hillsborough():
    print("🚀 Starting Hillsborough Scraper...")
    
    # 1. Run the solver
    solver_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'hillsborough_solver.py')
    
    try:
        # Run python script and capture stdout
        result = subprocess.run(['python3', solver_path], capture_output=True, text=True)
        
        # Print stderr (progress logs)
        print(result.stderr)
        
        if result.returncode != 0:
            print("❌ Scraper failed with exit code", result.returncode)
            return

        raw_json = result.stdout.strip()
        if not raw_json:
            print("⚠️ No data returned from scraper")
            return

        # 2. Parse JSON
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            # Sometimes prints might mix with json, try to find the list
            start = raw_json.find('[')
            end = raw_json.rfind(']') + 1
            if start != -1 and end != -1:
                data = json.loads(raw_json[start:end])
            else:
                print("❌ Could not parse JSON output")
                print("Raw output start:", raw_json[:200])
                return

        print(f"✅ Received {len(data)} raw records")

        # 3. Normalize & Score
        processed_records = []
        scorer = LeadScorer()
        
        for item in data:
            try:
                # Map fields to 34-col schema
                record = ArrestRecord()
                record.scraped_timestamp = item.get('Scrape_Timestamp')
                record.county = 'Hillsborough'
                record.booking_number = item.get('Booking_Number')
                record.full_name = item.get('Full_Name')
                record.last_name = item.get('Last_Name')
                record.first_name = item.get('First_Name')
                record.middle_name = item.get('Middle_Name')
                record.dob = item.get('DOB')
                record.booking_date = item.get('Booking_Date')
                record.booking_time = item.get('Booking_Time')
                record.arrest_date = item.get('Arrest_Date')
                record.status = item.get('Status')
                record.race = item.get('Race')
                record.sex = item.get('Sex')
                record.height = item.get('Height')
                record.weight = item.get('Weight')
                record.address = item.get('Address')
                record.city = item.get('City')
                record.state = item.get('State')
                record.zip_code = item.get('ZIP')
                record.mugshot_url = item.get('Mugshot_URL')
                record.charges = item.get('Charges')
                record.bond_amount = item.get('Bond_Amount')
                record.case_number = item.get('Case_Number')
                record.detail_url = item.get('Detail_URL')

                # Calculate Score
                score, status = scorer.score_arrest(record)
                record.lead_score = score
                record.lead_status = status
                
                processed_records.append(record)
                
            except Exception as e:
                print(f"⚠️ Error processing record {item.get('Booking_Number')}: {e}")

        # 4. Write to Sheets
        if processed_records:
            SPREADSHEET_ID = '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E'
            CREDENTIALS_PATH = '/Users/brendan/Desktop/swfl-arrest-scrapers/creds/service-account-key.json'
            writer = SheetsWriter(spreadsheet_id=SPREADSHEET_ID, credentials_path=CREDENTIALS_PATH)
            writer.write_records(processed_records, county='Hillsborough')
            print("✅ Done!")
        else:
            print("⚠️ No valid records to write")

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_hillsborough()
