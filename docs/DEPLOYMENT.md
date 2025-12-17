# Deployment Guide

This guide provides up‑to‑date instructions for deploying the **SWFL Arrest Scrapers** suite in production, including local cron, GitHub Actions, and Cloud Run options. All scrapers write to a single master Google Sheet, which also serves as the source of truth for downstream integrations.

## Master Google Sheet
All data is stored in the sheet identified by:
https://docs.google.com/spreadsheets/d/10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY/edit

The sheet contains tabs for each county, a `Qualified_Arrests` tab (records with `Lead_Score ≥ 70`), a `Logs` tab, and a `Manual_Bookings` tab used by the Google Apps Script form.

---

## Prerequisites
- **Node.js** 18+ and **Python 3.10+** (for the Palm Beach runner)
- **Google Cloud project** with the Sheets API enabled
- **Service account** with Editor access to the master sheet
- **Git** and optional **Docker** for container deployments
- **Slack webhook** (optional) for notifications

---

## Local Development & Cron
1. Clone and install dependencies:
```bash
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
npm ci   # Node deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r python_scrapers/requirements.txt
```
2. Create a `.env` file (copy from `.env.example`) and set:
```
GOOGLE_SHEETS_ID=10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY
GOOGLE_SERVICE_ACCOUNT_JSON=...   # Base64 or raw JSON
SLACK_WEBHOOK_URL=…
TZ=America/New_York
```
3. Test a single county:
```bash
npm run run:sarasota:v2   # Node scraper
python3 python_scrapers/scrapers/run_palm_beach.py   # Python scraper
```
4. Add a cron entry (run every 15 min) to execute all counties:
```cron
*/15 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/runAll.js >> logs/cron.log 2>&1
7,22,37,52 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/updateBondPaid.js >> logs/bonds.log 2>&1
```

---

## GitHub Actions Deployment
The repository includes a workflow per county (`.github/workflows/scrape_*.yml`). To enable them:
1. Fork the repo and enable Actions.
2. Add the following **secrets** in the repository settings:
| Secret | Value |
|--------|-------|
| `GOOGLE_SHEETS_ID` | `10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY` |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com` |
| `GOOGLE_SA_KEY_JSON` | Full JSON of the service‑account key (or Base64‑encoded) |
| `SLACK_WEBHOOK_URL` | (optional) Slack webhook URL |
3. Push any change to `main`; the workflows will run on the schedule defined in each file and can be triggered manually via the **Actions** tab.

---

## Cloud Run (Container) Deployment
A Dockerfile is provided for a lightweight Node.js image. The container runs the `runAll.js` job on a schedule using Cloud Scheduler.
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
CMD ["node", "jobs/runAll.js"]
```
Deploy with:
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/swfl-scrapers
# Create scheduled job
gcloud run jobs create swfl-scrapers \
  --image gcr.io/PROJECT_ID/swfl-scrapers \
  --schedule "*/15 * * * *" \
  --set-env-vars "GOOGLE_SHEETS_ID=10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY" \
  --service-account=bail-suite-sa@PROJECT_ID.iam.gserviceaccount.com
