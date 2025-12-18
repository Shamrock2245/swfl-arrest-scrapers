# Quick Start Guide

Get the Shamrock Bail Suite running in under 5 minutes.

---

## 1. Environment Setup

### A. Clone & Install
```bash
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
npm install
```

### B. Python Virtual Env (Required for 80% of counties)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r python_scrapers/requirements.txt
```

---

## 2. Credentials

1.  **Master Sheet:** ID is `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`.
2.  **Service Account:**
    *   Ensure your Google Service Account has **Editor** access to the sheet.
    *   Save your JSON key to `creds/service-account-key.json`.
3.  **Environment:**
    ```bash
    cp .env.example .env
    # Update GOOGLE_SA_KEY_JSON or GOOGLE_SERVICE_ACCOUNT_KEY_PATH
    ```

---

## 3. Basic Commands

### Run a Test Scrape
```bash
# Orange County (PDF based, very reliable for testing)
python3 python_scrapers/run_orange.py
```

### Run the Global Orchestrator
```bash
# This will run all counties with staggered start times
npm run scrape:all
```

---

## 4. Verification

*   **Google Sheets:** Open the [Master Database](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit) and check the `Ingestion_Log` tab.
*   **Slack:** Check for a "Run Summary" message in your configured channel.
*   **Dashboard:** Verify that high-score arrests are appearing in the Dashboard tab.

---

## 🆘 Common Fixes

- **"No such file" (Python):** Make sure you are in the root directory and the `.venv` is activated.
- **"Permission Denied" (Sheets):** Double check that the Service Account email is an **Editor** on the Master Sheet.
- **"Selectors failed":** Site layout may have changed. Run the county-specific `solver.py` directly to see raw output.

---
*Maintained by: Shamrock Engineering Team*
