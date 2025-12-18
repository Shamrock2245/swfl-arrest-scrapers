# County Adapter Template (v3.0)

This guide outlines how to add a new county to the SWFL Bail Suite using the primary **Python/DrissionPage** engine.

---

## 🏗️ The Adapter Pattern

Each new county requires two main files:
1.  **Solver (`python_scrapers/scrapers/<county>_solver.py`):** The raw logic for navigating the site, bypassing bot detection, and returning JSON.
2.  **Runner (`python_scrapers/run_<county>.py`):** A standard script that calls the solver, applies lead scoring, and writes to Google Sheets.

---

## 1. The Solver (Boilerplate)
Create `python_scrapers/scrapers/<county>_solver.py`:

```python
import sys, json, time
from DrissionPage import ChromiumPage, ChromiumOptions

def scrape_county():
    # 1. Setup Browser (Stealth Mode)
    co = ChromiumOptions().headless(False)
    co.set_argument('--no-sandbox')
    page = ChromiumPage(co)
    
    try:
        # 2. Navigate & Solve
        page.get('https://county-jail-site.com/bookings')
        
        # 3. Extract Data (Map to 34-column schema)
        records = []
        rows = page.eles('tag:tr')
        for row in rows:
            record = {
                "Booking_Number": row.ele('css:.id').text,
                "Full_Name": row.ele('css:.name').text,
                "County": "NEW_COUNTY",
                "Status": "In Custody",
                # ... other fields
            }
            records.append(record)
            
        # 4. Return as JSON
        print(json.dumps(records))
        
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
        print("[]")
    finally:
        page.quit()

if __name__ == "__main__":
    scrape_county()
```

---

## 2. The Runner (Boilerplate)
Create `python_scrapers/run_<county>.py`:

```python
import os, sys, subprocess, json
from writers.sheets_writer import SheetsWriter
from scoring.lead_scorer import LeadScorer
from models.arrest_record import ArrestRecord

def main():
    # 1. Execute Solver
    solver_path = os.path.join(os.path.dirname(__file__), 'scrapers', 'new_county_solver.py')
    result = subprocess.run(['python3', solver_path], capture_output=True, text=True)
    raw_data = json.loads(result.stdout)

    # 2. Process & Score
    scorer = LeadScorer()
    processed = []
    for raw in raw_data:
        record = ArrestRecord(**raw) # Ensure dict matches 34-column schema
        scored_record = scorer.score_and_update(record)
        processed.append(scored_record)

    # 3. Write to Sheets
    writer = SheetsWriter(spreadsheet_id=os.getenv('GOOGLE_SHEETS_ID'))
    writer.write_records(records=processed, county='NEW_COUNTY', deduplicate=True)

if __name__ == "__main__":
    main()
```

---

## 📝 Integration Checklist

- [ ] **Tab Creation:** Add a new tab in the [Master Sheet](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit) with the EXACT county name.
- [ ] **Requirements:** If you added new libraries, update `python_scrapers/requirements.txt`.
- [ ] **Orchestration:** Add the new `.py` script to `jobs/runAll.js` so it runs in the global stagger.
- [ ] **Verification:** Run `python3 python_scrapers/run_<county>.py` and verify:
    - Data appears in the correct tab.
    - `Lead_Score` is populated.
    - No duplicates on re-run.

---
*Maintained by: Shamrock Engineering Team*
