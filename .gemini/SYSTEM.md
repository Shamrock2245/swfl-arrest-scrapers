# 🏗 SYSTEM — Architecture & Topology

## This Repo's Place in the Shamrock Ecosystem

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shamrock Software Stack                      │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────┐  │
│  │ shamrock-bail-   │   │ shamrock-        │   │ shamrock-  │  │
│  │ portal-site      │   │ node-red         │   │ telegram-  │  │
│  │ (Wix + GAS)      │   │ (Ops Dashboard)  │   │ app        │  │
│  └────────┬─────────┘   └────────┬─────────┘   └─────┬──────┘  │
│           │                      │                    │         │
│           └──────────┬───────────┘                    │         │
│                      │                                │         │
│           ┌──────────▼──────────┐                     │         │
│           │   Google Apps       │◄────────────────────┘         │
│           │   Script (GAS)     │                                │
│           │   "The Factory"    │                                │
│           └──────────▲─────────┘                                │
│                      │                                          │
│  ┌───────────────────┴──────────────────────┐                   │
│  │         swfl-arrest-scrapers ◄── YOU ARE HERE                │
│  │         24 County Scrapers               │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Scraper → Lead Pipeline

```
67 Florida County Jail Websites
         │
         ▼
┌─────────────────────────┐
│  solver.py (per county) │  ← DrissionPage / requests+BS4 / Puppeteer
│  Scrape → Parse → Return│
└──────────┬──────────────┘
           │ list[dict]
           ▼
┌─────────────────────────┐
│  runner.py (universal)  │  ← Normalize → Score → Dedup → Write
└──────────┬──────────────┘
           │
     ┌─────┼─────────────────┐
     ▼     ▼                 ▼
┌────────┐ ┌──────────┐ ┌────────┐
│ Google │ │ MongoDB  │ │ Slack  │
│ Sheets │ │ Atlas    │ │ Alerts │
│ (34col)│ │ (backup) │ │ (#new- │
│        │ │          │ │arrests)│
└───┬────┘ └──────────┘ └────────┘
    │
    ▼
┌────────────────────────────────┐
│  GAS LeadScoringSystem.js     │  ← Scores ≥70 → Hot leads
│  → Qualified_Arrests tab      │
│  → Slack #leads @channel      │
│  → The Concierge (outreach)   │
└────────────────────────────────┘
```

## Deployment Topology

### GitHub Actions (Primary — CI/CD)
- **24 workflow files** in `.github/workflows/scrape_{county}.yml`
- Staggered cron schedules: every 20min (high-priority) to every 3h (low-volume)
- Ubuntu runners with Python 3.11 + Chrome/Chromium
- Secrets: `GOOGLE_SERVICE_ACCOUNT_JSON`, `SLACK_WEBHOOK_URL`, `MONGODB_URI`

### Docker (Local / Self-Hosted)
- `docker-compose.yml` — dual-stack: Python + Node.js services
- `Dockerfile` — Chromium + Python deps + Node deps
- Volume mounts for `creds/` and `config/`

### Hetzner VPS (Production Runners)
- `cpx21` servers, Ubuntu 24.04
- Self-hosted GitHub Actions runners for counties that need persistent browser sessions

## Storage Architecture

| Store | Role | Access Pattern |
|-------|------|----------------|
| **Google Sheets** | Primary database | Insert at row 2 (newest on top). One tab per county. |
| **MongoDB Atlas** | Analytics + dedup | Bulk upsert via Cloud Functions proxy. Cross-county queries. |
| **Google Drive** | Fixtures + PDFs | Saved HTML for regression testing. |
| **Slack** | Alert bus | Per-county channels + `#leads` for hot leads. |

### Google Sheets Layout
```
Master Spreadsheet (121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E)
├── Charlotte          ← County-specific arrest data (34 columns)
├── Collier            
├── DeSoto             
├── ... (24 county tabs)
├── Qualified_Arrests  ← Hot leads (Score ≥70) mirrored here
├── Ingestion_Log      ← Every scraper run logged here
└── Log_Archive        ← Ingestion logs >90 days old
```

## Config Architecture

```
Priority: Env Vars > County YAML > _defaults.yaml > global.yaml
```

| Layer | File | Example |
|-------|------|---------|
| **Global** | `config/global.yaml` | Timeouts, retry counts, browser settings |
| **Defaults** | `config/counties/_defaults.yaml` | Shared county defaults (days_back, max_pages) |
| **County** | `config/counties/{name}.yaml` | URLs, selectors, schedule, output tab |
| **Environment** | `.env` / GitHub Secrets | Credentials, sheet IDs, webhook URLs |

## Inter-Repo Data Flows

| Flow | Mechanism | What Moves |
|------|-----------|------------|
| **Scrapers → Sheets** | `gspread` via service account | 34-column arrest records |
| **Scrapers → MongoDB** | Cloud Functions proxy POST | Same records for analytics |
| **Scrapers → Slack** | Webhook POST | New arrest alerts, hot lead alerts |
| **Sheets → GAS** | `SpreadsheetApp` reads | Lead scoring, qualified lead mirroring |
| **GAS → Node-RED** | `NodeRedHandlers.js` JSON | Dashboard data (arrests, leads, revenue) |
| **Node-RED → Scrapers** | `exec` node triggers | Scheduled scraper runs on cron |
| **GAS → Slack** | Outbound webhooks | Business alerts, intake notifications |

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Primary scraper engine** | DrissionPage | Latest |
| **HTTP scraping** | requests + BeautifulSoup4 | Latest |
| **Legacy engine** | Puppeteer (Node.js) | v21+ |
| **Browser** | Chromium | Bundled with DP |
| **Sheets client** | gspread + google-auth | Latest |
| **MongoDB client** | pymongo[srv] | Latest |
| **Slack client** | Direct webhook POST | N/A |
| **Python** | 3.11+ | 3.11 |
| **Node.js** | 18+ (legacy only) | 18 |
| **CI/CD** | GitHub Actions | v4 |
| **Container** | Docker + docker-compose | Latest |
