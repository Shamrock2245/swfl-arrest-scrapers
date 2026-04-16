# 🔄 QUEUE — Pipeline Stages

> **Every arrest record flows through 8 stages from website to actionable lead.**

---

## Pipeline Overview

```
  Stage 1      Stage 2        Stage 3     Stage 4          Stage 5
  SCRAPE  →  NORMALIZE  →    SCORE   →  COMPLIANCE  →     DEDUP
(solver.py)  (normalizer)    (scorer)     (gate)          (writer)
                                           │
                               ┌───────────┘
                               ▼
                         REVIEW_HOLD (if flagged)
                               │
                               ▼
                    Stage 6        Stage 7       Stage 8
                    STORE     →    NOTIFY    →   CLOSE
                 (sheets/mongo)    (slack)     (lifecycle)
```

---

## Stage 1: SCRAPE

**Owner**: `counties/{name}/solver.py`
**Input**: County jail website URL
**Output**: `list[dict]` of raw arrest records

```python
def scrape_charlotte(days_back=7, max_pages=10) -> list[dict]:
    # Navigate to county site
    # Bypass anti-bot (Cloudflare, disclaimers)
    # Extract all booking records
    # Return list of raw dicts
    return records  # Never None, never raise. Return [] on failure.
```

**Success criteria**: Returns non-empty list of dicts with at least `Booking_Number` and `Full_Name`
**Failure mode**: Returns `[]`, logs error to stderr

---

## Stage 2: NORMALIZE

**Owner**: `core/normalizer.py` + `config/field_aliases.json`
**Input**: Raw dict from solver
**Output**: 34-column standardized dict

Steps:
1. Map raw field names → schema column names (via `field_aliases.json`)
2. Standardize values (dates, names, bonds, races, sex)
3. Apply defaults (`State` → `FL`, `County` → hardcoded)
4. Validate required fields (`Booking_Number`, `Full_Name`, `County`)
5. Skip records missing required fields

**Success criteria**: Every output dict has exactly the 34 schema columns
**Failure mode**: Skip the individual record, continue pipeline

---

## Stage 3: SCORE

**Owner**: `python_scrapers/scoring/lead_scorer.py`
**Input**: Normalized 34-column dict
**Output**: Same dict with `Lead_Score` (0-100) and `Lead_Status` (Hot/Warm/Cold/Disqualified)

Scoring factors (see `SCORING.md` for full rubric):
- Bond amount in sweet spot → +30 pts
- In custody → +20 pts
- Bondable charge type → +20 pts
- Cash/surety bond → +25 pts
- Data completeness → +15 pts
- Released → -30 pts
- No bond → -50 pts
- Capital charge → -100 pts

**Success criteria**: Every record has a numeric `Lead_Score` and valid `Lead_Status`
**Failure mode**: Default to `Lead_Score: 0`, `Lead_Status: Cold`

---

## Stage 4: COMPLIANCE GATE

**Owner**: Pipeline (inline checks)
**Input**: Scored 34-column dict
**Output**: `PASS`, `SUPPRESS`, or `REVIEW_HOLD`

Automatic checks before any storage or contact:

| Check | Action if Failed |
|-------|------------------|
| Minor (DOB → age < 18) | `SUPPRESS` — do not store or contact |
| Capital offense | `SUPPRESS` — mark `Lead_Status: Disqualified`, store for analytics only |
| Federal/ICE charge | `SUPPRESS` — different jurisdiction, cannot bond |
| Suppression list match | `SUPPRESS` — individual previously opted out |
| Incomplete required fields | `REVIEW_HOLD` — flag for human review |
| Anomalous data (future dates, negative bonds) | `REVIEW_HOLD` — possible parser error |

**`REVIEW_HOLD` records** are stored with `compliance_status: review_required` and do NOT trigger outreach until a human clears them.

**Success criteria**: Zero suppressed records reach outreach pipeline
**Failure mode**: If compliance check errors, default to `REVIEW_HOLD` (safer than passing through)

---

## Stage 5: DEDUP

**Owner**: `core/writers/sheets_writer.py` (dedup logic)
**Input**: Compliance-cleared 34-column dict
**Output**: Decision: INSERT, UPDATE, or SKIP

