# Unified Data Schema (34 Columns)

> Authoritative structure for ingestion, staging (Form.html), and SignNow merge.

**Required minimum**: `booking_id`, `full_name_last_first`, `arrest_date`, `booking_date`, `source_url`, `county`

| Column | Type | Notes |
|---|---|---|
| booking_id | string | County booking # (stable) |
| full_name_last_first | string | "Last, First Middle" |
| first_name | string | Parsed; optional |
| last_name | string | Parsed; optional |
| dob | string (YYYY-MM-DD) | Optional |
| sex | string | "M" / "F" / "" |
| race | string | Optional |
| arrest_date | string (YYYY-MM-DD) | Required |
| arrest_time | string | Optional HH:mm:ss |
| booking_date | string (YYYY-MM-DD) | Required |
| booking_time | string | Optional HH:mm:ss |
| agency | string | Arresting agency |
| address | string | Street |
| city | string | City |
| state | string | 2-letter (default FL) |
| zipcode | string | Optional |
| charges_raw | string | Original text blob |
| charge_1 | string | Primary charge |
| charge_1_statute | string | Statute |
| charge_1_bond | number/string | Currency parse |
| charge_2 | string | Secondary charge |
| charge_2_statute | string | Statute |
| charge_2_bond | number/string | Currency parse |
| total_bond | number | Sum of bonds |
| bond_paid | boolean/string | true/false/"" |
| court_date | string (YYYY-MM-DD) | Optional |
| case_number | string | Optional |
| mugshot_url | string | Optional |
| mugshot_image | string (formula) | `=IMAGE(url)` |
| source_url | string | County detail/list URL |
| county | string | `COLLIER`, `CHARLOTTE`, etc. |
| ingested_at_iso | string | ISO timestamp |
| qualified_score | number (0-100) | Computed |
| is_qualified | boolean | score ≥ 70 |
| extra_fields_json | string | JSON dump of leftovers |

## Qualification Scoring (Default)
- Bond ≥ 500 → +30  
- Bond ≥ 1500 → +20  
- Serious charge (battery, DUI, theft, fraud, etc.) → +20  
- Recency (≤ 2 days) → +20; (≤ 1 day) → +10  
**Qualified if ≥ 70.**  
_Tune in `config/schema.json` → `qualificationRules`._
