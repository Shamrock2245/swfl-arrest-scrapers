# SWFL Arrest Scrapers - Troubleshooting Guide

## Common Issues & Solutions

---

## GitHub Actions Issues

### Issue: Workflow not running

**Symptoms**:
- Workflow doesn't appear in Actions tab
- Scheduled runs not happening

**Possible Causes**:
1. Workflows disabled in repository settings
2. YAML syntax error
3. Repository is private and no Actions minutes available

**Solutions**:

```bash
# 1. Check workflow syntax
cd /path/to/swfl-arrest-scrapers
cat .github/workflows/scrape-hillsborough.yml | grep -E "^on:|schedule:|cron:"

# 2. Enable workflows
# Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/settings/actions
# Select "Allow all actions and reusable workflows"

# 3. Check Actions minutes
# Go to: https://github.com/settings/billing
# Verify you have Actions minutes remaining
```

---

### Issue: `npm ci` fails with "package-lock.json not found"

**Symptoms**:
```
Error: The `npm ci` command can only install with an existing package-lock.json
```

**Cause**: Workflow uses `npm ci` but package-lock.json is not in repository

**Solution**:

Change workflow file from:
```yaml
- run: npm ci
```

To:
```yaml
- run: npm install
```

**Files to update**:
- `.github/workflows/scrape-all-manual.yml`
- `.github/workflows/scrape-hillsborough.yml`
- `.github/workflows/scrape-manatee.yml`
- `.github/workflows/scrape-sarasota.yml`
- `.github/workflows/scrape-charlotte.yml`
- `.github/workflows/scrape-hendry.yml`

---

### Issue: Secrets not found

**Symptoms**:
```
Error: GOOGLE_SA_KEY_JSON is not set
Error: Cannot read property 'client_email' of undefined
```

**Cause**: GitHub secrets not configured

**Solution**:

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
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "arrest-scraper@project.iam.gserviceaccount.com",
  ...
}
```

3. Verify in workflow logs:
```yaml
- name: Debug environment
  run: |
    echo "GOOGLE_SHEETS_ID is set: ${{ secrets.GOOGLE_SHEETS_ID != '' }}"
    echo "GOOGLE_SA_KEY_JSON is set: ${{ secrets.GOOGLE_SA_KEY_JSON != '' }}"
```

---

### Issue: Workflow timeout

**Symptoms**:
```
Error: The job running on runner GitHub Actions X has exceeded the maximum execution time of 15 minutes.
```

**Cause**: Scraper taking too long (usually due to website slowness or CAPTCHA)

**Solution**:

1. **Increase timeout** in workflow file:
```yaml
jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # Increase from 15 to 30
```

2. **Optimize scraper**:
```javascript
// Reduce wait time
await page.goto(url, { waitUntil: 'domcontentloaded' });  // Instead of 'networkidle2'

// Skip unnecessary delays
await delay(500);  // Instead of 1000+
```

3. **Split into smaller jobs**:
```yaml
# Instead of scraping all at once, split by date range
- run: node scrapers/hendry_stealth.js --days=1
```

---

## Scraper Issues

### Issue: CAPTCHA detected

**Symptoms**:
```
⚠️  CAPTCHA detected, aborting...
Error: CAPTCHA challenge encountered
```

**Cause**: County website has CAPTCHA protection

**Solution**:

1. **Verify stealth plugin enabled**:
```javascript
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());  // ✅ Must be before launch()
```

2. **Use headful mode**:
```javascript
const browser = await puppeteer.launch({
  headless: false,  // ✅ Less detectable
});
```

3. **Add random delays**:
```javascript
await delay(800 + Math.random() * 600);  // Random 800-1400ms
```

4. **Try different User-Agent**:
```javascript
await page.setUserAgent(
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
);
```

5. **Manual intervention** (last resort):
```javascript
// Pause for manual CAPTCHA solving
console.log('⚠️  CAPTCHA detected. Please solve manually...');
await delay(60000);  // Wait 60 seconds
```

---

### Issue: Cloudflare challenge

**Symptoms**:
```
⚠️  Cloudflare challenge detected, waiting...
Page title: "Just a moment..."
```

**Cause**: Cloudflare protection on county website

**Solution**:

1. **Wait for challenge to complete**:
```javascript
const hasCloudflare = await page.evaluate(() => {
  return document.title.includes('Just a moment');
});

