# Manatee County Scraper - 34-Column Implementation

## Overview

This document describes the updated Manatee County scraper that outputs data in the 34-column Google Sheets format with Lead_Score and Lead_Status fields.

---

## Files Created/Updated

### 1. **config/schema.json** (Updated)
- Updated to match the 34-column Google Sheets format
- Columns now use Title_Case naming (e.g., `Booking_Number`, `Full_Name`)
- Added `Lead_Score` and `Lead_Status` columns (33-34)
- Updated field aliases for better mapping

### 2. **normalizers/normalize34.js** (New)
- Normalizer for 34-column schema
- Maps raw scraper data to Google Sheets column names
- Handles name parsing, date formatting, address parsing
- Outputs records matching the 34-column format

### 3. **writers/sheets34.js** (New)
- Google Sheets writer for 34-column schema
- Writes to columns A-AH (34 columns)
- Upserts records by `Booking_Number`
- Creates/formats sheets with proper headers

### 4. **scrapers/manatee34.js** (New)
- Updated Manatee scraper using 34-column output
- Fetches bookings from https://manatee-sheriff.revize.com/bookings
- Extracts detail pages and normalizes to 34-column format
- Writes directly to "Manatee" tab in Google Sheets

---

## 34-Column Schema

```
1.  Booking_Number
2.  Full_Name
3.  First_Name
4.  Last_Name
5.  DOB
6.  Sex
7.  Race
8.  Arrest_Date
9.  Arrest_Time
10. Booking_Date
11. Booking_Time
12. Agency
13. Address
14. City
15. State
16. Zipcode
17. Charges
18. Charge_1
19. Charge_1_Statute
20. Charge_1_Bond
21. Charge_2
22. Charge_2_Statute
23. Charge_2_Bond
24. Bond_Amount
25. Bond_Type
26. Status
27. Court_Date
28. Case_Number
29. Mugshot_URL
30. County
31. Court_Location
32. Detail_URL
33. Lead_Score       ← Calculated by Apps Script
34. Lead_Status     ← Calculated by Apps Script
```

---

## Environment Variables Required

```bash
# Google Sheets ID
export GOOGLE_SHEETS_ID="121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E"

# Path to Google Service Account credentials JSON
export GOOGLE_SERVICE_ACCOUNT_KEY_PATH="/path/to/service-account-key.json"
```

---

## Usage

### Run Manatee Scraper (34-column)

```bash
node scrapers/manatee34.js
```

### Expected Output

```
═══════════════════════════════════════
🚦 Starting Manatee County Scraper (34-column)
═══════════════════════════════════════
📡 GET https://manatee-sheriff.revize.com/bookings
📋 Found 25 booking detail URLs
🔍 [1/25] GET https://manatee-sheriff.revize.com/bookings/12345
   ✅ SMITH, JOHN (12345)
🔍 [2/25] GET https://manatee-sheriff.revize.com/bookings/12346
   ✅ DOE, JANE (12346)
...
📊 Parsed 25 valid records
✅ Manatee: inserted 20, updated 5
📝 Logged ingestion: MANATEE - SUCCESS
⏱️  Total execution time: 45s
═══════════════════════════════════════
```

---

## Integration with Apps Script

After the scraper writes data to the "Manatee" tab:

1. **Lead_Score** and **Lead_Status** columns (AG, AH) will be empty
2. Run the Apps Script scoring function:
   - Open Google Sheets
   - Click **🟩 Bail Suite** → **🎯 Lead Scoring** → **📈 Score Manatee County**
3. The Apps Script will calculate and populate:
   - **Lead_Score**: Numeric score (e.g., 90, 45, -20)
   - **Lead_Status**: "Hot", "Warm", "Cold", or "Disqualified"

---

## Data Flow

```
Manatee Sheriff Website
         ↓
  manatee34.js (scraper)
         ↓
  normalize34.js (normalizer)
         ↓
  sheets34.js (writer)
         ↓
Google Sheets (Manatee tab)
         ↓
Apps Script (LeadScoringSystem.gs)
         ↓
Lead_Score & Lead_Status populated
```

---

## Testing

### Test the Normalizer

```javascript
import { normalizeRecord34 } from './normalizers/normalize34.js';

const rawData = {
  'Booking #': '12345',
  'Name': 'SMITH, JOHN MICHAEL',
  'DOB': '01/15/1985',
  'Sex': 'M',
  'Race': 'White',
  'Booking Date': '11/25/2025 14:30',
  'Charges': 'DUI; Battery',
  'Bond': '$5,000.00',
  'mugshot': 'https://example.com/mugshot.jpg'
};

const record = normalizeRecord34(rawData, 'MANATEE', 'https://example.com/detail');
console.log(record);
```

### Expected Output

```javascript
{
  Booking_Number: '12345',
  Full_Name: 'Smith, John Michael',
  First_Name: 'John',
  Last_Name: 'Smith',
  DOB: '01/15/1985',
  Sex: 'M',
  Race: 'White',
  Arrest_Date: '',
  Arrest_Time: '',
  Booking_Date: '11/25/2025',
  Booking_Time: '14:30',
  Agency: '',
  Address: '',
  City: '',
  State: 'FL',
  Zipcode: '',
  Charges: 'DUI; Battery',
  Charge_1: 'DUI',
  Charge_1_Statute: '',
  Charge_1_Bond: '',
  Charge_2: 'Battery',
  Charge_2_Statute: '',
  Charge_2_Bond: '',
  Bond_Amount: '$5,000.00',
  Bond_Type: '',
  Status: '',
  Court_Date: '',
  Case_Number: '',
  Mugshot_URL: 'https://example.com/mugshot.jpg',
  County: 'MANATEE',
  Court_Location: '',
  Detail_URL: 'https://example.com/detail',
  Lead_Score: '',
  Lead_Status: ''
}
```

---

## Troubleshooting

### Issue: "GOOGLE_SERVICE_ACCOUNT_KEY_PATH not set"
**Solution**: Set the environment variable:
```bash
export GOOGLE_SERVICE_ACCOUNT_KEY_PATH="/path/to/credentials.json"
```

### Issue: "GOOGLE_SHEETS_ID not set"
**Solution**: Set the environment variable:
```bash
export GOOGLE_SHEETS_ID="121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E"
```

### Issue: "No bookings found"
**Solution**: 
- Check if the Manatee Sheriff website is accessible
- Verify the LIST_URL in config/counties.json
- Check if the website structure has changed

### Issue: "Missing Booking_Number after normalization"
**Solution**:
- Check the field aliases in config/schema.json
- Verify the website uses "Booking #" or similar label
- Add new aliases if needed

---

## Next Steps

1. **Test the scraper** with real data
2. **Verify output** in Google Sheets Manatee tab
3. **Run lead scoring** via Apps Script
4. **Update other county scrapers** to use 34-column format
5. **Schedule automated runs** via cron or Apps Script triggers

---

## Compatibility

- **Node.js**: 18.x or higher
- **Google Sheets API**: v4
- **Apps Script**: V8 runtime
- **Dependencies**: cheerio, googleapis

---

## Support

For issues or questions:
- Check the main README.md
- Review QUICK_START_GUIDE.md
- Check GitHub issues: https://github.com/Shamrock2245/swfl-arrest-scrapers/issues
