# SWFL Arrest Scrapers

**A full production-grade arrest data ingestion suite built for Shamrock Bail Bonds.**

Scrapes arrest data from **six Southwest Florida counties**, normalizes it into a unified schema, pushes results to Google Sheets (with deduplication and qualification scoring), and supports automated scheduling via **cron, GitHub Actions, or cloud runtimes**.

---

## 🗺️ Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Counties Covered](#counties-covered)
- [Setup](#setup)
- [Usage](#usage)
- [Google Sheets Output](#google-sheets-output)
- [Qualification Scoring](#qualification-scoring)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Performance & Costs](#performance--costs)
- [Customization](#customization)
- [Security Best Practices](#security-best-practices)
- [Support](#support)

---

## 🎯 Overview

A complete, production-ready system that:

- Scrapes **6 SWFL counties** every 15 minutes
- Normalizes to a **unified 34-column schema**
- Writes to **Google Sheets** with deduplication
- Mirrors **qualified leads (score ≥70)** to a dashboard tab
- Refreshes `bond_paid` for the last 14 days
- Runs via **cron**, **GitHub Actions**, or **Cloud Run**

---

## 🏗️ Architecture

swfl-arrest-scrapers/
├── scrapers/ # Puppeteer/Playwright scrapers per county
│ ├── collier.js
│ ├── charlotte.js
│ ├── sarasota.js
│ ├── hendry.js
│ ├── desoto.js
│ └── manatee.js
├── normalizers/ # Map county data → unified schema
│ └── normalize.js
├── writers/ # Sheets and Drive integrations
│ └── sheets.js
├── jobs/ # Orchestration scripts
│ ├── runAll.js
│ └── updateBondPaid.js
├── config/ # Schema + county configs
│ ├── counties.json
│ └── schema.json
├── shared/ # Browser helpers, CAPTCHA logic
│ └── browser.js
└── fixtures/ # Saved HTML for regression testing


---

## 🌎 Counties Covered

| County | URL | Notes |
|--------|-----|-------|
| **Collier** | https://www2.colliersheriff.org/arrestsearch/ | ✅ Stable |
| **Charlotte** | https://www.ccso.org/forms/arrestdb.cfm | ⚠️ Cloudflare |
| **Sarasota** | https://www.sarasotasheriff.org/arrest-reports/ | ✅ Simple HTML |
| **Hendry** | https://www.hendrysheriff.org/inmateSearch | ✅ Moderate |
| **DeSoto** | https://www.desotosheriff.com/... | ✅ Simple |
| **Manatee** | https://www.manateesheriff.com/arrest_inquiries/ | ✅ Stable |

---

## ⚙️ Setup

### Prerequisites

- Node.js 18+
- Google Cloud Project with Sheets API enabled
- Service Account with Editor access to spreadsheet

### Installation

```bash
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
npm install

Configure Environment

cp .env.example .env
# Edit .env to match your environment

Example:

GOOGLE_SHEETS_ID=1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc
GOOGLE_SERVICE_ACCOUNT_EMAIL=bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./creds/service-account-key.json
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
TZ=America/New_York

Share Spreadsheet with:

bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com

Permission: Editor

🚀 Usage
Run All Counties
npm start
# or
node jobs/runAll.js

Run a Specific County
npm run run:collier
npm run run:charlotte

Update Bond Status
npm run update:bonds
node jobs/updateBondPaid.js --days 14

📊 Google Sheets Output

Master Sheet ID: 1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc

Tab	Purpose
collier-county-arrests	Collier County data
charlotte-county-arrests	Charlotte County data
dashboard	Qualified leads (score ≥70)
ingestion_log	Job logs with timestamps, counts, errors
🧮 Qualification Scoring

Automatic scoring determines if an arrest qualifies as a potential lead.

Factor	Rule	Points
Bond ≥ $500	+30	
Bond ≥ $1500	+20	
Serious charge keywords (battery, DUI, theft, etc.)	+20	
Recent arrest ≤ 2 days	+20	
Recent arrest ≤ 1 day	+10	

Threshold: ≥70 = Qualified (mirrored to dashboard)

💾 Data Schema (34 columns)

See /config/schema.json.

Fully normalized across counties

Deduplication key: booking_id + arrest_date

mugshot_image uses =IMAGE(url) for inline thumbnails

📦 Deployment
Option 1: Local Cron

*/15 * * * * cd /path/to/swfl-arrest-scrapers && node jobs/runAll.js >> logs/cron.log 2>&1
7,22,37,52 * * * * cd /path/to/swfl-arrest-scrapers && node jobs/updateBondPaid.js >> logs/bonds.log 2>&1

Option 2: GitHub Actions

name: SWFL Scrapers
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: node jobs/runAll.js
        env:
          GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
          GOOGLE_SA_KEY_JSON: ${{ secrets.GOOGLE_SA_KEY_JSON }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

Option 3: Cloud Run

Serverless with per-minute billing and no server to manage.
(See /docs/DEPLOYMENT.md for container setup.)

🧰 Troubleshooting
Issue	Likely Cause	Fix
Permission denied	Service account not shared with sheet	Give Editor access
CAPTCHA detected	Cloudflare block	Add cookies in shared/browser.js
No arrests found	Site changed or slow	Recheck selectors / delays
Duplicate rows	Missing dedup keys	Ensure booking_id + arrest_date exist

Check ingestion_log tab for per-run diagnostics.

⚡ Performance & Costs
Metric	Average
County run	2–5 min
Full sweep (6)	15–20 min
Bond refresh	5–10 min
Sheets API	100–200 calls/run
GitHub Actions time	~40 min/day
Hosting cost	$0 (free tier)
🔧 Customization
Add a New County

Copy an existing scraper file

Add entry to config/counties.json

Register in jobs/runAll.js

Run test → verify sheet output

Adjust Scoring Rules

Edit config/schema.json → qualificationRules

Add Slack Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK


Triggers:

Run completed

Error or CAPTCHA

Qualified leads added

🔐 Security Best Practices

Never commit credentials

Rotate service account keys quarterly

Use GitHub Secrets for Actions

Limit permissions (Editor access only)

Enable 2FA in Google Cloud

Use .gitignore to exclude creds/

📞 Support

GitHub Issues: shamrock2245/swfl-arrest-scrapers/issues

Email: support@shamrockbailbonds.com

Logs: logs/cron.log, logs/bonds.log

Dashboard: Google Sheet dashboard tab

Built with ❤️ by Shamrock Bail Bonds
Automating the qualified lead pipeline for Southwest Florida.
