# Hillsborough County Scraper - 34-Column Implementation

## Overview

The Hillsborough County scraper (`scrapers/hillsborough_stealth.js`) uses Puppeteer with stealth mode to scrape arrest records from the Hillsborough County Sheriff's Office (HCSO) arrest inquiry system. It fills out the search form with today's date, includes arrest details, and normalizes the data to the 34-column schema.

## Key Features

### 1. **Stealth Mode** 🔒
- Uses `puppeteer-extra-plugin-stealth` to avoid detection
- Random delays between actions
- Handles reCAPTCHA (may require manual intervention on first run)

### 2. **Form Submission** 📝
- Automatically fills out arrest inquiry form
- Sets booking date (defaults to today)
- Checks "Include Arrest Details"
- Selects "Sort by Booking Date"
- Submits form and waits for results

### 3. **Date-Based Search** 📅
- Searches by booking date (MM/DD/YYYY format)
- Defaults to today's date
- Can specify custom date via command line

### 4. **34-Column Output** 📊
- Normalizes to standard schema
- Includes Lead_Score and Lead_Status placeholders
- Writes to "Hillsborough" sheet tab

## Website Structure

**Base URL**: `https://webapps.hcso.tampa.fl.us/arrestinquiry`

### Arrest Inquiry Form

**Form Fields:**
- **Booking #** - Optional
- **Name** - Optional (Last Name, First Name)
- **Booking Date** - MM/DD/YYYY format ✅ (we use this)
- **Release Date** - MM/DD/YYYY format
- **Race** - Dropdown (Asian, Black, Indian, White, Unknown)
- **Sex** - Dropdown (Male, Female)
- **Date of Birth** - MM/DD/YYYY format

**Options:**
- ✅ **Current Inmates Only** - Checkbox
- ✅ **Include Arrest Details** - Checkbox (we check this)

**Sorting:**
- ✅ **by Booking Date** - Radio button (we select this)
- **by Booking #** - Radio button
- **by Name** - Radio button

**reCAPTCHA:**
- ⚠️ Form has reCAPTCHA v2 protection
- Stealth mode may bypass it automatically
- May require manual solving on first run

### Results Page

After form submission, the results page displays:
- **Booking Number**
- **Name** (Last, First Middle)
- **Booking Date**
- **Release Date** (if released)
- **Race**
- **Sex**
- **Date of Birth**
- **Charges** (if "Include Arrest Details" was checked)
- **Bond Amount**
- **Booking Photo** (mugshot)

## Data Extraction

### Fields Extracted

**From Results Table:**
- Booking Number (used as Booking_Number)
- Full Name (Last, First Middle)
- Booking Date (MM/DD/YYYY)
- Release Date (if available)
- Race (single letter code)
- Sex (M/F)
- Date of Birth (MM/DD/YYYY)
- Charges (if "Include Arrest Details" was checked)
- Bond Amount (e.g., "$10,000.00")

### Normalization

The scraper normalizes Hillsborough data to the 34-column schema:
- **Booking_Number**: Extracted from "Booking #"
- **Full_Name**: Extracted from "Name" field
- **First_Name**: Parsed from Full_Name
- **Last_Name**: Parsed from Full_Name
- **DOB**: Extracted from "Date of Birth"
- **Sex**: M or F
- **Race**: Single letter code (B, W, H, A, I, U)
- **Booking_Date**: Extracted from "Booking Date"
- **Booking_Time**: Not available (empty)
- **Charges**: Extracted from arrest details
- **Bond_Amount**: Extracted from "Bond Amount"
- **Status**: "IN" if no release date, "RELEASED" if release date present
- **County**: "HILLSBOROUGH"

## Usage

### Run Manually

```bash
# Scrape today's arrests (default)
node scrapers/hillsborough_stealth.js

# Scrape specific date
node scrapers/hillsborough_stealth.js 11/25/2025

# Scrape yesterday
node scrapers/hillsborough_stealth.js 11/24/2025
```

### Import in Code

```javascript
import { runHillsboroughSteal } from './scrapers/hillsborough_stealth.js';

// Scrape today's arrests
await runHillsboroughSteal();

// Scrape specific date
await runHillsboroughSteal('11/25/2025');
```

## Configuration

Edit `config/counties.json`:

```json
{
  "hillsborough": {
    "name": "Hillsborough",
    "sheetName": "Hillsborough",
    "enabled": true
  }
}
```

## Output Format

### 34-Column Schema