```

---

## Google Apps Script (GAS) Integration
The `apps_script/Form.html` UI allows operators to manually add bookings. The accompanying Apps Script (`Code.gs`) writes rows to the **Manual_Bookings** tab and triggers the same scoring logic used by the scrapers. Deploy the script by opening the project URL (see README) and publishing it as a **Web App** with **Anyone** access.

---

## SignNow Integration (Future Roadmap)
Qualified leads (score ≥ 70) will be automatically sent to SignNow for contract generation:
1. A background job will query the `Qualified_Arrests` tab.
2. For each new qualified row, the job will call the SignNow API (via the `integrations/signnow.py` wrapper) to create a document from a template.
3. The generated PDF URL is stored in a new `packet_url` column, and the sheet is updated with `packet_status` = `sent`.
4. A SOCKS5 proxy can be configured in `integrations/signnow.py` to reach external risk databases (TLOx, TransUnion, iDiCore) before sending the packet.

---

## Monitoring & Alerts
- **Logs tab** in the master sheet records each run (timestamp, county, rows added/updated, errors).
- **Slack** notifications are sent for run completion, errors, and when a qualified lead is added.
- Health‑check script (`scripts/check-health.sh`) can be scheduled to alert if cron or Cloud Run jobs have not run within the expected window.

---

## Security Best Practices
- Never commit the service‑account JSON; use environment variables or GitHub Secrets.
- Rotate service‑account keys quarterly.
- Restrict the service‑account to **Editor** on the master sheet only.
- Enable 2FA on the Google Cloud account.

---

## Support
- **GitHub Issues**: https://github.com/shamrock2245/swfl-arrest-scrapers/issues
- **Email**: support@shamrockbailbonds.com
- **Slack**: #bail‑suite‑dev (invite via admin)

---

*Generated by Antigravity AI assistant.*

This guide provides up‑to‑date instructions for deploying the **SWFL Arrest Scrapers** suite in production, including local cron, GitHub Actions, and Cloud Run options. All scrapers write to a single master Google Sheet, which also serves as the source of truth for downstream integrations.

## Master Google Sheet
All data is stored in the sheet identified by:
https://docs.google.com/spreadsheets/d/10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY/edit

The sheet contains tabs for each county, a `Qualified_Arrests` tab (records with `Lead_Score ≥ 70`), a `Logs` tab, and a `Manual_Bookings` tab used by the Google Apps Script form.

---

## Prerequisites
- **Node.js** 18+ and **Python 3.10+** (for the Palm Beach runner)
- **Google Cloud project** with the Sheets API enabled
- **Service account** with Editor access to the master sheet
- **Git** and optional **Docker** for container deployments
- **Slack webhook** (optional) for notifications

---

## Local Development & Cron
1. Clone and install dependencies:
```bash
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
npm ci   # Node deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r python_scrapers/requirements.txt
```
2. Create a `.env` file (copy from `.env.example`) and set:
```
GOOGLE_SHEETS_ID=10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY
GOOGLE_SERVICE_ACCOUNT_JSON=...   # Base64 or raw JSON
SLACK_WEBHOOK_URL=…
TZ=America/New_York
```
3. Test a single county:
```bash
npm run run:sarasota:v2   # Node scraper
python3 python_scrapers/scrapers/run_palm_beach.py   # Python scraper
```
4. Add a cron entry (run every 15 min) to execute all counties:
```cron
*/15 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/runAll.js >> logs/cron.log 2>&1
7,22,37,52 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/updateBondPaid.js >> logs/bonds.log 2>&1
```

---

## GitHub Actions Deployment
The repository includes a workflow per county (`.github/workflows/scrape_*.yml`). To enable them:
1. Fork the repo and enable Actions.
2. Add the following **secrets** in the repository settings:
| Secret | Value |
|--------|-------|
| `GOOGLE_SHEETS_ID` | `10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY` |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com` |
| `GOOGLE_SA_KEY_JSON` | Full JSON of the service‑account key (or Base64‑encoded) |
| `SLACK_WEBHOOK_URL` | (optional) Slack webhook URL |
3. Push any change to `main`; the workflows will run on the schedule defined in each file and can be triggered manually via the **Actions** tab.

---

## Cloud Run (Container) Deployment
A Dockerfile is provided for a lightweight Node.js image. The container runs the `runAll.js` job on a schedule using Cloud Scheduler.
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
CMD ["node", "jobs/runAll.js"]
```
Deploy with:
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/swfl-scrapers
# Create scheduled job
gcloud run jobs create swfl-scrapers \
  --image gcr.io/PROJECT_ID/swfl-scrapers \
  --schedule "*/15 * * * *" \
  --set-env-vars "GOOGLE_SHEETS_ID=10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY" \
  --service-account=bail-suite-sa@PROJECT_ID.iam.gserviceaccount.com
```

---

## Google Apps Script (GAS) Integration
The `apps_script/Form.html` UI allows operators to manually add bookings. The accompanying Apps Script (`Code.gs`) writes rows to the **Manual_Bookings** tab and triggers the same scoring logic used by the scrapers. Deploy the script by opening the project URL (see README) and publishing it as a **Web App** with **Anyone** access.

---

