# Architecture

## Purpose
End-to-end ingestion and qualification of arrest data for six SWFL counties, with clean interfaces to Google Sheets/Drive, Slack, and (soon) SignNow + Apps Script “Form.html” for staging/editing.

## High-Level Flow
1. **Scrape (per county)**  
   - Headless browser (Puppeteer/Playwright) fetches list/detail pages or downloads CSV/XLS/PDF.
   - Rate-limited requests, retry/backoff, Cloudflare/CAPTCHA hints.

2. **Extract & Normalize**  
   - Parse tables/CSV/PDF into row objects.  
   - Normalize into the **Unified 34-field Schema** (see `SCHEMA.md`), compute `qualified_score`.

3. **Write & Mirror**  
   - Upsert to Google Sheets by `(booking_id, arrest_date)` keys.  
   - Mirror qualified (score ≥ 70) rows to `dashboard`.

4. **Post-process**  
   - `updateBondPaid` job re-checks `bond_paid` for last 14 days.  
   - Slack summary + error alerts.

5. **Staging + SignNow** *(New)*  
   - Apps Script web UI (`Form.html`) stages a single record for operator review.  
   - Operator can correct/complete fields and trigger **SignNow** packet generation.  
   - Final PDFs saved to Drive, Sheet updated with `packet_status`, `packet_url`.

## Repository Layout

swfl-arrest-scrapers/
├─ scrapers/ # county scrapers
├─ normalizers/ # unify shape & compute score
├─ writers/ # sheets/drive
├─ jobs/ # orchestration
├─ config/ # schema + county configs
├─ shared/ # browser helpers, retry, cf detection
├─ fixtures/ # saved HTML/CSV for tests
└─ docs/ # THIS folder


## Data Contracts
- **Input:** public county sites (list/detail pages, CSV/XLS/PDF).
- **Unified Schema (34 fields):** see `SCHEMA.md`.
- **Upsert Key:** `(booking_id, arrest_date)` → prevents dupes.
- **Qualified Rule:** `qualified_score >= 70`.

## Idempotency & Reliability
- Idempotent upserts.  
- Exponential backoff + jitter.  
- Per-origin concurrency limits.  
- Fixture-based tests to catch site drift.

## Interfaces
- **Google Sheets**: source of truth + dashboard.  
- **Apps Script `Form.html`**: staging tool to correct/complete a row and send to **SignNow**.  
- **SignNow**: document generation and e-signature.  
- **Drive**: long-term artifact storage (raw + final PDF).
