# Quick Start Guide - SWFL Arrest Scrapers

## Run Scrapers

### Collier County
```bash
cd /home/ubuntu/swfl-arrest-scrapers
node -r dotenv/config scrapers/collier.js
```

### Hendry County
```bash
cd /home/ubuntu/swfl-arrest-scrapers
node -r dotenv/config scrapers/hendry.js
```

### Collier Backfill (10 days)
```bash
cd /home/ubuntu/swfl-arrest-scrapers
node -r dotenv/config backfill_collier_enhanced.js 10
```

### Run All Counties
```bash
cd /home/ubuntu/swfl-arrest-scrapers
node jobs/runAll.js
```

## Verify Data

```bash
# Collier
node verify_collier_data.js

# Hendry
node verify_hendry_data.js

# Google Sheets connection
node test_sheets_connection.js
```

## Fix Headers (if misaligned)

```bash
# Collier
node fix_collier_headers.js

# Hendry
node fix_hendry_headers.js
```

## View Logs

Check the "Logs" tab in Google Sheets:
https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit#gid=LOGS

## Troubleshooting

### Permission Denied
Make sure the service account has Editor access to the Google Sheet.

### Headers Misaligned
Run the appropriate `fix_*_headers.js` script.

### DNS Error
The correct Collier domain is `www2.colliersheriff.org` (not `ww2`).

## Documentation

- **UNIFIED_SYSTEM.md** - Complete system documentation
- **DEPLOYMENT_GUIDE.md** - Deployment instructions
- **PROGRESS_SUMMARY.md** - Latest progress report