## SignNow Integration (Future Roadmap)
Qualified leads (score ≥ 70) will be automatically sent to SignNow for contract generation:
1. A background job will query the `Qualified_Arrests` tab.
2. For each new qualified row, the job will call the SignNow API (via the `integrations/signnow.py` wrapper) to create a document from a template.
3. The generated PDF URL is stored in a new `packet_url` column, and the sheet is updated with `packet_status` = `sent`.
4. A SOCKS5 proxy can be configured in `integrations/signnow.py` to reach external risk databases (TLOx, TransUnion, iDiCore) before sending the packet.

---

## Monitoring & Alerts
- **Logs tab** in the master sheet records each run (timestamp, county, rows added/updated, errors).
- **Slack** notifications are sent for run completion, errors, and when a qualified lead is added.
- Health‑check script (`scripts/check-health.sh`) can be scheduled to alert if cron or Cloud Run jobs have not run within the expected window.

---

## Security Best Practices
- Never commit the service‑account JSON; use environment variables or GitHub Secrets.
- Rotate service‑account keys quarterly.
- Restrict the service‑account to **Editor** on the master sheet only.
- Enable 2FA on the Google Cloud account.

---

## Support
- **GitHub Issues**: https://github.com/shamrock2245/swfl-arrest-scrapers/issues
- **Email**: support@shamrockbailbonds.com
- **Slack**: #bail‑suite‑dev (invite via admin)

---

*Generated by Antigravity AI assistant.*

Complete deployment instructions for production use.

## Prerequisites

- Node.js 18+ installed
- Google Cloud project with Sheets API enabled
- Google service account with Sheets access
- Git configured
- (Optional) GitHub repository access
- (Optional) Slack webhook for notifications

## Local Deployment

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers

# Install dependencies
npm install

# Create credentials directory
mkdir -p creds

# Copy environment template
cp .env.example .env
```

### 2. Configure Google Sheets Access

#### Create Service Account (if not exists)
```bash
# In Google Cloud Console:
# 1. IAM & Admin → Service Accounts
# 2. Create Service Account
# 3. Name: bail-suite-sa
# 4. Grant role: None (we'll use sheet-level permissions)
# 5. Create Key → JSON
# 6. Save as creds/service-account-key.json
```

#### Share Spreadsheet
```
Email: bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com
Permission: Editor
Spreadsheet: 1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc
```

### 3. Test Run

```bash
# Test single county
npm run run:collier

# Check Google Sheets for new data in:
# Tab: collier-county-arrests
```

### 4. Schedule with Cron

```bash
# Edit crontab
crontab -e

# Add these lines:

# Run all counties every 15 minutes
*/15 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/runAll.js >> logs/cron.log 2>&1

# Update bond status (offset by 7 minutes)
7,22,37,52 * * * * cd /path/to/swfl-arrest-scrapers && /usr/local/bin/node jobs/updateBondPaid.js >> logs/bonds.log 2>&1

# Save and exit
```

### 5. Monitor Logs

```bash
# Watch cron logs
tail -f logs/cron.log

# Check for errors
grep "❌\|Error" logs/cron.log
```

## GitHub Actions Deployment

### 1. Fork Repository

```bash
# Fork on GitHub: shamrock2245/swfl-arrest-scrapers
# Clone your fork
git clone https://github.com/YOUR_USERNAME/swfl-arrest-scrapers.git
```

### 2. Configure Secrets

In GitHub repository settings → Secrets and variables → Actions:

**Add these secrets:**

| Secret Name | Value |
|-------------|-------|
| `GOOGLE_SHEETS_ID` | `1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc` |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com` |
| `GOOGLE_SA_KEY_JSON` | Full JSON content of service account key |
| `SLACK_WEBHOOK_URL` | (Optional) Slack webhook URL |

### 3. Enable Workflow

```bash
# Push changes to enable workflow
git add .github/workflows/scrape.yml
git commit -m "Enable GitHub Actions workflow"
git push origin main
```

Workflow runs automatically:
- Every 15 minutes (scheduled)
- Manually via Actions tab

### 4. Monitor GitHub Actions

1. Go to Actions tab in repository
2. View workflow runs
3. Check logs for errors
4. Manually trigger if needed

## Cloud Deployment Options

### Option A: DigitalOcean Droplet

