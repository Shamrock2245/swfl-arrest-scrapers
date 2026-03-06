# AI Agent Operating Protocols

## 🧠 Project Context
**SWFL Arrest Scrapers** is a mission-critical data ingestion pipeline for Shamrock Bail Bonds. It aggregates arrest data from 6+ counties into a centralized Google Sheet for lead generation and bond processing.

### Key Architecture
* **Dual Stack:**
    * **Node.js/Puppeteer:** Legacy & simple scrapers (`/scrapers`).
    * **Python/DrissionPage:** Modern, anti-detection scrapers (`/python_scrapers`).
* **Data Source of Truth:** The [Master Google Sheet](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit).
* **Schema:** Dynamic. We capture *all* data a county provides. We maintain a baseline structure but expand columns freely to ensure no data is lost.

---

## 🤖 The Digital Team: Roles & Relationships

### "The Clerk" (Runtime Agent)
*   **Role:** The automated data-entry specialist operating this repository.
*   **Responsibility:** Booking scraper, OCR specialist, and county jail roster monitor.
*   **Goal:** Zero manual data entry. Instant, accurate case file creation in the Master Sheet.

### The Coding Assistant (Developer Agent)
*   **Role:** The AI software engineer (like me!) assisting the human Owner with building, scaling, and debugging the repo.
*   **Relationship to The Clerk:** We *build* the tools and environments that "The Clerk" runs in. The Clerk is our output. We do not *act* as The Clerk; we *program* The Clerk.

---

## 🛡️ Prime Directives & Rules
For strict constraints on data governance, credential safety, sheet idempotency, and stealth operations (anti-bot workarounds), you **MUST** consult:
👉 **`docs/RULES.md`**

---

## ⚙️ Interaction & Budgeting

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

## 🚨 Error Handling & Operational Memory

1.  **Platform Quirks & Overrides:** Before debugging a scraper that is suddenly failing (especially due to Cloudflare), check **`docs/MEMORY.md`**.
2.  **Import Errors:** Check `package.json` or `requirements.txt` first.
3.  **Selector Failures:** Request a fresh HTML fixture (save page as HTML) to debug offline.
4.  **Cloudflare Blocks:** Do not brute force. Consult `MEMORY.md` and default to `DrissionPage`.

---
*Maintained by: Admin & AI Agents*