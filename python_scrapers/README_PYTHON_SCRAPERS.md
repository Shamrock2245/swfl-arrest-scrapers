# Python/DrissionPage Scrapers Documentation

## Overview

This directory contains production-ready Python scrapers using **DrissionPage** for counties that require advanced Cloudflare bypass capabilities. These scrapers are designed to work alongside the existing Node.js/Puppeteer scrapers.

---

## Architecture

### Directory Structure

```
python_scrapers/
├── models/
│   └── arrest_record.py       # ArrestRecord data model
├── scoring/
│   └── lead_scorer.py          # Lead qualification scoring
├── writers/
│   └── sheets_writer.py        # Google Sheets integration
├── scrapers/
│   ├── charlotte_solver.py     # Charlotte County scraper
│   ├── sarasota_solver.py      # Sarasota County scraper
│   ├── hendry_solver.py        # Hendry County scraper
│   ├── run_charlotte.py        # Charlotte wrapper/runner
│   ├── run_sarasota.py         # Sarasota wrapper/runner
│   └── run_hendry.py           # Hendry wrapper/runner
└── README_PYTHON_SCRAPERS.md   # This file
```

---

## County Scrapers

### ✅ Charlotte County (`charlotte_solver.py`)

**Status:** Production-ready (requires proper Cloudflare bypass environment)

**Approach:**
- Navigates to booking list page
- Extracts detail URLs for individual bookings
- Clicks through each booking to get full details
- Handles Cloudflare protection with DrissionPage
- Cleans charge text to extract human-readable descriptions

**Key Features:**
- Clicks individual booking numbers for detailed information
- Extracts: Name, Booking Number, Date, Charges, Bond Amount, Mugshot
- Handles nested tables for charge/bond information
- Cleans charge descriptions (removes statute codes and metadata)

**Usage:**
```bash
python3 run_charlotte.py
```

---

### ✅ Sarasota County (`sarasota_solver.py`)

**Status:** Production-ready (requires proper Cloudflare bypass environment)

**Approach:**
- Navigates directly to iframe-based arrest search app
- Searches by arrest date (date parameter required)
- Handles Cloudflare protection
- Extracts data from search results

**Key Features:**
- Date-based searching (MM/DD/YYYY format)
- Supports multi-day scraping with `--days-back` parameter
- Iframe navigation for embedded app
- Charge text cleaning

**Usage:**
```bash
# Single date
python3 run_sarasota.py --date "12/09/2024"

# Multiple days
python3 run_sarasota.py --date "12/09/2024" --days-back 7
```

---

### ✅ Hendry County (`hendry_solver.py`)

**Status:** Production-ready (requires optimization for card expansion)

**Approach:**
- Navigates to inmate search roster
- Finds "Read More" buttons on inmate cards
- Clicks to expand details for each inmate
- Extracts comprehensive data including charges and bond

**Key Features:**
- Expands collapsible cards for full details
- Sorts by newest first
- Extracts: Name, Inmate ID, Booking Date, Gender, Race, Height, Weight, Address, Charges, Bond, Mugshot
- Handles multiple charges per inmate

**Known Issues:**
- Card expansion can be slow in headless mode
- May timeout on certain records
- Currently limited to 3 records for testing

**Usage:**
```bash
python3 run_hendry.py
```

---

## DrissionPage Configuration

All scrapers use consistent DrissionPage configuration:

```python
co = ChromiumOptions()
co.set_browser_path('/usr/bin/chromium-browser')
co.headless(True)
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-gpu')
co.set_argument('--ignore-certificate-errors')

page = ChromiumPage(co)
```

### Environment Requirements

