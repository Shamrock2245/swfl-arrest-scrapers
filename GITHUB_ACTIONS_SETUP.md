# GitHub Actions Setup Guide

This guide walks you through setting up automated arrest scraping that runs every 20-30 minutes.

## Overview

Two workflow files have been created:

1. **`scrape-arrests.yml`** - Runs every 20 minutes (3x per hour) with parallel execution
2. **`scrape-arrests-30min.yml`** - Runs every 30 minutes (2x per hour) with sequential execution

**Recommendation:** Start with the **30-minute workflow** to avoid rate limits and reduce GitHub Actions usage. You can switch to 20 minutes later if needed.

---

## Step 1: Push Workflow Files to GitHub

The workflow files are already created in `.github/workflows/`. You need to commit and push them:

```bash
cd /home/ubuntu/swfl-arrest-scrapers

# Stage the workflow files
git add .github/workflows/scrape-arrests.yml
git add .github/workflows/scrape-arrests-30min.yml
git add GITHUB_ACTIONS_SETUP.md

# Commit
git commit -m "Add GitHub Actions workflows for automated scraping every 20-30 minutes"

# Push to GitHub
git push origin main
```

---

## Step 2: Configure GitHub Repository Secrets

GitHub Actions needs access to your Google Sheets via the service account. You must add these secrets to your repository.

### 2.1 Navigate to Repository Settings

