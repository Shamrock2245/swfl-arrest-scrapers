# SWFL Arrest Scrapers

Multi-county arrest data pipeline for Southwest Florida bail bonds. Scrapes recent arrests from county sheriff websites and writes to Google Sheets with automated qualification scoring.

## Counties Covered

- **Collier County** - https://www2.colliersheriff.org/arrestsearch/
- **Charlotte County** - https://www.ccso.org/forms/arrestdb.cfm (Cloudflare protected)
- **Sarasota County** - https://www.sarasotasheriff.org/arrest-reports/
- **Hendry County** - https://www.hendrysheriff.org/inmateSearch
- **DeSoto County** - https://www.desotosheriff.com/bureaus/detention_bureau_jail/jail_roster.php
- **Manatee County** - https://www.manateesheriff.com/arrest_inquiries/

## Architecture

```
swfl-arrest-scrapers/
├── scrapers/           # Per-county scraper modules (Puppeteer)
│   ├── collier.js
│   ├── charlotte.js
│   ├── sarasota.js
│   ├── hendry.js
│   ├── desoto.js
│   └── manatee.js
├── jobs/               # Orchestration & cron jobs
│   ├── runAll.js       # Run all counties (staggered)
│   └── updateBondPaid.js  # Refresh bond status for last 14 days
├── shared/             # Common utilities
│   └── browser.js      # Puppeteer helpers, retry logic, CAPTCHA detection
├── normalizers/        # Data harmonization
│   └── normalize.js    # Map county-specific fields → unified schema
├── writers/            # Google Sheets integration
│   └── sheets.js       # Upsert, dashboard mirroring, logging
├── config/             # Configuration files
│   ├── counties.json   # County-specific URLs, selectors, aliases
│   └── schema.json     # Unified schema + qualification rules
└── fixtures/           # Saved HTML samples (for testing)
```

## Setup

### 1. Prerequisites
- Node.js 18+
- Google Cloud project with Sheets API enabled
- Service account with access to target spreadsheet

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```env
GOOGLE_SHEETS_ID=1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc
GOOGLE_SERVICE_ACCOUNT_EMAIL=bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./creds/service-account-key.json
```

### 4. Add Service Account Key
Place your Google service account JSON key at:
```
creds/service-account-key.json
```

Make sure the service account has edit access to the spreadsheet.

## Usage

### Run All Counties (Staggered)
```bash
npm start
# or
node jobs/runAll.js
```

### Run Specific County
```bash
npm run run:collier
npm run run:charlotte
npm run run:sarasota
npm run run:hendry
npm run run:desoto
npm run run:manatee
```

### Update Bond Status (Last 14 Days)
```bash
npm run update:bonds
# or with custom lookback:
node jobs/updateBondPaid.js --days 30
```

## Unified Schema

All counties normalize to this schema:

| Column | Type | Description |
|--------|------|-------------|
| booking_id | string | Unique booking number |
| full_name_last_first | string | "Last, First Middle" |
| first_name | string | First name |
| last_name | string | Last name |
| dob | string | YYYY-MM-DD |
| sex | string | M/F |
| race | string | Race/ethnicity |
| arrest_date | string | YYYY-MM-DD |
| arrest_time | string | HH:mm:ss |
| booking_date | string | YYYY-MM-DD |
| booking_time | string | HH:mm:ss |
| agency | string | Arresting agency |
| address | string | Street address |
| city | string | City |
| state | string | State (default: FL) |
| zipcode | string | ZIP code |
| charges_raw | string | Full charges text |
| charge_1 | string | Primary charge description |
| charge_1_statute | string | Statute number |
| charge_1_bond | string | Bond for this charge |
| charge_2 | string | Secondary charge (if any) |
| charge_2_statute | string | Statute number |
| charge_2_bond | string | Bond for this charge |
| total_bond | string | Total bond amount (numeric) |
| bond_paid | string | "TRUE" / "FALSE" / "" |
| court_date | string | YYYY-MM-DD |
| case_number | string | Case number |
| mugshot_url | string | URL to mugshot image |
| mugshot_image | formula | `=IMAGE(mugshot_url)` |
| source_url | string | Detail page URL |
| county | string | County code (COLLIER, CHARLOTTE, etc.) |
| ingested_at_iso | string | ISO timestamp |
| qualified_score | number | 0-100 qualification score |
| is_qualified | boolean | TRUE if score >= 70 |
| extra_fields_json | string | Unmapped fields as JSON |

