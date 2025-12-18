# Automation & Helper Ecosystem

This document outlines the background processes, scripts, and integrations that power the **Shamrock Bail Suite**.

## 📊 Master Data Store
All automated workflows synchronize with the Master Google Sheet.
* **Link:** [Shamrock Master Database](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit)
* **Schema:** Strict 34-column format. See [SCHEMA.md](file:///Users/brendan/Desktop/swfl-arrest-scrapers/docs/SCHEMA.md) for field definitions.

---

## 🚀 Job Orchestration
We use a staggered orchestration model to prevent rate-limiting and IP bans.

### `jobs/runAll.js`
The primary runner that coordinates all county scrapers.
* **Execution:** `npm run scrape:all`
* **Logic:**
    * **Staggered Start:** Executes scrapers with increasing offsets (60s, 120s, etc.) to minimize concurrent load.
    * **Dual-Engine Support:** Triggers both Python (`DrissionPage`) and Node (`Puppeteer`) scrapers.
    * **Failure Isolation:** One county's failure does not stop the entire run.

### `jobs/updateBondPaid.js`
A background utility that periodically checks the "Bond Paid" status of current leads.

---

## 🎯 Lead Scoring System
Located in `apps_script/LeadScoringSystem.gs`, this engine qualifies incoming leads.

### Scoring Rubric (Max 100)
| Factor | Score Adjustment | Notes |
| :--- | :--- | :--- |
| **Bond $500 - $50k** | +30 | Sweet spot for bond processing. |
| **Bond > $100k** | +10 | High risk, lower priority. |
| **Cash/Surety** | +25 | High qualification indicator. |
| **In Custody** | +20 | Immediate opportunity. |
| **Released** | -30 | Lead is no longer active. |
| **Capital Charge** | -100 | Automatic Disqualification (Murder/Federal). |

### Thresholds
* **HOT (≥ 70):** Triggers immediate Slack alert.
* **WARM (≥ 40):** Visible in Dashboard "Priority" section.
* **COLD (< 40):** Logged for archival purposes only.

---

## 💬 Notifications (Slack)
Integrated via `slack/notify.js`. Requires `SLACK_WEBHOOK_URL` environment variable.

* **Run Summary:** Sends a breakdown of records added per county after every `runAll` execution.
* **Qualified Alerts:** Triggered by `notifyQualifiedArrest(record)` when a lead hits the **HOT** threshold.
* **Error Reporting:** Sends critical alerts if a scraper is blocked or encounters a CAPTCHA.

---

## ✍️ SignNow Integration
Supported via `apps_script/SignNowAPI.gs`.

### Capabilities:
1.  **PDF Pre-filling:** Auto-populates forms using data from the 34-column schema.
2.  **Delivery Methods:**
    * **Email:** Standard remote signing.
    * **SMS:** Mobile-optimized signing links.
    * **Embedded:** Kiosk mode for in-person bond processing.
3.  **Automation:** Completed documents are automatically moved to the "Completed Bonds" folder in Google Drive.

---
*Maintained by: Shamrock Engineering Team*
