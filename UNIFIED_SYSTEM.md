# Shamrock Bail Bonds - Unified Arrest Scraping System

## Overview

This is a **unified multi-county arrest scraping system** that combines:

1. **Google Apps Script** scrapers for simple API-based counties (e.g., Lee County)
2. **Node.js/Puppeteer** scrapers for complex sites (e.g., Collier County with ASP.NET WebForms)
3. **Google Sheets** as the central data hub (`Shamrock_Arrests_Master`)

Both systems write to the same Google Sheets workbook, creating a cohesive data pipeline for all Southwest Florida counties.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Shamrock_Arrests_Master                      │
│              (Google Sheets - Central Hub)                   │
│                                                              │
│  Tabs: Lee | Collier | Hendry | Charlotte |                │
│        Qualified_Arrests | Config | Logs                    │
└─────────────────────────────────────────────────────────────┘
                    ▲                    ▲
                    │                    │
        ┌───────────┴──────────┐    ┌───┴────────────────────┐
        │  Google Apps Script  │    │  Node.js Scrapers      │
        │  (Simple APIs)       │    │  (Complex Sites)       │
        │                      │    │                        │
        │  • Lee County        │    │  • Collier County      │
        │    (JSON API)        │    │    (ASP.NET WebForms)  │
        │                      │    │  • Charlotte County    │
        │  Location:           │    │    (Cloudflare)        │
        │  Apps Script Project │    │  • Others...           │
        │  (admin@shamrock...) │    │                        │
        └──────────────────────┘    │  Location:             │
                                    │  GitHub repo           │
                                    │  shamrock2245/         │
                                    │  swfl-arrest-scrapers  │
                                    └────────────────────────┘
```

---

## Google Sheets Configuration

**Spreadsheet ID:** `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`

**URL:** https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit

**Service Account:** `shamrock-mcp-bot@shamrock-mcp-automation.iam.gserviceaccount.com`

**Owner:** `admin@shamrockbailbonds.biz`

### Sheet Tabs

| Tab Name | Purpose | Data Source |
|----------|---------|-------------|
| **Lee** | Lee County arrests | Google Apps Script |
| **Collier** | Collier County arrests | Node.js scraper (this repo) |
| **Hendry** | Hendry County arrests | Node.js scraper (this repo) |
| **Charlotte** | Charlotte County arrests | Node.js scraper (this repo) |
| **Qualified_Arrests** | High-value leads (score ≥70) | Auto-mirrored from all counties |
| **Config** | System configuration | Manual |
| **Logs** | Ingestion logs | Auto-generated |

---

## Data Schema

All counties use a **unified 35-column schema** for consistency:

```
booking_id, full_name_last_first, first_name, last_name, dob, sex, race,
arrest_date, arrest_time, booking_date, booking_time, agency, address,
city, state, zipcode, charges_raw, charge_1, charge_1_statute,
charge_1_bond, charge_2, charge_2_statute, charge_2_bond, total_bond,
bond_paid, court_date, case_number, mugshot_url, mugshot_image,
source_url, county, ingested_at_iso, qualified_score, is_qualified,
extra_fields_json
```

See `config/schema.json` for field aliases and normalization rules.

---

## Node.js Scrapers (This Repo)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
   cd swfl-arrest-scrapers
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Add service account key:**
   - Place `shamrock-mcp-automation.json` in `creds/service-account-key.json`
   - Make sure the service account has **Editor** access to the Google Sheet

### Running Scrapers

**Run Collier County scraper:**
```bash
npm run run:collier
# or
node -r dotenv/config scrapers/collier.js
```

**Run all counties:**
```bash
npm start
# or
node jobs/runAll.js
```

**Update bond status:**
```bash
npm run update:bonds
```

### Collier County Scraper

**File:** `scrapers/collier.js`

**Target Site:** https://www2.colliersheriff.org/arrestsearch/Report.aspx

**Method:** Puppeteer browser automation

**Features:**
- Extracts arrest records from server-rendered HTML tables
- Parses complex nested table structures
- Extracts mugshot URLs
- Normalizes to unified schema
- Writes to "Collier" tab in Google Sheets
- Deduplicates by `booking_id + arrest_date`

**Schedule:** Run every 15 minutes via cron or GitHub Actions

---

## Google Apps Script Scrapers

### Lee County Scraper

**File:** `ArrestScraper_LeeCounty.gs` (in Apps Script project)

**Apps Script Project:** https://script.google.com/u/0/home/projects/1-AidUbJivXw_t2eUw4mMX5GiJjvWtqL8SGuHDLaBCYFKYt8Pcba6uZIt/edit

**Target Site:** Lee County Sheriff JSON API

**Method:** `UrlFetchApp.fetch()` to JSON endpoint

**Features:**
- Simple HTTP GET to JSON API
- Parses JSON response
- Normalizes to unified schema
- Writes to "Lee" tab in Google Sheets

**Schedule:** Triggered by Apps Script time-based trigger (every 15 minutes)

---

## Deployment

### Option 1: Local Cron (Development)

```bash
# Edit crontab
crontab -e

