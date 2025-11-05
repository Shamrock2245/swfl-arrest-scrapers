# Deployment Guide

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
