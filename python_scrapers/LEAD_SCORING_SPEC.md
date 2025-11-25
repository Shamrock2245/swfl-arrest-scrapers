# Lead Scoring System Specification

## Overview

This document specifies the integrated lead scoring system for the SWFL Arrest Scrapers project. The system extends the original 32-column universal schema with two additional fields for lead qualification scoring.

**Version:** 2.0  
**Date:** November 24, 2025  
**Author:** SWFL Arrest Scrapers Team

---

## Schema Extension

### Original Schema (32 columns)

The original universal schema included these 32 fields:

1. Booking_Number
2. Full_Name
3. First_Name
4. Last_Name
5. DOB
6. Sex
7. Race
8. Arrest_Date
9. Arrest_Time
10. Booking_Date
11. Booking_Time
12. Agency
13. Address
14. City
15. State
16. Zipcode
17. Charges
18. Charge_1
19. Charge_1_Statute
20. Charge_1_Bond
21. Charge_2
22. Charge_2_Statute
23. Charge_2_Bond
24. Bond_Amount
25. Bond_Type
26. Status
27. Court_Date
28. Case_Number
29. Mugshot_URL
30. County
31. Court_Location

### Extended Schema (34 columns)

**NEW FIELDS:**

32. **Lead_Score** (Number) - Calculated qualification score
33. **Lead_Status** (String) - Hot, Warm, Cold, or Disqualified

---

## Final Header Order (34 Columns)

```
Booking_Number, Full_Name, First_Name, Last_Name, DOB, Sex, Race, 
Arrest_Date, Arrest_Time, Booking_Date, Booking_Time, Agency, 
Address, City, State, Zipcode, Charges, Charge_1, Charge_1_Statute, 
Charge_1_Bond, Charge_2, Charge_2_Statute, Charge_2_Bond, Bond_Amount, 
Bond_Type, Status, Court_Date, Case_Number, Mugshot_URL, County, 
Court_Location, Lead_Score, Lead_Status
```

---

## Scoring Logic

### Input Fields

The scoring algorithm uses these fields from the ArrestRecord:

- **Bond_Amount** - Numeric value extracted from string (removes $, commas)
- **Bond_Type** - Uppercased string (CASH, SURETY, ROR, NO BOND, etc.)
- **Status** - Uppercased string (IN CUSTODY, RELEASED, etc.)
- **Charges** - Free text string
- **Data Completeness** - Checks Full_Name, Charges, Bond_Amount, Court_Date

### Scoring Rules

#### 1. Bond Amount Scoring

| Bond Amount Range | Points | Reason |
|-------------------|--------|--------|
| $500 - $50,000 | +30 | Optimal bond range |
| $50,001 - $100,000 | +20 | High bond |
| > $100,000 | +10 | Very high bond |
| $1 - $499 | -10 | Too low |
| $0 | -50 | No bond required |

#### 2. Bond Type Scoring

| Bond Type Contains | Points | Reason |
|--------------------|--------|--------|
| CASH or SURETY | +25 | Bondable type |
| NO BOND or HOLD | -50 | Not bondable |
| ROR or R.O.R | -30 | Released on recognizance |

#### 3. Status Scoring

| Status Contains | Points | Reason |
|-----------------|--------|--------|
| IN CUSTODY or INCUSTODY | +20 | Still in jail |
| RELEASED | -30 | Already out |

#### 4. Data Completeness Scoring

| Condition | Points | Reason |
|-----------|--------|--------|
| All required fields present* | +15 | Complete data |
| Any required field missing | -10 | Missing data |

*Required fields: Full_Name, Charges, Bond_Amount, Court_Date

#### 5. Disqualifying Charges

| Charge Contains | Points | Reason |
|-----------------|--------|--------|
| capital | -100 | DISQUALIFIED: Severe charge |
| murder | -100 | DISQUALIFIED: Severe charge |
| federal | -100 | DISQUALIFIED: Severe charge |

### Lead Status Mapping

Based on the final calculated score:

| Score Range | Lead_Status | Description |
|-------------|-------------|-------------|
| < 0 | Disqualified | Not a viable lead |
| 0 - 39 | Cold | Low priority |
| 40 - 69 | Warm | Medium priority |
| ≥ 70 | Hot | High priority |

---

## Python Implementation

### ArrestRecord Model

