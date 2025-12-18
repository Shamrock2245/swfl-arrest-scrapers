# SWFL Bail Suite - Deployment Guide

This guide covers the setup and deployment of the SWFL Bail Suite SCRAPING and DASHBOARD systems.

---

## 📋 Prerequisites

### 1. Infrastructure
*   **Google Cloud Project:** "swfl-arrest-scrapers"
*   **Service Account:** JSON Key with `Editor` access to the Master Sheet.
*   **Google Sheet ID:** `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`

### 2. Environment
*   **Node.js:** v20.x or higher.
*   **Python:** v3.10.x or higher.
*   **Git:** Correct line endings (`.gitattributes` recommended).

---

## 💻 Local Development Setup

### Step 1: Clone and Install
```bash
git clone https://github.com/Shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
npm install
```

### Step 2: Python Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r python_scrapers/requirements.txt
```

### Step 3: Environment Variables
Create a `.env` file in the root:
```env
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SA_KEY_JSON={"your": "service_account_json_content"}
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## 🚀 Deployment: GitHub Actions (Production)

Automated scraping is handled via CI/CD.

### GitHub Secrets
Ensure the following are set in **Settings > Secrets > Actions**:
1.  `GOOGLE_SA_KEY_JSON`: The full service account JSON (Base64 encoded if necessary).
2.  `GOOGLE_SHEETS_ID`: `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`
3.  `SLACK_WEBHOOK_URL`: For notifications.

### Verifying Workflows
Check the **Actions** tab. You should see individual county workflows (e.g., `scrape_charlotte.yml`) and a manual "Scrape All" runner.

---

## 🛠️ Deployment: Google Apps Script

The Apps Script environment powers the Dashboard and Lead Scoring.

1.  **Open Project:** [Apps Script Console](https://script.google.com/u/0/home/projects/12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo/edit)
2.  **Verify Triggers:**
    *   `runLeeCountyScraper`: Every 30 minutes.
    *   `scoreAllSheets`: Twice daily.
3.  **Update Properties:** Ensure `SIGNNOW_API_TOKEN` and `GOOGLE_SHEETS_ID` are in **Project Settings > Script Properties**.

---

## 🚑 Rollback & Maintenance

### Git Rollback
If a deployment fails:
```bash
git revert HEAD
git push origin main
```

### Monitoring
*   **Success Check:** Monitor the `Ingestion_Log` tab in Sheets.
*   **Troubleshooting:** Consult `TROUBLESHOOTING.md`.

---
*Maintained by: Shamrock Engineering Team*
