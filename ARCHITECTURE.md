# SWFL Bail Suite - Architecture

The SWFL Bail Suite is an enterprise-grade lead generation and management ecosystem for Shamrock Bail Bonds. It utilizes a **Dual-Stack** architecture to achieve maximum reliability and anti-detection capabilities across diverse Florida county websites.

---

## 🏗️ System Overview

The system follows a modular "Scrape-Normalize-Sync" pipeline.

### 1. **The Dual-Stack Engine**

We maintain two distinct scraping stacks optimized for different environments:

#### **A. Primary: Python/DrissionPage (High-Stealth)**
*   **Location:** `/python_scrapers`
*   **Target Counties:** Orange, Hillsborough, Manatee, Sarasota, Charlotte, Hendry, Palm Beach.
*   **Tech:** DrissionPage (replaces Puppeteer for superior Cloudflare/CAPTCHA bypass), Python 3.10+.
*   **Output:** Standardized `ArrestRecord` objects written via Python's `SheetsWriter`.

#### **B. Secondary: Node.js/Puppeteer (Legacy & Simple)**
*   **Location:** `/scrapers`
*   **Target Counties:** DeSoto, Collier (Legacy).
*   **Tech:** `puppeteer-extra-plugin-stealth`, Node.js 20+.
*   **Output:** JSON records normalized via `normalize34.js`.

#### **C. Native: Google Apps Script (Internal)**
*   **Location:** `/apps_script`
*   **Target Counties:** Lee (Direct Trigger), Collier.
*   **Tech:** GAS (V8 Engine).
*   **Usage:** Internal triggers and UI components.

---

## 🔄 Data Pipeline

### 1. Ingestion & Normalization
Regardless of the stack, all data is normalized into a **34-Column Schema** before reaching the database.
*   **Key Fields:** `Booking_Number` (Primary Key), `County`, `Lead_Score`, `Lead_Status`.
*   **Rule:** Idempotent writes based on `Booking_Number` + `County`.

### 2. The Database (Google Sheets)
The Master Sheet acts as our centralized database.
*   **URL:** [Shamrock Master Database](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit)
*   **Tabs:** One per county, plus `Qualified_Arrests` and `Ingestion_Log`.

### 3. Lead Qualification (Apps Script)
The `LeadScoringSystem.gs` runs post-ingestion (or via trigger) to calculate:
*   **Lead_Score (0-100):** Based on bond amount, status, and charge severity.
*   **Lead_Status:** Hot (≥70), Warm, Cold.

---

## 🛠️ Infrastructure & CI/CD

### **GitHub Actions**
We use staggered workflows to prevent IP blocks.
*   **Location:** `.github/workflows/`
*   **Schedule:** Optimized based on county traffic (e.g., Hillsborough every 20m, Hendry every 2h).
*   **Environment:** Ubuntu Runners with Python/Node pre-installed.

### **Monitoring**
*   **Slack Alerts:** Success/Failure and "Hot Lead" notifications via `slack/notify.js`.
*   **Ingestion Log:** A dedicated tab in the Master Sheet for audit trails.

---

## 📂 Repository Map

| Path | Purpose | Key Files |
| :--- | :--- | :--- |
| `/python_scrapers` | **Main Scraper Logic** | `run_pipeline.py`, `scrapers/*.py` |
| `/apps_script` | **Dashboard & CRM Logic** | `Code.gs`, `SignNowAPI.gs`, `Dashboard.html` |
| `/jobs` | **Orchestration** | `runAll.js` |
| `/docs` | **System Manuals** | `SCHEMA.md`, `AUTOMATION_HELPERS.md` |

---
*Last Updated: December 18, 2025*
