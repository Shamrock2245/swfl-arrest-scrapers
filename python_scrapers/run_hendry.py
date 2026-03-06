import json
import logging
import os
import subprocess
from datetime import datetime, time
import re

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.arrest_record import ArrestRecord
from writers.sheets_writer import SheetsWriter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def map_hendry_record(record_dict):
    """Maps Hendry scraper output to the standard ArrestRecord schema."""
    import copy
    d = copy.deepcopy(record_dict)
    
    # Hendry Specific Parsing (Date)
    if 'booking_date' in d and d['booking_date']:
        try:
            # Example: "02/28/2025" or similar
            parts = d['booking_date'].split()
            date_str = parts[0]
            val = datetime.strptime(date_str, "%m/%d/%Y")
            d['booking_date'] = val.strftime("%Y-%m-%d")
            d['booking_time'] = "00:00:00" if len(parts) == 1 else parts[1]
        except ValueError:
            pass # Keep as is

    valid_fields = {}
    for key, value in d.items():
        if key in ArrestRecord.__annotations__:
            valid_fields[key] = value

    return ArrestRecord(**valid_fields)

def main():
    try:
        logging.info("Starting Hendry scraper execution...")
        solver_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'hendry_solver.py')
        
        result = subprocess.run(
            ['python3', solver_path, '2'],
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            records_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logging.error(f"Failed to parse solver JSON. Raw output:\n{result.stdout}")
            return

        logging.info(f"Retrieved {len(records_data)} raw records from Hendry solver.")

        processed_records = []
        for rd in records_data:
            rec = map_hendry_record(rd)
            processed_records.append(rec)
            
        logging.info(f"Successfully mapped {len(processed_records)} Hendry records.")
        
        # Write to sheets
        sheets_id = os.getenv("GOOGLE_SHEETS_ID", "19t4jBfE0q7g5c5jQ7q84nF93ZtIfzX-GgU5H7PZ5q8Y")
        creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "credentials.json")
        writer = SheetsWriter(spreadsheet_id=sheets_id, credentials_path=creds_path)
        
        writer.write_records(records=processed_records, county="Hendry", deduplicate=True)
        logging.info("Finished writing Hendry records to Google Sheets.")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Hendry solver failed with exit code {e.returncode}")
        logging.error(f"Solver Error Output:\n{e.stderr}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
