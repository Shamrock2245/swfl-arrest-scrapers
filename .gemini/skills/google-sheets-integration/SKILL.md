---
name: google-sheets-integration
description: Use when working with Google Sheets data output — writing arrest records, managing tabs, handling schema, debugging API errors.
source: Adapted from googleworkspace/cli GWS skills
---

# Google Sheets Integration

## Overview

Google Sheets is our primary arrest data store. Each county gets its own tab.
The `core/writers/sheets_writer.py` module handles all writes using the
Google Sheets API v4 via a service account.

## Architecture

```
Solver → returns List[dict] → Runner → SheetsWriter.append_rows()
                                    → Google Sheets API v4
                                    → Sheet: "121z5R...IV_0E"
                                    → Tab: "{County}" (auto-created)
```

## The 39-Column Schema

Our standard HEADER_ROW (defined in `sheets_writer.py`):

```python
HEADER_ROW = [
    'Booking_Number', 'County', 'State', 'Facility',
    'Full_Name', 'First_Name', 'Last_Name', 'Middle_Name',
    'DOB', 'Sex', 'Race', 'Height', 'Weight',
    'Hair_Color', 'Eye_Color',
    'Address', 'City', 'Zipcode',
    'Booking_Date', 'Release_Date', 'Status',
    'Charges', 'Bond_Amount', 'Bond_Type', 'Bond_Status',
    'Agency', 'Case_Number',
    'Court_Date', 'Court_Type', 'Court_Location',
    'Mugshot_URL', 'Detail_URL', 'Scrape_Timestamp',
    'Person_ID', 'Notes', 'Phone', 'Email',
    'Emergency_Contact', 'Occupation'
]
```

## Writing Records

### Deduplication
Every write checks for existing `Booking_Number` + `County` combination:
```python
# The writer handles dedup internally
writer = SheetsWriter(sheet_id, service_account_path)
new_count = writer.append_rows(county_tab, records)
# new_count = number of genuinely new records appended
```

### Record Format
Solvers return dicts — the writer maps them to columns:
```python
record = {
    'Booking_Number': '2026-04140123',
    'County': 'Collier',
    'State': 'FL',
    'Full_Name': 'SMITH, JOHN A',
    'First_Name': 'JOHN',
    'Last_Name': 'SMITH',
    'DOB': '01/15/1990',
    'Charges': 'Battery | Disorderly Conduct',
    'Bond_Amount': '5000.00',
    'Booking_Date': '04/14/2026',
    'Scrape_Timestamp': '2026-04-14 15:30:00',
}
# Missing fields default to empty string
```

## Service Account Setup

1. Service account key stored as GitHub Secret: `GOOGLE_SERVICE_ACCOUNT_KEY`
2. At runtime, decoded to `creds/service-account-key.json`
3. The sheet must be shared with the service account email

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `HttpError 403: insufficient permissions` | Sheet not shared with SA | Share sheet with SA email |
| `HttpError 429: Rate limit exceeded` | Too many API calls | Add retry with exponential backoff |
| Tab not found | County tab doesn't exist yet | Writer auto-creates tabs |
| Wrong column count | Schema mismatch | Verify HEADER_ROW matches |
| Duplicate records | Dedup check failed | Verify Booking_Number is populated |

## Best Practices

1. **Always populate `Booking_Number`** — it's the dedup key
2. **Always populate `County`** — second part of dedup key  
3. **Use ISO-ish dates** — `MM/DD/YYYY` or `YYYY-MM-DD` (both work)
4. **Pipe-delimit charges** — `Charge 1 | Charge 2 | Charge 3`
5. **Bond as string** — `"5000.00"` not `5000.00` (avoids float issues)
6. **Scrape_Timestamp always** — `datetime.now().strftime('%Y-%m-%d %H:%M:%S')`
