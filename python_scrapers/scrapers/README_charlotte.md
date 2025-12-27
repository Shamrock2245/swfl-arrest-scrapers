# Charlotte County Arrest Scraper

## Overview
Scrapes arrest/booking data from Charlotte County Sheriff's Office inmate roster.

**Target Site**: https://inmates.charlottecountyfl.revize.com/bookings  
**Technology**: Python + DrissionPage (Chromium automation)  
**County**: Charlotte County, Florida

## Features
- ✅ Multi-page pagination support
- ✅ Resume capability (skips already-scraped records)
- ✅ Cloudflare/Turnstile bypass
- ✅ Click-through to detail pages
- ✅ Date filtering (days_back parameter)
- ✅ Configurable headless mode
- ✅ Auto-save progress to JSONL file

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
python charlotte_solver.py
```

### With Parameters
```bash
# Scrape last 7 days, up to 5 pages
python charlotte_solver.py 7 5

# Arguments: <days_back> <max_pages>
```

### Environment Variables
```bash
# Enable headless mode (default: true)
export HEADLESS=true
python charlotte_solver.py

# Disable headless mode for debugging
export HEADLESS=false
python charlotte_solver.py
```

## Configuration

### Default Settings
- **days_back**: 21 (scrapes arrests from last 3 weeks)
- **max_pages**: 10 (scrapes up to 10 pages of results)
- **headless**: true (runs without visible browser window)

### Recommended Settings for Automation
```bash
# Run every 6 hours
# Scrape 3 days back, 10 pages max
python charlotte_solver.py 3 10
```

## Output Format

### JSON Structure
```json
{
  "Detail_URL": "https://inmates.charlottecountyfl.revize.com/bookings/12345",
  "County": "Charlotte",
  "State": "FL",
  "Booking_Number": "12345",
  "Full_Name": "DOE, JOHN",
  "First_Name": "JOHN",
  "Last_Name": "DOE",
  "DOB": "01/15/1985",
  "Sex": "M",
  "Race": "White",
  "Height": "5'10\"",
  "Weight": "180",
  "Address": "123 Main St",
  "City": "Port Charlotte",
  "State": "FL",
  "ZIP": "33952",
  "Booking_Date": "12/26/2025",
  "Charges": "DUI | POSSESSION OF CONTROLLED SUBSTANCE",
  "Bond_Amount": "5000",
  "Mugshot_URL": "https://..."
}
```

### Output Methods
1. **stdout**: JSON array of all records (including previously scraped)
2. **charlotte_progress.jsonl**: Incremental JSONL file (one record per line)

## Resume Capability

The scraper automatically saves progress to `charlotte_progress.jsonl`. If interrupted:
- Re-run the same command
- Previously scraped records are skipped
- Only new records are processed

To start fresh:
```bash
rm charlotte_progress.jsonl
python charlotte_solver.py
```

## Error Handling

### Cloudflare Protection
- Automatically waits up to 30 seconds for Cloudflare challenge
- Uses stealth mode to avoid detection
- Logs Cloudflare status to stderr

### Site Changes
If the scraper fails with parsing errors:
1. Check if site structure changed
2. Review stderr logs for specific errors
3. Verify site is accessible in browser

## Logging

All logs go to **stderr** (not stdout):
- Progress updates
- Record counts
- Warnings and errors
- Cloudflare status

To save logs:
```bash
python charlotte_solver.py 2> charlotte.log
```

## Troubleshooting

### "Could not clear Cloudflare"
- Try running in headed mode: `HEADLESS=false python charlotte_solver.py`
- Manually solve CAPTCHA if it appears
- Check internet connection

### "No booking links found"
- Site may have changed structure
- Verify site is accessible: https://inmates.charlottecountyfl.revize.com/bookings
- Check if site requires VPN or has IP restrictions

### "Content not loaded"
- Increase wait times in code
- Check if site is down
- Try headed mode for debugging

## Schema Compliance

This scraper extracts the following standard fields:
- ✅ Booking_Number
- ✅ Full_Name, First_Name, Last_Name
- ✅ DOB
- ✅ Sex, Race, Height, Weight
- ✅ Address, City, State, ZIP
- ✅ Booking_Date
- ✅ Charges
- ✅ Bond_Amount
- ✅ Mugshot_URL
- ✅ County, State

## Known Limitations

1. **Pagination**: Scrapes up to `max_pages` only (default 10)
2. **Cloudflare**: May require manual intervention if challenge appears
3. **Rate Limiting**: No built-in rate limiting (relies on time.sleep)
4. **Booking Number**: Extracted from URL (may fail if URL structure changes)

## Maintenance

### Regular Checks
- Verify site structure hasn't changed
- Monitor for Cloudflare issues
- Check progress file size (grows indefinitely)

### Progress File Cleanup
```bash
# Archive old progress file
mv charlotte_progress.jsonl charlotte_progress_$(date +%Y%m%d).jsonl

# Or delete to start fresh
rm charlotte_progress.jsonl
```

## Support

For issues or questions:
1. Check stderr logs for specific errors
2. Try headed mode for visual debugging
3. Verify site is accessible in browser
4. Review code comments for implementation details