if (hasCloudflare) {
  console.warn('⚠️  Cloudflare challenge detected, waiting...');
  await delay(5000);  // Wait 5 seconds
  await page.waitForNavigation({ waitUntil: 'networkidle2' });
}
```

2. **Use stealth plugin** (should bypass most challenges):
```javascript
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
puppeteer.use(StealthPlugin());
```

3. **Try self-hosted runner** (different IP):
```yaml
jobs:
  scrape:
    runs-on: self-hosted  # Instead of ubuntu-latest
```

---

### Issue: Socket hang up

**Symptoms**:
```
Error: socket hang up
Error: net::ERR_CONNECTION_RESET
```

**Cause**: County website blocking requests or network issue

**Solution**:

1. **Add retry logic**:
```javascript
async function gotoWithRetry(page, url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      return;
    } catch (error) {
      if (i === retries - 1) throw error;
      console.warn(`⚠️  Retry ${i+1}/${retries}: ${error.message}`);
      await delay(5000);
    }
  }
}
```

2. **Increase timeout**:
```javascript
await page.goto(url, {
  waitUntil: 'networkidle2',
  timeout: 60000  // Increase from 30000 to 60000
});
```

3. **Use different waitUntil**:
```javascript
await page.goto(url, {
  waitUntil: 'domcontentloaded'  // Less strict than 'networkidle2'
});
```

---

### Issue: Element not found

**Symptoms**:
```
Error: No node found for selector: .booking-link
Error: Cannot read property 'textContent' of null
```

**Cause**: Website HTML structure changed or element not loaded

**Solution**:

1. **Wait for element**:
```javascript
await page.waitForSelector('.booking-link', { timeout: 10000 });
```

2. **Check if element exists**:
```javascript
const element = await page.$('.booking-link');
if (!element) {
  console.warn('⚠️  Element not found, skipping...');
  return;
}
```

3. **Use alternative selector**:
```javascript
// Try multiple selectors
const element = await page.$('.booking-link') ||
                await page.$('a[href*="booking"]') ||
                await page.$('td:nth-child(1) a');
```

4. **Inspect HTML** (debug mode):
```javascript
const html = await page.content();
console.log(html);  // Print entire page HTML
```

---

### Issue: Duplicate records

**Symptoms**:
- Same booking appears multiple times in Google Sheets
- Ingestion_Log shows "inserted" instead of "updated"

**Cause**: Deduplication logic not working

**Solution**:

1. **Verify Booking_Number is unique**:
```javascript
if (!record.Booking_Number || record.Booking_Number.trim() === '') {
  throw new Error('Booking_Number is required for deduplication');
}
```

2. **Check deduplication in sheets34.js**:
```javascript
// Find existing row by Booking_Number
const existingRow = existingData.findIndex(row => row[0] === record.Booking_Number);

