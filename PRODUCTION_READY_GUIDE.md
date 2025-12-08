# Production Ready Scrapers - Quick Start Guide

## ✅ Ready for Production

The following scrapers are **fully operational** and ready for deployment:

1. **Collier County** - Fast, reliable, excellent data quality
2. **Hendry County** - Reliable, good data quality

---

## Running the Scrapers

### Individual County Runs

```bash
# Collier County (recommended - fastest)
npm run run:collier

# Hendry County
npm run run:hendry
```

### Run All Counties (includes non-working ones)

```bash
npm start
# or
node jobs/runAll.js
```

**Note:** This will attempt all counties including blocked ones. Use individual runs for production.

---

## Expected Output

### Collier County Example
```
═══════════════════════════════════════
🚦 Starting Collier County Scraper
═══════════════════════════════════════
📡 Loading: https://www2.colliersheriff.org/arrestsearch/Report.aspx
📊 Extracted 13 raw records
   ✅ Argenal, Oscar Antonio
   ✅ Bhargave, Saatvik Tapan
   ...
📊 Parsed 13 valid records
✅ Inserted: 13, Updated: 0
✅ Finished Collier successfully.
```

### Hendry County Example
```
[HENDRY] Starting scrape...
[HENDRY] Found 5 unique inmate detail links
[HENDRY] Extracted: Adams, Tyjae Isaiah (HCSO16MNI004458)
[HENDRY] Extracted: Alfaro, Gustavo Antonio (HCSO12MNI000379)
...
[HENDRY] Parsed 5 valid records
✅ Hendry: inserted 5, updated 0
```

---

## Google Sheets Output

All data is automatically written to:

**Spreadsheet:** https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit

### Tabs:
- **Collier** - Collier County arrests
- **Hendry** - Hendry County arrests
- **Qualified_Arrests** - High-value leads (score ≥70)
- **Logs** - Ingestion logs with timestamps

---

## Automation Setup

### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/scrapers.yml`:

```yaml
name: SWFL Arrest Scrapers

on:
  schedule:
    # Run Collier every 15 minutes
    - cron: '*/15 * * * *'
    # Run Hendry every 30 minutes
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  scrape-collier:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm run run:collier
        env:
          GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
          GOOGLE_SERVICE_ACCOUNT_KEY_PATH: ./creds/service-account-key.json

  scrape-hendry:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm run run:hendry
        env:
          GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
          GOOGLE_SERVICE_ACCOUNT_KEY_PATH: ./creds/service-account-key.json
```

**Required Secrets:**
- `GOOGLE_SHEETS_ID`: `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`
- Service account credentials are already in the repo

### Option 2: Cron Jobs (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add these lines:
# Run Collier every 15 minutes
*/15 * * * * cd /path/to/swfl-arrest-scrapers && npm run run:collier >> logs/collier.log 2>&1

# Run Hendry every 30 minutes
*/30 * * * * cd /path/to/swfl-arrest-scrapers && npm run run:hendry >> logs/hendry.log 2>&1
```

### Option 3: Manual Runs

Simply run the commands manually whenever you need fresh data:

```bash
cd /path/to/swfl-arrest-scrapers
npm run run:collier
npm run run:hendry
```

---

## Monitoring & Logs

### Check Ingestion Logs

Open the Google Sheet and check the **Logs** tab for:
- Timestamp of last run
- Number of records inserted/updated
- Any errors or warnings

### Local Logs

```bash
# View recent scraper output
tail -f logs/cron.log
tail -f logs/collier.log
tail -f logs/hendry.log
```

---

## Troubleshooting

### Issue: "Missing Google Credentials"

**Solution:** Ensure `.env` file exists with:
```
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./creds/service-account-key.json
```

### Issue: "Permission denied" on Google Sheets

**Solution:** Verify service account has Editor access:
- Email: `arrest-scraper-bot@swfl-arrest-scrapers.iam.gserviceaccount.com`
- Share spreadsheet with this email

### Issue: Scraper hangs or times out

**Solution:** 
- Check internet connection
- Verify target website is accessible
- Increase timeout in `.env`: `RETRY_LIMIT=6`

---

## Performance Benchmarks

| County  | Avg Records | Avg Time | Status |
|---------|-------------|----------|--------|
| Collier | 10-15       | 30s      | ✅ Fast |
| Hendry  | 5-10        | 90s      | ✅ Good |

---

## Next Steps

1. **Test the working scrapers** - Run them manually to verify
2. **Set up automation** - Choose GitHub Actions or cron jobs
3. **Monitor for 24 hours** - Check logs and data quality
4. **Fix remaining counties** - Manatee, Charlotte, Sarasota (see SCRAPER_STATUS_REPORT.md)

---

## Support

- **Issues:** https://github.com/Shamrock2245/swfl-arrest-scrapers/issues
- **Documentation:** See README.md and SCRAPER_STATUS_REPORT.md
- **Google Sheet:** https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit

---

**Last Updated:** December 8, 2024  
**Status:** 2/6 Counties Production Ready ✅
