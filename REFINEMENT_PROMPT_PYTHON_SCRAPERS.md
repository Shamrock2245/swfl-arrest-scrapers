# Python Scrapers Refinement Request

## 🎯 Objective

Refine and optimize the **Charlotte, Manatee, and Sarasota County** Python scrapers to ensure reliable data collection with proper Cloudflare bypass, pagination support, and robust error handling.

---

## 📋 Scrapers to Refine

1. **Charlotte County** - `python_scrapers/scrapers/charlotte_solver.py`
2. **Manatee County** - `python_scrapers/scrapers/manatee_solver.py`
3. **Sarasota County** - `python_scrapers/scrapers/sarasota_solver.py`

---

## 🚨 Current Issues

### Charlotte County (`charlotte_solver.py`)

**Status**: Cloudflare bypass works, but data extraction is failing

**Issues**:
1. ❌ Scraper reports "0 records collected" even though Cloudflare is bypassed
2. ❌ Table detection fails: "Table not found after wait"
3. ❌ Booking links are not being extracted properly
4. ⚠️ Pagination may not be working correctly

**Current Output**:
```
🚀 Starting Charlotte County scraper
📅 Days back: 21
📄 Max pages: 10

📄 Processing page 1...
Checking for Cloudflare...
[1/15] Page Title: Charlotte County FL Inmate Search
✅ Cloudflare cleared - content found!
⚠️  Table not found after wait - page may not have loaded
💾 Saved HTML to charlotte_list_page_fail.html for debugging

📊 Total inmates found across 1 page(s): 0
📊 Total records collected: 0
[]
```

**Expected Behavior**:
- Should find 50+ booking links per page
- Should extract detail URLs like: `https://inmates.charlottecountyfl.revize.com/bookings/202506950`
- Should paginate through multiple pages (12+ pages available)
- Should collect 100-200 records over 21 days

**Page Structure** (verified working):
```html
<table>
  <tbody>
    <tr>
      <td><a href="/bookings/202506950">202506950</a></td>
      <td>EUBANKS</td>
      <td>ALEXANDER</td>
      <td>C</td>
      <td>New Charge: 901.04 - Out of County Warrant...</td>
      <td>12-09-2025</td>
    </tr>
  </tbody>
</table>
```

**Pagination**: Bottom shows `‹ 1 2 3 4 5 6 7 8 9 10 11 12 ›`

---

### Manatee County (`manatee_solver.py`)

**Status**: Unknown - needs testing and verification

**Potential Issues**:
1. ⚠️ Cloudflare bypass may fail (similar to Charlotte)
2. ⚠️ Pagination may not work correctly
3. ⚠️ Date cutoff logic needs verification
4. ⚠️ Data extraction may be incomplete

**Expected Behavior**:
- Should collect 100-200 records over 21 days
- Should paginate through multiple pages
- Should stop at date cutoff (21 days back)
- Should handle iframe content properly

**URL**: `https://manatee-sheriff.revize.com/bookings`

---

### Sarasota County (`sarasota_solver.py`)

**Status**: Unknown - needs testing and verification

**Potential Issues**:
1. ⚠️ Cloudflare bypass may fail
2. ⚠️ Date range iteration may be slow/inefficient
3. ⚠️ Deduplication logic needs verification
4. ⚠️ Data extraction may be incomplete

**Expected Behavior**:
- Should search each day individually (21 days)
- Should collect 150-300 records over 21 days
- Should deduplicate across dates
- Should handle Cloudflare on both list and detail pages

**URL**: `https://cms.revize.com/revize/apps/sarasota/index.php`

---

## ✅ Requirements for All Three Scrapers

### 1. Cloudflare Bypass

**Must**:
- ✅ Run in **headful mode** (not headless) for better bypass
- ✅ Use realistic user agent (Mac Chrome or Windows Chrome)
- ✅ Wait for Cloudflare challenge to complete (up to 30 seconds)
- ✅ Verify content is loaded (check for actual elements, not just title)
- ✅ Handle Turnstile challenges
- ✅ Save HTML to file if bypass fails (for debugging)

**Current Implementation** (Charlotte):
```python
co.headless(False)  # Headful mode
co.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...')
co.set_argument('--disable-blink-features=AutomationControlled')
```

**Verification Logic**:
```python
def handle_cloudflare(page):
    for i in range(15):  # 30 seconds total
        time.sleep(2)
        title = page.title.lower()
        
        # Check if past Cloudflare
        if "just a moment" not in title and "security challenge" not in title and "attention required" not in title:
            # Verify actual content exists
            if page.ele('tag:table', timeout=2) or page.ele('tag:a', timeout=2):
                return True
        
        # Check for Turnstile
        if page.ele('@id=turnstile-wrapper', timeout=1):
            continue
    
    return False
```

---

### 2. Data Extraction

