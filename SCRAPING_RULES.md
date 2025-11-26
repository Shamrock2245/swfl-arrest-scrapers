# SWFL Arrest Scrapers - Scraping Rules & Best Practices

## Core Principles

### 1. **Stealth First**
Always use stealth mode to avoid detection and IP bans.

### 2. **Respect Rate Limits**
Don't overwhelm county websites with requests.

### 3. **Handle Errors Gracefully**
Expect failures and retry intelligently.

### 4. **Normalize Data**
Convert all county formats to standard 34-column schema.

### 5. **Log Everything**
Track all scraper runs for audit and debugging.

---

## Stealth Mode Requirements

### Puppeteer Stealth Plugin

**MUST USE** in all scrapers:

```javascript
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());
```

### Browser Configuration

```javascript
const browser = await puppeteer.launch({
  headless: false,  // ✅ Headful mode (less detectable)
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',  // Remove automation flags
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--disable-gpu'
  ]
});
```

### User-Agent Spoofing

```javascript
await page.setUserAgent(
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
);
```

### Viewport Randomization

```javascript
await page.setViewport({
  width: 1920 + Math.floor(Math.random() * 100),
  height: 1080 + Math.floor(Math.random() * 100)
});
```

---

## Rate Limiting

### Delays Between Requests

**Minimum**: 800ms  
**Jitter**: +600ms random

```javascript
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Between page navigations
await delay(800 + Math.random() * 600);

// Between clicks
await delay(500 + Math.random() * 300);
```

### Request Throttling

**Maximum concurrent requests**: 1 per scraper

```javascript
// ✅ Sequential (one at a time)
for (const url of detailUrls) {
  await page.goto(url);
  await delay(800 + Math.random() * 600);
}

// ❌ Parallel (too aggressive)
await Promise.all(detailUrls.map(url => page.goto(url)));
```

### Scraping Frequency

| County | Daily Arrests | Frequency | Justification |
|--------|---------------|-----------|---------------|
| Hillsborough | 100 | Every 20 min | High volume, time-sensitive |
| Manatee | 50 | Every 30 min | Moderate volume |
| Sarasota | 40 | Every 45 min | Moderate volume |
| Charlotte | 25 | Every hour | Low-moderate volume |
| Hendry | 8 | Every 2 hours | Low volume |

---

## Error Handling

### Try-Catch Blocks

**REQUIRED** around all async operations:

```javascript
try {
  const data = await scrapePage(url);
  await writeToSheets(data);
} catch (error) {
  console.error(`❌ Fatal error: ${error.message}`);
  await logIngestion(county, 'FAILURE', 0, error.message);
  process.exit(1);
}
```

### Timeout Handling

```javascript
try {
  await page.goto(url, {
    waitUntil: 'networkidle2',
    timeout: 30000  // 30 seconds
  });
} catch (error) {
  if (error.name === 'TimeoutError') {
    console.warn('⚠️  Page load timeout, retrying...');
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
  } else {
    throw error;
  }
}
```

### CAPTCHA Detection

```javascript
// Check for CAPTCHA
const hasCaptcha = await page.evaluate(() => {
  return document.body.innerText.includes('captcha') ||
         document.body.innerText.includes('CAPTCHA') ||
         document.querySelector('iframe[src*="recaptcha"]') !== null ||
         document.querySelector('.g-recaptcha') !== null;
});

if (hasCaptcha) {
  console.warn('⚠️  CAPTCHA detected, aborting...');
  throw new Error('CAPTCHA challenge encountered');
}
```

### Cloudflare Detection

```javascript
// Check for Cloudflare
const hasCloudflare = await page.evaluate(() => {
  return document.title.includes('Just a moment') ||
         document.body.innerText.includes('Checking your browser') ||
         document.querySelector('#challenge-running') !== null;
});

if (hasCloudflare) {
  console.warn('⚠️  Cloudflare challenge detected, waiting...');
  await delay(5000);  // Wait for challenge to complete
}
```

---

## Data Extraction

### Click-Through to Detail Pages

