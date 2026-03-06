# MEMORY.md - Operational "Gotchas" & Solutions

This document serves as a persistent repository for hard-learned lessons, quirky system behaviors, and operational "gotchas". Add to this document when you spend hours solving an obscure edge-case so the next agent won't have to.

## Cloudflare Bypassing & Bot Detection

### Sarasota Scraper (`sarasota_scraper`)
*   **Issue:** Sarasota Sheriff's website (`https://www.sarasotasheriff.org/arrest-reports/index.php`) enforces strict Cloudflare challenges. Standard `requests`, `cloudscraper`, and basic browser automation frequently fail or hit infinite challenge loops.
*   **Workaround:** 
    *   We use Python's **`DrissionPage`** to bypass these blocks.
    *   Direct HTTP Requests using Scrapling, curl_cffi, or cloudscraper were failing. Browser automation was required to successfully execute the JS challenge and click into the arrest details.
*   **Key Lesson:** When Cloudflare strict mode is engaged, default to headful or highly-stealthy Chromium instances (`DrissionPage`). Do not waste time trying to reverse-engineer Cloudflare JS challenges.

## Platform Quirks

### Wix Velo Constraints
*   **Issue:** API Keys and secrets must never be exposed or logged in frontend code.
*   **Workaround:** Always use **Wix Secrets Manager**. "Wix is the clipboard; GAS is the brain."

### Third-Party APIs
*(Add future API quirks here)*
