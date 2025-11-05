# Operations Runbook

## Routine
- County pipelines run every 15 min (staggered).
- Slack: `#bail-ops-alerts` receives summaries & warnings.

## Manual Execution
```bash
# Single county
npm run run:collier

# All counties
npm start

# Bond refresh (14 days)
npm run update:bonds

Monitoring

Google Sheets → ingestion_log tab: timestamp, county, status, counts, duration, errors.

Dashboard tab: qualified leads across all counties.

Incident Response

RED (no rows; expected arrests): run county locally, capture HTML, create issue.

YELLOW (header drift or high nulls): adjust mapping; rerun.

CF/CAPTCHA: add delay, cookies, or enable proxy; reduce frequency temporarily.

Rollbacks

Revert last change; rerun pipeline.

Reprocess raw artifacts if needed (fixtures/).

SLOs (suggested)

Freshness: data ≤ 90 minutes old.

Reliability: ≥ 98% successful runs/day.

Data quality: null-rate on required < 10%.