```
Dedup Key: County + Booking_Number

IF key not found in existing data → INSERT (new record)
IF key found AND data changed      → UPDATE (refresh record)
IF key found AND data unchanged    → SKIP (no action)
```

**Check order**:
1. Check Google Sheets (county tab) for existing `Booking_Number`
2. Check MongoDB (if enabled) for existing key
3. Make insert/update/skip decision

**Success criteria**: Zero duplicate rows created
**Failure mode**: If dedup check fails, default to SKIP (safer than duplicating)

---

## Stage 6: STORE

**Owner**: `core/writers/sheets_writer.py` + `core/writers/mongo_writer.py`
**Input**: Dedup decision + scored record
**Output**: Written to storage

### Google Sheets (Primary — MUST succeed)
- Insert at **row 2** (header stays at row 1, newest on top)
- Tab name matches county config (`config/counties/{name}.yaml` → `sheet_tab`)
- If `Lead_Score ≥ 70` → also mirror to `Qualified_Arrests` tab

### MongoDB Atlas (Secondary — NON-FATAL)
- Bulk upsert with `{Booking_Number, County}` as key
- Failure does NOT crash the pipeline
- Logs warning to stderr on failure

### Ingestion Log (Metadata)
- Append run summary to `Ingestion_Log` tab
- Records: found, inserted, updated, skipped, errors, duration

**Success criteria**: Record appears in Google Sheets with correct data
**Failure mode**: Sheets failure = critical error. MongoDB failure = log and continue.

---

## Stage 7: NOTIFY

**Owner**: `core/writers/slack_notifier.py`
**Input**: Newly inserted/updated records
**Output**: Slack messages

### Alert routing:
| Condition | Channel | Alert Level |
|---|---|---|
| Any new record | `#new-arrests-{county}` | INFO |
| `Lead_Score ≥ 70` | `#leads` | HIGH (`@channel`) |
| Scraper error | `#scraper-alerts` | ERROR |
| Run complete | `#drive` | INFO (summary) |
| `REVIEW_HOLD` flagged | `#scraper-alerts` | WARN |

**Success criteria**: Slack messages delivered within 60 seconds of record storage
**Failure mode**: Non-fatal. Log warning and continue. Bad Slack should never crash a scraper.

---

## Stage 8: CLOSE (Lifecycle)

**Owner**: GAS backend (`shamrock-bail-portal-site`)
**Input**: Stored record lifecycle events
**Output**: Status transitions

Records move through these terminal states downstream:

| Status | Meaning | Trigger |
|---|---|---|
| `exported` | Sent to outreach queue (The Closer / Concierge) | `Lead_Score ≥ 50` + compliance PASS |
| `contacted` | Outreach attempted | The Closer touches 1-4 |
| `converted` | Client signed paperwork | SignNow `document.complete` |
| `closed` | Bond posted or lead expired | Human action or 30-day timeout |
| `suppressed` | Opted out or compliance block | Opt-out reply or manual flag |

**Note**: Stage 8 lives outside this repo — it's documented here for pipeline completeness.

---

## Pipeline Guarantees

| Property | Guarantee |
|---|---|
| **Idempotent** | Running the same scraper twice produces no duplicates |
| **Partial failure safe** | One bad record doesn't crash the whole run |
| **Order independent** | Records can be processed in any order |
| **Non-fatal secondary stores** | MongoDB/Slack failures don't affect primary (Sheets) |
| **Auditable** | Every run logged in `Ingestion_Log` with counts and timing |
| **Compliance-gated** | No record reaches outreach without passing compliance checks |

---

## Pipeline Timing (Typical)

| Stage | Duration | Notes |
|---|---|---|
| Scrape | 10-120s | Depends on county site speed + anti-bot delays |
| Normalize | <1s | Pure in-memory transformation |
| Score | <1s | Pure computation |
| Compliance Gate | <1s | In-memory checks |
| Dedup | 2-5s | Sheets API read to check existing records |
| Store | 2-10s | Sheets API write (batch if >5 records) |
| Notify | 1-3s | Slack webhook POST |
| **Total** | 15-140s | Most time spent in scraping stage |
