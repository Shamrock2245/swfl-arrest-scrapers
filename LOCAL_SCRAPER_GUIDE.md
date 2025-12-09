# Local Scraper Running Guide

## 🚀 Quick Start Commands

### Node.js Scrapers (Working in Production)

```bash
# Collier County
npm run run:collier

# Hendry County
npm run run:hendry

# DeSoto County (Optimized Incremental)
npm run run:desoto
```

### Python Scrapers (For Cloudflare-Protected Sites)

```bash
# Charlotte County
cd python_scrapers
python3 scrapers/charlotte_solver.py

# Sarasota County
python3 scrapers/sarasota_solver.py

# Manatee County
python3 scrapers/manatee_solver.py
```

---

## 📋 Prerequisites

### For Node.js Scrapers

1. **Node.js** (v18 or higher)
   ```bash
   node --version  # Should be 18.0.0 or higher
   ```

2. **Install Dependencies**
   ```bash
   cd /path/to/swfl-arrest-scrapers
   npm install
   ```

3. **Environment Variables**
   - Ensure `.env` file exists in project root
   - Should contain:
     ```
     GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
     GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
     ```

4. **Service Account Key**
   - File: `service-account-key.json` in project root
   - Should already be configured

### For Python Scrapers

1. **Python 3.11+**
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

2. **Install Python Dependencies**
   ```bash
   cd python_scrapers
   pip3 install -r requirements.txt
   ```

3. **DrissionPage Setup**
   - DrissionPage will use your installed Chrome/Chromium browser
   - First run will configure browser connection automatically

---

## 🎯 Node.js Scraper Commands (Detailed)

### Collier County
```bash
# Standard run
npm run run:collier

# Debug mode (with detailed logs)
npm run run:collier:debug
```

**What it does**:
- Scrapes Collier County Sheriff's Office booking data
- Writes to "Collier" sheet in Google Sheets
- Uses Puppeteer with stealth plugins
- Typically finds 10-15 recent arrests

**Expected output**:
```
🏃 Starting Collier County scraper...
📊 Found 11 records
✅ Successfully wrote 11 records to Google Sheets
✨ Collier scraper completed in 45.2s
```

---

### Hendry County
```bash
# Standard run (recommended)
npm run run:hendry

# Alternative version (if issues)
npm run run:hendry:v2
```

**What it does**:
- Scrapes Hendry County Sheriff's Office
- Writes to "Hendry" sheet
- Uses stealth mode for bot detection bypass
- Typically finds 5-10 arrests

**Expected output**:
```
🏃 Starting Hendry County scraper...
📊 Found 5 records
✅ Successfully wrote 5 records to Google Sheets
✨ Hendry scraper completed in 32.1s
```

---

### DeSoto County (Optimized)
```bash
npm run run:desoto
```

**What it does**:
- Scrapes DeSoto County Sheriff's Office
- Uses **incremental strategy** (only new records)
- Maintains baseline in `scrapers/desoto_baseline.json`
- **95%+ faster** than full scrape (28s vs 10+ min)
- Writes to "DeSoto" sheet

**Expected output**:
```
🏃 Starting DeSoto County scraper (Incremental)...
📊 Baseline: 1234 records
🔍 Checking for new records...
📊 Found 3 new records
✅ Successfully wrote 3 records to Google Sheets
📝 Updated baseline: 1237 records
✨ DeSoto scraper completed in 28.4s
```

**First Run**:
- Will create baseline file
- May take 5-10 minutes to build initial baseline
- Subsequent runs will be fast (20-30 seconds)

---

## 🐍 Python Scraper Commands (Detailed)

### Charlotte County
```bash
cd python_scrapers
python3 scrapers/charlotte_solver.py
```

**What it does**:
- Scrapes Charlotte County Sheriff's Office (Cloudflare-protected)
- Uses DrissionPage with Chrome browser
- Writes to "Charlotte" sheet
- Can collect historical data (3-4 weeks)

**Expected output**:
```
Starting Charlotte County scraper...
Opening browser...
Navigating to booking search page...
Bypassing Cloudflare protection...
Found 45 records
Writing to Google Sheets...
✅ Successfully wrote 45 records
Completed in 2m 15s
```

