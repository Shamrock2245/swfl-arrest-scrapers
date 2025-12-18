# Glossary of Terms

| Term | Definition |
| :--- | :--- |
| **34-Column Schema** | The universal data format used across all counties and integrations. |
| **DrissionPage** | Our primary Python scraping technology, designed to bypass Cloudflare and CAPTCHAs. |
| **Dual-Stack** | The hybrid architecture using both Python (DrissionPage) and Node.js (Puppeteer). |
| **Hot Lead** | An arrest record with a qualification score ≥ 70. |
| **Idempotency** | The principle that processing the same record twice results in a single, updated entry (no duplicates). |
| **Ingestion Log** | The "audit trail" tab in the Master Sheet documenting every scraper run. |
| **Master Sheet** | The primary Google Sheet database (`121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`). |
| **Normalizer** | The logic (JS/Python) that maps raw county data to our standard schema. |
| **Qualified_Arrests** | A dedicated tab in the Master Sheet where High-Score (Hot) leads are mirrored. |
| **SignNow Packet** | A bundled set of bond documents (Intake, Indemnity, etc.) sent for signature. |
| **Staggered Run** | The orchestration method (`jobs/runAll.js`) that spaces out scraper starts by 60s+ intervals. |

---
*Maintained by: Shamrock Engineering Team*
