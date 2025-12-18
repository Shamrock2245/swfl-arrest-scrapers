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
    print(f"🍊 Running Orange County Scraper Runner at {datetime.now()}")
    print("================================================================================")

    # 1. Run the Solver
    # We call the solver script as a subprocess to keep it isolated or direct import
    # Direct import is cleaner if in same package.
    
    # Using subprocess to match pattern of others and capture stdout
    solver_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'orange_solver.py')
    
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
            # Map raw fields to ArrestRecord model
            # Our solver already creates a dict that matches Schema effectively
            # But we should ensure type safety with the Model
            
            # Create ArrestRecord (handles normalization)
            # Use PascalCase to match Dataclass fields or use from_dict helper
            record = ArrestRecord(
                Booking_Number=raw.get('Booking_Number'),
                Booking_Date=raw.get('Booking_Date'),
                Full_Name=raw.get('Full_Name'),
                County='Orange',
                Status=raw.get('Status', 'Active'),
                Charges=raw.get('Charges', ''),
                Bond_Amount=raw.get('Bond_Amount', '0'),
                Mugshot_URL=raw.get('Mugshot_URL', ''), # PDF often has no mugs
                Arrest_Date=raw.get('Arrest_Date'),
                # Pass extra data to dictionary if needed, but dataclass strict init prevents it
                # So we only pass known fields
                Address=raw.get('Address', ''),
                # Facility=raw.get('Facility', ''), # Not in model
                Race=raw.get('Race', ''),
                Sex=raw.get('Sex', ''),
                # Age=raw.get('Age', ''), # Not in model
                Case_Number=raw.get('Case_Number', ''),
                Agency=raw.get('Arrest_Agency', '') # Mapped from Arrest_Agency
            )
            
            # Fallback for fields not in constructor explicit args but in model
            # The model __init__ might not take all args, so we set them manually if needed
            # Checking ArrestRecord definition... usually it takes a dict or kwargs
            # Assuming standard structure from other runners
            
            # Score
            score_result = scorer.score_and_update(record)
            
            processed_records.append(score_result)
            
        except Exception as e:
            print(f"⚠️ Error processing record {raw.get('Booking_Number')}: {e}")
            continue

    print(f"📊 Processed {len(processed_records)} valid records")

    # 3. Write to Sheets
    sheets_id = os.getenv('GOOGLE_SHEETS_ID', '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E')
    creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH', '/Users/brendan/Desktop/swfl-arrest-scrapers/creds/service-account-key.json')
    
    if not processed_records:
        print("No records to write.")
    else:
        # ordered_headers = list(processed_records[0].keys()) # Removed: ArrestRecord is object
        pass

    try:
        writer = SheetsWriter(
            spreadsheet_id=sheets_id,
            credentials_path=creds_path
        )
        
        # Write to "Orange" tab
        # Ensure tab exists? Writer usually handles or throws
        stats = writer.write_records(
            records=processed_records,
            county='Orange',
            deduplicate=True
        )
        
        print(f"✅ Write Complete - Inserted: {stats.get('new_records', 0)}, Total: {stats.get('total_records', 0)}")
        
    except Exception as e:
        print(f"❌ Sheets Write Failed: {e}")

if __name__ == "__main__":
    main()
