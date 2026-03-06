# RULES.md - Strict Constraints & Policies

This document outlines the strict, non-negotiable constraints for the SWFL Arrest Scrapers repository.

## 🛡️ Prime Directives

1.  **Schema Flexibility:**
    *   The 34-column schema is a baseline, but **NOT** a strict constraint.
    *   Scrapers must extract **ALL** available data that each county provides. If a county provides more data than fits the 34 columns, append new columns to that county's sheet.
    *   Normalize common fields (Name, Booking Number, DOB, Charges, Mugs) where possible, but prioritize data completeness over strict schema adherence.

2.  **Idempotency & Integrity:**
    *   All writers must check for existing records using the composite key: `County` + `Booking_Number` (or equivalent unique agency ID).
    *   Duplicates must be **updated** or **skipped**, never inserted as new rows.

3.  **Stealth First:**
    *   Scrapers must assume hostile environments (Cloudflare, CAPTCHA).
    *   Use `DrissionPage` (Python) or `puppeteer-extra-plugin-stealth` (Node.js) by default.
    *   Implement random delays and user-agent rotation. Avoid brute force.

4.  **Credential Safety:**
    *   **NEVER** expose, log, output, or commit Twilio secrets, `GOOGLE_SA_KEY_JSON`, `SLACK_WEBHOOK_URL`, `SIGNNOW_TOKEN`, or any other API Keys.
    *   Always refer to credentials via environment variables or Wix Secrets Manager.

## 📂 Data Governance & Retention Master Database
All production data is stored in the **Shamrock Master Sheet**: `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`

### 🕒 Data Retention Policies
1.  **Scrape Fixtures (`fixtures/`):** 30 Days. Pruned by CI maintenance.
2.  **Google Sheets Data:** Indefinite. Rows are appended or upserted; bots do not delete from the county primary tabs.
3.  **Log Data (`Ingestion_Log`):** 90 Days. Older logs are archived to the `Log_Archive` tab.

### 🔒 Security & Access
1.  **Service Account:** Access restricted to `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com`.
2.  **Permissions:** The service account has **Editor** permissions only on specifically authorized spreadsheets.
3.  **PII:** We only ingest and store data explicitly marked as "Public Record" by the source county.

### ⚖️ Compliance
*   **Deduplication:** The `Booking_Number` + `County` composite key is the authoritative unique identifier.
*   **Audit Trail:** Every write operation includes a `Scrape_Timestamp` (Line 1 of the schema).
