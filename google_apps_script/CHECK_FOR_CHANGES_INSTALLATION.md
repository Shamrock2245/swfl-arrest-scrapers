# Check for Changes - Installation Guide

## Overview

The "Check for Changes" feature dynamically updates the **In Custody** status for all arrest records across all counties by analyzing current bond information and status indicators.

## What It Does

✅ **Checks all county sheets**: Lee, Collier, Hendry, Charlotte, Manatee, Sarasota, Hillsborough, DeSoto  
✅ **Updates Status column (Column Z)** based on:
- Bond Amount
- Bond Type
- Current Status indicators

✅ **Smart Status Detection**:
- "In Custody" - Has bond, not released
- "In Custody - No Bond" - No bond/hold status
- "Released" - Zero bond (not no-bond)
- "Released - ROR" - Released on own recognizance
- Preserves existing clear statuses

✅ **Provides Summary Report** showing:
- Total records checked
- Total records updated
- County-by-county breakdown

## Installation Steps

### Step 1: Open Google Apps Script Editor

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
2. Click **Extensions** → **Apps Script**
3. You should see your existing files:
   - `ComprehensiveMenuSystem`
   - `ArrestScraper_LeeCounty.gs`
   - `LeadScoringSystem.gs`
   - Other files...

### Step 2: Replace ComprehensiveMenuSystem.gs

1. In the Apps Script editor, click on **ComprehensiveMenuSystem** in the left sidebar
2. **Select ALL the current code** (Ctrl+A or Cmd+A)
3. **Delete it**
4. Open the file `ComprehensiveMenuSystem_UPDATED.gs` from this directory
5. **Copy ALL the code** from that file
6. **Paste it** into the ComprehensiveMenuSystem editor
7. Click **Save** (💾 icon or Ctrl+S)

### Step 3: Test the Installation

1. Go back to your Google Sheet
2. **Refresh the page** (F5 or reload)
3. Wait a few seconds for the sheet to load
4. You should see the **🟩 Bail Suite** menu appear
5. Click **🟩 Bail Suite** → **🔍 Check for Changes**
6. The function will run and show a summary dialog when complete

## How It Works

### Status Detection Logic

The function analyzes each record and determines custody status based on:

#### 1. **Existing Clear Status** (No Change)
If the record already has a clear status, it's preserved:
- "Released", "Bonded", "ROR", "Discharged" → No change
- "In Custody", "Booked", "Active", "Held" → No change

#### 2. **Bond Type Indicators**
- **No Bond / Hold** → "In Custody - No Bond"
- **ROR / Release** → "Released - ROR"

#### 3. **Bond Amount**
- **Bond > $0** → "In Custody" (awaiting bond)
- **Bond = $0** (and not "No Bond") → "Released"

#### 4. **Default**
If status is unclear, defaults to "In Custody" (conservative approach)

### Column Mapping

The function uses the 34-column unified schema:

| Column | Field | Index |
|--------|-------|-------|
| A | Booking_Number | 0 |
| X | Bond_Amount | 23 |
| Y | Bond_Type | 24 |
| Z | **Status** | 25 |

## Usage

### Manual Check

1. Click **🟩 Bail Suite** → **🔍 Check for Changes**
2. Wait for processing (typically 5-30 seconds depending on data volume)
3. Review the summary dialog showing updates

### Expected Results

Example output:
```
📊 Check for Changes - Summary Report

Total Records Checked: 156
Total Records Updated: 23

County Breakdown:
Lee: 5/45 updated
Collier: 3/11 updated
Hendry: 2/5 updated
Charlotte: 8/32 updated
Manatee: 0/15 updated
Sarasota: 3/28 updated
Hillsborough: 2/20 updated
DeSoto: 0/0 updated

✅ Check completed successfully!
```

## What Gets Updated

### Before Check for Changes
| Booking_Number | Full_Name | Bond_Amount | Bond_Type | Status |
|----------------|-----------|-------------|-----------|--------|
| 2024-001234 | DOE, JOHN | 5000 | Cash Bond | (empty) |
| 2024-001235 | SMITH, JANE | 0 | No Bond | (empty) |
| 2024-001236 | JONES, BOB | 1500 | ROR | (empty) |