**REQUIRED** for counties with limited summary data:

```javascript
// Extract detail URLs from list page
const detailUrls = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('a.booking-link'))
    .map(a => a.href);
});

console.log(`📋 Found ${detailUrls.length} booking detail URLs`);

// Navigate to each detail page
const records = [];
for (let i = 0; i < detailUrls.length; i++) {
  console.log(`🔍 [${i+1}/${detailUrls.length}] Navigating to ${detailUrls[i]}`);
  
  await page.goto(detailUrls[i], { waitUntil: 'networkidle2' });
  await delay(800 + Math.random() * 600);
  
  const record = await extractDetailPage(page);
  records.push(record);
}
```

### Sorting by Date

**REQUIRED** to get most recent arrests first:

```javascript
// Click "Sort by Date (Newest - Oldest)"
await page.select('select#sort-order', 'date-desc');
await delay(1000);  // Wait for page to reload
```

### Date-Based Searching

**RECOMMENDED** for counties with search forms:

```javascript
// Fill in today's date
const today = new Date().toLocaleDateString('en-US', {
  month: '2-digit',
  day: '2-digit',
  year: 'numeric'
});

await page.type('input[name="booking_date"]', today);
await page.click('button[type="submit"]');
await page.waitForNavigation({ waitUntil: 'networkidle2' });
```

---

## Data Normalization

### Required Fields

**MUST** populate these fields (or empty string if not available):

```javascript
{
  Booking_Number: '',    // ✅ REQUIRED (primary key)
  Full_Name: '',         // ✅ REQUIRED
  County: '',            // ✅ REQUIRED
  Booking_Date: '',      // ✅ REQUIRED
  // ... other fields
}
```

### Field Parsing

**Name Parsing**:
```javascript
// Handle "LAST, FIRST MIDDLE"
const [lastName, firstMiddle] = fullName.split(',').map(s => s.trim());
const [firstName, ...middleParts] = firstMiddle.split(' ');

// Handle "FIRST MIDDLE LAST"
const parts = fullName.split(' ');
const firstName = parts[0];
const lastName = parts[parts.length - 1];
```

**Date Parsing**:
```javascript
// Handle various formats
const parseDate = (dateStr) => {
  // MM/DD/YYYY
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateStr)) {
    return dateStr;
  }
  
  // YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [year, month, day] = dateStr.split('-');
    return `${month}/${day}/${year}`;
  }
  
  // Nov 25, 2025
  const date = new Date(dateStr);
  if (!isNaN(date)) {
    return date.toLocaleDateString('en-US');
  }
  
  return '';
};
```

**Bond Amount Parsing**:
```javascript
// Remove $ and commas, convert to number
const parseBond = (bondStr) => {
  if (!bondStr) return '$0.00';
  
  const num = parseFloat(bondStr.replace(/[$,]/g, ''));
  return isNaN(num) ? '$0.00' : `$${num.toFixed(2)}`;
};
```

**Charge Parsing**:
```javascript
// Combine multiple charges
const charges = chargeArray.map(c => c.description).join('; ');

// Extract first charge
const charge1 = chargeArray[0]?.description || '';
const charge1Statute = chargeArray[0]?.statute || '';
const charge1Bond = chargeArray[0]?.bond || '$0.00';
```

---

## County-Specific Rules

### Hendry County

**Website**: https://www.hendrysheriff.org/inmateSearch

**Requirements**:
- Sort by "Date (Newest - Oldest)"
- Click "Read More" for each inmate
- Extract all charges (up to 10+)
- Calculate total bond from all charges
- Initial scrape: Last 30 days

**Unique Fields**:
- Custody Status: "IN" or "OUT"
- Multiple charges per booking

### Charlotte County

**Website**: https://inmates.charlottecountyfl.revize.com/bookings

**Requirements**:
- Revize platform (same as Manatee)
- Click booking number for details
- Stealth mode essential (Cloudflare protection)

**Unique Fields**:
- Booking number format: `202506681`

### Manatee County