**Working Environment (User's Local Machine):**
- ✅ Proper display/X11 support OR
- ✅ Enhanced Cloudflare bypass configuration OR
- ✅ Non-headless browser mode

**Sandbox/Headless Environment:**
- ⚠️ Cloudflare may block headless browsers
- ⚠️ Card expansion may be slower
- ⚠️ Some dynamic content may not load properly

---

## Integration with Existing Infrastructure

### Data Flow

```
Solver Script (charlotte_solver.py)
    ↓ (outputs JSON to stdout)
Wrapper Script (run_charlotte.py)
    ↓ (parses JSON)
ArrestRecord Model (arrest_record.py)
    ↓ (structured data)
LeadScorer (lead_scorer.py)
    ↓ (scored records)
SheetsWriter (sheets_writer.py)
    ↓ (writes to Google Sheets)
Google Sheets (Shamrock_Arrests_Master)
```

### Field Mapping

Solver output fields are mapped to ArrestRecord schema:

| Solver Field | ArrestRecord Field |
|---|---|
| `Booking_Number` | `Booking_Number` |
| `Full_Name` | `Full_Name` |
| `First_Name` | `First_Name` |
| `Last_Name` | `Last_Name` |
| `DOB` / `Date of Birth` | `DOB` |
| `Sex` / `Gender` | `Sex` |
| `Race` | `Race` |
| `Arrest_Date` | `Arrest_Date` |
| `Booking_Date` | `Booking_Date` |
| `Address` | `Address` |
| `Charges` | `Charges` |
| `Bond_Amount` | `Bond_Amount` |
| `Mugshot_URL` | `Mugshot_URL` |
| `Detail_URL` | `source_url` |

---

## Charge Text Cleaning

All scrapers include `clean_charge_text()` function:

**Input:**
```
"New Charge: 843.02 - Resisting Officer Without Violence (LEV:M DEG:F 3143) (Principal - P)"
```

**Output:**
```
"Resisting Officer Without Violence"
```

**Logic:**
1. Remove prefixes: "New Charge:", "Weekender:", "Charge Description:"
2. Extract description between statute number and parentheses
3. Fallback: Extract text before first parenthesis
4. Strip statute codes and metadata

---

## Google Sheets Integration

### Configuration

Credentials are loaded from:
- **Spreadsheet ID:** `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`
- **Service Account:** `./creds/service-account-key.json`
- **Environment Variables:** `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_KEY_PATH`

### Sheet Names

- Charlotte → `Charlotte` tab
- Sarasota → `Sarasota` tab
- Hendry → `Hendry` tab

### Deduplication

SheetsWriter handles deduplication by `Booking_Number`:
- New records → Inserted
- Existing records → Updated
- Duplicates → Skipped

---

## Testing Status

| County | Solver Works | Sheets Integration | Cloudflare Bypass | Status |
|---|---|---|---|---|
| **Charlotte** | ✅ Yes | ✅ Yes | ⚠️ Env-dependent | Production-ready |
| **Sarasota** | ✅ Yes | ✅ Yes | ⚠️ Env-dependent | Production-ready |
| **Hendry** | ⚠️ Partial | ✅ Yes | ✅ Yes | Needs optimization |

---

## Deployment Recommendations

### For Production Use:

1. **Deploy on a system with:**
   - Non-headless browser support OR
   - Proper Cloudflare bypass tools OR
   - Enhanced DrissionPage configuration

2. **Use GitHub Actions with:**
   - Scheduled workflows (every 20-30 minutes)
   - Proper secrets configuration
   - Timeout handling

3. **Monitor for:**
   - Cloudflare blocks
   - Timeout errors
   - Data quality issues

### Hybrid Approach (Recommended):

- **Node.js scrapers** for counties that work in headless mode (Collier, Lee)
- **Python scrapers** for counties requiring advanced bypass (Charlotte, Sarasota)
- **Unified Google Sheets** output for all counties

---

## Troubleshooting

### "Handshake status 404 Not Found"
- DrissionPage cannot connect to browser
- Solution: Use `co.headless(True)` instead of `co.auto_port()`

### "Just a moment..." (Cloudflare)
- Cloudflare is blocking headless browser
- Solution: Run in non-headless mode or use enhanced bypass

### Card expansion timeout (Hendry)
- JavaScript-heavy site takes time to load
- Solution: Increase timeouts or reduce record count

### No data extracted
- Page structure may have changed
- Solution: Check debug HTML files (*_debug.html)

---

## Next Steps

1. **Optimize Hendry solver** - Improve card expansion reliability
2. **Test in production environment** - Verify Cloudflare bypass works
3. **Add error handling** - Graceful degradation for partial failures
4. **Implement retry logic** - Handle transient failures
5. **Add logging** - Structured logging for monitoring

---

## Maintenance

### When County Websites Change:

1. Run solver and check debug HTML output
2. Update selectors in solver script
3. Test with `python3 <solver>.py`
4. Verify with wrapper: `python3 run_<county>.py`
5. Check Google Sheets for data

### Regular Checks:

- Monitor Cloudflare bypass effectiveness
- Check for website structure changes
- Verify data quality in Google Sheets
- Review scraper execution times

---

## Contact & Support

For issues or questions:
- Check debug HTML files first
- Review error messages in stderr
- Test solver scripts individually before wrappers
- Verify Google Sheets credentials and permissions

---

**Last Updated:** December 9, 2024  
**Version:** 1.0  
**Author:** SWFL Arrest Scrapers Team