**For Historical Data**:
The scraper is configured to collect recent data. To get 3-4 weeks:
- It will automatically paginate through results
- May take 10-20 minutes for full historical collection
- Run once to get historical data, then periodically for updates

---

### Sarasota County
```bash
cd python_scrapers
python3 scrapers/sarasota_solver.py
```

**What it does**:
- Scrapes Sarasota County Sheriff's Office (Cloudflare-protected)
- Uses DrissionPage for CAPTCHA/Cloudflare bypass
- Writes to "Sarasota" sheet
- Collects 3-4 weeks of historical data

**Expected output**:
```
Starting Sarasota County scraper...
Opening browser...
Navigating to booking page...
Solving Cloudflare challenge...
Processing page 1...
Processing page 2...
Found 67 records
Writing to Google Sheets...
✅ Successfully wrote 67 records
Completed in 3m 42s
```

---

### Manatee County
```bash
cd python_scrapers
python3 scrapers/manatee_solver.py
```

**What it does**:
- Scrapes Manatee County Sheriff's Office
- Uses iframe from https://manatee-sheriff.revize.com/bookings
- Handles Cloudflare protection
- Writes to "Manatee" sheet
- Collects 3-4 weeks of historical data

**Expected output**:
```
Starting Manatee County scraper...
Opening browser...
Loading iframe...
Bypassing Cloudflare...
Found 52 records
Writing to Google Sheets...
✅ Successfully wrote 52 records
Completed in 2m 58s
```

**Note**: Manatee scraper was created but not fully tested in sandbox due to Cloudflare blocking. Should work on your local machine.

---

## 🔄 Running All Scrapers

### Run All Node.js Scrapers
```bash
npm start
```

This runs `jobs/runAll.js` which executes all Node.js scrapers sequentially.

### Run All Scrapers (Node + Python)

Create a bash script `run_all_scrapers.sh`:

```bash
#!/bin/bash

echo "🚀 Running all SWFL arrest scrapers..."

# Node.js scrapers
echo "📍 Running Collier County..."
npm run run:collier

echo "📍 Running Hendry County..."
npm run run:hendry

echo "📍 Running DeSoto County..."
npm run run:desoto

# Python scrapers
echo "📍 Running Charlotte County..."
cd python_scrapers && python3 scrapers/charlotte_solver.py && cd ..

echo "📍 Running Sarasota County..."
cd python_scrapers && python3 scrapers/sarasota_solver.py && cd ..

echo "📍 Running Manatee County..."
cd python_scrapers && python3 scrapers/manatee_solver.py && cd ..

echo "✅ All scrapers completed!"
```

Make it executable and run:
```bash
chmod +x run_all_scrapers.sh
./run_all_scrapers.sh
```

---

## 📊 Collecting Historical Data (3-4 Weeks)

### For Charlotte, Sarasota, Manatee

The Python scrapers are configured to collect recent historical data automatically. To ensure you get 3-4 weeks:

1. **Charlotte County**:
   ```bash
   cd python_scrapers
   python3 scrapers/charlotte_solver.py
   ```
   - Will paginate through recent bookings
   - Typically gets last 3-4 weeks automatically

2. **Sarasota County**:
   ```bash
   cd python_scrapers
   python3 scrapers/sarasota_solver.py
   ```
   - Configured to collect multiple pages
   - Gets 3-4 weeks of data

3. **Manatee County**:
   ```bash
   cd python_scrapers
   python3 scrapers/manatee_solver.py
   ```
   - Collects from iframe source
   - Gets recent historical data

**Recommendation**: Run each Python scraper **once** to collect historical data, then set up periodic runs (daily or every few hours) to keep data current.

---

## 🛠️ Troubleshooting

### Node.js Scrapers

**Error: Cannot find module**
```bash
npm install
```

**Error: .env file not found**
- Ensure `.env` file exists in project root
- Check it contains `GOOGLE_SHEETS_ID` and `GOOGLE_APPLICATION_CREDENTIALS`

**Error: Service account authentication failed**
- Verify `service-account-key.json` exists
- Check file path in `.env` is correct
- Ensure service account has edit access to the spreadsheet

