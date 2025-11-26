# Hendry County Scraper - 34-Column Implementation

## Overview

The Hendry County scraper (`scrapers/hendry_stealth.js`) uses Puppeteer with stealth mode to scrape arrest records from the Hendry County Sheriff's Office website. It clicks "Read More" on each inmate to reveal full bond and charge information, then normalizes the data to the 34-column schema.

## Key Features

### 1. **Stealth Mode**
- Uses `puppeteer-extra-plugin-stealth` to avoid detection
- Random delays between requests (800ms + 600ms jitter)
- Removes automation flags
- Handles Cloudflare and CAPTCHA detection

### 2. **"Read More" Click-Through**
- Navigates to each inmate detail page
- Extracts complete information including:
  - All charges with individual bond amounts
  - Full custody details
  - Complete demographic information
  - Mugshot URLs

### 3. **Date-Based Filtering**
- Scrapes last N days of arrests (default: 30 days)
- Stops when reaching the cutoff date
- Sorts by "Date (Newest - Oldest)" automatically

### 4. **34-Column Output**
- Normalizes to standard schema with Lead_Score and Lead_Status placeholders
- Writes directly to "Hendry" tab in Google Sheets

## Website Structure

**Base URL**: `https://www.hendrysheriff.org/inmateSearch`

### List Page
- Shows collapsed inmate cards with partial information
- Each card has a "Read More" button
- Must sort by "Date (Newest - Oldest)" to get recent arrests

### Detail Page
- URL pattern: `https://www.hendrysheriff.org/inmateSearch/{ID}`
- Contains complete information:
  - **Record Details**: Inmate ID, Address, Height, Weight, Gender, Race, Age, Eye Color, Hair Color
  - **Custody Details**: Custody Status, Booked Date
  - **Charges**: Multiple charges with individual bond amounts

## Data Extraction

### Fields Extracted

**From List Page:**
- Name (heading)
- Posted date

**From Detail Page:**
- Inmate ID (used as Booking_Number)
- Main Address
- Height, Weight, Gender, Race, Age
- Eye Color, Hair Color
- Custody Status
- Booked Date
- **All Charges** (code, description, bond amount)
- Mugshot URL

### Charge Handling

The scraper extracts **all charges** for each inmate, including:
- Charge Code (e.g., "893.13.1A1")
- Charge Description (e.g., "COCAINE-SELL: SCHEDULE II")
- Bond Amount (e.g., "$25000.00" or "$.00")

**Total Bond** is calculated as the sum of all individual charge bonds.

## Usage

### Run Manually

```bash
# Scrape last 30 days (default)
node scrapers/hendry_stealth.js

# Scrape last 7 days
node scrapers/hendry_stealth.js 7

# Scrape last 60 days
node scrapers/hendry_stealth.js 60
```

### Import in Code

```javascript
import { runHendrySteal } from './scrapers/hendry_stealth.js';

// Scrape last 30 days
await runHendrySteal(30);
```

## Configuration

Edit `config/counties.json`:

```json
{
  "hendry": {
    "name": "Hendry",
    "sheetName": "Hendry",
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
  "Booking_Number": "HCSO16MNI004458",
  "Full_Name": "ADAMS, TYJAE ISAIAH",
  "First_Name": "TYJAE",
  "Last_Name": "ADAMS",
  "Sex": "M",
  "Race": "B",
  "Booking_Date": "04/03/2025",
  "Booking_Time": "12:36:34",
  "Address": "890 W LINCOLN AVE",
  "City": "LABELLE",
  "State": "FL",
  "Zipcode": "33935",
  "Charges": "COCAINE-SELL: SCHEDULE II; PROB VIOLATION - MISD: PROBATION VIOLATION; ...",
  "Charge_1": "COCAINE-SELL: SCHEDULE II",
  "Charge_1_Statute": "893.13.1A1",
  "Charge_1_Bond": "$25000.00",
  "Charge_2": "PROB VIOLATION - MISD: PROBATION VIOLATION",
  "Charge_2_Statute": "948.06",
  "Charge_2_Bond": "$0.00",
  "Bond_Amount": "$200000.00",
  "Status": "IN",
  "Mugshot_URL": "https://www.hendrysheriff.org/...",
  "County": "HENDRY",
  "Detail_URL": "https://www.hendrysheriff.org/inmateSearch/46367113",
  "Lead_Score": "",
  "Lead_Status": ""
}
```

## Error Handling

- **Cloudflare/CAPTCHA Detection**: Logs warning and retries
- **Missing Data**: Skips records with missing Booking_Number
- **Navigation Errors**: Logs error and continues to next inmate
- **Timeout**: 30-60 second timeouts with retry logic

## Performance

- **Speed**: ~2-3 seconds per inmate (with random delays)
- **Typical Run**: 30-50 inmates in 60-150 seconds
- **First Run**: May take longer to scrape last 30 days

## Scheduling

Recommended schedule for automated runs:

```yaml
# GitHub Actions (.github/workflows/scrape.yml)
schedule:
  - cron: '*/20 * * * *'  # Every 20 minutes
```

Or use Google Apps Script triggers:
- **Time-driven**: Every 15-30 minutes
- **Manual**: Via "🟩 Bail Suite" menu

## Troubleshooting

### No Inmates Found
- Check if website is accessible
- Verify sorting is set correctly
- Check for CAPTCHA or blocking

### Missing Bond Information
- Ensure "Read More" click is working
- Check if detail page loaded completely
- Verify charge extraction logic

### Duplicate Records
- The scraper uses `upsertRecords34()` which updates existing records by Booking_Number
- No duplicates should occur

## Dependencies

```json
{
  "puppeteer-extra": "^3.3.6",
  "puppeteer-extra-plugin-stealth": "^2.11.2",
  "puppeteer": "^21.0.0"
}
```

## Related Files

- `scrapers/hendry_stealth.js` - Main scraper
- `normalizers/normalize34.js` - 34-column normalizer
- `writers/sheets34.js` - Google Sheets writer
- `shared/browser.js` - Stealth browser utilities
- `config/counties.json` - County configuration

## Notes

- Hendry County website uses a custom CMS (not Revize)
- Detail pages have unique IDs (e.g., `46367113`)
- Mugshots are available on detail pages
- Multiple charges per inmate are common
- Bond amounts can be $0.00 for holds/warrants
