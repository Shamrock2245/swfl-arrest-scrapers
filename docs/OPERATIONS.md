# Operations Runbook

This document defines the daily routine and emergency procedures for the Shamrock Bail Suite.

---

## 🔄 Daily Routine

1.  **Automated Runs:** All county scrapers are scheduled via GitHub Actions (every 15-60 minutes).
2.  **Monitoring:** Review the `Ingestion_Log` tab in Google Sheets once per day.
3.  **Alerts:** Monitor Slack for `@hot-lead` notifications and critical error alerts.

---

## 🛠️ Manual Interventions

### Running a specific county
```bash
# Primary (Python)
python3 python_scrapers/run_hillsborough.py

# Legacy (Node)
npm run run:desoto
```

### Forcing a Lead Rescore
In Google Sheets, use the **🟩 Bail Suite** menu:
`Bail Suite > Advanced > Rescore All Records`

### Updating Bond Status
```bash
# Refreshes the "Bond Paid" status for the last 14 days of arrests
npm run update:bonds
```

---

## 🚨 Incident Response

| Symptom | Diagnosis | Fix |
| :--- | :--- | :--- |
| **0 Records added** | Site down or selectors changed | Run `solver.py` locally to inspect the page HTML. |
| **"Turnstile" Error** | IP block or CAPTCHA trigger | Reduce frequency in GitHub Actions or check `shared/browser.js` for stealth flags. |
| **Sheets Write Error** | API Quota or Permission | Verify service account Editor access. |

---

## 📈 Service Levels (SLOs)
*   **Freshness:** Data for all counties should be no more than 2 hours old.
*   **Success Rate:** > 95% of scheduled GitHub Action runs should complete without a fatal error.
*   **Sync:** Dashboard leads must update within 60 seconds of a successful ingestion.

---
*Maintained by: Shamrock Engineering Team*
