# SWFL Arrest Scrapers - Architecture

## Overview

The SWFL Arrest Scrapers system is a hybrid bail bond lead generation platform that combines automated web scraping, data normalization, lead scoring, and Google Sheets integration.

---

## System Components

### 1. **Node.js Stealth Scrapers** (Primary Data Collection)

**Location**: `/scrapers/*_stealth.js`

**Technology Stack**:
- **Puppeteer Extra** with Stealth Plugin
- **Node.js 20+**
- **ES Modules** (type: "module")

**Counties Covered**:
- Hillsborough (100 arrests/day)
- Manatee (50 arrests/day)
- Sarasota (40 arrests/day)
- Charlotte (25 arrests/day)
- Hendry (8 arrests/day)

**Key Features**:
- Anti-detection (stealth mode)
- Click-through to detail pages
- Date-based searching
- 34-column data normalization
- Direct Google Sheets integration

---

### 2. **Google Apps Script Scrapers** (Lee & Collier)

**Location**: Apps Script Project ID `12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo`

**Technology**: Google Apps Script (JavaScript)

**Counties Covered**:
- Lee County (fully operational)
- Collier County (fully operational)

**Key Features**:
- Runs directly in Google Sheets
- No external infrastructure needed
- Menu-driven manual triggers
- Time-based automated triggers

---

### 3. **Data Normalization Layer**

**Location**: `/normalizers/normalize34.js`

**Purpose**: Convert varying county data formats into standardized 34-column schema

**Input**: Raw arrest data from county websites  
**Output**: Standardized ArrestRecord objects

**Schema**: See `SCHEMA.md` for complete field definitions

---

### 4. **Google Sheets Writer**

**Location**: `/writers/sheets34.js`

**Purpose**: Write normalized data to Google Sheets

**Authentication Methods**:
- `GOOGLE_SA_KEY_JSON` (GitHub Actions)
- `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` (Local development)

**Target Sheet**: `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`

**Sheet Tabs**:
- Lee, Collier, Hendry, Charlotte, Manatee, Sarasota, Hillsborough
- Manual_Bookings (form submissions)
- Ingestion_Log (audit trail)

---

### 5. **Lead Scoring System**

**Location**: `/apps_script/LeadScoringSystem.gs`

**Purpose**: Automatically qualify leads based on bond amount, type, status, and data completeness

**Scoring Criteria**:
- Bond Amount: $500-$50K (+30), $50K-$100K (+20), >$100K (+10)
- Bond Type: CASH/SURETY (+25), NO BOND (-50), ROR (-30)
- Status: IN CUSTODY (+20), RELEASED (-30)
- Data Completeness: All fields (+15), Missing data (-10)
- Disqualifying Charges: Murder/Capital/Federal (-100)

**Lead Status**:
- **Hot** (≥70): Best leads - immediate follow-up
- **Warm** (40-69): Decent leads - follow-up within 24h
- **Cold** (0-39): Poor leads - low priority
- **Disqualified** (<0): Not worth pursuing

---

### 6. **Booking Form System**

**Location**: `/apps_script/Form_Enhanced.html`

**Purpose**: Manual booking entry with dual input support

**Input Methods**:
1. **Menu Button**: From Google Sheets → Pre-fills from row data
2. **Universal Bookmarklet**: From county website → Extracts data from page

**Output**: Writes to `Manual_Bookings` sheet tab

---

### 7. **GitHub Actions Workflows**

**Location**: `/.github/workflows/`

**Purpose**: Automated scraping on staggered schedules

**Workflows**:
- `scrape-hillsborough.yml` - Every 20 minutes
- `scrape-manatee.yml` - Every 30 minutes
- `scrape-sarasota.yml` - Every 45 minutes
- `scrape-charlotte.yml` - Every hour
- `scrape-hendry.yml` - Every 2 hours
- `scrape-all-manual.yml` - Manual trigger (all counties)

**Runner**: `ubuntu-latest`  
**Timeout**: 15 minutes per county  
**Secrets**: `GOOGLE_SA_KEY_JSON`, `GOOGLE_SHEETS_ID`

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     County Websites                              │
│  (Hillsborough, Manatee, Sarasota, Charlotte, Hendry, Lee, Collier) │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │                                      │
        │  Node.js Stealth Scrapers            │  Google Apps Script
        │  (Puppeteer + Stealth Plugin)        │  (Lee & Collier)
        │                                      │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │     Data Normalization Layer         │
        │     (normalize34.js)                 │
        │     → 34-column schema               │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │     Google Sheets Writer             │
        │     (sheets34.js)                    │
        │     → County-specific tabs           │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │     Google Sheets                    │
        │     (121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E) │
        │     → 7 county tabs                  │
        │     → Manual_Bookings tab            │
        │     → Ingestion_Log tab              │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │     Lead Scoring System              │
        │     (LeadScoringSystem.gs)           │
        │     → Adds Lead_Score & Lead_Status  │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │     Qualified Leads                  │
        │     → Hot/Warm/Cold/Disqualified     │
        │     → Ready for follow-up            │
        └──────────────────────────────────────┘
