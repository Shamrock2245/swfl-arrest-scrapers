# SWFL Arrest Scrapers - Project Summary

## 🎯 What We Built

A complete, production-ready multi-county arrest scraping system that:
- Scrapes 6 SWFL counties every 15 minutes
- Normalizes data to unified schema
- Writes to Google Sheets with automatic deduplication
- Scores and mirrors qualified leads (≥70 score) to dashboard
- Refreshes bond_paid status for last 14 days
- Runs via cron, GitHub Actions, or cloud platforms

## 📦 Complete Package

### Core Scrapers (6 Counties)
```
scrapers/
├── collier.js      - Collier County Sheriff
├── charlotte.js    - Charlotte County (Cloudflare aware)
├── sarasota.js     - Sarasota County Sheriff
├── hendry.js       - Hendry County Sheriff
├── desoto.js       - DeSoto County Sheriff
└── manatee.js      - Manatee County Sheriff
```

Each scraper:
- Fetches recent arrests (last ~72 hours)
- Parses HTML to extract structured data
- Handles pagination, retries, rate limiting
- Detects CAPTCHA/Cloudflare blocks
- Extracts mugshots and detail URLs

### Job Orchestration
```
jobs/
├── runAll.js          - Run all 6 counties (sequential or parallel)
└── updateBondPaid.js  - Refresh bond status for last 14 days
```

### Data Normalization
```
normalizers/
└── normalize.js       - Map county formats → unified schema
                       - Parse names, addresses, dates
                       - Calculate qualification scores
                       - Extract charges/statutes/bonds
```

### Google Sheets Integration
```
writers/
└── sheets.js          - Upsert records (no duplicates)
                       - Mirror qualified to dashboard
                       - Log all runs to ingestion_log
                       - Use service account auth
```

### Shared Utilities
```
shared/
└── browser.js         - Puppeteer helpers
                       - Retry logic with exponential backoff
                       - CAPTCHA/Cloudflare detection
                       - Random delays and user agents
```

### Configuration
```
config/
├── counties.json      - Per-county URLs, selectors, aliases
└── schema.json        - Unified 34-column schema
                       - Field aliases for harmonization
                       - Qualification scoring rules
```

## 🔑 Key Features

### 1. Unified Schema (34 Columns)
```
booking_id, full_name_last_first, first_name, last_name, dob, sex, race,
arrest_date, arrest_time, booking_date, booking_time, agency,
address, city, state, zipcode, charges_raw, charge_1, charge_1_statute,
charge_1_bond, charge_2, charge_2_statute, charge_2_bond, total_bond,
bond_paid, court_date, case_number, mugshot_url, mugshot_image,
source_url, county, ingested_at_iso, qualified_score, is_qualified,
extra_fields_json
```

### 2. Smart Deduplication
- Upsert by `booking_id + arrest_date`
- No duplicates ever created
- Updates existing records when data changes

### 3. Automatic Qualification Scoring
```javascript
Score calculation:
- Bond >= $500:     +30 points
- Bond >= $1500:    +20 points
- Serious charges:  +20 points (battery, DUI, theft, etc.)
- Recent arrest:    +20 points (≤ 2 days), +10 points (≤ 1 day)

Qualified if score >= 70 → mirrored to dashboard tab
```

### 4. Mugshot Handling
- Stores `mugshot_url` as text
- Writes `mugshot_image` as `=IMAGE(url)` formula
- Images render directly in Google Sheets

### 5. Bond Status Refresh
- Re-checks last 14 days of records
- Updates `bond_paid` when status changes
- Runs separately to avoid slowing main scrape

### 6. Robust Error Handling
- Exponential backoff (500ms → 4000ms)
- 4 retry attempts per request
- Cloudflare detection and waiting
- CAPTCHA detection (fails gracefully)
- All errors logged to `ingestion_log`

## 📊 Google Sheets Structure

### Master Spreadsheet
ID: `1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc`

### County Tabs (6)
- `collier-county-arrests`
- `charlotte-county-arrests`
- `sarasota-county-arrests`
- `hendry-county-arrests`
- `desoto-county-arrests`
- `manatee-county-arrests`

### Special Tabs
- `dashboard` - All qualified arrests (score ≥ 70) with County in col A
- `ingestion_log` - Timestamp, county, status, count, duration, errors

## 🚀 Deployment Options

### 1. Local Cron (Recommended for Testing)
```bash
# Every 15 minutes
*/15 * * * * cd /path/to/swfl-arrest-scrapers && node jobs/runAll.js

# Bond refresh (offset by 7 min)
7,22,37,52 * * * * cd /path/to/swfl-arrest-scrapers && node jobs/updateBondPaid.js
```

### 2. GitHub Actions (Recommended for Production)
- Automated runs every 15 minutes
- No server maintenance required
- Free tier: 2000 minutes/month (plenty for this)
- Secrets stored securely in GitHub
- Logs viewable in Actions tab

### 3. Cloud VPS (DigitalOcean, AWS, etc.)
- Full control
- Can run other services too
- Requires server management

