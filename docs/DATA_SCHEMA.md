# 📋 DATA_SCHEMA — Universal 34-Column Arrest Record

> **Every record across all 67 counties conforms to this structure.**

---

## The 34-Column Universal Schema

| # | Column | Type | Required | Format / Constraints | Example |
|---|---|---|---|---|---|
| 1 | `Scrape_Timestamp` | String | ✅ | ISO 8601: `YYYY-MM-DDTHH:MM:SSZ` | `2026-04-16T14:30:00Z` |
| 2 | `County` | String | ✅ **PK** | UPPERCASE county name | `LEE` |
| 3 | `Booking_Number` | String | ✅ **PK** | Unique per county. Alphanumeric. | `2026-00142857` |
| 4 | `Person_ID` | String | ⚪ | System-assigned person ID | `P-987654` |
| 5 | `Full_Name` | String | ✅ | `LAST, FIRST MIDDLE` (UPPERCASE) | `SMITH, JOHN MICHAEL` |
| 6 | `First_Name` | String | ✅ | Parsed from Full_Name | `JOHN` |
| 7 | `Middle_Name` | String | ⚪ | Parsed from Full_Name | `MICHAEL` |
| 8 | `Last_Name` | String | ✅ | Parsed from Full_Name | `SMITH` |
| 9 | `DOB` | Date | ⚪ | `MM/DD/YYYY` | `05/15/1985` |
| 10 | `Booking_Date` | String | ⚪ | `MM/DD/YYYY` | `04/16/2026` |
| 11 | `Booking_Time` | String | ⚪ | `HH:MM` (24hr) | `15:45` |
| 12 | `Status` | String | ⚪ | `In Custody`, `Released`, `Bonded Out` | `In Custody` |
| 13 | `Facility` | String | ⚪ | Detention facility name | `Lee County Jail` |
| 14 | `Race` | String | ⚪ | `W`, `B`, `H`, `A`, `I`, `U` | `W` |
| 15 | `Sex` | String | ⚪ | `M`, `F`, `U` | `M` |
| 16 | `Height` | String | ⚪ | Feet and inches | `5'11"` |
| 17 | `Weight` | String | ⚪ | Pounds | `185` |
| 18 | `Address` | String | ⚪ | Street address | `1528 Broadway` |
| 19 | `City` | String | ⚪ | City name | `Fort Myers` |
| 20 | `State` | String | ⚪ | 2-letter code (default: `FL`) | `FL` |
| 21 | `ZIP` | String | ⚪ | 5 or 9 digit | `33901` |
| 22 | `Mugshot_URL` | URL | ⚪ | Direct link to source image | `https://...jpg` |
| 23 | `Charges` | String | ✅ | Pipe-separated `\|` list | `DUI\|RECKLESS DRIVING` |
| 24 | `Bond_Amount` | Number | ⚪ | Numeric only. No `$`, no commas. | `5000` |
| 25 | `Bond_Paid` | String | ⚪ | `Yes`, `No`, or empty | `No` |
| 26 | `Bond_Type` | String | ⚪ | `Cash`, `Surety`, `ROR`, `No Bond` | `Surety` |
| 27 | `Court_Type` | String | ⚪ | Type of court proceeding | `Criminal` |
| 28 | `Case_Number` | String | ⚪ | Court case ID | `26-CF-001234` |
| 29 | `Court_Date` | Date | ⚪ | `MM/DD/YYYY` | `05/15/2026` |
| 30 | `Court_Time` | String | ⚪ | `HH:MM` (24hr) | `09:00` |
| 31 | `Court_Location` | String | ⚪ | Courthouse name | `Lee County Justice Center` |
| 32 | `Detail_URL` | URL | ⚪ | Link to county detail page | `https://...` |
| 33 | `Lead_Score` | Number | ✅ | 0–100, calculated by scorer | `85` |
| 34 | `Lead_Status` | String | ✅ | `Hot`, `Warm`, `Cold`, `Disqualified` | `Hot` |

### Composite Primary Key
```
UNIQUE KEY = County + Booking_Number
```
This key is used for deduplication across ALL storage systems (Sheets, MongoDB, Slack).

---

## Field Validation Rules

### Required Fields (Must Never Be Empty)
| Field | Fallback if Missing |
|---|---|
| `Booking_Number` | **Skip entire record** — cannot ingest without a key |
| `Full_Name` | **Skip entire record** — cannot identify defendant |
| `County` | Hardcoded by the scraper (never from source data) |
| `Scrape_Timestamp` | Auto-generated at scrape time |
| `Lead_Score` | Default to `0` if scorer fails |
| `Lead_Status` | Default to `Cold` if scorer fails |
| `Charges` | Set to `UNKNOWN` — still ingest the record |

### Standardization Rules
| Field | Rule |
|---|---|
| `Full_Name` | `UPPERCASE`. Format: `LAST, FIRST MIDDLE` |
| `DOB` | Always `MM/DD/YYYY`. Parse from any source format. |
| `Sex` | Normalize: `Male`→`M`, `Female`→`F`, else→`U` |
| `Race` | Normalize: `White`→`W`, `Black`→`B`, `Hispanic`→`H`, `Asian`→`A`, else→`U` |
| `Bond_Amount` | Strip `$`, commas, spaces. Parse to integer. `No Bond`→`0`. |
| `Charges` | Pipe-separate multiple charges: `CHARGE_1\|CHARGE_2\|CHARGE_3` |
| `County` | UPPERCASE: `LEE`, `PALM_BEACH`, `ST_LUCIE` |
| `Scrape_Timestamp` | ISO 8601: `2026-04-16T14:30:00Z` |

---

## County-Specific Extensions

The 34-column schema is a **floor**, not a ceiling. Counties may provide additional data.

```
Base Columns (1-34):  Universal across all counties
Extended Columns (35+):  County-specific bonus fields
```

**Rule:** If a county provides it, we capture it. Append new columns to the right of the sheet. Never discard data.

---

## Data Lifecycle

```
County Website → Scrape → Normalize (34-col) → Score (0-100) → Dedup
    → Google Sheets (county tab, insert at row 2)
    → MongoDB Atlas (bulk upsert)
    → Qualified_Arrests tab (if Score ≥ 70)
    → Slack alert (#new-arrests-{county})
    → Ingestion_Log (run metadata)
```

### Retention Policy
| Data | Location | Retention |
|---|---|---|
| Arrest records | County sheet tabs | **Indefinite** — never delete |
| Qualified leads | `Qualified_Arrests` tab | **Indefinite** |
| Ingestion logs | `Ingestion_Log` tab | 90 days → archive to `Log_Archive` |
| MongoDB records | Atlas cluster | **Indefinite** |
| HTML fixtures | `counties/*/fixtures/` | 30 days — CI prunes |

---

## Ingestion Log Schema

Every scraper run appends a row to `Ingestion_Log`:

| Column | Type | Example |
|---|---|---|
| `Timestamp` | ISO 8601 | `2026-04-16T14:30:00Z` |
| `County` | String | `CHARLOTTE` |
| `Records_Found` | Number | `47` |
| `Records_Inserted` | Number | `3` |
| `Records_Updated` | Number | `1` |
| `Records_Skipped` | Number | `43` |
| `Errors` | Number | `0` |
| `Duration_Seconds` | Number | `28` |
| `Engine` | String | `python/drissionpage` |
| `Status` | String | `SUCCESS` or error code |

---

## Source of Truth
- **Schema definition**: `config/schema.json`
- **Field aliases**: `config/field_aliases.json`
- **Sheets header**: `core/writers/sheets_writer.py` → `HEADER_ROW`
