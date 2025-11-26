# Quick Run Guide - Get 30 Days of Data NOW

## 🚀 Run All Counties Immediately

### Prerequisites (5 minutes)

1. **Install Node.js** (if not already installed)
   - Download: https://nodejs.org/ (LTS version)
   - Verify: `node --version` (should be 18+)

2. **Clone Repository**
   ```bash
   git clone https://github.com/Shamrock2245/swfl-arrest-scrapers.git
   cd swfl-arrest-scrapers
   ```

3. **Install Dependencies**
   ```bash
   npm install
   ```

4. **Set Up Google Sheets Credentials**
   
   Create `.env` file in project root:
   ```
   GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
   GOOGLE_SERVICE_ACCOUNT_KEY=<your_service_account_json>
   ```

---

## ▶️ Run All Scrapers (10-15 minutes)

```bash
node run_all_counties.js
```

This will:
- ✅ Run Hendry County (last 30 days)
- ✅ Run Charlotte County (recent bookings)
- ✅ Run Manatee County (recent bookings)
- ✅ Run Sarasota County (recent bookings)
- ✅ Run Hillsborough County (today's bookings)
- ✅ Populate all data to Google Sheets
- ✅ Show summary of results

**Expected Output:**
```
═══════════════════════════════════════════════════════════
  SWFL ARREST SCRAPERS - INITIAL 30-DAY DATA COLLECTION
═══════════════════════════════════════════════════════════

Starting at: 11/25/2025, 9:30:00 PM
Counties to scrape: 5
Estimated total time: 10-15 minutes

════════════════════════════════════════════════════════════
🚀 Starting Hendry County scraper...
   Daily Average: 8 arrests
   Priority: 3 (1=highest)
════════════════════════════════════════════════════════════

[Scraper output...]

✅ Hendry County completed in 120.5s

⏳ Waiting 30 seconds before next county...

[... continues for all counties ...]

═══════════════════════════════════════════════════════════
  SUMMARY
═══════════════════════════════════════════════════════════

Completed at: 11/25/2025, 9:45:00 PM
Total duration: 15.2 minutes

✅ Successful: 5/5
❌ Failed: 0/5

Detailed Results:
------------------------------------------------------------
✅ Hendry          - 120.5s
✅ Charlotte       - 95.3s
✅ Manatee         - 110.7s
✅ Sarasota        - 88.2s
✅ Hillsborough    - 102.1s
------------------------------------------------------------
```

---

## 🔧 Troubleshooting

### Issue: "Cannot find module"

**Solution:**
```bash
npm install
```

### Issue: "Google Sheets authentication failed"

**Solution:**
1. Create service account: https://console.cloud.google.com/
2. Download JSON key
3. Share Google Sheet with service account email
4. Add JSON to `.env` file

### Issue: "Scraper gets blocked"

**Solution:**
- Wait 15-30 minutes for block to expire
- Stealth mode is enabled, but some sites may still block
- Try running one county at a time

### Issue: "Timeout error"

**Solution:**
- Increase timeout in scraper file (default: 30s)
- Check internet connection
- Try again later (site may be slow)

---

## 📊 Verify Data in Google Sheets

After running, check:
1. Open: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
2. Check each county tab (Hendry, Charlotte, Manatee, Sarasota, Hillsborough)
3. Verify data is populated in all 34 columns
4. Run lead scoring: **🟩 Bail Suite** → **🎯 Lead Scoring** → **📊 Score All Sheets**
5. Check columns AG (Lead_Score) and AH (Lead_Status)

---

## 🎯 Next: Set Up Automated Scheduling

### Option A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add these lines (staggered schedule based on arrest frequency):

# Hillsborough (every 20 min) - Highest volume
*/20 * * * * cd /path/to/swfl-arrest-scrapers && node scrapers/hillsborough_stealth.js >> /var/log/scrapers.log 2>&1

# Manatee (every 30 min) - High volume
*/30 * * * * cd /path/to/swfl-arrest-scrapers && node scrapers/manatee_stealth.js >> /var/log/scrapers.log 2>&1

# Sarasota (every 45 min) - Medium-high volume
*/45 * * * * cd /path/to/swfl-arrest-scrapers && node scrapers/sarasota_stealth.js >> /var/log/scrapers.log 2>&1

# Charlotte (every 60 min) - Medium volume
0 * * * * cd /path/to/swfl-arrest-scrapers && node scrapers/charlotte_stealth.js >> /var/log/scrapers.log 2>&1

# Hendry (every 2 hours) - Low volume
0 */2 * * * cd /path/to/swfl-arrest-scrapers && node scrapers/hendry_stealth.js >> /var/log/scrapers.log 2>&1
```

### Option B: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create 5 tasks (one per county)
3. Set triggers based on frequency:
   - Hillsborough: Every 20 minutes
   - Manatee: Every 30 minutes
   - Sarasota: Every 45 minutes
   - Charlotte: Every 60 minutes
   - Hendry: Every 2 hours
4. Action: `node C:\path\to\scrapers\[county]_stealth.js`

### Option C: PM2 (Recommended for servers)

```bash
# Install PM2
npm install -g pm2

# Start all scrapers with PM2
pm2 start ecosystem.config.js

# View logs
pm2 logs

# Monitor
pm2 monit

# Save configuration
pm2 save
pm2 startup
```

---

## 📋 Scheduling Strategy

Based on mean daily arrest frequency:

| County | Daily Arrests | Frequency | Rationale |
|--------|---------------|-----------|-----------|
| **Hillsborough** | 100 | Every 20 min | Highest volume, need real-time |
| **Manatee** | 50 | Every 30 min | High volume, frequent checks |
| **Sarasota** | 40 | Every 45 min | Medium-high, regular checks |
| **Charlotte** | 25 | Every 60 min | Medium, hourly sufficient |
| **Hendry** | 8 | Every 2 hours | Low volume, less frequent |

**Staggered start times** (to avoid overwhelming system):
- Hillsborough: :00, :20, :40
- Manatee: :05, :35
- Sarasota: :10, :55
- Charlotte: :15
- Hendry: :00 (even hours only)

---

## 🎉 Success Metrics

After initial run, you should see:
- ✅ 30 days of Hendry County data (~240 records)
- ✅ Recent Charlotte County bookings (~50-100 records)
- ✅ Recent Manatee County bookings (~100-150 records)
- ✅ Recent Sarasota County bookings (~80-120 records)
- ✅ Today's Hillsborough County bookings (~20-40 records)
- ✅ All 34 columns populated
- ✅ Lead scores calculated
- ✅ Hot/Warm/Cold/Disqualified statuses

**Total expected records**: 400-650 arrests across all 5 counties

---

## 📞 Support

If you encounter issues:
1. Check execution logs in Apps Script
2. Check Node.js console output
3. Verify Google Sheets permissions
4. Check GitHub Issues: https://github.com/Shamrock2245/swfl-arrest-scrapers/issues

---

**Ready to run?** 🚀

```bash
node run_all_counties.js
```
