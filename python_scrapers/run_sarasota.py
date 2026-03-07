import os
import sys
import json
import subprocess
from datetime import datetime

# Add parent directory (swfl-arrest-scrapers) to path to allow importing python_scrapers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from writers.sheets_writer import SheetsWriter
    from scoring.lead_scorer import LeadScorer
    from models.arrest_record import ArrestRecord
except ImportError:
    # Fallback/Debug
    print(" Import Error: checking path...")
    print(sys.path)
    raise

def main():
    print("================================================================================")
    print(f"🏖️ Running Sarasota County Scraper Runner at {datetime.now()}")
    print("================================================================================")

    # 1. Run the Solver
    solver_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'sarasota_solver.py')
    
    try:
        result = subprocess.run(
            ['python3', solver_path],
            capture_output=True,
            text=True,
            check=True
        )
        raw_data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Solver failed: {e.stderr}")
        return
    except json.JSONDecodeError:
        print(f"❌ Failed to parse solver output: {result.stdout}")
        return

    print(f"📥 Received {len(raw_data)} records from solver")

    # 2. Process Records
    scorer = LeadScorer()
    processed_records = []
    
    for raw in raw_data:
        try:
            record = ArrestRecord(
                Booking_Number=raw.get('Booking_Number'),
                Booking_Date=raw.get('Booking_Date'),
                Full_Name=raw.get('Full_Name'),
                First_Name=raw.get('First_Name', ''),
                Last_Name=raw.get('Last_Name', ''),
                County='Sarasota',
                Booking_Time=raw.get('Booking_Time', ''),
                Status=raw.get('Status', 'Active'),
                Charges=raw.get('Charges', ''),
                Bond_Amount=raw.get('Bond_Amount', '0'),
                Mugshot_URL=raw.get('Mugshot_URL', ''),
                Address=raw.get('Address', ''),
                City=raw.get('City', ''),
                State=raw.get('State', 'FL'),
                ZIP=raw.get('Zipcode', raw.get('ZIP', '')),
                Race=raw.get('Race', ''),
                Sex=raw.get('Sex', ''),
                Case_Number=raw.get('Case_Number', ''),
                Detail_URL=raw.get('URL', '')
            )
            
            # Score
            score_result = scorer.score_and_update(record)
            
            processed_records.append(score_result)
            
        except Exception as e:
            print(f"⚠️ Error processing record {raw.get('Booking_Number')}: {e}")
            continue

    print(f"📊 Processed {len(processed_records)} valid records")

    # 3. Write to Sheets
    sheets_id = os.getenv('GOOGLE_SHEETS_ID', '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E')
    
    possible_creds = [
        os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH'),
        os.path.join(os.path.dirname(__file__), '../credentials/shamrock-bail-suite-fd1834493ea7.json'),
        os.path.join(os.path.dirname(__file__), '../creds/service-account-key.json'),
        os.path.join(os.path.dirname(__file__), 'creds/service-account-key.json'),
        os.path.join(os.path.dirname(__file__), '../../creds/service-account-key.json')
    ]
    
    creds_path = None
    for path in possible_creds:
        if path and os.path.exists(path):
            creds_path = path
            break

    try:
        writer = SheetsWriter(
            spreadsheet_id=sheets_id,
            credentials_path=creds_path
        )
        
        stats = writer.write_records(
            records=processed_records,
            county='Sarasota',
            deduplicate=True
        )
        
        print(f"✅ Write Complete - Inserted: {stats.get('new_records', 0)}, Total: {stats.get('total_records', 0)}")
        
    except Exception as e:
        print(f"❌ Sheets Write Failed: {e}")

if __name__ == "__main__":
    main()
