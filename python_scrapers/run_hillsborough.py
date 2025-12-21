
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
                record.Scrape_Timestamp = item.get('Scrape_Timestamp')
                record.County = 'Hillsborough'
                record.Booking_Number = item.get('Booking_Number')
                record.Full_Name = item.get('Full_Name')
                record.Last_Name = item.get('Last_Name')
                record.First_Name = item.get('First_Name')
                record.Middle_Name = item.get('Middle_Name')
                record.DOB = item.get('DOB')
                record.Booking_Date = item.get('Booking_Date')
                record.Booking_Time = item.get('Booking_Time')
                record.Status = item.get('Status')
                record.Race = item.get('Race')
                record.Sex = item.get('Sex')
                record.Height = item.get('Height')
                record.Weight = item.get('Weight')
                record.Address = item.get('Address')
                record.City = item.get('City')
                record.State = item.get('State')
                record.ZIP = item.get('ZIP')
                record.Mugshot_URL = item.get('Mugshot_URL')
                record.Charges = item.get('Charges')
                record.Bond_Amount = item.get('Bond_Amount')
                record.Case_Number = item.get('Case_Number')
                record.Detail_URL = item.get('Detail_URL')

                # Calculate Score
                score, status = scorer.score_arrest(record)
                record.Lead_Score = score
                record.Lead_Status = status
                
                processed_records.append(record)
                
            except Exception as e:
                print(f"⚠️ Error processing record {item.get('Booking_Number')}: {e}")

        # 4. Write to Sheets
        if processed_records:
            SPREADSHEET_ID = '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E'
            
            # Check standard credential locations
            possible_creds = [
                os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH'),
                os.path.join(os.path.dirname(__file__), '../creds/service-account-key.json'),
                os.path.join(os.path.dirname(__file__), 'creds/service-account-key.json'),
                os.path.join(os.path.dirname(__file__), '../../creds/service-account-key.json')
            ]
            
            creds_path = None
            for path in possible_creds:
                if path and os.path.exists(path):
                    creds_path = path
                    break
                    
            writer = SheetsWriter(spreadsheet_id=SPREADSHEET_ID, credentials_path=creds_path)
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
