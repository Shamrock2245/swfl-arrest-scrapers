# SWFL Bail Suite - Universal Schema (v3.0)

**Authoritative Data Structure for All County Arrest Scrapers**

All scrapers in the `swfl-arrest-scrapers` repository must conform to this schema. This structure is based on the proven Lee County scraper implementation.

---

## 📋 Core Principles

### 1. Fail-Quietly Behavior
- Scrapers MUST NOT crash when a field is unavailable
- Missing data → leave field **blank/empty**, do NOT use placeholders like "N/A" or "Unknown"
- Extract all available information; skip unavailable fields silently

### 2. Recency-Based Updates
- Scrapers should only check **recent bookings** (past few days) when run for updates
- Do NOT scan the entire historical dataset for status changes
- Focus on new bookings and recent custody status updates

### 3. Chronological Fallback Logic
At least **ONE** chronological field must be populated per record:
- **Priority 1:** `Booking_Date` and `Booking_Time`
- **Priority 2:** `Arrest_Date` and `Arrest_Time` (if Booking unavailable)
- **Priority 3:** `Scrape_Timestamp` (if neither Booking nor Arrest available)

This ensures every record has a temporal reference point for tracking.

### 4. Dynamic Charge Handling
- The `Charges` field contains a **pipe-separated list** (`|`) of all charges
- Additional charge detail columns can be added dynamically if needed
- If a county provides structured charge data, capture it in additional columns
- Minimum: capture the `Charges` field as a single concatenated string

---

## 🗂️ Column Definitions (36 Base Columns)

| # | Column | Type | Required | Notes |
|:---|:---|:---|:---|:---|
| 1 | `Scrape_Timestamp` | DateTime | **YES** | ISO 8601 format: `YYYY-MM-DD HH:MM:SS` |
| 2 | `County` | String | **YES** | Uppercase (e.g., LEE, COLLIER, CHARLOTTE) |
| 3 | `Booking_Number` | String | **YES** | Primary key (unique per county) |
| 4 | `Person_ID` | String | No | Internal identifier if available |
| 5 | `Full_Name` | String | **YES** | Preferred format: "LAST, FIRST MIDDLE" |
| 6 | `First_Name` | String | **YES** | Parsed from Full_Name |
| 7 | `Middle_Name` | String | No | Parsed from Full_Name if available |
| 8 | `Last_Name` | String | **YES** | Parsed from Full_Name |
| 9 | `DOB` | Date | No | Format: `YYYY-MM-DD` or `MM/DD/YYYY` |
| 10 | `Arrest_Date` | Date | No | Date of arrest (if available) |
| 11 | `Arrest_Time` | Time | No | Time of arrest (if available) |
| 12 | `Booking_Date` | Date | **Preferred** | Date admitted to facility |
| 13 | `Booking_Time` | Time | **Preferred** | Time admitted to facility |
| 14 | `Status` | String | **YES** | `In Custody`, `Released`, `Bonded Out`, etc. |
| 15 | `Facility` | String | No | Jail/facility name |
| 16 | `Agency` | String | No | Arresting agency (Sheriff, Police Dept, etc.) |
| 17 | `Race` | String | No | Standardized codes: W, B, H, A, etc. |
| 18 | `Sex` | String | No | M, F, U |
| 19 | `Height` | String | No | Format: `5'10"` or `510` |
| 20 | `Weight` | String | No | Numeric (pounds) |
| 21 | `Address` | String | No | Street address |
| 22 | `City` | String | No | City |
| 23 | `State` | String | No | 2-letter state code |
| 24 | `ZIP` | String | No | 5-digit ZIP code |
| 25 | `Mugshot_URL` | URL | No | Direct link to mugshot image |
| 26 | `Charges` | String | **YES** | Pipe-separated list: `CHARGE1 \| CHARGE2 \| CHARGE3` |
| 27 | `Bond_Amount` | Number | No | Numeric only (no `$` or commas) |
| 28 | `Bond_Paid` | String | No | YES, NO, PARTIAL |
| 29 | `Bond_Type` | String | No | CASH, SURETY, ROR, NO BOND |
| 30 | `Court_Type` | String | No | County Court, Circuit Court, etc. |
| 31 | `Case_Number` | String | No | Court case identifier |
| 32 | `Court_Date` | Date | No | Next scheduled court date |
| 33 | `Court_Time` | Time | No | Next scheduled court time |
| 34 | `Court_Location` | String | No | Courthouse name/address |
| 35 | `Detail_URL` | URL | **YES** | Direct link to booking detail page |
| 36 | `Lead_Score` | Number | No | Calculated score (0-100) |
| 37 | `Lead_Status` | String | No | HOT, WARM, COLD, DISQUALIFIED |
| 38 | `LastChecked` | DateTime | No | Last time this record was verified |
| 39 | `LastCheckedMode` | String | No | INITIAL, UPDATE, MANUAL |

