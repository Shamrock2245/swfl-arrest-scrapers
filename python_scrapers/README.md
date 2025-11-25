# Python Scrapers - Lead Scoring System

Python implementation of the SWFL Arrest Scrapers lead scoring system with integrated Google Sheets support.

## Overview

This module extends the original 32-column universal schema with integrated lead scoring, adding `Lead_Score` and `Lead_Status` fields to create a complete 34-column schema.

## Features

- ✅ **34-Column Universal Schema** - Extended ArrestRecord model
- ✅ **Automated Lead Scoring** - Python port of LeadScoring.js logic
- ✅ **Google Sheets Integration** - Direct write to county tabs and Qualified_Arrests
- ✅ **Deduplication** - Based on County:Booking_Number
- ✅ **Batch Processing** - Efficient bulk operations
- ✅ **Comprehensive Logging** - Ingestion tracking and error handling

## Installation

### 1. Install Dependencies

```bash
cd python_scrapers
pip install -r requirements.txt
```

### 2. Configure Credentials

Set up your Google Service Account credentials:

```bash
# Create credentials directory
mkdir -p ../creds

# Place your service account key JSON file
cp /path/to/service-account-key.json ../creds/

# Set environment variable
export GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./creds/service-account-key.json
export GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
```

## Quick Start

### Score a Single Record

```python
from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import score_and_update

# Create a record
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

# Score it
record = score_and_update(record)

print(f"Score: {record.Lead_Score}")  # 90
print(f"Status: {record.Lead_Status}")  # Hot
```

### Write Records to Google Sheets

```python
from python_scrapers.writers.sheets_writer import SheetsWriter

# Initialize writer
writer = SheetsWriter(
    spreadsheet_id="121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E",
    credentials_path="./creds/service-account-key.json"
)

# Write records (auto-scores if needed)
stats = writer.write_records(records, county="Lee")

print(f"New records: {stats['new_records']}")
print(f"Qualified: {stats['qualified_records']}")
```

### Run Examples

```bash
python examples/scoring_example.py
```

## Module Structure

```
python_scrapers/
├── models/
│   ├── __init__.py
│   └── arrest_record.py      # 34-column ArrestRecord model
├── scoring/
│   ├── __init__.py
│   └── lead_scorer.py         # Lead scoring logic
├── writers/
│   ├── __init__.py
│   └── sheets_writer.py       # Google Sheets integration
├── examples/
│   ├── __init__.py
│   └── scoring_example.py     # Example usage
├── utils/
│   └── __init__.py
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── LEAD_SCORING_SPEC.md      # Complete specification
```

## Schema

### 34-Column Header Order

```
Booking_Number, Full_Name, First_Name, Last_Name, DOB, Sex, Race,
Arrest_Date, Arrest_Time, Booking_Date, Booking_Time, Agency,
Address, City, State, Zipcode, Charges, Charge_1, Charge_1_Statute,
Charge_1_Bond, Charge_2, Charge_2_Statute, Charge_2_Bond, Bond_Amount,
Bond_Type, Status, Court_Date, Case_Number, Mugshot_URL, County,
Court_Location, Lead_Score, Lead_Status
```

### New Fields (33-34)

- **Lead_Score** (Number) - Calculated qualification score
- **Lead_Status** (String) - "Hot", "Warm", "Cold", or "Disqualified"

## Scoring Rules

### Bond Amount
- $500 - $50,000 → +30 points
- $50,001 - $100,000 → +20 points
- > $100,000 → +10 points
- $1 - $499 → -10 points
- $0 → -50 points

### Bond Type
- CASH or SURETY → +25 points
- NO BOND or HOLD → -50 points
- ROR → -30 points

### Status
- IN CUSTODY → +20 points
- RELEASED → -30 points

### Data Completeness
- All required fields present → +15 points
- Missing data → -10 points

### Disqualifying Charges
- Contains "capital", "murder", or "federal" → -100 points