if (existingRow !== -1) {
  // Update existing row
  await sheets.spreadsheets.values.update({
    spreadsheetId: GOOGLE_SHEETS_ID,
    range: `${sheetTab}!A${existingRow + 2}:AH${existingRow + 2}`,
    valueInputOption: 'USER_ENTERED',
    resource: { values: [rowData] }
  });
  updated++;
} else {
  // Insert new row
  await sheets.spreadsheets.values.append({
    spreadsheetId: GOOGLE_SHEETS_ID,
    range: `${sheetTab}!A:AH`,
    valueInputOption: 'USER_ENTERED',
    resource: { values: [rowData] }
  });
  inserted++;
}
```

3. **Manual cleanup**:
```
1. Open Google Sheets
2. Data → Remove duplicates
3. Select "Booking_Number" column
4. Click "Remove duplicates"
```

---

## Google Sheets Issues

### Issue: Permission denied

**Symptoms**:
```
Error: The caller does not have permission
Error: 403 Forbidden
```

**Cause**: Service account not shared with Google Sheet

**Solution**:

1. **Share sheet with service account**:
```
1. Open Google Sheet
2. Click "Share" button
3. Add service account email: arrest-scraper@project.iam.gserviceaccount.com
4. Set permission to "Editor"
5. Uncheck "Notify people"
6. Click "Share"
```

2. **Verify Sheets API enabled**:
```
1. Go to: https://console.cloud.google.com/apis/library
2. Search "Google Sheets API"
3. Click "Enable" if not already enabled
```

---

### Issue: Sheet tab not found

**Symptoms**:
```
Error: Unable to parse range: Hendry!A:AH
Error: Sheet not found
```

**Cause**: Sheet tab doesn't exist or name mismatch

**Solution**:

1. **Create missing tab**:
```
1. Open Google Sheet
2. Click "+" at bottom to add new sheet
3. Rename to exact county name (e.g., "Hendry")
4. Add header row with 34 column names
```

2. **Verify tab name in scraper**:
```javascript
const CONFIG = {
  sheetTab: 'Hendry',  // Must match exact tab name (case-sensitive)
};
```

---

### Issue: Lead scoring not working

**Symptoms**:
- Lead_Score column is empty
- Lead_Status column is empty

**Cause**: Apps Script not deployed or trigger not set up

**Solution**:

1. **Check Apps Script project**:
```
URL: https://script.google.com/u/0/home/projects/12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo/edit
```

2. **Verify LeadScoringSystem.gs exists**

3. **Run manual scoring**:
```
1. Open Google Sheets
2. Click "🟩 Bail Suite" menu
3. Click "Score All Sheets"
4. Wait for completion message
```

4. **Check trigger**:
```
1. Open Apps Script project
2. Click "Triggers" (clock icon)
3. Verify "scoreAllSheets" trigger exists
4. Frequency: Every 1 hour (or as desired)
```

---

## Local Development Issues

### Issue: Cannot find module

**Symptoms**:
```
Error: Cannot find module '../writers/sheets34.js'
Error: Cannot find module 'puppeteer-extra'
```

**Cause**: Missing dependencies or incorrect import path

**Solution**:

1. **Install dependencies**:
```bash
npm install
```

2. **Verify .js extension in imports**:
```javascript
// ✅ Correct (ES modules require .js)
import { writeToSheets } from '../writers/sheets34.js';

// ❌ Incorrect
import { writeToSheets } from '../writers/sheets34';
```

3. **Check package.json has type: "module"**:
```json
{
  "type": "module",
  ...
}
```

---

### Issue: GOOGLE_SA_KEY_JSON not set

**Symptoms**:
```
Error: GOOGLE_SA_KEY_JSON environment variable is not set
```

**Cause**: Missing .env file or environment variable

**Solution**:

1. **Create .env file**:
```bash
cat > .env << EOF
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
EOF
```

2. **Add service account JSON file**:
```bash
# Download from Google Cloud Console
# Save as service-account-key.json in project root
```

3. **Load dotenv in scraper**:
```javascript
import dotenv from 'dotenv';
dotenv.config();
```

---

### Issue: Browser doesn't launch

**Symptoms**:
```
Error: Failed to launch the browser process
Error: Could not find Chrome
```

**Cause**: Chrome/Chromium not installed

**Solution**:

**macOS**:
```bash
brew install --cask google-chrome
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y chromium-browser
```

**GitHub Actions**:
```yaml
- run: npx puppeteer browsers install chrome
```

---

## Data Quality Issues

### Issue: Missing fields

**Symptoms**:
- Many columns are empty
- Required fields like Full_Name are blank

**Cause**: Website structure changed or scraper logic incorrect

**Solution**:

1. **Inspect website HTML**:
```javascript
// Add debug logging
const html = await page.content();
console.log(html);