**Website**: https://manatee-sheriff.revize.com/bookings

**Requirements**:
- Revize platform (same as Charlotte)
- Click booking number for details
- Stealth mode essential (Cloudflare protection)

**Unique Fields**:
- Booking number format: `2025010028`

### Sarasota County

**Website**: https://cms.revize.com/revize/apps/sarasota/index.php

**Requirements**:
- Embedded iframe
- Search by arrest date
- Click case number for details

**Unique Fields**:
- Case number format: `2025-CF-001234`

### Hillsborough County

**Website**: https://webapps.hcso.tampa.fl.us/arrestinquiry

**Requirements**:
- Fill form with today's date
- Check "Include Arrest Details"
- Sort by "Booking Date"
- Handle reCAPTCHA (stealth mode helps)

**Unique Fields**:
- Booking number format: `2025012345`

---

## Logging Requirements

### Console Logging

```javascript
// Start
console.log('🚀 Starting [County] County scraper...');

// Progress
console.log(`📋 Found ${count} booking detail URLs`);
console.log(`🔍 [${i+1}/${total}] Navigating to ${url}`);

// Success
console.log(`✅ ${county}: inserted ${inserted}, updated ${updated}`);

// Error
console.error(`❌ Fatal ${county} error: ${error.message}`);

// Warning
console.warn(`⚠️  ${county}: ${warning}`);
```

### Ingestion Logging

**REQUIRED** at end of every scraper run:

```javascript
import { logIngestion } from '../writers/sheets34.js';

// Success
await logIngestion(county, 'SUCCESS', recordCount);

// Failure
await logIngestion(county, 'FAILURE', 0, error.message);
```

---

## Testing Requirements

### Before Committing

- [ ] Test locally with `node scrapers/[county]_stealth.js`
- [ ] Verify data in Google Sheets
- [ ] Check Ingestion_Log for SUCCESS
- [ ] No duplicate records
- [ ] All 34 fields populated (or empty)
- [ ] Lead scoring works (if applicable)

### Before Deploying to GitHub Actions

- [ ] Test manual workflow
- [ ] Check logs for errors
- [ ] Verify scheduled workflow syntax
- [ ] Monitor first few automated runs

---

## Anti-Patterns (DO NOT DO)

### ❌ Parallel Requests
```javascript
// ❌ Too aggressive
await Promise.all(urls.map(url => page.goto(url)));
```

### ❌ No Delays
```javascript
// ❌ Will get blocked
for (const url of urls) {
  await page.goto(url);  // No delay!
}
```

### ❌ Headless Mode
```javascript
// ❌ More detectable
const browser = await puppeteer.launch({ headless: true });
```

### ❌ No Error Handling
```javascript
// ❌ Will crash on first error
const data = await scrapePage(url);  // No try-catch!
```

### ❌ Hardcoded Credentials
```javascript
// ❌ Security risk
const GOOGLE_SHEETS_ID = '121z5R6...';  // Use env vars!
```

---

## Best Practices

### ✅ Use Environment Variables
```javascript
const GOOGLE_SHEETS_ID = process.env.GOOGLE_SHEETS_ID;
```

### ✅ Random Delays
```javascript
await delay(800 + Math.random() * 600);
```

### ✅ Headful Mode
```javascript
const browser = await puppeteer.launch({ headless: false });
```

### ✅ Error Handling
```javascript
try {
  // ...
} catch (error) {
  console.error(`❌ Error: ${error.message}`);
  await logIngestion(county, 'FAILURE', 0, error.message);
}
```

### ✅ Data Validation
```javascript
if (!record.Booking_Number || !record.Full_Name) {
  console.warn(`⚠️  Skipping invalid record: ${JSON.stringify(record)}`);
  continue;
}
```

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture
- **DEVELOPMENT.md** - Development guidelines
- **DEPLOYMENT.md** - Deployment procedures
- **SCHEMA.md** - 34-column data schema
- **TROUBLESHOOTING.md** - Common issues
- **SECURITY.md** - Security guidelines

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