---

## 🔧 Additional Charge Columns (Optional/Dynamic)

If a county provides structured charge details, add these columns **after** column 26 (`Charges`):

| Column | Type | Notes |
|:---|:---|:---|
| `Charge_1` | String | Primary charge description |
| `Charge_1_Statute` | String | Statute/code for Charge_1 |
| `Charge_1_Level` | String | Felony/Misdemeanor/etc. |
| `Charge_1_Degree` | String | 1st, 2nd, 3rd degree |
| `Charge_2` | String | Secondary charge description |
| `Charge_2_Statute` | String | Statute/code for Charge_2 |
| `Charge_2_Level` | String | Felony/Misdemeanor/etc. |
| `Charge_2_Degree` | String | 1st, 2nd, 3rd degree |
| ... | ... | Continue for Charge_3, Charge_4, etc. as needed |

**Note:** These are optional. The base `Charges` field (column 26) is mandatory and sufficient for most counties.

---

## 🎯 Lead Scoring (Authoritative)

The `Lead_Score` and `Lead_Status` fields are calculated post-scraping using the following rules:

### Positive Modifiers
- **Bond $500 - $50,000:** +30 points
- **Bond $50,001 - $100,000:** +20 points
- **Status "In Custody":** +20 points
- **Charge Keywords:** +20 points (Battery, DUI, Theft, Assault, etc.)
- **Data Completeness:** +15 points (all core fields populated)

### Negative Modifiers
- **Status "Released":** -30 points
- **Bond $0 / No Bond:** -50 points
- **Capital/Federal Charge:** -100 points (auto-disqualified)

### Lead Status Thresholds
- **HOT:** Score ≥ 70
- **WARM:** Score 40-69
- **COLD:** Score 10-39
- **DISQUALIFIED:** Score < 10 or capital charge

---

## 📝 Scraper Implementation Rules

### 1. Output Format
- All scrapers MUST output CSV files with this exact column order
- Use UTF-8 encoding
- Use comma (`,`) as delimiter
- Enclose fields containing commas or newlines in double quotes (`"`)

### 2. Data Extraction Priority
1. Extract `Booking_Number`, `Full_Name`, `County`, `Status`, `Charges`, `Detail_URL` (mandatory)
2. Extract `Booking_Date`/`Booking_Time` (strongly preferred)
3. Extract all other available fields
4. Leave unavailable fields **blank** (do not use "N/A", "Unknown", etc.)

### 3. Error Handling
- If a source is down: log error, return empty dataset
- If a field is missing: leave blank, continue scraping
- If a record is malformed: log warning, skip record, continue
- NEVER crash the entire scraper due to a single bad record

### 4. Update Mode Behavior
When running in update mode:
- Only scrape bookings from the **past 3-7 days** (county-dependent)
- Check for status changes on recent bookings
- Do NOT re-scrape the entire historical dataset
- Append new bookings to existing dataset

---

## 📚 Reference Implementation

**Lee County Scraper** (`scrapers/lee_county/lee_scraper.py`) is the gold standard.

All new scrapers should follow its structure:
- Fail-quietly on missing fields
- Extract all available data
- Output matches this schema exactly
- Handles updates efficiently (recent bookings only)

---

## 🔒 Schema Version Control

- **Version:** 3.0
- **Last Updated:** 2025-12-27
- **Authoritative Source:** `SCHEMA.md` in `swfl-arrest-scrapers` repository
- **Supersedes:** All previous schema versions (v2.1 and earlier)

---

**All scrapers MUST conform to this schema. No exceptions.**
