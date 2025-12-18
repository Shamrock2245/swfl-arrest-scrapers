# SWFL Bail Suite - Universal Schema (v2.1)

All data ingested into the Shamrock Bail Suite must conform to this 34-column structure.

## 📋 Column Map

| # | Column | Type | Notes |
| :--- | :--- | :--- | :--- |
| 1 | `Booking_Number` | String | **Primary Key** (Unique per County) |
| 2 | `Full_Name` | String | "Last, First Middle" |
| 3-4 | `First_Name` / `Last_Name` | String | Parsed components |
| 5 | `DOB` | Date | MM/DD/YYYY |
| 6-7 | `Sex` / `Race` | String | Standardized codes (M/F, W/B/H/etc.) |
| 8-9 | `Arrest_Date` / `Time` | String | Date/Time of custodial arrest |
| 10-11 | `Booking_Date` / `Time` | String | Date/Time admitted to facility |
| 12 | `Agency` | String | Arresting agency |
| 13-16 | `Address` Suite | String | Street, City, State, Zip |
| 17 | `Charges` | String | Pipe-separated `|` list of all charges |
| 18-23 | `Charge_1` & `Charge_2` | Mixed | Specifics for primary/secondary charges |
| 24 | `Bond_Amount` | Number | Numeric value (no symbols) |
| 25 | `Bond_Type` | String | Cash, Surety, ROR, No Bond |
| 26 | `Status` | String | In Custody, Released |
| 27 | `Court_Date` | Date | Upcoming hearing date |
| 28 | `Case_Number` | String | Court case identifier |
| 29 | `Mugshot_URL` | URL | Link to source image |
| 30 | `County` | String | **Primary Key** (LEE, COLLIER, etc.) |
| 31 | `Court_Location` | String | Courthouse name |
| 32 | `Detail_URL` | URL | Direct link to county detail page |
| 33 | `Lead_Score` | Number | Calculated (0-100) |
| 34 | `Lead_Status` | String | Hot, Warm, Cold, Disqualified |

---

## 🎯 Lead Scoring (Authoritative)

The `LeadScoringSystem.gs` (Apps Script) and `LeadScorer` (Python) use the following rules:

### Positive Modifiers
*   **Bond $500 - $50,000:** +30 points.
*   **Bond $50,001 - $100,000:** +20 points.
*   **Status "In Custody":** +20 points.
*   **Charge Keywords:** +20 points (e.g., Battery, DUI, Theft).
*   **Data Completeness:** +15 points.

### Negative Modifiers
*   **Status "Released":** -30 points.
*   **Bond $0 / No Bond:** -50 points.
*   **Capital/Federal Charge:** -100 points (Disqualified).

**THRESHOLD:** Score **≥ 70** is marked as **HOT** and triggers alerts.

---
*Reference: apps_script/LeadScoringSystem.gs*
