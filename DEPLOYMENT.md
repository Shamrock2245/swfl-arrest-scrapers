# SWFL Arrest Scrapers - Deployment Guide

## Deployment Environments

### 1. Local Development
- **Purpose**: Testing and development
- **Authentication**: Service account JSON file
- **Execution**: Manual (`node scrapers/[county]_stealth.js`)

### 2. GitHub Actions (Production)
- **Purpose**: Automated scraping on schedule
- **Authentication**: GitHub Secrets
- **Execution**: Automated (cron schedule)

### 3. Google Apps Script (Hybrid)
- **Purpose**: Lee & Collier counties
- **Authentication**: Bound to Google Sheet
- **Execution**: Time-based triggers

---

## Prerequisites

### For All Environments

1. **Google Cloud Project**
   - Project ID: `swfl-arrest-scrapers` (or your choice)
   - APIs enabled: Google Sheets API

2. **Service Account**
   - Email: `arrest-scraper@[project-id].iam.gserviceaccount.com`
   - Role: Editor (for Sheets API)
   - JSON Key: Downloaded and secured

3. **Google Sheet**
   - ID: `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`
   - Shared with service account email (Editor permission)
   - Tabs: Lee, Collier, Hendry, Charlotte, Manatee, Sarasota, Hillsborough, Manual_Bookings, Ingestion_Log

4. **GitHub Repository**
   - URL: https://github.com/Shamrock2245/swfl-arrest-scrapers
   - Visibility: Private
   - Secrets configured (see below)

---

## Local Development Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/Shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Configure Environment

Create `.env` file:

```bash
cat > .env << EOF
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
EOF
```

Add service account key:

```bash
# Download JSON key from Google Cloud Console
# Save as service-account-key.json in project root
```

### Step 4: Test Scraper

```bash
# Test single county
node scrapers/hendry_stealth.js

# Test all counties
node run_all_counties.js
```

### Step 5: Verify Data

Open Google Sheets and check:
- County tabs have new data
- Ingestion_Log shows SUCCESS
- No duplicate records

---

## GitHub Actions Deployment

### Step 1: Configure GitHub Secrets

1. Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/settings/secrets/actions

2. Add these secrets:

**GOOGLE_SHEETS_ID**:
```
121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
```

**GOOGLE_SA_KEY_JSON**:
```json
{
  "type": "service_account",
  "project_id": "swfl-arrest-scrapers",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "arrest-scraper@project.iam.gserviceaccount.com",
  ...
}
```
*(Paste entire JSON content)*

### Step 2: Enable GitHub Actions

1. Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/settings/actions

2. Under "Actions permissions":
   - Select "Allow all actions and reusable workflows"

3. Under "Workflow permissions":
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

### Step 3: Verify Workflows

1. Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/actions

2. You should see 6 workflows:
   - Scrape Hillsborough County
   - Scrape Manatee County
   - Scrape Sarasota County
   - Scrape Charlotte County
   - Scrape Hendry County
   - Scrape All Counties (Manual)

### Step 4: Test Manual Workflow

1. Click "Scrape All Counties (Manual)"
2. Click "Run workflow" → "Run workflow"
3. Wait 10-15 minutes
4. Check logs for errors
5. Verify data in Google Sheets

### Step 5: Monitor Automated Runs

Workflows will run automatically on schedule:
- **Hillsborough**: Every 20 minutes
- **Manatee**: Every 30 minutes
- **Sarasota**: Every 45 minutes
- **Charlotte**: Every hour
- **Hendry**: Every 2 hours

Check Actions tab for status.

---

## Google Apps Script Deployment

### Step 1: Access Apps Script Project

URL: https://script.google.com/u/0/home/projects/12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo/edit

### Step 2: Verify Files

Ensure these files exist:
- `Code.gs` (or main file)
- `ComprehensiveMenuSystem.gs`
- `ArrestScraper_LeeCounty.gs`
- `ArrestScraper_CollierCounty.gs`
- `LeadScoringSystem.gs`
- `Form_Enhanced.html`
- `FormDataHandler.gs`

### Step 3: Set Up Triggers

1. Click "Triggers" (clock icon, left sidebar)
2. Click "+ Add Trigger"

**For Lee County**:
- Function: `runLeeCountyScraper`
- Event source: Time-driven
- Type: Minutes timer
- Interval: Every 30 minutes

**For Collier County**:
- Function: `runCollierCountyScraper`
- Event source: Time-driven
- Type: Minutes timer
- Interval: Every 30 minutes

### Step 4: Deploy Web App (for Bookmarklet)

1. Click "Deploy" → "New deployment"
2. Type: Web app
3. Description: "Booking Form"
4. Execute as: Me
5. Who has access: Anyone
6. Click "Deploy"
7. Copy deployment ID from URL

### Step 5: Update Bookmarklet

Replace `YOUR_DEPLOYMENT_ID` in `UniversalBookmarklet.js` with actual deployment ID.

### Step 6: Test