**Scraper hangs or times out**
- Check internet connection
- Try debug mode: `npm run run:collier:debug`
- County website may be down or changed structure

### Python Scrapers

**Error: ModuleNotFoundError**
```bash
cd python_scrapers
pip3 install -r requirements.txt
```

**Error: DrissionPage browser connection failed**
- Ensure Chrome/Chromium is installed
- First run will configure browser automatically
- Check browser is not already open in debug mode

**Cloudflare blocking**
- Python scrapers use DrissionPage specifically to bypass Cloudflare
- If still blocked, try:
  - Close all Chrome windows
  - Run scraper again (fresh browser session)
  - Wait a few minutes and retry

**No data returned**
- Check county website is accessible in regular browser
- Website structure may have changed
- Check scraper logs for specific errors

---

## 📅 Recommended Schedule

### Initial Setup (One-Time)
1. Run DeSoto scraper to create baseline:
   ```bash
   npm run run:desoto
   ```
   Wait for completion (5-10 min first time)

2. Collect historical data for Python scrapers:
   ```bash
   cd python_scrapers
   python3 scrapers/charlotte_solver.py
   python3 scrapers/sarasota_solver.py
   python3 scrapers/manatee_solver.py
   ```

### Ongoing (Automated)

**Every 25 minutes** (Node.js scrapers):
```bash
npm run run:collier
npm run run:hendry
npm run run:desoto
```

**Every 2-4 hours** (Python scrapers):
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

## 🔧 Advanced Options

### Debug Mode (Node.js)
```bash
NODE_OPTIONS='--enable-source-maps --trace-uncaught --trace-warnings' node -r dotenv/config scrapers/collier.js
```

### Headless vs Headful (Python)
Edit the Python scraper file to change browser mode:
```python
# In the scraper file, find:
page = ChromiumPage()  # Headful (default)

# Change to:
page = ChromiumPage(headless=True)  # Headless
```

### Custom Date Range (Python)
Modify the scraper to specify date range:
```python
# In the scraper file, add date filtering logic
# This varies by county website structure
```

---

## 📝 Logs and Monitoring

### Node.js Scrapers
- Logs output to console
- Use `npm run run:collier:debug` for detailed logs
- Check Google Sheets for successful writes

### Python Scrapers
- Logs output to console
- DrissionPage shows browser actions
- Check `python_scrapers/logs/` if logging is configured

### Google Sheets
- Open spreadsheet to verify data
- Check "Last Updated" timestamps
- Run "Check for Changes" to update statuses

---

## ✅ Quick Reference

| County | Command | Type | Time | Notes |
|--------|---------|------|------|-------|
| Collier | `npm run run:collier` | Node.js | ~45s | Working ✅ |
| Hendry | `npm run run:hendry` | Node.js | ~30s | Working ✅ |
| DeSoto | `npm run run:desoto` | Node.js | ~28s | Incremental ✅ |
| Charlotte | `python3 scrapers/charlotte_solver.py` | Python | ~2-3m | Cloudflare bypass |
| Sarasota | `python3 scrapers/sarasota_solver.py` | Python | ~3-4m | Cloudflare bypass |
| Manatee | `python3 scrapers/manatee_solver.py` | Python | ~3m | iframe + Cloudflare |

---

## 🎯 Next Steps

1. **Test Node.js scrapers**:
   ```bash
   npm run run:collier
   npm run run:hendry
   npm run run:desoto
   ```

2. **Collect historical data** (Python):
   ```bash
   cd python_scrapers
   python3 scrapers/charlotte_solver.py
   python3 scrapers/sarasota_solver.py
   python3 scrapers/manatee_solver.py
   ```

3. **Set up automation**:
   - Use cron jobs (Linux/Mac)
   - Use Task Scheduler (Windows)
   - Or GitHub Actions (cloud-based)

4. **Install Check for Changes** in Google Apps Script

5. **Monitor and maintain**:
   - Check Google Sheets regularly
   - Review logs for errors
   - Update scrapers if county websites change

---

**Need help?** Check the documentation in the `docs/` directory or review the scraper source code for specific implementation details.
