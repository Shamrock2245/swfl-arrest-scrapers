# Sarasota County Arrest Scraper

## Overview
Scrapes arrest/booking data from Sarasota County Sheriff's Office inmate search system.

**Target Site**: https://cms.revize.com/revize/apps/sarasota/index.php  
**Technology**: Python + DrissionPage (Chromium automation)  
**County**: Sarasota County, Florida

## Features
- ✅ Date range search (day-by-day iteration)
- ✅ Resume capability (skips already-scraped records)
- ✅ Cloudflare/Turnstile bypass with manual CAPTCHA support
- ✅ Click-through to detail pages
- ✅ Configurable headless mode
- ✅ Auto-save progress to JSONL file
- ✅ Dynamic field extraction with multiple strategies
- ✅ Data integrity protection (skips records with missing dates)

## Requirements

### Python Dependencies
```bash
pip install DrissionPage
```

### System Requirements
- Python 3.7+
- Chromium or Chrome browser
- For headless mode: xvfb or similar display server (Linux servers)

## Usage

### Basic Usage
```bash
python sarasota_solver.py
```

### With Parameters
```bash
# Scrape last 14 days
python sarasota_solver.py 14

# Arguments: <days_back>
```

### Environment Variables
```bash
# Enable headless mode (default: true)
export HEADLESS=true
python sarasota_solver.py

# Disable headless mode for debugging
export HEADLESS=false
python sarasota_solver.py
```

## Configuration

### Default Settings
- **days_back**: 7 (scrapes arrests from last week)
- **headless**: true (runs without visible browser window)

### Recommended Settings for Automation
```bash
# Run every 6 hours
# Scrape 7 days back for safety margin
python sarasota_solver.py 7
```

## How It Works

### Date-Based Search Strategy
Unlike other scrapers, Sarasota searches **by date**:

1. **Generate date range**: From (today - days_back) to today
2. **For each date**:
   - Navigate to search page
   - Handle Cloudflare if needed
   - Click "Arrest Date" tab
   - Enter date in mm/dd/yyyy format
   - Click "SEARCH" button
   - Extract all inmate detail URLs
3. **Visit each detail page**:
   - Extract personal info, charges, bond, mugshot
   - Save to progress file immediately
4. **Output**: Combined JSON of all records

### Why Day-by-Day?
- Site requires specific arrest date input
- No "all arrests" or date range option
- Ensures complete coverage of date range

## Output Format

### JSON Structure
```json
{
  "Detail_URL": "https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id=12345",
  "County": "Sarasota",
  "State": "FL",
  "Full_Name": "DOE, JOHN",
  "First_Name": "JOHN",
  "Last_Name": "DOE",
  "DOB": "01/15/1985",
  "Race": "White",
  "Sex": "M",
  "Height": "5'10\"",
  "Weight": "180",
  "Address": "123 Main St",
  "City": "Sarasota",
  "State": "FL",
  "Zipcode": "34231",
  "Booking_Date": "12/26/2025 14:30",
  "Booking_Number": "2025-12345",
  "Charges": "DUI | POSSESSION OF CONTROLLED SUBSTANCE",
  "Bond_Amount": "5000.0",
  "Mugshot_URL": "data:image/jpeg;base64,..."
}
```

### Output Methods
1. **stdout**: JSON array of all records (including previously scraped)
2. **sarasota_progress.jsonl**: Incremental JSONL file (one record per line)

## Resume Capability

The scraper automatically saves progress to `sarasota_progress.jsonl`. If interrupted:
- Re-run the same command
- Previously scraped detail URLs are skipped
- Only new records are processed

To start fresh:
```bash
rm sarasota_progress.jsonl
python sarasota_solver.py
```

## Data Integrity Protection

**CRITICAL**: This scraper will **skip records without booking dates** instead of using fallback dates.

Why?
- Wrong dates corrupt downstream processes
- Better to have no record than wrong record
- Preserves data integrity

If you see:
```
⚠️  Missing Booking_Date, skipping record to avoid data corruption
```

This is **intentional** and protects your data quality.

## Error Handling

### Cloudflare Protection
- Automatically waits up to 60 seconds for Cloudflare challenge
- Attempts to click Turnstile checkbox automatically
- Provides manual instructions if stuck:
  ```
  ⚠️  STUCK? Please click the Cloudflare checkbox manually in the browser window!
  ```

### Manual CAPTCHA Handling
If Cloudflare requires manual intervention:
1. Run in headed mode: `HEADLESS=false python sarasota_solver.py`
2. Watch for browser window to appear
3. Solve CAPTCHA manually when prompted
4. Scraper will continue automatically

### Site Changes
If the scraper fails with parsing errors:
1. Check if site structure changed
2. Review stderr logs for specific errors
3. Verify site is accessible in browser
4. Check if search form still uses same field names

## Logging

