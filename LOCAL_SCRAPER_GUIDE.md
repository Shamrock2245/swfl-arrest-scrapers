# Local Scraper Running Guide (Updated with Pagination)

## 🚀 Quick Start Commands

### Node.js Scrapers (Working in Production)

```bash
# Collier County (~45 seconds)
npm run run:collier

# Hendry County (~2-5 minutes with pagination)
npm run run:hendry

# DeSoto County (~28 seconds - Optimized!)
npm run run:desoto
```

### Python Scrapers (For Historical Data Collection)

```bash
# First, navigate to python_scrapers directory
cd python_scrapers

# Charlotte County (21 days back, 10 pages max)
python3 scrapers/charlotte_solver.py

# Sarasota County (21 days back)
python3 scrapers/sarasota_solver.py

# Manatee County (21 days back, 10 pages max)
python3 scrapers/manatee_solver.py
```

---

## 📋 One-Time Setup

### For Node.js Scrapers:
```bash
cd /path/to/swfl-arrest-scrapers
npm install
```

### For Python Scrapers:
```bash
cd python_scrapers
pip3 install -r requirements.txt
```

---

## 🎯 NEW: Pagination & Historical Data Collection

### Hendry County (Node.js) - NOW WITH PAGINATION!

**Default (21 days, 10 pages):**
```bash
npm run run:hendry
```

**Custom Parameters:**
```bash
# Syntax: node -r dotenv/config scrapers/hendry_stealth.js [daysBack] [maxPages]

# 30 days back, max 15 pages
node -r dotenv/config scrapers/hendry_stealth.js 30 15

# 7 days back, max 5 pages (quick update)
node -r dotenv/config scrapers/hendry_stealth.js 7 5
```

**What it does:**
- ✅ **Sorts by newest first** - Gets most recent arrests
- ✅ **Paginates through multiple pages** - Collects historical data
- ✅ **Stops at date cutoff** - Won't scrape older than specified days
- ✅ **Clicks into each detail page** - Full data extraction

**Expected output:**
```
🚦 Starting Hendry County Scraper (Stealth + Pagination + 34-column)
📅 Scraping last 21 days of arrests
📄 Maximum pages to scrape: 10

🔽 Setting sort order to "Date (Newest - Oldest)"...
✅ Sort order set to "Date (Newest - Oldest)"

📄 Processing page 1...
   📋 Found 5 inmates on page 1

📊 Total inmates found across 3 page(s): 15
🔍 [1/15] Navigating to https://www.hendrysheriff.org/inmateSearch/12345
   ✅ DOE, JOHN (HCSO24001234) - Bond: $5000.00

📊 Parsed 15 valid records from last 21 days
✅ Inserted: 12, Updated: 3
⏱️  Total execution time: 125s
```

---

### Charlotte County (Python) - NOW WITH PAGINATION!

**Default (21 days, 10 pages):**
```bash
cd python_scrapers
python3 scrapers/charlotte_solver.py
```

**Custom Parameters:**
```bash
# Syntax: python3 scrapers/charlotte_solver.py [daysBack] [maxPages]

# 30 days back, max 15 pages
python3 scrapers/charlotte_solver.py 30 15

# 7 days back, max 5 pages (quick update)
python3 scrapers/charlotte_solver.py 7 5
```

**What it does:**
- ✅ **Paginates through multiple pages**
- ✅ **Stops at date cutoff**
- ✅ **Bypasses Cloudflare**
- ✅ **Collects 3+ weeks of data**

**Expected output:**
```
🚀 Starting Charlotte County scraper
📅 Days back: 21
📄 Max pages: 10

📄 Processing page 1...
   📋 Found 45 inmates on page 1

📊 Total inmates found across 3 page(s): 127
🔍 [1/127] Processing https://inmates.charlottecountyfl.revize.com/bookings/12345
   ✅ Added record (Total: 1)

📊 Total records collected: 127
```

---

### Sarasota County (Python) - NOW WITH DATE RANGE!

**Default (21 days):**
```bash
cd python_scrapers
python3 scrapers/sarasota_solver.py
```

**Custom Parameters:**
```bash
# Syntax: python3 scrapers/sarasota_solver.py [daysBack]

# 30 days back
python3 scrapers/sarasota_solver.py 30

# 7 days back (quick update)
python3 scrapers/sarasota_solver.py 7
```

**What it does:**
- ✅ **Searches each day individually**
- ✅ **Deduplicates across dates**
- ✅ **Bypasses Cloudflare**
- ✅ **Collects 3+ weeks of data**