**Must**:
- ✅ Extract booking links from list page
- ✅ Navigate to each detail page
- ✅ Extract all required fields (name, booking number, charges, bond, mugshot, etc.)
- ✅ Handle missing/optional fields gracefully
- ✅ Clean charge text (remove statute codes, keep descriptions)
- ✅ Calculate total bond from multiple charges
- ✅ Format data according to 34-column schema

**Required Fields**:
- `Booking_Number` (unique identifier)
- `Full_Name` (Last, First format)
- `First_Name`
- `Last_Name`
- `Booking_Date`
- `Arrest_Date`
- `Charges` (all charges, pipe-separated)
- `Bond_Amount` (total bond)
- `Mugshot_URL`
- `Detail_URL`
- County-specific fields (DOB, Race, Gender, Height, Weight, etc.)

---

### 3. Pagination

**Must**:
- ✅ Start at page 1
- ✅ Extract all booking links from current page
- ✅ Check for "Next" button or page number links
- ✅ Navigate to next page if available
- ✅ Stop when no more pages or max pages reached
- ✅ Report progress (e.g., "📄 Processing page 2...")

**Parameters**:
- `days_back` (default: 21) - Number of days to go back
- `max_pages` (default: 10) - Maximum pages to scrape

**Expected Output**:
```
📄 Processing page 1...
   📋 Found 45 inmates on page 1

📄 Processing page 2...
   📋 Found 42 inmates on page 2

📊 Total inmates found across 3 page(s): 127
```

---

### 4. Date Cutoff

**Must**:
- ✅ Parse booking date from each record
- ✅ Compare to cutoff date (today - days_back)
- ✅ Stop scraping when reaching old records
- ✅ Report when stopped early

**Implementation**:
```python
cutoff_date = datetime.now() - timedelta(days=days_back)

# After extracting record
if 'Booking_Date' in record:
    try:
        booking_date = datetime.strptime(record['Booking_Date'], '%m/%d/%Y')
        if booking_date < cutoff_date:
            sys.stderr.write(f"   ⏸️  Reached cutoff date ({booking_date.strftime('%Y-%m-%d')}), stopping...\n")
            stopped_early = True
            break
    except:
        pass  # Continue if date parsing fails
```

---

### 5. Error Handling