// Or save to file
const fs = require('fs');
fs.writeFileSync('debug.html', html);
```

2. **Update selectors**:
```javascript
// Old selector (may not work)
const name = await page.$eval('.inmate-name', el => el.textContent);

// New selector (updated)
const name = await page.$eval('td:nth-child(2)', el => el.textContent);
```

3. **Add fallbacks**:
```javascript
const name = await page.evaluate(() => {
  return document.querySelector('.inmate-name')?.textContent ||
         document.querySelector('td:nth-child(2)')?.textContent ||
         '';
});
```

---

### Issue: Incorrect date format

**Symptoms**:
- Dates appear as "Invalid Date"
- Dates in wrong format (YYYY-MM-DD instead of MM/DD/YYYY)

**Cause**: Date parsing logic incorrect

**Solution**:

```javascript
function parseDate(dateStr) {
  if (!dateStr) return '';
  
  // Handle MM/DD/YYYY
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
    return dateStr;
  }
  
  // Handle YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [year, month, day] = dateStr.split('-');
    return `${month}/${day}/${year}`;
  }
  
  // Handle "Nov 25, 2025"
  const date = new Date(dateStr);
  if (!isNaN(date)) {
    return date.toLocaleDateString('en-US');
  }
  
  return '';
}
```

---

## Performance Issues

### Issue: Scraper too slow

**Symptoms**:
- Takes 30+ minutes to scrape one county
- GitHub Actions timeout

**Cause**: Too many delays or inefficient logic

**Solution**:

1. **Reduce delays**:
```javascript
// Before
await delay(2000);

// After
await delay(800 + Math.random() * 400);
```

2. **Use faster waitUntil**:
```javascript
// Before
await page.goto(url, { waitUntil: 'networkidle2' });

// After
await page.goto(url, { waitUntil: 'domcontentloaded' });
```

3. **Limit records**:
```javascript
// Only scrape first 50 records (for testing)
const detailUrls = allUrls.slice(0, 50);
```

---

## Debugging Tips

### Enable verbose logging

```javascript
// Add to scraper
console.log('🔍 Debug:', {
  url: page.url(),
  title: await page.title(),
  html: await page.content()
});
```

### Take screenshots

```javascript
// Save screenshot for debugging
await page.screenshot({ path: 'debug.png', fullPage: true });
```

### Pause execution

```javascript
// Wait for manual inspection
console.log('⏸️  Paused for inspection...');
await delay(60000);  // 60 seconds
```

### Use browser DevTools

```javascript
// Launch with DevTools open
const browser = await puppeteer.launch({
  headless: false,
  devtools: true
});
```

---

## Getting Help

### Check logs

**GitHub Actions**:
```
1. Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/actions
2. Click on failed workflow run
3. Click on "scrape" job
4. Expand steps to see logs
```

**Apps Script**:
```
1. Open Apps Script project
2. View → Logs (Ctrl+Enter)
3. See console.log() output
```

**Local**:
```bash
# Run scraper and save output
node scrapers/hendry_stealth.js > debug.log 2>&1
cat debug.log
```

### Contact support

**Email**: admin@shamrockbailbonds.biz  
**GitHub Issues**: https://github.com/Shamrock2245/swfl-arrest-scrapers/issues

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture
- **DEVELOPMENT.md** - Development guidelines
- **DEPLOYMENT.md** - Deployment procedures
- **SCRAPING_RULES.md** - Scraping best practices
- **SCHEMA.md** - 34-column data schema
- **SECURITY.md** - Security guidelines

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