**Expected output:**
```
🚀 Starting Sarasota County scraper
📅 Days back: 21

📅 Searching for arrests on 12/01/2024...
   📋 Found 8 inmates for 12/01/2024

📊 Total unique inmates found: 156
🔍 [1/156] Processing https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id=12345
   ✅ Added record (Total: 1)

📊 Total records collected: 156
```

---

### Manatee County (Python) - NOW WITH PAGINATION!

**Default (21 days, 10 pages):**
```bash
cd python_scrapers
python3 scrapers/manatee_solver.py
```

**Custom Parameters:**
```bash
# Syntax: python3 scrapers/manatee_solver.py [daysBack] [maxPages]

# 30 days back, max 15 pages
python3 scrapers/manatee_solver.py 30 15

# 7 days back, max 5 pages (quick update)
python3 scrapers/manatee_solver.py 7 5
```

**What it does:**
- ✅ **Paginates through multiple pages**
- ✅ **Stops at date cutoff**
- ✅ **Handles iframe content**
- ✅ **Collects 3+ weeks of data**

**Expected output:**
```
🚦 Starting Manatee County Scraper
📅 Days back: 21
📄 Max pages: 10

📄 Processing page 1...
   📋 Found 52 inmates on page 1

📊 Total inmates found across 3 page(s): 150
🔍 [1/150] Processing: 2024-001234
   ✅ SMITH, JOHN (Total: 1)

📊 Total records collected: 150
```

---

## 🔄 Running All Scrapers

### Run All Node.js Scrapers
```bash
npm start
```

### Run All Scrapers (Node + Python) - UPDATED

Create a bash script `run_all_scrapers.sh`:

```bash
#!/bin/bash

echo "🚀 Running all SWFL arrest scrapers..."

# Node.js scrapers
echo "📍 Running Collier County..."
npm run run:collier

echo "📍 Running Hendry County (with pagination)..."
npm run run:hendry

echo "📍 Running DeSoto County..."
npm run run:desoto

# Python scrapers (with default pagination)
echo "📍 Running Charlotte County (21 days, 10 pages)..."
cd python_scrapers && python3 scrapers/charlotte_solver.py && cd ..

echo "📍 Running Sarasota County (21 days)..."
cd python_scrapers && python3 scrapers/sarasota_solver.py && cd ..

echo "📍 Running Manatee County (21 days, 10 pages)..."
cd python_scrapers && python3 scrapers/manatee_solver.py && cd ..

echo "✅ All scrapers completed!"
```

Make it executable and run:
```bash
chmod +x run_all_scrapers.sh
./run_all_scrapers.sh
```

---

## 📊 Initial Historical Data Collection (One-Time)

Run each scraper with extended parameters to collect 3-4 weeks of data:

```bash
# Hendry (Node.js) - 28 days, 15 pages
node -r dotenv/config scrapers/hendry_stealth.js 28 15

# Charlotte (Python) - 28 days, 15 pages
cd python_scrapers
python3 scrapers/charlotte_solver.py 28 15

# Sarasota (Python) - 28 days
python3 scrapers/sarasota_solver.py 28

# Manatee (Python) - 28 days, 15 pages
python3 scrapers/manatee_solver.py 28 15
```

**After initial collection:**
1. Check Google Sheets for new records
2. Run "Check for Changes" in Google Apps Script
3. Review and verify data accuracy
4. Set up regular schedule with default parameters

---

## 📅 Recommended Schedule

### Initial Setup (One-Time)

**Collect historical data (28 days):**
```bash
# Hendry
node -r dotenv/config scrapers/hendry_stealth.js 28 15

# Python scrapers
cd python_scrapers
python3 scrapers/charlotte_solver.py 28 15
python3 scrapers/sarasota_solver.py 28
python3 scrapers/manatee_solver.py 28 15
```

### Ongoing (Automated)

**Every 25 minutes** (Node.js scrapers):
```bash
npm run run:collier
npm run run:hendry  # Now with pagination!
npm run run:desoto
```

**Every 2-4 hours** (Python scrapers with default 21 days):
```bash
cd python_scrapers
python3 scrapers/charlotte_solver.py
python3 scrapers/sarasota_solver.py
python3 scrapers/manatee_solver.py
```

**Daily** (Check for Changes):
- Use Google Apps Script "Check for Changes" button
- Or set up automated trigger in Apps Script

---

## ✅ Quick Reference Table (UPDATED)

| County | Command | Type | Time | Coverage | Parameters |
|--------|---------|------|------|----------|------------|
| **Collier** | `npm run run:collier` | Node.js | ~45s | Current | None |
| **Hendry** | `npm run run:hendry` | Node.js | ~2-5m | 21 days | [days] [pages] |
| **DeSoto** | `npm run run:desoto` | Node.js | ~28s | Incremental | None |
| **Charlotte** | `python3 scrapers/charlotte_solver.py` | Python | ~5-15m | 21 days | [days] [pages] |
| **Sarasota** | `python3 scrapers/sarasota_solver.py` | Python | ~10-20m | 21 days | [days] |
| **Manatee** | `python3 scrapers/manatee_solver.py` | Python | ~5-15m | 21 days | [days] [pages] |