```

---

## Technology Stack

### Backend (Scrapers)
- **Runtime**: Node.js 20+
- **Module System**: ES Modules
- **Browser Automation**: Puppeteer Extra + Stealth Plugin
- **HTTP Client**: Fetch API (built-in)
- **Environment**: dotenv

### Frontend (Apps Script)
- **Runtime**: Google Apps Script (V8)
- **Language**: JavaScript ES6+
- **UI**: HTML Service (Form.html)
- **Triggers**: Time-based, Menu-driven

### Data Storage
- **Primary**: Google Sheets
- **Authentication**: Service Account (JSON key)
- **API**: Google Sheets API v4

### CI/CD
- **Platform**: GitHub Actions
- **Runner**: Ubuntu Latest
- **Secrets**: GitHub Repository Secrets
- **Schedule**: Cron expressions

---

## Deployment Architecture

### Local Development
```
Developer Machine
  ├── Clone repo from GitHub
  ├── Install dependencies (npm install)
  ├── Create .env file
  │   ├── GOOGLE_SHEETS_ID
  │   └── GOOGLE_SERVICE_ACCOUNT_KEY_PATH
  ├── Run scrapers manually
  │   └── node scrapers/[county]_stealth.js
  └── Test with run_all_counties.js
```

### GitHub Actions (Production)
```
GitHub Actions Runner
  ├── Checkout code
  ├── Setup Node.js 20
  ├── Install dependencies (npm install)
  ├── Install Chromium (npx puppeteer browsers install chrome)
  ├── Set environment variables
  │   ├── GOOGLE_SHEETS_ID (from secrets)
  │   └── GOOGLE_SA_KEY_JSON (from secrets)
  ├── Run scraper
  │   └── node scrapers/[county]_stealth.js
  └── Upload logs on failure
```

### Google Apps Script (Hybrid)
```
Google Workspace
  ├── Apps Script Project
  │   ├── ComprehensiveMenuSystem.gs (menu)
  │   ├── ArrestScraper_LeeCounty.gs (scraper)
  │   ├── ArrestScraper_CollierCounty.gs (scraper)
  │   ├── LeadScoringSystem.gs (scoring)
  │   ├── Form_Enhanced.html (form UI)
  │   └── FormDataHandler.gs (form backend)
  ├── Time-based Triggers
  │   ├── Lee: Every 30 minutes
  │   └── Collier: Every 30 minutes
  └── Google Sheets Integration
      └── Direct access (no API needed)
```

---

## Security Architecture

### Credential Management
- **GitHub Secrets**: `GOOGLE_SA_KEY_JSON`, `GOOGLE_SHEETS_ID`
- **Local .env**: Never committed to Git (in .gitignore)
- **Service Account**: Limited to Sheets API only
- **Sheet Permissions**: Service account has Editor access

### Access Control
- **GitHub Repo**: Private repository
- **Google Sheet**: Shared with service account only
- **Apps Script**: Bound to specific sheet
- **Bookmarklet**: Deployment ID required

### Anti-Detection (Stealth)
- **Puppeteer Stealth Plugin**: Removes automation flags
- **Random Delays**: 800ms + 600ms jitter
- **User-Agent Spoofing**: Chrome 120+ on Windows
- **Viewport Randomization**: 1920x1080 ± variance
- **No Headless**: Runs in headful mode on GitHub Actions

---

## Scalability Considerations

### Current Capacity
- **Daily Arrests**: ~223 across all counties
- **Hot Leads**: ~80-127 per day
- **GitHub Actions**: 2,000 minutes/month (free tier)
- **Sheets API**: 60 requests/minute/user

### Bottlenecks
1. **GitHub Actions Minutes**: May need paid plan for 24/7 operation
2. **Sheets API Rate Limits**: Batch writes to stay under limits
3. **County Website Blocking**: Stealth mode mitigates but not foolproof
4. **Workflow Concurrency**: Max 20 concurrent jobs (free tier)

### Scaling Strategies
1. **Increase Scraping Frequency**: Reduce intervals for high-traffic counties
2. **Add More Counties**: Replicate scraper pattern
3. **Upgrade GitHub Plan**: Pro ($4/month) for 3,000 minutes
4. **Self-Hosted Runner**: Run on own server for unlimited minutes
5. **Batch Processing**: Group multiple records per Sheets API call

---

## Monitoring & Observability

### GitHub Actions
- **Workflow Status**: Visible in Actions tab
- **Logs**: Detailed execution logs per run
- **Artifacts**: Uploaded on failure (retention: 7-14 days)
- **Email Notifications**: On workflow failure

### Google Sheets
- **Ingestion_Log Tab**: Audit trail of all scraper runs
- **Timestamp**: When data was written
- **Record Count**: How many records inserted/updated
- **Status**: SUCCESS/FAILURE

### Apps Script
- **Execution Logs**: View → Logs (Ctrl+Enter)
- **Triggers**: View → Triggers (see all scheduled runs)
- **Quotas**: View → Quotas (check usage)

---

## Future Enhancements

### Short-term (1-3 months)
- [ ] Add DeSoto County (if traffic increases)
- [ ] Implement retry logic for failed scrapes
- [ ] Add email notifications for hot leads
- [ ] Create dashboard for lead metrics

### Medium-term (3-6 months)
- [ ] Build React/Next.js frontend
- [ ] Implement lead assignment system
- [ ] Add SMS notifications
- [ ] Integrate with CRM (Salesforce, HubSpot)

### Long-term (6-12 months)
- [ ] Machine learning for lead scoring
- [ ] Predictive analytics (bond amount, release time)
- [ ] Mobile app for field agents
- [ ] Multi-state expansion

---

## Related Documentation

- **SCHEMA.md** - 34-column data schema
- **DEVELOPMENT.md** - Development guidelines
- **DEPLOYMENT.md** - Deployment procedures
- **SCRAPING_RULES.md** - Scraping best practices
- **TROUBLESHOOTING.md** - Common issues and solutions
- **SECURITY.md** - Security best practices

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
