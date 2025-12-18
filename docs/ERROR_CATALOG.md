# Error Catalog

This catalog provides context for error codes found in the `Ingestion_Log`.

---

| Code | Description | Resolution |
| :--- | :--- | :--- |
| **`E_EMPTY`** | Scraper returned 0 rows. | Verify the county listing page has data; if so, update CSS selectors. |
| **`E_CLOUDFLARE`** | Blocked by anti-bot screening. | Switching to `DrissionPage` (Python) usually resolves this. If using Node, check `shared/browser.js`. |
| **`E_403`** | Forbidden/Blocked IP. | Delay the scrape, use a proxy, or switch to a different GitHub Action runner region. |
| **`E_SHEET_PERM`** | Access Denied to Google Sheet. | Re-share the sheet with the Service Account email as "Editor". |
| **`E_PARSE_DATE`** | Date format mismatch. | Adjust the `date_formats` array in the county config or solver. |
| **`E_SIGNNOW`** | Packet generation failed. | Check the `SignNowAPI` logs; usually caused by a missing field (e.g., defendant email). |
| **`E_DRISSION_CRASH`** | Browser crashed during scrape. | Increase memory limits or update the DrissionPage library. |

---
*Maintained by: Shamrock Engineering Team*
