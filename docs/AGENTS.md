# Agents Guide (Manus/LLM Operators)

## Mission
1) Scrape a county reliably. 2) Normalize to unified schema. 3) Upsert to Sheets. 4) Mirror qualified to dashboard. 5) Stage & send docs via Apps Script + SignNow.

## Tools Agents Should Use
- **Browser**: Puppeteer/Playwright to fetch list/detail pages or exports.
- **Extractor**: Parse HTML tables / CSV / XLS / PDF+OCR.
- **Normalizer**: Apply `config/schema.json` mapping and score rules.
- **Writers**: Google Sheets `upsert`, Drive save of raw + final PDFs.
- **Slack**: Post summaries and errors.
- **GitHub**: File issues when headers/selectors drift.

## Success Criteria
- ≥1 row when county shows arrests.
- Required fields filled; null-rate on required < 10% (warn >10%, error >30%).
- Upsert keys stable: `(booking_id, arrest_date)`.
- Dashboard reflects qualified rows within one run.

## Failure Handling
- Missing export → scrape table HTML directly.
- CAPTCHA/Cloudflare → backoff, slower schedule, optional cookies, or Worker proxy.
- Header drift → create GitHub issue + attach sample HTML.

## Staging & SignNow (Operator Flow)
1. Agent selects a row (from dashboard or master) and opens **Form.html**.
2. Prefill values; operator edits/approves.
3. Agent calls SignNow template fill (with mapped fields).
4. Save PDF to Drive; update Sheet with `packet_status`, `packet_url`, `signed_at`.
