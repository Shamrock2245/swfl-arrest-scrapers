# 🔗 INTEGRATION — How Scrapers Feed the Shamrock Ecosystem

> **This repo is Station 1 of a 5-station pipeline. Here's how every arrest record flows downstream.**

---

## The Big Picture

```
THIS REPO                    DOWNSTREAM SYSTEMS
─────────                    ──────────────────

County Jail     ┌──────────────────────────────────────────────────────────────┐
  Website       │                                                              │
    │           │   Google Sheets                                              │
    ▼           │   ┌──────────────┐     ┌──────────────────┐                  │
 solver.py ────►│   │ County Tab   │────►│ GAS: LeadScoring │                  │
    │           │   │ (34-col row) │     │ System.js        │                  │
 runner.py      │   ├──────────────┤     └────────┬─────────┘                  │
    │           │   │ Qualified_   │              │                            │
    ├──────────►│   │ Arrests Tab  │              ▼                            │
    │           │   └──────────────┘     ┌──────────────────┐                  │
    │           │                        │ GAS: IntakeQueue  │                  │
    │           │   MongoDB Atlas        │ (Wix CMS sync)   │                  │
    ├──────────►│   ┌──────────────┐     └────────┬─────────┘                  │
    │           │   │ arrests      │              │                            │
    │           │   │ collection   │              ▼                            │
    │           │   └──────────────┘     ┌──────────────────┐  ┌────────────┐  │
    │           │                        │ The Closer        │─►│ Twilio SMS │  │
    │           │   Slack                │ (drip campaigns)  │  │ /WhatsApp  │  │
    └──────────►│   ┌──────────────┐     └──────────────────┘  └────────────┘  │
                │   │ #new-arrests │                                            │
                │   │ #leads       │     ┌──────────────────┐                  │
                │   │ #scraper-    │     │ Node-RED Bounty   │                  │
                │   │  alerts      │────►│ Board (dashboard) │                  │
                │   └──────────────┘     └──────────────────┘                  │
                │                                                              │
                └──────────────────────────────────────────────────────────────┘
```

---

## Downstream Consumers (Who Reads Our Data)

### 1. GAS — Lead Scoring & Intake Hydration
**Repo:** `shamrock-bail-portal-site/backend-gas/`
**Reads from:** `Qualified_Arrests` tab in Google Sheets
**What it does:**
- `LeadScoringSystem.js` re-scores qualified arrests against historical data
- Matched leads are pushed into `IntakeQueue` (Wix CMS collection)
- `DashboardHydration.js` pre-fills intake forms with arrest data

**How it works:**
```
Qualified_Arrests tab (our output)
    │
    ▼ (GAS reads via Sheets API, triggered by Node-RED cron)
LeadScoringSystem.js
    │
    ├── Score ≥ threshold → IntakeQueue (Wix CMS)
    │                        └── Available to all client surfaces:
    │                            Wix Portal, Telegram Bot, Shannon (voice)
    │
    └── Score < threshold → Archive (stays in Sheets for analytics)
```

**Contract:** Our `Qualified_Arrests` tab MUST have these fields for GAS to work:
| Field | Used By | Purpose |
|-------|---------|---------|
| `Full_Name` | DashboardHydration | Pre-fill defendant name |
| `Booking_Number` | Dedup against IntakeQueue | Prevent double-intake |
| `County` | DashboardHydration | Route to correct office/agent |
| `Bond_Amount` | LeadScoring | Calculate premium estimate |
| `Charges` | LeadScoring | Risk assessment |
| `Lead_Score` | LeadScoring | Compare with GAS-side scoring |
| `Mugshot_URL` | IntakeQueue | Display in staff dashboard |
| `Booking_Date` | LeadScoring | Recency factor |
| `Status` | LeadScoring | Skip if already released |

### 2. Node-RED — Bounty Board & Ops Dashboard
**Repo:** `shamrock-node-red/`
**Reads from:** GAS endpoints (which read our Sheets data)
**What it does:**
- Bounty Board page shows live high-value unposted bonds (>$2,500)
- Operations Radar shows latest arrest bookings across all counties
- 39+ cron jobs schedule scraper runs and data pipeline tasks

**GAS Endpoints consumed by Node-RED:**
| Endpoint | Method | Returns |
|----------|--------|---------|
| `fetchLatestArrests` | POST | Last 50 arrests across all counties |
| `fetchQualifiedRows` | POST | Current qualified leads |
| `scoreAndSyncQualifiedRows` | POST | Re-scored leads synced to CMS |
| `health` | GET | System health status |
| `fetchBountyBoard` | POST | Bonds >$2,500, unposted, in-custody |

**Node-RED Scheduling of our scrapers:**
Node-RED triggers scraper runs via `exec` nodes that call GitHub Actions API or local Docker scripts. The schedule in Node-RED should match our `.github/workflows/*.yml` cron schedules.

### 3. Slack — Alert Channels
**Reads from:** Direct webhook POST from `slack_notifier.py`
**Channels we write to:**