```python
from dataclasses import dataclass

@dataclass
class ArrestRecord:
    # ... original 31 fields ...
    Lead_Score: int = 0
    Lead_Status: str = "Cold"
    
    @classmethod
    def get_header_row(cls) -> list:
        """Returns the 34-column header row."""
        return [
            "Booking_Number", "Full_Name", "First_Name", "Last_Name",
            "DOB", "Sex", "Race", "Arrest_Date", "Arrest_Time",
            "Booking_Date", "Booking_Time", "Agency", "Address",
            "City", "State", "Zipcode", "Charges", "Charge_1",
            "Charge_1_Statute", "Charge_1_Bond", "Charge_2",
            "Charge_2_Statute", "Charge_2_Bond", "Bond_Amount",
            "Bond_Type", "Status", "Court_Date", "Case_Number",
            "Mugshot_URL", "County", "Court_Location",
            "Lead_Score", "Lead_Status"
        ]
    
    def to_sheet_row(self) -> list:
        """Returns a list of 34 values for Google Sheets."""
        return [
            self.Booking_Number, self.Full_Name, self.First_Name,
            # ... all 34 fields in order ...
            self.Lead_Score, self.Lead_Status
        ]
```

### Scoring Function

```python
from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import score_and_update

# Score a record
record = ArrestRecord(
    Booking_Number="2025-001234",
    Full_Name="SMITH, JOHN",
    Bond_Amount="$10,000",
    Bond_Type="SURETY",
    Status="IN CUSTODY",
    Charges="DUI",
    Court_Date="2025-12-15",
    County="Lee"
)

# Score and update in place
record = score_and_update(record)

print(f"Score: {record.Lead_Score}")  # e.g., 90
print(f"Status: {record.Lead_Status}")  # e.g., "Hot"
```

### Google Sheets Writer

```python
from python_scrapers.writers.sheets_writer import SheetsWriter

# Initialize writer
writer = SheetsWriter(
    spreadsheet_id="121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E",
    credentials_path="./creds/service-account-key.json"
)

# Write records (auto-scores if not already scored)
stats = writer.write_records(records, county="Lee")

print(f"New records: {stats['new_records']}")
print(f"Qualified: {stats['qualified_records']}")
```

---

## Example JSON Output

### Hot Lead Example

```json
{
  "Booking_Number": "2025-001234",
  "Full_Name": "SMITH, JOHN MICHAEL",
  "First_Name": "JOHN",
  "Last_Name": "SMITH",
  "DOB": "1985-06-15",
  "Sex": "M",
  "Race": "White",
  "Arrest_Date": "2025-11-24",
  "Arrest_Time": "14:30:00",
  "Booking_Date": "2025-11-24",
  "Booking_Time": "16:45:00",
  "Agency": "Lee County Sheriff's Office",
  "Address": "123 Main St",
  "City": "Fort Myers",
  "State": "FL",
  "Zipcode": "33901",
  "Charges": "DUI with Property Damage",
  "Charge_1": "DUI",
  "Charge_1_Statute": "316.193",
  "Charge_1_Bond": "$5,000",
  "Charge_2": "Property Damage",
  "Charge_2_Statute": "806.13",
  "Charge_2_Bond": "$5,000",
  "Bond_Amount": "$10,000",
  "Bond_Type": "SURETY",
  "Status": "IN CUSTODY",
  "Court_Date": "2025-12-15",
  "Case_Number": "2025-CF-001234",
  "Mugshot_URL": "https://example.com/mugshots/2025-001234.jpg",
  "County": "Lee",
  "Court_Location": "Lee County Courthouse",
  "Lead_Score": 90,
  "Lead_Status": "Hot"
}
```

### Disqualified Lead Example

```json
{
  "Booking_Number": "2025-001238",
  "Full_Name": "MARTINEZ, CARLOS",
  "First_Name": "CARLOS",
  "Last_Name": "MARTINEZ",
  "DOB": "1990-03-15",
  "Sex": "M",
  "Race": "Hispanic",
  "Arrest_Date": "2025-11-23",
  "Arrest_Time": "",
  "Booking_Date": "2025-11-23",
  "Booking_Time": "",
  "Agency": "Lee County Sheriff's Office",
  "Address": "",
  "City": "Fort Myers",
  "State": "FL",
  "Zipcode": "",
  "Charges": "First Degree Murder",
  "Charge_1": "First Degree Murder",
  "Charge_1_Statute": "782.04",
  "Charge_1_Bond": "$0",
  "Charge_2": "",
  "Charge_2_Statute": "",
  "Charge_2_Bond": "",
  "Bond_Amount": "$0",
  "Bond_Type": "NO BOND",
  "Status": "IN CUSTODY",
  "Court_Date": "2025-12-20",
  "Case_Number": "2025-CF-001238",
  "Mugshot_URL": "https://example.com/mugshots/2025-001238.jpg",
  "County": "Lee",
  "Court_Location": "Lee County Courthouse",
  "Lead_Score": -165,
  "Lead_Status": "Disqualified"
}
```

