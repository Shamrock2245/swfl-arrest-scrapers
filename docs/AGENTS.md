# AI Agent Operating Protocols

## 🧠 Project Context
**SWFL Arrest Scrapers** is a mission-critical data ingestion pipeline for Shamrock Bail Bonds. It aggregates arrest data from 6+ counties into a centralized Google Sheet for lead generation and bond processing.

### Key Architecture
* **Dual Stack:**
    * **Node.js/Puppeteer:** Legacy & simple scrapers (`/scrapers`).
    * **Python/DrissionPage:** Modern, anti-detection scrapers (`/python_scrapers`).
* **Data Source of Truth:** The [Master Google Sheet](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit).
* **Schema:** Strict **34-column** format defined in `config/schema.json` and `docs/SCHEMA.md`.

---

## 🛡️ Prime Directives

1.  **Schema Sanctity:**
    * **NEVER** alter the column order or names in the Google Sheet output without explicit authorization.
    * All scrapers must normalize data to `ArrestRecord` (Python) or `normalizeRecord` (JS) specifications before writing.
    * **Lead_Score** and **Lead_Status** are mandatory calculated fields.

2.  **Idempotency:**
    * All writers must check for existing records using the composite key: `County` + `Booking_Number`.
    * Duplicates must be **updated** or **skipped**, never inserted as new rows.

3.  **Stealth First:**
    * Scrapers must assume hostile environments (Cloudflare, CAPTCHA).
    * Use `DrissionPage` (Python) or `puppeteer-extra-plugin-stealth` (Node) by default.
    * Implement random delays and user-agent rotation.

4.  **Credential Safety:**
    * **NEVER** output, log, or commit `GOOGLE_SA_KEY_JSON`, `SLACK_WEBHOOK_URL`, or `SIGNNOW_TOKEN`.
    * Always refer to credentials via environment variables.

---

## 🤖 Interaction & Budgeting

### Complexity Tiers
* **Tier 1 (Routine):** Typo fixes, comment updates, markdown formatting. *Action: Execute immediately.*
* **Tier 2 (Logic):** Fixing a selector, adjusting a timeout, adding a helper function. *Action: Plan → Execute → Test.*
* **Tier 3 (Architectural):** Changing the Schema, adding a new county, modifying core writer logic. *Action: Detailed Plan → User Approval → Branching → Execute.*

### Standard Workflow
1.  **Orient:** Identify if the task involves Node.js (`/scrapers`) or Python (`/python_scrapers`).
2.  **Plan:** State the intended changes and the specific files involved.
3.  **Execute:** Apply changes.
4.  **Verify:**
    * For Scrapers: Run locally and check `ingestion_log` in Sheets.
    * For GAS: Deploy as Web App and test via `Form.html`.

---

## 📂 Quick Reference Map

| Directory | Purpose | Key Files |
| :--- | :--- | :--- |
| `/python_scrapers` | **Primary** scraping engine (DrissionPage) | `run_pipeline.py`, `scrapers/*.py` |
| `/scrapers` | **Secondary** scraping engine (Node/Puppeteer) | `desoto_incremental.js`, `collier.js` |
| `/apps_script` | Google Apps Script UI & Backend | `Code.gs`, `Form.html`, `SignNowAPI.gs` |
| `/normalizers` | JS Data Normalization | `normalize34.js` |
| `/writers` | JS Sheets Integration | `sheets34.js` |
| `/jobs` | Node.js Orchestration | `runAll.js`, `updateBondPaid.js` |
| `/.github/workflows` | CI/CD Automation | `scrape_*.yml` |

---

## 🚨 Error Handling Strategy

1.  **Import Errors:** Check `package.json` or `requirements.txt` first. Suggest installation commands.
2.  **Selector Failures:** Request a fresh HTML fixture (save page as HTML) to debug offline.
3.  **Cloudflare Blocks:** Suggest increasing delays or switching to "headful" mode locally. Do not brute force.

---
*Maintained by: Admin & AI Agents*