| Channel | Message Format | Trigger |
|---------|---------------|---------|
| `#new-arrests-{county}` | Embed with name, charges, bond, mugshot | Every new record inserted |
| `#leads` | `@channel` alert with lead details | `Lead_Score ≥ 70` |
| `#scraper-alerts` | Error details + county + error code | Scraper failure |
| `#drive` | Run summary (found/inserted/skipped/errors) | Successful run completion |

**Slack message payload format:**
```json
{
  "text": "🚨 Hot Lead — LEE COUNTY",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*SMITH, JOHN MICHAEL*\n📋 DUI | RECKLESS DRIVING\n💰 Bond: $5,000\n🏛️ Lee County Jail\n📊 Score: 85 (Hot)"
      },
      "accessory": {
        "type": "image",
        "image_url": "https://...",
        "alt_text": "Mugshot"
      }
    }
  ]
}
```

### 4. MongoDB Atlas — Analytics Store
**Reads from:** Direct write via `mongo_writer.py` (through Cloud Functions proxy)
**What it does:**
- Cross-county deduplication
- Historical trend analysis
- Arrest volume analytics

**Collection: `arrests`**
```json
{
  "_id": ObjectId(),
  "county": "LEE",
  "booking_number": "2026-00142857",
  "full_name": "SMITH, JOHN MICHAEL",
  "lead_score": 85,
  "lead_status": "Hot",
  "scrape_timestamp": ISODate("2026-04-16T14:30:00Z"),
  "meta": {
    "source": "swfl-arrest-scrapers",
    "engine": "python/drissionpage",
    "version": "1.0"
  }
}
```

**Upsert key:** `{ county, booking_number }`

### 5. The Closer — Drip Campaign Engine
**Repo:** `shamrock-bail-portal-site/backend-gas/TheCloser.js`
**Reads from:** IntakeQueue (via GAS, populated from our qualified leads)
**What it does:**
- 4-touch SMS/WhatsApp drip campaign for abandoned intakes
- Only contacts leads that passed through the full pipeline (scraper → scoring → intake)
- See `OUTREACH_RULES.md` for timing and content rules

**Currently:** ⏸️ Paused — blocked on 10DLC reapplication

---

## What This Repo Does NOT Control

| System | Owner | This Repo's Role |
|--------|-------|------------------|
| Wix Portal | `shamrock-bail-portal-site` | None — we feed data via Sheets → GAS → Wix CMS |
| Telegram Bot | `shamrock-bail-portal-site` | None — bot reads from IntakeQueue post-scoring |
| Shannon (Voice AI) | `shamrock-bail-portal-site` | None — voice agent reads from IntakeQueue |
| Node-RED Dashboard | `shamrock-node-red` | We provide raw data; Node-RED builds the UI |
| SignNow Packet | `shamrock-bail-portal-site` | None — triggered after successful intake |
| Court Reminders | `shamrock-bail-portal-site` | None — GAS handles SMS scheduling |
| Payment Processing | `shamrock-bail-portal-site` | None — SwipeSimple integration in GAS |

---

## Data Flow Summary

```
Stage 1: SCRAPE (this repo)
    └── County jail → solver.py → raw records

Stage 2: NORMALIZE + SCORE + DEDUP (this repo)
    └── 34-column → Lead_Score 0-100 → dedup

Stage 3: STORE (this repo → external systems)
    ├── Google Sheets (county tab + Qualified_Arrests)
    ├── MongoDB Atlas (arrests collection)
    └── Slack (#new-arrests-{county}, #leads)

Stage 4: INTAKE HYDRATION (GAS — outside this repo)
    └── GAS reads Qualified_Arrests → pushes to IntakeQueue

Stage 5: CLIENT CONTACT (GAS/Twilio — outside this repo)
    └── The Closer pulls from IntakeQueue → SMS/WhatsApp drip

Stage 6: PAPERWORK (GAS/SignNow — outside this repo)
    └── Client signs → SignNow webhook → GAS closes case

Stage 7: BOND POSTED (Human — outside this repo)
    └── Staff posts bond at jail → case marked complete
```

---

## Breaking Changes That Affect Downstream

**If you change any of these, you MUST coordinate with other repos:**

| Change | Affected System | Risk |
|--------|----------------|------|
| Column order in Sheets | GAS (reads by column index) | 🔴 Critical |
| Tab naming convention | GAS + Node-RED (match by tab name) | 🔴 Critical |
| `Lead_Score` range (0-100) | GAS LeadScoring (threshold comparisons) | 🔴 Critical |
| `Lead_Status` values | GAS routing logic (Hot/Warm/Cold/DQ) | 🟡 High |
| Slack message format | Node-RED Slack parser (if applicable) | 🟡 High |
| `Qualified_Arrests` tab name | GAS + Node-RED (hardcoded reference) | 🔴 Critical |
| MongoDB schema | Cloud Functions proxy (field mapping) | 🟡 High |
| Sheet ID | GAS + Node-RED (env var reference) | 🔴 Critical |

> **Rule:** If it goes into a Google Sheet or Slack channel, assume another system is reading it. Never change output format without checking downstream.