1. Go to https://github.com/shamrock2245/swfl-arrest-scrapers
2. Click **Settings** (top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**

### 2.2 Add Required Secrets

Add the following three secrets:

#### Secret 1: `GOOGLE_SERVICE_ACCOUNT_EMAIL`

- **Name:** `GOOGLE_SERVICE_ACCOUNT_EMAIL`
- **Value:** `shamrock-mcp-bot@shamrock-mcp-automation.iam.gserviceaccount.com`

#### Secret 2: `GOOGLE_SERVICE_ACCOUNT_KEY`

- **Name:** `GOOGLE_SERVICE_ACCOUNT_KEY`
- **Value:** Copy the **entire contents** of `creds/service-account-key.json`

**Important:** Copy the entire JSON object from your local `creds/service-account-key.json` file, including the curly braces. The file should contain your Google Cloud service account credentials with the private key.

#### Secret 3: `GOOGLE_SHEET_ID`

- **Name:** `GOOGLE_SHEET_ID`
- **Value:** `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`

---

## Step 3: Choose Which Workflow to Enable

You have two options:

### Option A: 30-Minute Intervals (Recommended)

**File:** `.github/workflows/scrape-arrests-30min.yml`

**Pros:**
- Lower GitHub Actions usage (48 runs per day)
- Runs all scrapers sequentially in one job
- Simpler to monitor
- Less likely to hit rate limits

**Cons:**
- Slightly slower to detect new arrests (30 min vs 20 min)

**To enable:** This workflow is already enabled by default.

### Option B: 20-Minute Intervals

**File:** `.github/workflows/scrape-arrests.yml`

**Pros:**
- Faster detection of new arrests (20 min intervals)
- Parallel execution (all counties scrape simultaneously)

**Cons:**
- Higher GitHub Actions usage (72 runs per day)
- More complex (4 parallel jobs)
- May hit rate limits more frequently

**To enable:** Rename or delete `scrape-arrests-30min.yml` to use this workflow exclusively.

### Option C: Disable One Workflow

If you want to use only one workflow, you can disable the other by:

1. Renaming the file to add `.disabled` (e.g., `scrape-arrests.yml.disabled`)
2. Or deleting the file entirely

---

## Step 4: Test the Workflow Manually

Before waiting for the scheduled run, test the workflow manually:

1. Go to https://github.com/shamrock2245/swfl-arrest-scrapers/actions
2. Click on **"Scrape Arrests - Every 30 Minutes"** (or 20 minutes)
3. Click **"Run workflow"** (right side)
4. Click the green **"Run workflow"** button
5. Wait for the workflow to complete (~5-10 minutes)

### What to Look For

- ✅ All jobs should turn green (success)
- 📊 Check the logs for scraper output
- 📋 Verify data appears in Google Sheets

### If the Workflow Fails

1. Click on the failed job
2. Expand the failed step to see error logs
3. Common issues:
   - **Missing secrets:** Double-check all three secrets are added correctly
   - **Service account permissions:** Ensure the service account has access to the Google Sheet
   - **Scraper errors:** Individual scrapers may fail due to website changes

---

## Step 5: Monitor Workflow Runs

### View Workflow History

- Go to https://github.com/shamrock2245/swfl-arrest-scrapers/actions
- You'll see all workflow runs (scheduled and manual)
- Green checkmark = success, Red X = failure

### Download Logs on Failure

If a scraper fails, GitHub Actions automatically uploads logs and screenshots:

1. Click on the failed workflow run
2. Scroll to **Artifacts** section at the bottom
3. Download the log files for debugging

### Email Notifications

GitHub will email you when workflows fail. To configure:

1. Go to https://github.com/settings/notifications
2. Under **Actions**, enable **"Send notifications for failed workflows"**

---

## Step 6: Adjust Frequency (Optional)

If you want to change the scraping frequency:

### Edit the Cron Schedule

Open `.github/workflows/scrape-arrests-30min.yml` and find this line:

```yaml
- cron: '*/30 * * * *'
```

**Common intervals:**
- Every 15 minutes: `*/15 * * * *`
- Every 20 minutes: `*/20 * * * *`
- Every 30 minutes: `*/30 * * * *`
- Every hour: `0 * * * *`

**Important:** GitHub Actions has a minimum interval of 5 minutes, but frequent runs may be throttled.

---

## Step 7: GitHub Actions Usage Limits

### Free Tier Limits

GitHub provides **2,000 minutes per month** for free on public repositories. Private repositories have different limits.

### Estimated Usage

**30-minute workflow:**
- 48 runs per day × 10 minutes per run = 480 minutes/day
- 480 × 30 days = **14,400 minutes/month**

**20-minute workflow:**
- 72 runs per day × 10 minutes per run = 720 minutes/day
- 720 × 30 days = **21,600 minutes/month**

**Recommendation:** If you exceed the free tier, consider:
1. Running less frequently (every hour)
2. Upgrading to GitHub Pro ($4/month for 3,000 minutes)
3. Self-hosting a runner on your own server (unlimited)

---

## Troubleshooting

### Workflow Not Running on Schedule

- **Wait 10-15 minutes:** GitHub Actions can have delays
- **Check workflow syntax:** Use https://crontab.guru to validate cron expressions
- **Repository activity:** GitHub may disable workflows on inactive repositories

### Scrapers Failing

- **Website changes:** County websites may have changed structure
- **CAPTCHA:** Some counties may have added CAPTCHA protection
- **Rate limiting:** Too many requests may trigger blocks

### Google Sheets Not Updating

- **Service account permissions:** Ensure the service account has "Editor" access to the sheet
- **Sheet ID:** Verify the `GOOGLE_SHEET_ID` secret is correct
- **API quotas:** Google Sheets API has rate limits (100 requests per 100 seconds)

---

## Next Steps

1. ✅ Push workflow files to GitHub
2. ✅ Add GitHub secrets
3. ✅ Test workflow manually
4. ✅ Monitor first scheduled run
5. ✅ Verify data in Google Sheets
6. ✅ Adjust frequency if needed

---

## Summary

You now have automated arrest scraping running every 20-30 minutes! The system will:

- ✅ Scrape Collier, Hendry, Lee, and DeSoto counties
- ✅ Update Google Sheets automatically
- ✅ Run 24/7 without manual intervention
- ✅ Send email notifications on failures
- ✅ Store logs for debugging

**For immediate prospecting:** Data will be available within 20-30 minutes of a booking occurring at the county jail.

---

*Last updated: November 21, 2025*