### After Check for Changes
| Booking_Number | Full_Name | Bond_Amount | Bond_Type | Status |
|----------------|-----------|-------------|-----------|--------|
| 2024-001234 | DOE, JOHN | 5000 | Cash Bond | **In Custody** |
| 2024-001235 | SMITH, JANE | 0 | No Bond | **In Custody - No Bond** |
| 2024-001236 | JONES, BOB | 1500 | ROR | **Released - ROR** |

## Troubleshooting

### Menu Doesn't Appear
- **Refresh the page** (F5)
- Wait 10-15 seconds for scripts to load
- Check that you saved the script properly

### "Check for Changes" Button Missing
- Verify you replaced the entire ComprehensiveMenuSystem.gs file
- Look for line 23 in the code: `.addItem('🔍 Check for Changes', 'checkForChanges')`
- Save and refresh

### Function Runs But No Updates
- Check that your data has the Status column (Column Z)
- Verify bond amounts and types are populated
- Check the Logger (Apps Script → Executions) for details

### Permission Error
- First run may ask for permissions
- Click "Review Permissions"
- Select your Google account
- Click "Advanced" → "Go to [Project Name] (unsafe)"
- Click "Allow"

## Advanced: Automated Checks

To run Check for Changes automatically:

### Option 1: Add to Existing Trigger
Modify the existing scraper trigger to also check for changes:

```javascript
function runAllScrapersAndCheck() {
  runAllScrapers();
  Utilities.sleep(5000);  // Wait 5 seconds
  checkForChanges();
}
```

Then update the trigger to call `runAllScrapersAndCheck` instead of `runAllScrapers`.

### Option 2: Separate Trigger
Create a new trigger in Apps Script:

1. Click **Triggers** (⏰ icon in left sidebar)
2. Click **+ Add Trigger**
3. Choose function: `checkForChanges`
4. Event source: **Time-driven**
5. Type: **Hour timer**
6. Interval: **Every hour** (or your preference)
7. Click **Save**

## Code Functions Added

### Main Functions

1. **`checkForChanges()`**
   - Main entry point
   - Processes all county sheets
   - Shows summary dialog

2. **`checkCountyForChanges(sheet, countyName)`**
   - Processes a single county sheet
   - Returns {checked, updated} counts

3. **`determineInCustodyStatus(currentStatus, bondAmount, bondType)`**
   - Core logic for status determination
   - Returns new status or null if no change

4. **`parseBondAmount(bondValue)`**
   - Parses bond amounts from various formats
   - Handles "$5,000", "5000", "No Bond", etc.

## Testing Checklist

- [ ] Menu appears after page refresh
- [ ] "Check for Changes" button is visible in menu
- [ ] Function runs without errors
- [ ] Summary dialog appears with results
- [ ] Status column (Z) updates correctly
- [ ] Existing clear statuses are preserved
- [ ] Logger shows detailed updates (Apps Script → Executions)

## Support

If you encounter issues:

1. Check the **Execution log** in Apps Script:
   - Click **Executions** in left sidebar
   - View the latest run
   - Check for error messages

2. Verify your data structure:
   - 34 columns in each county sheet
   - Status is column Z (column 26)
   - Bond_Amount is column X (column 24)
   - Bond_Type is column Y (column 25)

3. Test on a single county first:
   - Modify the `counties` array to test one county
   - Example: `const counties = ['Collier'];`

## Next Steps

After successful installation:

1. ✅ Run manual check to verify functionality
2. ✅ Review updated statuses for accuracy
3. ✅ Consider setting up automated triggers
4. ✅ Document any county-specific status patterns
5. ✅ Integrate with lead scoring workflow

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Compatibility**: All SWFL counties (Lee, Collier, Hendry, Charlotte, Manatee, Sarasota, Hillsborough, DeSoto)
