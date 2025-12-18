# SWFL Arrest Scrapers

**A production-grade arrest data ingestion and lead management suite built for Shamrock Bail Bonds.**

This system leverages a **Dual-Stack** architecture (Python/DrissionPage + Node.js/Puppeteer) to scrape arrest data from across Florida, normalize it into a unified 34-column schema, and manage the lead lifecycle via Google Sheets and SignNow.

---

## 🗺️ Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Counties Covered](#counties-covered)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Lead Scoring](#lead-scoring)
- [Deployment](#deployment)
- [Security](#security)

---

## 🎯 Overview

The SWFL Bail Suite provides real-time visibility into new arrests:
- **High-Stealth Scraping:** Bypasses Cloudflare/CAPTCHA via DrissionPage.
- **Unified Data:** All 8+ counties map to the same **34-column schema**.
- **Algorithmic Qualification:** Leads are automatically scored and prioritized.
- **Dashboard Integration:** Qualified leads (Score ≥ 70) mirror to a centralized dashboard.
- **SignNow Automation:** Field-prefilled bond paperwork via Email, SMS, or Embedded links.

---

## 🏗️ Architecture

The system follows a modular "Sync-Normalize-Notify" pattern:

1.  **Ingestion:** Python/DrissionPage (Primary) and Node.js (Legacy) scrapers collect raw data.
2.  **Normalization:** Data is mapped to the `ArrestRecord` model and the 34-column master schema.
3.  **Storage:** The [Master Google Sheet](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit) acts as the primary database.
4.  **Automation:** Apps Script triggers lead scoring, Slack alerts, and SignNow workflows.

---

## 🌎 Counties Covered

| County | Stack | Status |
| :--- | :--- | :--- |
| **Orange** | Python / PDF | ✅ Stable |
| **Hillsborough** | Python / DrissionPage | ✅ Stable |
| **Manatee** | Python / DrissionPage | ✅ Stable |
| **Sarasota** | Python / DrissionPage | ✅ Stable |
| **Charlotte** | Python / DrissionPage | ✅ Stable |
| **Hendry** | Python / DrissionPage | ✅ Stable |
| **Palm Beach** | Python / DrissionPage | ⚠️ Beta |
| **Lee / Collier** | Apps Script | ✅ Stable |
| **DeSoto** | Node.js | ⚠️ Legacy |

---

## ⚙️ Quick Start

### 1. Prerequisites
- Python 3.10+ & Node.js 20+
- Google Cloud Service Account with Editor access to the Master Sheet.

### 2. Installation
```bash
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers

# Python Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r python_scrapers/requirements.txt

# Node Environment
npm install
```

### 3. Configuration
Create a `.env` file in the root:
```env
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SA_KEY_JSON={"your_key": "here"}
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

---

## 🚀 Usage

### Run a Single County (Python)
```bash
python3 python_scrapers/run_orange.py
python3 python_scrapers/run_hillsborough.py
```

### Run All Counties (Orchestrated)
```bash
npm run scrape:all
```

---

## 🧮 Lead Scoring
Leads are evaluated on a 0-100 scale:
*   **HOT (≥ 70):** Triggers immediate Slack alert.
*   **WARM (≥ 40):** Priority follow-up.
*   **COLD (< 40):** Standard archival.

*See `docs/SCHEMA.md` for the full scoring rubric.*

---

## 📦 Deployment
The system is optimized for **GitHub Actions**. Staggered workflows ensure we remain under rate limits and avoid IP blocks.

*   **Workflow Path:** `.github/workflows/scrape_*.yml`
*   **Manual Trigger:** Available via the "Actions" tab in GitHub.

---
*Maintained by: Shamrock Engineering Team*
