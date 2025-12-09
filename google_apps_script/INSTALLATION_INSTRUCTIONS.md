# Installation Instructions for "Check for Changes" Feature

## Overview
This feature adds a "Check for Changes" button to your Bail Suite menu that updates the "In Custody" status for all counties in your Google Sheets.

---

## Step 1: Access the Apps Script Editor

1. Open your Google Sheets: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
2. Click on **Extensions** > **Apps Script**
3. You should see your existing project files

---

## Step 2: Add the Check for Changes Code

### Option A: Add to Existing ComprehensiveMenuSystem File

1. Click on `ComprehensiveMenuSystem.gs` in the file list
2. Scroll to the bottom of the file
3. Add the code from `CheckForChanges.gs` (provided in this directory)

### Option B: Create a New File

1. Click the **+** button next to "Files"
2. Select "Script"
3. Name it `CheckForChanges`
4. Paste the code from `CheckForChanges.gs`

---

## Step 3: Update the Menu

Find the `onOpen()` function in your `ComprehensiveMenuSystem.gs` or `Code.gs` file and add this line:

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🟩 Bail Suite')
    // ... existing menu items ...
    .addItem('🔄 Check for Changes', 'checkForChanges')  // ADD THIS LINE
    .addToUi();
}
```

---

## Step 4: Save and Test

1. Click the **Save** button (disk icon)
2. Close the Apps Script editor
3. Refresh your Google Sheets
4. Click **🟩 Bail Suite** > **🔄 Check for Changes**
5. You should see a progress message and then a summary of updates

---

## What It Does

The "Check for Changes" function:

1. **Checks all county sheets**: Lee, Charlotte, Sarasota, Hendry, Collier, Manatee, Hillsborough, DeSoto
2. **Updates "In Custody" status**: 
   - If "Released_Date" column has a date → Status = "Released"
   - If "Released_Date" is empty → Status = "In Custody"
3. **Shows a summary**: Tells you how many records were updated in each county

---

## Troubleshooting

### Menu doesn't appear
- Make sure you saved the script
- Refresh the Google Sheets page
- Check that the `onOpen()` function includes the menu item

### "Function not found" error
- Make sure the `checkForChanges()` function is in your script
- Check that the function name matches exactly (case-sensitive)

### Permission error
- The first time you run it, Google will ask for permissions
- Click "Review Permissions" and authorize the script

---

## Support

If you encounter issues, check the execution log:
1. In Apps Script editor, click **Execution log** at the bottom
2. Look for error messages
3. Common issues:
   - Sheet names don't match (check spelling)
   - Column names don't match (check "Status" and "Released_Date" columns exist)

---

**Created:** December 9, 2025  
**Repository:** https://github.com/Shamrock2245/swfl-arrest-scrapers