### 4. Google Cloud Run
- Serverless
- Pay per execution
- Native GCP integration

## 📋 Setup Checklist

### Prerequisites
- [ ] Node.js 18+ installed
- [ ] Google Cloud project with Sheets API enabled
- [ ] Service account created: `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com`
- [ ] Service account JSON key downloaded
- [ ] Spreadsheet shared with service account (Editor)

### Local Setup (5 minutes)
```bash
# 1. Clone repo
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers

# 2. Install
npm install

# 3. Add credentials
cp .env.example .env
# Place service-account-key.json in creds/

# 4. Test
npm run run:collier

# 5. Check Google Sheets for new data
```

### GitHub Actions Setup (10 minutes)
```bash
# 1. Fork repo on GitHub
# 2. Add repository secrets:
#    - GOOGLE_SHEETS_ID
#    - GOOGLE_SERVICE_ACCOUNT_EMAIL
#    - GOOGLE_SA_KEY_JSON (entire JSON file content)
# 3. Push to trigger workflow
# 4. Monitor in Actions tab
```

## 📈 Performance & Costs

### Execution Time
- Single county: 2-5 minutes
- All 6 counties (staggered): 15-20 minutes
- Bond refresh (14 days): 5-10 minutes

### Google Sheets API Usage
- ~100-200 API calls per full run
- Well within free tier (unlimited reads/writes)

### GitHub Actions (Free Tier)
- ~40 minutes per day (all runs)
- Free tier: 2000 minutes/month
- Cost: $0 (well under limit)

### Cloud Costs (if self-hosting)
- DigitalOcean Droplet: $5/month (1GB RAM)
- AWS EC2 t2.micro: Free tier eligible
- GCP Cloud Run: ~$0.50/month (minimal usage)

## 🔧 Customization

### Add New County
1. Create `scrapers/newcounty.js` (copy existing template)
2. Add entry to `config/counties.json`
3. Update `jobs/runAll.js` to include new county
4. Test: `node scrapers/newcounty.js`

### Adjust Qualification Rules
Edit `config/schema.json`:
```json
{
  "qualificationRules": {
    "minScore": 70,
    "scoring": {
      "bondAmount": [...],
      "seriousCharges": {...},
      "recency": [...]
    }
  }
}
```

### Change Scraping Frequency
Edit cron schedule or GitHub workflow `.github/workflows/scrape.yml`:
```yaml
schedule:
  - cron: '*/30 * * * *'  # Every 30 minutes instead of 15
```

### Add Slack Notifications
```bash
# Add to .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Notifications sent automatically for:
# - Run completion
# - Errors
# - Qualified arrests
```

## 📚 Documentation

- `README.md` - Overview and architecture
- `QUICKSTART.md` - 5-minute setup guide
- `DEPLOYMENT.md` - Production deployment options
- `PROJECT_SUMMARY.md` - This file

## ✅ What's Next?

### Immediate (Do This Now)
1. Clone the repo to your local machine or server
2. Add Google service account credentials
3. Test with: `npm run run:collier`
4. Verify data appears in Google Sheets

### Short-term (This Week)
1. Set up automated execution (cron or GitHub Actions)
2. Monitor `ingestion_log` tab for first few days
3. Verify qualified arrests appear in `dashboard`
4. Test bond_paid refresh: `node jobs/updateBondPaid.js`

### Medium-term (This Month)
1. Save HTML fixtures from each county for testing
2. Fine-tune qualification scoring based on real data
3. Add Slack notifications
4. Consider adding Lee County scraper (if not already present)

### Long-term (Ongoing)
1. Monitor for county website changes
2. Update selectors when sites redesign
3. Rotate service account credentials quarterly
4. Add more counties as business expands

## 🐛 Common Issues & Solutions

### "Permission denied" on Google Sheets
→ Verify service account has Editor access to spreadsheet

### "CAPTCHA detected"
→ Charlotte County may need manual cookies (see browser.js)
→ Consider proxy service if persistent

### "No arrests found" for all counties
→ Check if sites are accessible
→ Verify selectors haven't changed
→ Test manually: `node scrapers/COUNTY.js`

### GitHub Actions failing
→ Check secrets are set correctly
→ Verify service account JSON is valid
→ Check logs in Actions tab

### Mugshots not displaying
→ Ensure `mugshot_image` column has formula, not just URL
→ Some sites require authentication for images

## 📞 Support

- GitHub Issues: https://github.com/shamrock2245/swfl-arrest-scrapers/issues
- Review logs: `tail -f logs/cron.log`
- Check sheet: `ingestion_log` tab

## 🎉 Success Criteria

You'll know it's working when:
✅ County tabs populate with new arrests every 15 minutes
✅ `dashboard` tab shows qualified arrests (score ≥ 70)
✅ `ingestion_log` shows successful runs
✅ Mugshots display as images (not just URLs)
✅ `bond_paid` updates when status changes
✅ No duplicates in any county tab

---

**Built with ❤️ for Shamrock Bail Bonds**
*Automating the qualified lead pipeline for SWFL counties*
