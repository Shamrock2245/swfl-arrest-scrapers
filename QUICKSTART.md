# Quick Start Guide

Get up and running in 5 minutes.

## 1. Clone & Install

```bash
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
npm install
```

## 2. Setup Credentials

### A. Create Service Account Key
1. Go to Google Cloud Console
2. Create/select project with Sheets API enabled
3. Create service account: `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com`
4. Generate JSON key
5. Save as `creds/service-account-key.json`

### B. Share Spreadsheet
Share spreadsheet `1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc` with service account email (Editor access).

### C. Configure Environment
```bash
cp .env.example .env
# Edit .env - update paths if needed
```

## 3. Test Single County

```bash
# Test Collier (simplest)
npm run run:collier

# Check output in Google Sheets:
# Tab: collier-county-arrests
# Should see new rows with today's arrests
```

## 4. Run All Counties

```bash
npm start
# Runs all 6 counties with staggered timing
# Takes ~15-20 minutes
```

## 5. Schedule (Optional)

### Using Cron
```bash
crontab -e
# Add:
*/15 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/runAll.js >> logs/cron.log 2>&1
```

### Using GitHub Actions
1. Fork repo
2. Add secrets:
   - `GOOGLE_SHEETS_ID`
   - `GOOGLE_SERVICE_ACCOUNT_EMAIL`
   - `GOOGLE_SA_KEY_JSON` (entire JSON key as secret)
3. Workflow runs automatically every 15 min

## Troubleshooting

### "Permission denied" on sheets
→ Verify service account has Editor access to spreadsheet

### "CAPTCHA detected"
→ Charlotte County may need manual cookies (see README)

### "No arrests found"
→ Normal if county has no recent arrests. Check ingestion_log tab.

### Network errors
→ Increase REQUEST_DELAY_MS in .env to 1500-2000

## Next Steps

- Review `dashboard` tab for qualified arrests (score >= 70)
- Check `ingestion_log` for run history
- Customize qualification rules in `config/schema.json`

## Support

GitHub Issues: https://github.com/shamrock2245/swfl-arrest-scrapers/issues