```
Booking_Number, Full_Name, First_Name, Last_Name, DOB, Sex, Race,
Arrest_Date, Arrest_Time, Booking_Date, Booking_Time, Agency,
Address, City, State, Zipcode, Charges, Charge_1, Charge_1_Statute,
Charge_1_Bond, Charge_2, Charge_2_Statute, Charge_2_Bond, Bond_Amount,
Bond_Type, Status, Court_Date, Case_Number, Mugshot_URL, County,
Court_Location, Lead_Score, Lead_Status, Detail_URL
```

### Example Record

```json
{
  "Booking_Number": "2025012345",
  "Full_Name": "SMITH, JOHN MICHAEL",
  "First_Name": "JOHN",
  "Last_Name": "SMITH",
  "DOB": "01/15/1990",
  "Sex": "M",
  "Race": "W",
  "Booking_Date": "11/25/2025",
  "Charges": "DUI; DRIVING WITH SUSPENDED LICENSE",
  "Bond_Amount": "$2,500.00",
  "Status": "IN",
  "County": "HILLSBOROUGH",
  "Detail_URL": "https://webapps.hcso.tampa.fl.us/arrestinquiry",
  "Lead_Score": "",
  "Lead_Status": ""
}
```

## reCAPTCHA Handling

### Automatic Bypass (Stealth Mode)

The scraper uses `puppeteer-extra-plugin-stealth` which often bypasses reCAPTCHA automatically by:
- Removing automation flags
- Mocking browser properties
- Using realistic user behavior

### Manual Intervention

If reCAPTCHA blocks the scraper:

1. **Run with visible browser** (set `headless: false` in `shared/browser.js`)
2. **Solve CAPTCHA manually** once
3. **Cookies will be saved** for future runs
4. **Subsequent runs** should work automatically

### Alternative: 2Captcha Integration

For fully automated CAPTCHA solving, integrate 2Captcha service:

```javascript
import { Solver } from '2captcha';

const solver = new Solver(process.env.TWOCAPTCHA_API_KEY);

// Solve reCAPTCHA
const sitekey = await page.$eval('iframe[src*="recaptcha"]', el => 
  new URL(el.src).searchParams.get('k')
);

const solution = await solver.recaptcha(sitekey, page.url());
await page.evaluate((token) => {
  document.getElementById('g-recaptcha-response').value = token;
}, solution.data);
```

## Error Handling

- **reCAPTCHA Blocked**: Logs warning and returns error
- **No Results**: Returns success with count=0
- **Form Submission Failed**: Retries with Enter key
- **Timeout**: 30-60 second timeouts with retry logic

## Performance

- **Speed**: ~5-10 seconds per search (including form submission)
- **Typical Run**: 10-50 arrests per day
- **CAPTCHA Delay**: +5-10 seconds if CAPTCHA appears

## Scheduling

Recommended schedule for automated runs:

```yaml
# GitHub Actions (.github/workflows/scrape.yml)
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
```

Or use Google Apps Script triggers:
- **Time-driven**: Every 2-4 hours
- **Manual**: Via "🟩 Bail Suite" menu

**Note**: Less frequent than other counties due to reCAPTCHA

## Troubleshooting

### reCAPTCHA Blocking
**Symptoms**: "reCAPTCHA blocked" error  
**Solution**:
- Run with visible browser and solve CAPTCHA once
- Use 2Captcha service for automated solving
- Increase delays between requests

### No Results Found
**Symptoms**: 0 arrests returned  
**Solution**:
- Verify date format (MM/DD/YYYY)
- Check if any arrests occurred on that date
- Ensure "Include Arrest Details" is checked

### Form Submission Failed
**Symptoms**: Form doesn't submit  
**Solution**:
- Check if form fields are correctly filled
- Verify search button selector
- Try pressing Enter key instead of clicking button

## Dependencies

```json
{
  "puppeteer-extra": "^3.3.6",
  "puppeteer-extra-plugin-stealth": "^2.11.2",
  "puppeteer": "^21.0.0"
}
```

## Related Files

- `scrapers/hillsborough_stealth.js` - Main scraper
- `normalizers/normalize34.js` - 34-column normalizer
- `writers/sheets34.js` - Google Sheets writer
- `shared/browser.js` - Stealth browser utilities
- `config/counties.json` - County configuration

## Notes

- Hillsborough County has reCAPTCHA protection
- Form requires specific date format (MM/DD/YYYY)
- "Include Arrest Details" checkbox must be checked to get charges
- Results are updated every 30 minutes on HCSO website
- Arrests appear for 90 days after release date
- Stealth mode significantly improves CAPTCHA bypass rate