```bash
# Create Ubuntu 22.04 droplet
# SSH into droplet

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone and setup
cd /opt
sudo git clone https://github.com/shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers
sudo npm install

# Setup credentials
sudo mkdir creds
# Upload service-account-key.json via SCP

# Copy environment
sudo cp .env.example .env
sudo nano .env  # Edit values

# Add to cron
sudo crontab -e
# Add cron lines from above
```

### Option B: AWS EC2

Similar to DigitalOcean, but use Amazon Linux 2:

```bash
# Update system
sudo yum update -y

# Install Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Continue with clone and setup...
```

### Option C: Google Cloud Run

Deploy as a scheduled Cloud Run job:

```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
CMD ["node", "jobs/runAll.js"]
```

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/swfl-scrapers
gcloud run jobs create swfl-scrapers \
  --image gcr.io/PROJECT_ID/swfl-scrapers \
  --schedule="*/15 * * * *" \
  --set-env-vars="GOOGLE_SHEETS_ID=..." \
  --service-account=bail-suite-sa@PROJECT_ID.iam.gserviceaccount.com
```

## Monitoring & Alerts

### Check Ingestion Log

View the `ingestion_log` tab in Google Sheets:
- Timestamp of each run
- County
- Success/failure status
- Record count
- Duration
- Error messages

### Slack Notifications (Optional)

```bash
# Add to .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Notifications will be sent for:
# - Run completion
# - Errors
# - Qualified arrests (optional)
```

### Health Checks

Create a simple health check script:

```bash
#!/bin/bash
# check-health.sh

LAST_RUN=$(tail -n 1 /path/to/swfl-arrest-scrapers/logs/cron.log)
AGE_MINUTES=$(( ($(date +%s) - $(date -r /path/to/swfl-arrest-scrapers/logs/cron.log +%s)) / 60 ))

if [ $AGE_MINUTES -gt 30 ]; then
  echo "WARNING: Last run was $AGE_MINUTES minutes ago"
  # Send alert (email, Slack, etc.)
fi
```

## Maintenance

### Update Scrapers

```bash
cd /path/to/swfl-arrest-scrapers
git pull origin main
npm install
# Restart cron jobs automatically pick up changes
```

### Rotate Credentials

```bash
# 1. Create new service account key in Google Cloud Console
# 2. Download new key
# 3. Replace creds/service-account-key.json
# 4. Update GitHub secrets if using Actions
# 5. Delete old key from Google Cloud Console
```

### Handle Site Changes

When a county website changes:

1. Save new HTML fixtures:
```bash
# Visit site in browser
# Save page as HTML
# Move to fixtures/COUNTY/
```

2. Update selectors in scraper:
```javascript
// scrapers/collier.js
// Adjust CSS selectors in parseListPage() and extractDetailPairs()
```

3. Test locally:
```bash
npm run run:collier
```

4. Commit and push changes

## Troubleshooting

### No Data Being Scraped

- Check if county website is accessible
- Verify selectors haven't changed
- Check logs for CAPTCHA detection
- Test manually: `node scrapers/COUNTY.js`

### Permission Errors

- Verify service account has Editor access to sheet
- Check credentials file path in .env
- Ensure .env is loaded (not .env.example)

### Rate Limiting

- Increase `REQUEST_DELAY_MS` in .env
- Reduce concurrent requests
- Add more jitter/randomization

### Cloudflare Blocking (Charlotte)

- May require manual cookie extraction
- Save browser cookies after solving challenge
- Inject cookies in browser.js
- Consider using proxy service

## Performance Optimization

### Reduce Execution Time

- Run counties in parallel: `node jobs/runAll.js --parallel`
- Limit detail pages per county (adjust in county config)
- Cache mugshot URLs instead of re-downloading

### Reduce API Calls

- Only update bond_paid for records with source_url
- Skip weekends if arrests are low
- Adjust DAYS_BACK in config to fetch fewer days

## Security Best Practices

✅ Never commit credentials to git
✅ Rotate service account keys quarterly
✅ Use secrets management (GitHub Secrets, AWS Secrets Manager)
✅ Limit service account permissions to specific sheet
✅ Enable 2FA on Google Cloud account
✅ Monitor access logs
✅ Use environment variables for all sensitive data

## Support

- GitHub Issues: https://github.com/shamrock2245/swfl-arrest-scrapers/issues
- Email: support@shamrockbailbonds.com