1. Open Google Sheets
2. Reload page (Ctrl+R)
3. Check "🟩 Bail Suite" menu appears
4. Test "Run Lee County Scraper"
5. Test "Open Booking Form"

---

## Rollback Procedures

### GitHub Actions Rollback

```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Or reset to specific commit
git reset --hard <commit-hash>
git push --force origin main
```

### Apps Script Rollback

1. Go to Apps Script project
2. Click "Executions" (left sidebar)
3. Find last successful version
4. Click "..." → "View version"
5. Click "Restore this version"

### Google Sheets Rollback

1. Go to Google Sheets
2. File → Version history → See version history
3. Find version before issue
4. Click "Restore this version"

---

## Monitoring

### GitHub Actions

**View Workflow Runs**:
https://github.com/Shamrock2245/swfl-arrest-scrapers/actions

**Check Logs**:
1. Click on workflow run
2. Click on "scrape" job
3. Expand steps to see detailed logs

**Download Artifacts**:
- Failed runs upload logs as artifacts
- Retention: 7-14 days
- Download from workflow run page

### Google Sheets

**Ingestion_Log Tab**:
- Timestamp: When scraper ran
- County: Which county
- Status: SUCCESS/FAILURE
- Records: How many records processed
- Error: Error message (if failed)

**Data Validation**:
- Check for duplicate Booking_Numbers
- Verify Lead_Score and Lead_Status populated
- Look for missing required fields

### Apps Script

**Execution Logs**:
1. Open Apps Script project
2. View → Logs (Ctrl+Enter)
3. See console.log() output

**Trigger History**:
1. Click "Executions" (left sidebar)
2. See all trigger runs
3. Filter by status (success/failure)

---

## Scaling

### Increase Scraping Frequency

Edit `.github/workflows/scrape-[county].yml`:

```yaml
on:
  schedule:
    - cron: '*/10 * * * *'  # Change from */20 to */10 (every 10 min)
```

### Add More Counties

1. Create scraper: `/scrapers/[county]_stealth.js`
2. Create workflow: `/.github/workflows/scrape-[county].yml`
3. Add sheet tab: `[County]` in Google Sheets
4. Update documentation

### Upgrade GitHub Plan

**Free Tier**:
- 2,000 minutes/month
- 20 concurrent jobs

**Pro Tier** ($4/month):
- 3,000 minutes/month
- 5 concurrent jobs

**Team Tier** ($4/user/month):
- 10,000 minutes/month
- 60 concurrent jobs

### Self-Hosted Runner

```bash
# On your server
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
./config.sh --url https://github.com/Shamrock2245/swfl-arrest-scrapers --token <TOKEN>
./run.sh
```

Update workflows to use self-hosted runner:

```yaml
jobs:
  scrape:
    runs-on: self-hosted  # Instead of ubuntu-latest
```

---

## Troubleshooting Deployment

### Issue: GitHub Actions not running

**Check**:
1. Workflows enabled? (Actions tab)
2. Secrets configured? (Settings → Secrets)
3. Syntax errors in YAML? (Check logs)

**Solution**:
```bash
# Test workflow locally with act
npm install -g act
act -l  # List workflows
act -j scrape  # Run specific job
```

### Issue: Service account permission denied

**Check**:
1. Sheet shared with service account email?
2. Service account has Editor permission?
3. Sheets API enabled in Google Cloud?

**Solution**:
1. Open Google Sheet
2. Click "Share"
3. Add service account email
4. Set permission to "Editor"

### Issue: Scraper fails with "Socket hang up"

**Check**:
1. County website blocking GitHub IPs?
2. Stealth plugin enabled?
3. Delays configured?

**Solution**:
- Increase delays in scraper
- Try self-hosted runner (different IP)
- Contact county IT (if persistent)

---

## Security Checklist

- [ ] `.env` file in `.gitignore`
- [ ] Service account JSON not committed
- [ ] GitHub secrets configured
- [ ] Google Sheet shared only with service account
- [ ] Apps Script deployment ID not public
- [ ] Repository is private
- [ ] No hardcoded credentials in code
- [ ] Logs don't expose sensitive data

---

## Deployment Checklist

### Before Deployment

- [ ] Code tested locally
- [ ] All tests pass (when implemented)
- [ ] Documentation updated
- [ ] Secrets configured
- [ ] Service account permissions verified
- [ ] GitHub Actions workflows reviewed
- [ ] Rollback plan ready

### After Deployment

- [ ] Manual workflow test successful
- [ ] Data appearing in Google Sheets
- [ ] Ingestion_Log shows SUCCESS
- [ ] No errors in GitHub Actions logs
- [ ] Lead scoring working
- [ ] Automated workflows running on schedule
- [ ] Monitoring set up

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture
- **DEVELOPMENT.md** - Development guidelines
- **SCRAPING_RULES.md** - Scraping best practices
- **TROUBLESHOOTING.md** - Common issues
- **SECURITY.md** - Security guidelines

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