### Lead Status Mapping
- Score < 0 → Disqualified
- Score >= 70 → Hot
- Score >= 40 → Warm
- Otherwise → Cold

## API Reference

### ArrestRecord

```python
from python_scrapers.models.arrest_record import ArrestRecord

# Create a record
record = ArrestRecord(
    Booking_Number="2025-001234",
    Full_Name="DOE, JOHN",
    # ... other fields
)

# Get header row (class method)
headers = ArrestRecord.get_header_row()  # Returns list of 34 column names

# Convert to sheet row
row = record.to_sheet_row()  # Returns list of 34 values

# Convert to dict
data = record.to_dict()

# Convert to JSON
json_str = record.to_json(indent=2)

# Check if qualified
is_qualified = record.is_qualified(min_score=70)

# Get dedup key
key = record.get_dedup_key()  # Returns "County:Booking_Number"
```

### LeadScorer

```python
from python_scrapers.scoring.lead_scorer import LeadScorer

scorer = LeadScorer()

# Score a record
score, status = scorer.score_arrest(record)

# Get detailed breakdown
breakdown = scorer.get_score_breakdown()
for reason in breakdown:
    print(reason)

# Score and update in place
record = scorer.score_and_update(record)
```

### SheetsWriter

```python
from python_scrapers.writers.sheets_writer import SheetsWriter

writer = SheetsWriter(
    spreadsheet_id="121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E",
    credentials_path="./creds/service-account-key.json",
    qualified_min_score=70  # Default
)

# Write records to county sheet
stats = writer.write_records(
    records=records,
    county="Lee",
    auto_score=True,      # Auto-score if not already scored
    deduplicate=True      # Skip duplicates
)

# Log ingestion
writer.log_ingestion("Lee", stats)

# Get qualified records
qualified = writer.get_qualified_records(limit=100)

# Clear a sheet
writer.clear_sheet("Lee", keep_header=True)
```

## Environment Variables

```bash
# Required
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./creds/service-account-key.json

# Optional
QUALIFIED_ARRESTS_MIN_SCORE=70  # Default threshold
```

## Google Sheets Structure

### County Tabs
- Lee
- Collier
- Hendry
- Charlotte
- Manatee
- Sarasota
- DeSoto

Each uses the full 34-column schema with automatic header creation.

### Qualified_Arrests Sheet
- Same 34-column schema
- Only records with Lead_Score >= 70
- Automatically populated
- Deduplicated

### Logs Sheet
Tracks ingestion runs:
- Timestamp
- County
- Total_Records
- New_Records
- Duplicates_Skipped
- Qualified_Records
- Status
- Error

## Testing

Run the example script to see scoring in action:

```bash
python examples/scoring_example.py
```

This demonstrates 7 different scenarios:
1. Hot Lead (high bond, in custody, complete data)
2. Warm Lead (medium bond, cash bond)
3. Cold Lead (low bond, released, incomplete)
4. Disqualified (ROR bond)
5. Disqualified (murder charge)
6. Hot Lead (high bond, surety)
7. Warm Lead (very high bond)

## Integration with Node.js Scrapers

The Python module is designed to work alongside the existing Node.js scrapers:

1. **Node.js scrapers** collect raw data
2. **Python module** normalizes, scores, and writes to Sheets
3. **Apps Script** provides UI and manual triggers

All three components work in harmony using the same 34-column schema.

## Documentation

See [LEAD_SCORING_SPEC.md](./LEAD_SCORING_SPEC.md) for the complete specification including:
- Detailed scoring rules
- Example JSON outputs
- Migration notes
- Testing guidelines

## Support

- **GitHub:** https://github.com/Shamrock2245/swfl-arrest-scrapers
- **Google Sheet:** https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
- **Account:** admin@shamrockbailbonds.biz

---

**Version:** 2.0  
**Last Updated:** November 24, 2025