## Qualification Scoring

Automatic lead scoring based on:
- **Bond Amount**: +30 if >= $500, +20 if >= $1500
- **Serious Charges**: +20 if contains keywords (battery, DUI, theft, fraud, etc.)
- **Recency**: +20 if arrested <= 2 days ago, +10 if <= 1 day

**Qualified threshold**: Score >= 70 → mirrored to `dashboard` tab

## Deduplication

Records are upserted by `booking_id + arrest_date`:
- **New record**: Insert
- **Existing record**: Update in place

This prevents duplicates while allowing updates (e.g., bond paid status changes).

## Rate Limiting & Retries

- **Target**: 1 req/sec with 400ms jitter
- **Backoff**: Exponential (500ms, 1000ms, 2000ms, 4000ms)
- **Retry limit**: 4 attempts per request
- **Cloudflare sites**: Extra 1200ms + 600ms jitter

## Google Sheets Output

### Target Spreadsheet
`1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc`

### County Tabs
- `collier-county-arrests`
- `charlotte-county-arrests`
- `sarasota-county-arrests`
- `hendry-county-arrests`
- `desoto-county-arrests`
- `manatee-county-arrests`

### Special Tabs
- `dashboard` - Qualified arrests (score >= 70) from all counties
- `ingestion_log` - Timestamp, county, status, count, duration, errors

## Scheduled Execution

### Option 1: Cron (Linux/Mac)
```bash
# Every 15 minutes
*/15 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/runAll.js >> logs/cron.log 2>&1

# Update bond status (offset by 7 minutes)
7,22,37,52 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/updateBondPaid.js >> logs/bonds.log 2>&1
```

### Option 2: GitHub Actions
```yaml
name: Run Scrapers
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:

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
          GOOGLE_SERVICE_ACCOUNT_KEY_PATH: ${{ secrets.GOOGLE_SA_KEY }}
```

### Option 3: Google Apps Script Wrapper
Create time-based triggers in Apps Script that call:
```javascript
function runSwflScrapers() {
  // Shell out to Node.js via Apps Script execution API
  // or use UrlFetchApp to hit a Cloud Run deployment
}
```

## Troubleshooting

### CAPTCHA Detected
- **Charlotte County** may require manual cookie extraction if Cloudflare is aggressive
- Save browser session cookies and inject them (see `shared/browser.js`)

### Sheet Permission Errors
Ensure service account `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com` has **Editor** access to spreadsheet.

### Empty Results
- Check if county site structure changed (view saved fixtures)
- Enable DEBUG mode: `export DEBUG=true`
- Manually test scrapers: `node scrapers/collier.js`

### Rate Limit / Timeout
- Increase `REQUEST_DELAY_MS` in `.env`
- Reduce `MAX_CONCURRENT_DETAILS` if running parallel

## Development

### Save Fixtures
When site structure changes, save new HTML samples:
```bash
node scrapers/collier.js --save-fixtures
```

Fixtures go in `fixtures/collier/list.html`, `fixtures/collier/detail-1.html`, etc.

### Test Normalization
```javascript
import { normalizeRecord } from './normalizers/normalize.js';

const raw = {
  'Booking Number': '2025-0001234',
  'Name': 'SMITH, JOHN MICHAEL',
  'DOB': '1990-05-15',
  'Charges': 'DUI - 1st Offense | Battery (784.03)',
  'Bond': '$2,500.00'
};

const normalized = normalizeRecord(raw, 'COLLIER', 'https://...');
console.log(normalized);
```

## Contributing

1. Test on individual county first
2. Save fixtures before submitting PR
3. Verify qualification scores match expected values
4. Check for duplicate records in test sheet

## License

MIT

## Support

Issues: https://github.com/shamrock2245/swfl-arrest-scrapers/issues