**Must**:
- ✅ Wrap all operations in try/except blocks
- ✅ Log errors to stderr with context
- ✅ Continue processing other records if one fails
- ✅ Save HTML for debugging on failures
- ✅ Return empty list on fatal errors (don't crash)

**Example**:
```python
try:
    # Extract data
    data = extract_detail_data(page, booking_number, detail_url)
    records.append(data)
except Exception as e:
    sys.stderr.write(f"   ⚠️  Error processing {booking_number}: {e}\n")
    continue  # Don't stop entire scrape
```

---

### 6. Progress Reporting

**Must**:
- ✅ Report to stderr (not stdout - stdout is for JSON output)
- ✅ Show current page being processed
- ✅ Show current record being processed (e.g., "🔍 [5/127]")
- ✅ Show total records collected
- ✅ Show if stopped early due to date cutoff

**Example Output**:
```
🚀 Starting Charlotte County scraper
📅 Days back: 21
📄 Max pages: 10

📄 Processing page 1...
✅ Cloudflare cleared - content found!
✅ Found 50 booking links on page
   📋 Found 45 inmates on page 1

🔍 [1/45] Processing: 202506950
   ✅ EUBANKS, ALEXANDER (Total: 1)

🔍 [2/45] Processing: 202506946
   ✅ RICE, JACOB (Total: 2)

...

📊 Total records collected: 127
```

---

## 🎯 Specific Refinement Tasks

### Charlotte County

1. **Fix booking link extraction**
   - Current: `page.eles('tag:a')` gets ALL links
   - Should: `page.eles('css:a[href*="/bookings/"]')` gets only booking links
   - Filter out `/bookings/` and `/bookings` (no ID)
   - Keep only `/bookings/{NUMBER}` pattern

2. **Fix pagination**
   - Look for "Next" button or page number links
   - Pattern: `?page=2`, `?page=3`, etc.
   - Stop when no "Next" button or reached max_pages

3. **Verify data extraction**
   - Test on detail page: `https://inmates.charlottecountyfl.revize.com/bookings/202506950`
   - Ensure all fields are extracted
   - Handle missing fields gracefully

4. **Add debug output**
   - Show how many links found: "✅ Found 50 booking links on page"
   - Show which links are being processed
   - Show what data is extracted

---

### Manatee County

1. **Test Cloudflare bypass**
   - Run scraper and verify it gets past Cloudflare
   - If fails, implement same fix as Charlotte (headful mode, better detection)

2. **Verify pagination**
   - Test that it goes through multiple pages
   - Verify "Next" button detection works
   - Test with `max_pages=3` to verify

3. **Test data extraction**
   - Verify all fields are extracted from detail pages
   - Check that booking table data is captured
   - Check that charges table data is captured

4. **Verify date cutoff**
   - Test with `days_back=7` to verify it stops early
   - Check that date parsing works correctly

---

### Sarasota County

1. **Test Cloudflare bypass**
   - Run scraper and verify it gets past Cloudflare
   - If fails, implement same fix as Charlotte

2. **Optimize date range iteration**
   - Currently searches each day individually (21 API calls)
   - Consider if there's a way to search by date range
   - If not, keep current approach but add progress reporting

3. **Verify deduplication**
   - Test that duplicate inmates across dates are removed
   - Use `set()` to track unique booking numbers

4. **Test data extraction**
   - Verify all fields are extracted from detail pages
   - Check that charges table data is captured
   - Handle base64 mugshots properly

---

## 📊 Testing Checklist

For each scraper, verify:

- [ ] **Cloudflare bypass works** - Gets past challenge page
- [ ] **Booking links extracted** - Finds 40+ links per page
- [ ] **Pagination works** - Goes through multiple pages
- [ ] **Detail pages load** - Successfully navigates to detail URLs
- [ ] **Data extraction works** - All required fields captured
- [ ] **Date cutoff works** - Stops at specified date
- [ ] **Error handling works** - Doesn't crash on errors
- [ ] **Progress reporting works** - Shows meaningful output
- [ ] **JSON output valid** - Outputs valid JSON to stdout
- [ ] **Performance acceptable** - Completes in reasonable time

---

## 🎯 Success Criteria

### Charlotte County
- ✅ Collects 100-200 records in 5-15 minutes (21 days, 10 pages)
- ✅ Extracts all required fields from detail pages
- ✅ Handles pagination correctly (12+ pages available)
- ✅ Stops at date cutoff

### Manatee County
- ✅ Collects 100-200 records in 5-15 minutes (21 days, 10 pages)
- ✅ Extracts all required fields from detail pages
- ✅ Handles iframe content properly
- ✅ Stops at date cutoff

### Sarasota County
- ✅ Collects 150-300 records in 10-20 minutes (21 days)
- ✅ Searches each day individually without errors
- ✅ Deduplicates inmates across dates
- ✅ Extracts all required fields from detail pages

---

## 📁 Files to Modify

1. `python_scrapers/scrapers/charlotte_solver.py`
2. `python_scrapers/scrapers/manatee_solver.py`
3. `python_scrapers/scrapers/sarasota_solver.py`

---

## 🚀 Testing Commands

### Charlotte County
```bash
cd python_scrapers

# Quick test (7 days, 3 pages)
python3 scrapers/charlotte_solver.py 7 3

# Full test (21 days, 10 pages)
python3 scrapers/charlotte_solver.py 21 10
```

### Manatee County
```bash
cd python_scrapers

# Quick test (7 days, 3 pages)
python3 scrapers/manatee_solver.py 7 3

# Full test (21 days, 10 pages)
python3 scrapers/manatee_solver.py 21 10
```

### Sarasota County
```bash
cd python_scrapers

# Quick test (7 days)
python3 scrapers/sarasota_solver.py 7

# Full test (21 days)
python3 scrapers/sarasota_solver.py 21
```

---

## 📚 Reference Files

- **PAGINATION_UPDATE.md** - Pagination implementation details
- **CHARLOTTE_FIX_NOTES.md** - Charlotte-specific debugging notes
- **LOCAL_SCRAPER_GUIDE.md** - Usage instructions
- **python_scrapers/normalizers/normalize34.py** - Data normalization logic
- **python_scrapers/writers/sheets34.py** - Google Sheets writing logic

---

## 💡 Additional Notes

### Cloudflare Best Practices
- Always run in **headful mode** (visible browser window)
- Use realistic user agents
- Add random delays between requests (1-3 seconds)
- Don't make too many requests too quickly
- Save HTML for debugging when bypass fails

### Data Quality
- Clean charge descriptions (remove statute codes)
- Calculate total bond from all charges
- Handle missing/optional fields gracefully
- Validate booking numbers are unique
- Format names consistently (Last, First)

### Performance
- Charlotte: ~5-15 minutes for 21 days
- Manatee: ~5-15 minutes for 21 days
- Sarasota: ~10-20 minutes for 21 days (searches each day)

---

## 🎯 Priority Order

1. **Charlotte County** (highest priority - currently broken)
2. **Manatee County** (medium priority - needs testing)
3. **Sarasota County** (medium priority - needs testing)

---

## ✅ Deliverables

1. **Updated scraper files** with fixes applied
2. **Test results** showing successful data collection
3. **Sample output** (JSON) from each scraper
4. **Any issues encountered** and how they were resolved

---

**Good luck! Let me know if you have any questions or need clarification on any of these requirements.**