# Add this line to run every 15 minutes
*/15 * * * * cd /path/to/swfl-arrest-scrapers && node jobs/runAll.js >> logs/cron.log 2>&1
```

### Option 2: GitHub Actions (Recommended)

Create `.github/workflows/scrape.yml`:

```yaml
name: SWFL Arrest Scrapers

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: node jobs/runAll.js
        env:
          GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
          GOOGLE_SERVICE_ACCOUNT_KEY_PATH: ./creds/service-account-key.json
```

### Option 3: Cloud Run (Production)

See `docs/DEPLOYMENT.md` for containerized deployment.

---

## Qualification Scoring

Records are automatically scored to identify high-value leads:

| Factor | Points |
|--------|--------|
| Bond ≥ $500 | +30 |
| Bond ≥ $1500 | +20 |
| Serious charge (DUI, battery, theft, etc.) | +20 |
| Recent arrest ≤ 2 days | +20 |
| Recent arrest ≤ 1 day | +10 |

**Threshold:** Score ≥ 70 = Qualified (auto-mirrored to `Qualified_Arrests` tab)

---

## Troubleshooting

### Google Sheets Permission Denied

**Error:** `403 Forbidden` or `Permission denied`

**Solution:**
1. Go to Google Sheets
2. Click **Share**
3. Add `shamrock-mcp-bot@shamrock-mcp-automation.iam.gserviceaccount.com`
4. Set permission to **Editor**

### DNS Error for Collier County

**Error:** `ENOTFOUND ww2.colliersheriff.org`

**Solution:** The correct domain is `www2.colliersheriff.org` (not `ww2`). The scraper uses the correct domain.

### Headers Misaligned in Google Sheets

**Solution:** Run the header fix script:
```bash
node fix_collier_headers.js
```

---

## Testing

**Test Google Sheets connection:**
```bash
node test_sheets_connection.js
```

**Test Collier normalization:**
```bash
node test_normalize_collier.js
```

**Debug Collier raw data:**
```bash
node debug_collier_raw.js
```

**Verify Collier data in Sheets:**
```bash
node verify_collier_data.js
```

---

## Integration with Apps Script

The Node.js scrapers and Apps Script scrapers work together seamlessly:

1. **Both write to the same Google Sheets** (`Shamrock_Arrests_Master`)
2. **Both use the same unified schema** (35 columns)
3. **Both use the same qualification scoring** (score ≥ 70)
4. **Both log to the same `Logs` tab**

This allows you to:
- Use Apps Script for simple API-based counties (fast, no server needed)
- Use Node.js for complex sites that require browser automation
- View all data in one central location
- Run automated workflows on the combined data

---

## Maintenance

### Adding a New County

1. **Determine scraping method:**
   - Simple API → Add to Apps Script project
   - Complex site → Add to this Node.js repo

2. **For Node.js scrapers:**
   - Create `scrapers/{county_name}.js`
   - Add entry to `config/counties.json`
   - Add to `jobs/runAll.js`
   - Create corresponding tab in Google Sheets

3. **For Apps Script scrapers:**
   - Create `ArrestScraper_{CountyName}.gs`
   - Add trigger in Apps Script project
   - Create corresponding tab in Google Sheets

### Updating the Schema

1. Edit `config/schema.json`
2. Update all sheet headers using `fix_collier_headers.js` (adapt for other counties)
3. Update normalization logic in `normalizers/normalize.js`

---

## Support

**GitHub:** https://github.com/shamrock2245/swfl-arrest-scrapers

**Owner:** admin@shamrockbailbonds.biz

**Service Account:** shamrock-mcp-bot@shamrock-mcp-automation.iam.gserviceaccount.com

---

## License

MIT License - Shamrock Bail Bonds © 2025