All logs go to **stderr** (not stdout):
- Date being searched
- Number of inmates found per date
- Progress updates
- Record counts
- Warnings and errors
- Cloudflare status

Example log output:
```
🚀 Starting Sarasota County scraper
📅 Date range: 12/19/2025 to 12/26/2025

📅 Searching for arrests on 12/19/2025...
✅ Cloudflare cleared!
   📋 Found 15 inmates for 12/19/2025

📅 Searching for arrests on 12/20/2025...
   📋 Found 12 inmates for 12/20/2025

📊 Total unique inmates found: 27
📉 Skipping 5 already scraped records. 22 remaining.

🔍 [1/22] Processing https://...
   👤 Name: DOE, JOHN | Date: 12/19/2025
   ✅ Added & Saved record (Total New: 1)
```

To save logs:
```bash
python sarasota_solver.py 2> sarasota.log
```

## Troubleshooting

### "Could not clear Cloudflare"
- Try running in headed mode: `HEADLESS=false python sarasota_solver.py`
- Manually solve CAPTCHA if it appears
- Check internet connection
- Wait longer (increase timeout in code)

### "Could not find arrest_date input"
- Site structure may have changed
- Check if search form still exists
- Verify field name is still `name="date"`
- Try headed mode to see actual page

### "Could not find SEARCH button"
- Site may have changed button text or class
- Check if button still says "SEARCH"
- Verify button is visible and clickable

### "Missing Booking_Date, skipping record"
- **This is normal** and protects data integrity
- Some records genuinely lack booking dates
- Do NOT modify code to use fallback dates

### "No inmates found for date"
- Normal if no arrests on that date
- Verify date format is mm/dd/yyyy
- Check if site is accessible for that date

## Schema Compliance

This scraper extracts the following standard fields:
- ✅ Booking_Number
- ✅ Full_Name, First_Name, Last_Name
- ✅ DOB
- ✅ Sex, Race, Height, Weight
- ✅ Address, City, State, Zipcode (note: ZIP renamed to Zipcode)
- ✅ Booking_Date (includes time if available)
- ✅ Charges (multiple, pipe-separated)
- ✅ Bond_Amount (sum of all charges)
- ✅ Mugshot_URL (often base64-encoded)
- ✅ County, State

### Field Notes
- **Zipcode**: Renamed from ZIP for consistency
- **Mugshot_URL**: May contain base64-encoded image data
- **Booking_Date**: May include time (e.g., "12/26/2025 14:30")
- **Charges**: Cleaned to remove statute numbers

## Known Limitations

1. **No pagination within date results**: If a single date has >1 page of results, only first page is scraped
   - **Risk**: Data loss on high-volume days
   - **Mitigation**: Run frequently with overlapping date ranges

2. **Slow execution**: Searches each date individually
   - 7 days = 7 separate searches
   - Each search requires Cloudflare bypass

3. **Cloudflare challenges**: May require manual intervention
   - More common in headless mode
   - Use headed mode if automation fails

4. **Table column indices hardcoded**: Assumes table structure doesn't change
   - Column 0 = Booking Number
   - Column 1 = Offense
   - Column 4 = Bond
   - Column 6 = Intake Date

5. **Base64 mugshots**: Some mugshots are embedded as base64 data
   - May be very large strings
   - Consider extracting and saving separately

## Maintenance

### Regular Checks
- Verify Cloudflare bypass is working
- Monitor for "Could not find" errors (indicates site changes)
- Check progress file size (grows indefinitely)
- Verify booking dates are being extracted

### Progress File Cleanup
```bash
# Archive old progress file
mv sarasota_progress.jsonl sarasota_progress_$(date +%Y%m%d).jsonl

# Or delete to start fresh
rm sarasota_progress.jsonl
```

### Testing Date Search
```bash
# Run in headed mode and watch browser
HEADLESS=false python sarasota_solver.py 1

# Verify:
# 1. "Arrest Date" tab is clicked
# 2. Date is entered in correct format
# 3. "SEARCH" button is clicked
# 4. Results appear
```

## Performance

### Execution Time
Approximate times (varies by Cloudflare):
- 1 day: ~2-3 minutes
- 7 days: ~15-20 minutes
- 14 days: ~30-40 minutes

### Optimization Tips
- Use smaller date ranges with frequent runs
- Run during off-peak hours to avoid Cloudflare challenges
- Use headless mode for faster execution (if Cloudflare allows)

## Support

For issues or questions:
1. Check stderr logs for specific errors
2. Try headed mode for visual debugging
3. Verify site is accessible in browser
4. Check if search form still exists and works
5. Review code comments for implementation details

## Future Improvements

- [ ] Add pagination detection within date results
- [ ] Implement dynamic table column mapping (header-based)
- [ ] Add retry logic for failed Cloudflare bypasses
- [ ] Optimize date search (parallel or batch)
- [ ] Add rate limiting
- [ ] Extract and save base64 mugshots separately
- [ ] Add validation for required fields before save