---

## 🔧 Troubleshooting

### Hendry Scraper

**Issue**: Not getting newest records
- **Solution**: Check logs for "✅ Sort order set to 'Date (Newest - Oldest)'"
- **If missing**: Sorting may have failed, check website structure

**Issue**: Stops after first page
- **Solution**: Increase `maxPages` parameter
- **Example**: `node -r dotenv/config scrapers/hendry_stealth.js 21 20`

**Issue**: Takes too long
- **Solution**: Reduce `daysBack` or `maxPages`
- **Example**: `node -r dotenv/config scrapers/hendry_stealth.js 7 5`

### Python Scrapers

**Issue**: Cloudflare blocking
- **Solution**: Run on local machine (not sandbox)
- **Note**: Python scrapers work best on local machines

**Issue**: No records found
- **Solution**: Check date range - may be no arrests
- **Try**: Extend `days_back` parameter

**Issue**: Takes too long
- **Solution**: Reduce parameters
- **Charlotte/Manatee**: `python3 scrapers/charlotte_solver.py 7 5`
- **Sarasota**: `python3 scrapers/sarasota_solver.py 7`

---

## 📈 Expected Results (UPDATED)

### Initial Run (28 days)

| County | Records | Time |
|--------|---------|------|
| Hendry | 20-40 | 3-8m |
| Charlotte | 150-250 | 10-20m |
| Sarasota | 200-400 | 15-30m |
| Manatee | 150-250 | 10-20m |

### Regular Run (21 days, default)

| County | Records | Time |
|--------|---------|------|
| Hendry | 15-30 | 2-5m |
| Charlotte | 100-200 | 5-15m |
| Sarasota | 150-300 | 10-20m |
| Manatee | 100-200 | 5-15m |

### Quick Update (7 days)

| County | Records | Time |
|--------|---------|------|
| Hendry | 5-15 | 1-3m |
| Charlotte | 30-70 | 2-5m |
| Sarasota | 50-100 | 3-8m |
| Manatee | 30-70 | 2-5m |

---

## 🎯 Best Practices

### Initial Setup

1. ✅ Run historical collection **once** (28 days)
2. ✅ Verify data in Google Sheets
3. ✅ Run "Check for Changes" to update statuses
4. ✅ Set up regular schedule with default parameters

### Regular Maintenance

1. ✅ **Hendry**: Every 25 minutes (or daily with default 21 days)
2. ✅ **Python scrapers**: Every 2-4 hours (default 21 days)
3. ✅ **Check for Changes**: Daily or after scraper runs
4. ✅ **Lead Scoring**: After Check for Changes

### Monitoring

- Check Google Sheets for new records
- Review scraper logs for errors
- Monitor execution times
- Adjust parameters if needed

---

## 🎉 What's New

### Hendry County
- ✅ **Newest-first sorting** - Ensures recent arrests are scraped first
- ✅ **Pagination** - Goes through multiple pages
- ✅ **Configurable** - Set days back and max pages

### Charlotte County
- ✅ **Pagination** - Collects from multiple pages
- ✅ **Date cutoff** - Stops at specified date
- ✅ **Configurable** - Set days back and max pages

### Sarasota County
- ✅ **Date range** - Searches each day individually
- ✅ **Deduplication** - Removes duplicates across dates
- ✅ **Configurable** - Set days back

### Manatee County
- ✅ **Pagination** - Collects from multiple pages
- ✅ **Date cutoff** - Stops at specified date
- ✅ **Configurable** - Set days back and max pages

---

## 📚 Full Documentation

See these files for detailed information:

- **PAGINATION_UPDATE.md** - Comprehensive pagination documentation
- **CHECK_FOR_CHANGES_SUMMARY.md** - Check for Changes feature
- **SESSION_SUMMARY.md** - Overall project summary

---

**Last Updated**: December 2024  
**Version**: 2.0 (with Pagination)  
**Status**: ✅ Ready for Production  

---

## 🚀 Start Now!

**For immediate testing**, run:
```bash
# Hendry with pagination (21 days)
npm run run:hendry
```

**For historical collection**, run:
```bash
# Hendry (28 days, 15 pages)
node -r dotenv/config scrapers/hendry_stealth.js 28 15

# Charlotte (28 days, 15 pages)
cd python_scrapers
python3 scrapers/charlotte_solver.py 28 15
```

Let me know if you need help with any specific scraper or want to set up automation!
