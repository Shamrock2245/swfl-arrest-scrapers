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
    print(" Import Error: checking path...")
    print(sys.path)
    raise

def main():
    print("================================================================================")
    print(f"🌴 Running Collier County Scraper Runner at {datetime.now()}")
    print("================================================================================")

    # 1. Run the Solver
    solver_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'collier_solver.py')
    
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
            # Parse Name
            full_name = raw.get('name', '')
            parts = full_name.split(',', 1)
            last_name = parts[0].strip() if len(parts) > 0 else ''
            first_name = parts[1].strip() if len(parts) > 1 else ''

            # Create ArrestRecord (handles normalization)
            record = ArrestRecord(
                Booking_Number=raw.get('booking_number', ''),
                Booking_Date=raw.get('booking_date', ''),
                Full_Name=full_name,
                First_Name=first_name,
                Last_Name=last_name,
                DOB=raw.get('dob', ''),
                County='Collier',
                Agency=raw.get('agency', ''),
                Charges=raw.get('charges', ''),
                Bond_Paid=raw.get('bond_paid', 'NO'),
                Mugshot_URL=raw.get('mugshot_url', ''),
                Address=raw.get('address', ''),
                Race=raw.get('race', ''),
                Sex=raw.get('sex', ''),
                Height=raw.get('height', ''),
                Weight=raw.get('weight', ''),
                Detail_URL='https://www2.colliersheriff.org/arrestsearch/Report.aspx'
            )
            
            # Score
            score_result = scorer.score_and_update(record)
            
            processed_records.append(score_result)
            
        except Exception as e:
            print(f"⚠️ Error processing record {raw.get('booking_number')}: {e}")
            continue

    print(f"📊 Processed {len(processed_records)} valid records")

    # 3. Write to Sheets
    sheets_id = os.getenv('GOOGLE_SHEETS_ID', '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E')
    
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

    try:
        writer = SheetsWriter(
            spreadsheet_id=sheets_id,
            credentials_path=creds_path
        )
        
        # Write to "Collier" tab
        stats = writer.write_records(
            records=processed_records,
            county='Collier',
            deduplicate=True
        )
        
        print(f"✅ Write Complete - Inserted: {stats.get('new_records', 0)}, Total: {stats.get('total_records', 0)}")
        
    except Exception as e:
        print(f"❌ Sheets Write Failed: {e}")

if __name__ == "__main__":
    main()
