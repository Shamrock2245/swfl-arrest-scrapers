# Hendry County Arrest Scraper

## Overview
Scrapes current inmate data from Hendry County Sheriff's Office inmate roster.

**Target Site**: https://www.hendrysheriff.org/inmateSearch  
**Technology**: Python + DrissionPage (Chromium automation)  
**County**: Hendry County, Florida

## Features
- ✅ **Sorts by newest first** (critical requirement)
- ✅ Resume capability (skips already-scraped records)
- ✅ Cloudflare/Turnstile bypass
- ✅ Click-through "Read More" buttons for detail extraction
- ✅ Label-based field extraction (robust)
- ✅ Configurable headless mode
- ✅ Auto-save progress to JSONL file
- ✅ Session duplicate detection

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
python hendry_solver.py
```

### With Parameters
```bash
# Scrape with 30 days lookback (parameter currently unused)
python hendry_solver.py 30

# Arguments: <days_back>
```

### Environment Variables
```bash
# Enable headless mode (default: true)
export HEADLESS=true
python hendry_solver.py

# Disable headless mode for debugging
export HEADLESS=false
python hendry_solver.py
```

## Configuration

### Default Settings
- **days_back**: 30 (currently unused - site shows current inmates only)
- **headless**: true (runs without visible browser window)
- **sort_order**: dateDesc (newest first - CRITICAL)

### Recommended Settings for Automation
```bash
# Run every 12 hours
python hendry_solver.py
```

## Critical: Sorting Requirement

**The scraper MUST sort by "Newest First" to capture recent arrests.**

This is implemented at line 147:
```python
sort_select.select.by_value('dateDesc')
```

If this fails, recent arrests will be missed. Monitor logs for:
```
✅ Sorted by Date (Newest First)
```

## Output Format

### JSON Structure
```json
{
  "County": "Hendry",
  "State": "FL",
  "Facility": "Hendry County Jail",
  "Full_Name": "DOE, JOHN",
  "First_Name": "JOHN",
  "Last_Name": "DOE",
  "Booking_Number": "2025-12345",
  "Booking_Date": "12/26/2025",
  "Sex": "M",
  "Race": "White",
  "Height": "5'10\"",
  "Weight": "180 lbs",
  "Address": "123 Main St, LaBelle, FL 33935",
  "Charges": "DUI | POSSESSION OF CONTROLLED SUBSTANCE",
  "Bond_Amount": "5000.0",
  "Mugshot_URL": "https://www.hendrysheriff.org/...",
  "Detail_URL": "https://www.hendrysheriff.org/inmateSearch"
}
```

### Output Methods
1. **stdout**: JSON array of all records (including previously scraped)
2. **hendry_progress.jsonl**: Incremental JSONL file (one record per line)

## Resume Capability

The scraper automatically saves progress to `hendry_progress.jsonl`. If interrupted:
- Re-run the same command
- Previously scraped booking numbers are skipped
- Only new inmates are processed

To start fresh:
```bash
rm hendry_progress.jsonl
python hendry_solver.py
```

## How It Works

### Step-by-Step Process
1. **Load page**: Navigate to inmateSearch
2. **Wait for Cloudflare**: Handle any security challenges
3. **Sort by newest**: Select "dateDesc" from sort dropdown
4. **Find "Read More" buttons**: Locate all expandable inmate cards
5. **Click each button**: Expand card to reveal details
6. **Extract data**: Use label-based extraction (robust)
7. **Parse charges**: Extract all charges and sum bond amounts
8. **Save record**: Write to progress file immediately
9. **Collapse card**: Click "Read Less" to clean up
10. **Repeat**: Process all inmates on page

### Label-Based Extraction
Uses `get_text_by_label()` helper function:
```python
booking_number = get_text_by_label(card, "Inmate ID:")
booking_date = get_text_by_label(card, "Booked Date:")
sex = get_text_by_label(card, "Gender:")
```

This is more robust than CSS selectors and adapts to layout changes.

## Error Handling

### Cloudflare Protection
- Automatically waits up to 20 seconds for Cloudflare challenge
- Uses stealth mode to avoid detection
- Logs Cloudflare status to stderr

### Duplicate Detection
- **Progress file**: Skips booking numbers already in `hendry_progress.jsonl`
- **Session duplicates**: Tracks booking numbers within current run
- Prevents duplicate records from being saved

### Site Changes
If the scraper fails with parsing errors:
1. Check if site structure changed
2. Review stderr logs for specific errors
3. Verify site is accessible in browser
4. Check if sort dropdown still exists

## Logging

All logs go to **stderr** (not stdout):
- Progress updates (e.g., `[5/23] Processing inmate...`)
- Sort status (CRITICAL: verify "Sorted by Date (Newest First)")
- Record counts
- Warnings and errors
- Cloudflare status

To save logs:
```bash
python hendry_solver.py 2> hendry.log
```

## Troubleshooting

### "Sort warning: ..."
**CRITICAL**: Sorting failed, recent arrests may be missed!
- Check if site changed sort dropdown
- Try headed mode to see what's happening
- Verify sort dropdown exists on page

### "Could not clear Cloudflare"
- Try running in headed mode: `HEADLESS=false python hendry_solver.py`
- Manually solve CAPTCHA if it appears
- Check internet connection

### "Skipping - missing name or booking number"
- Normal for cards with incomplete data
- If all records skipped, site structure may have changed

### "Error: ..."
- Check stderr for specific error message
- Try headed mode for visual debugging
- Verify site is accessible

## Schema Compliance

This scraper extracts the following standard fields:
- ✅ Booking_Number (as "Inmate ID")
- ✅ Full_Name, First_Name, Last_Name
- ✅ Booking_Date (as "Booked Date")
- ✅ Sex (as "Gender")
- ✅ Race
- ✅ Height
- ✅ Weight
- ✅ Address (as "Main Address")
- ✅ Charges (multiple, pipe-separated)
- ✅ Bond_Amount (sum of all charges)
- ✅ Mugshot_URL
- ✅ County (hardcoded: Hendry)
- ✅ State (hardcoded: FL)
- ✅ Facility (hardcoded: Hendry County Jail)

### Missing Fields
- ❌ DOB (not available on site)
- ❌ City (included in Address field)
- ❌ ZIP (included in Address field)

## Known Limitations

1. **No pagination**: Only scrapes inmates visible on first page load
   - **Risk**: If site paginates, some inmates will be missed
   - **Mitigation**: Run frequently (every 12 hours)

2. **days_back parameter unused**: Site shows current inmates only (no date filtering)

3. **Fragile parent traversal**: Uses `btn.parent(4)` to find card container
   - May break if HTML structure changes

4. **No rate limiting**: Relies on time.sleep between records

## Maintenance

### Regular Checks
- **Verify sorting works**: Check logs for "Sorted by Date (Newest First)"
- Monitor for Cloudflare issues
- Check progress file size (grows indefinitely)
- Verify booking numbers are being extracted

### Progress File Cleanup
```bash
# Archive old progress file
mv hendry_progress.jsonl hendry_progress_$(date +%Y%m%d).jsonl

# Or delete to start fresh
rm hendry_progress.jsonl
```

### Testing Sort Functionality
```bash
# Run in headed mode and watch browser
HEADLESS=false python hendry_solver.py

# Verify:
# 1. Sort dropdown is clicked
# 2. "Newest" or similar option is selected
# 3. Page reloads with newest inmates first
```

## Support

For issues or questions:
1. Check stderr logs for specific errors
2. **Verify sort is working** (most critical)
3. Try headed mode for visual debugging
4. Verify site is accessible in browser
5. Review code comments for implementation details

## Future Improvements

- [ ] Add pagination support
- [ ] Implement date filtering if site adds it
- [ ] Use more robust card selectors (class/id based)
- [ ] Add retry logic for failed extractions
- [ ] Implement rate limiting