**Scoring Breakdown for Disqualified Example:**
- Bond amount: $0 (-50)
- Bond type: NO BOND (-50)
- Status: IN CUSTODY (+20)
- Data completeness: Missing data (-10)
- Disqualifying charge: murder (-100)
- **Total: -165 → Disqualified**

---

## Google Sheets Integration

### County Tabs

Each county tab (Lee, Collier, Hendry, Charlotte, Manatee, Sarasota, DeSoto) uses the full 34-column schema:

- Header row is automatically created if missing
- All new records include Lead_Score and Lead_Status
- Records are deduplicated based on County:Booking_Number

### Qualified_Arrests Sheet

The Qualified_Arrests sheet:

- Uses the same 34-column schema
- Only includes records where Lead_Score >= 70
- Automatically populated when records are written to county tabs
- Deduplicated to prevent duplicates

### Logs Sheet

Tracks all ingestion runs with:

- Timestamp
- County
- Total_Records
- New_Records
- Duplicates_Skipped
- Qualified_Records
- Status (SUCCESS/ERROR)
- Error message (if any)

---

## Usage Examples

### Example 1: Score a Single Record

```python
from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import LeadScorer

record = ArrestRecord(
    Booking_Number="2025-001234",
    Full_Name="DOE, JOHN",
    Bond_Amount="$5,000",
    Bond_Type="SURETY",
    Status="IN CUSTODY",
    Charges="Battery",
    Court_Date="2025-12-01",
    County="Lee"
)

scorer = LeadScorer()
score, status = scorer.score_arrest(record)

print(f"Score: {score}, Status: {status}")
print("Breakdown:", scorer.get_score_breakdown())
```

### Example 2: Batch Score and Write to Sheets

```python
from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.writers.sheets_writer import SheetsWriter

# Create records (from scraper)
records = [
    ArrestRecord(...),
    ArrestRecord(...),
    # ... more records
]

# Write to sheets (auto-scores)
writer = SheetsWriter(
    spreadsheet_id="121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E",
    credentials_path="./creds/service-account-key.json"
)

stats = writer.write_records(records, county="Lee", auto_score=True)

# Log the results
writer.log_ingestion("Lee", stats)

print(f"Wrote {stats['new_records']} new records")
print(f"Qualified leads: {stats['qualified_records']}")
```

### Example 3: Run the Example Script

```bash
cd /home/ubuntu/swfl-arrest-scrapers
python3 python_scrapers/examples/scoring_example.py
```

This will demonstrate 7 different scoring scenarios with detailed breakdowns.

---

## Configuration

### Environment Variables

```bash
# Google Sheets Configuration
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./creds/service-account-key.json
GOOGLE_ACCOUNT=admin@shamrockbailbonds.biz

# Scoring Configuration
QUALIFIED_ARRESTS_MIN_SCORE=70  # Default threshold for qualified leads
```

### Python Dependencies

```txt
gspread>=5.0.0
google-auth>=2.0.0
google-auth-oauthlib>=0.5.0
google-auth-httplib2>=0.1.0
```

Install with:
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

## Testing

### Unit Tests

```python
import unittest
from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import LeadScorer

class TestLeadScoring(unittest.TestCase):
    def test_hot_lead(self):
        record = ArrestRecord(
            Bond_Amount="$10,000",
            Bond_Type="SURETY",
            Status="IN CUSTODY",
            Full_Name="TEST",
            Charges="DUI",
            Court_Date="2025-12-01"
        )
        scorer = LeadScorer()
        score, status = scorer.score_arrest(record)
        self.assertEqual(status, "Hot")
        self.assertGreaterEqual(score, 70)
    
    def test_disqualified_murder(self):
        record = ArrestRecord(
            Bond_Amount="$0",
            Bond_Type="NO BOND",
            Charges="First Degree Murder"
        )
        scorer = LeadScorer()
        score, status = scorer.score_arrest(record)
        self.assertEqual(status, "Disqualified")
        self.assertLess(score, 0)
```

---

## Migration Notes

### From 32-Column to 34-Column Schema

1. **Existing Data:** Old records in sheets will not have Lead_Score and Lead_Status
2. **Header Update:** The writer automatically updates headers to 34 columns
3. **Backward Compatibility:** Old 32-column data remains valid
4. **Rescoring:** Existing records can be rescored by reading, scoring, and rewriting

### Apps Script Integration

The Python scoring logic mirrors the original `LeadScoring.js` implementation. Both can coexist:

- **Python:** Used for scrapers and batch processing
- **Apps Script:** Used for manual triggers and UI interactions

---

## Support

For questions or issues:

- **GitHub:** https://github.com/Shamrock2245/swfl-arrest-scrapers
- **Google Sheet:** https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
- **Apps Script:** https://script.google.com/u/0/home/projects/12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo/edit

---

**End of Specification**
