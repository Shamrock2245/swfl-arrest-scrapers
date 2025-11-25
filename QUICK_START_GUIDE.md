# 🚀 Lead Scoring System - Quick Start Guide

## Copy-Paste Ready Code

Below is the complete `LeadScoringSystem.gs` code. Follow the 3 simple steps to get it running.

---

## Step 1: Create New Script File (2 minutes)

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
2. Click **Extensions** → **Apps Script**
3. Click the **+** button next to "Files"
4. Select **Script**
5. Type filename: `LeadScoringSystem` (without .gs extension)
6. Press Enter

---

## Step 2: Paste the Code (1 minute)

**Copy ALL the code below** (click the copy button or select all with Ctrl+A):

```javascript
/**
 * LeadScoringSystem.gs
 * 
 * Lead scoring system for SWFL Arrest Scrapers
 * Extends schema from 32 to 34 columns with Lead_Score and Lead_Status
 * 
 * Author: SWFL Arrest Scrapers Team
 * Date: November 25, 2025
 */

// ============================================================================
// SCHEMA CONSTANTS
// ============================================================================

const SCHEMA_VERSION = "2.0";
const TOTAL_COLUMNS = 34;

// 34-column header order
const HEADERS = [
  "Booking_Number", "Full_Name", "First_Name", "Last_Name", "DOB", "Sex", "Race",
  "Arrest_Date", "Arrest_Time", "Booking_Date", "Booking_Time", "Agency",
  "Address", "City", "State", "Zipcode", "Charges", "Charge_1", "Charge_1_Statute",
  "Charge_1_Bond", "Charge_2", "Charge_2_Statute", "Charge_2_Bond", "Bond_Amount",
  "Bond_Type", "Status", "Court_Date", "Case_Number", "Mugshot_URL", "County",
  "Court_Location", "Detail_URL", "Lead_Score", "Lead_Status"
];

// County tabs to update
const COUNTY_TABS = ["Lee", "Collier", "Hendry", "Charlotte", "Manatee", "Sarasota", "DeSoto"];
const QUALIFIED_TAB = "Qualified_Arrests";

// Scoring thresholds
const HOT_THRESHOLD = 70;
const WARM_THRESHOLD = 40;

// ============================================================================
// SCHEMA UPDATE FUNCTIONS
// ============================================================================

/**
 * Add Lead_Score and Lead_Status columns to all county sheets
 * Run this once to update the schema from 32 to 34 columns
 */
function updateSchemaTo34Columns() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let results = {
    success: [],
    errors: [],
    timestamp: new Date()
  };
  
  Logger.log("Starting schema update to 34 columns...");
  
  // Update all county tabs
  COUNTY_TABS.forEach(countyName => {
    try {
      const sheet = ss.getSheetByName(countyName);
      if (!sheet) {
        results.errors.push(`Sheet "${countyName}" not found`);
        return;
      }
      
      updateSheetSchema(sheet);
      results.success.push(countyName);
      Logger.log(`✓ Updated ${countyName}`);
    } catch (error) {
      results.errors.push(`${countyName}: ${error.message}`);
      Logger.log(`✗ Error updating ${countyName}: ${error.message}`);
    }
  });
  
  // Update Qualified_Arrests tab
  try {
    const qualifiedSheet = ss.getSheetByName(QUALIFIED_TAB);
    if (qualifiedSheet) {
      updateSheetSchema(qualifiedSheet);
      results.success.push(QUALIFIED_TAB);
      Logger.log(`✓ Updated ${QUALIFIED_TAB}`);
    }
  } catch (error) {
    results.errors.push(`${QUALIFIED_TAB}: ${error.message}`);
    Logger.log(`✗ Error updating ${QUALIFIED_TAB}: ${error.message}`);
  }
  
  // Show results
  const message = `Schema Update Complete!\n\n` +
    `✓ Successfully updated: ${results.success.length} sheets\n` +
    `${results.success.join(", ")}\n\n` +
    (results.errors.length > 0 ? `✗ Errors: ${results.errors.length}\n${results.errors.join("\n")}` : "");
  
  SpreadsheetApp.getUi().alert("Schema Update", message, SpreadsheetApp.getUi().ButtonSet.OK);
  
  return results;
}

/**
 * Update a single sheet's schema to 34 columns
 */
function updateSheetSchema(sheet) {
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  
  // Check if already has 34 columns
  if (lastCol >= TOTAL_COLUMNS) {
    const currentHeaders = sheet.getRange(1, 1, 1, TOTAL_COLUMNS).getValues()[0];
    if (currentHeaders[32] === "Lead_Score" && currentHeaders[33] === "Lead_Status") {
      Logger.log(`${sheet.getName()} already has 34-column schema`);
      return;
    }
  }
  
  // Update header row
  sheet.getRange(1, 1, 1, TOTAL_COLUMNS).setValues([HEADERS]);
  
  // Format new columns
  const leadScoreCol = 33; // AG column (33rd)
  const leadStatusCol = 34; // AH column (34th)
  
  // Set header formatting
  sheet.getRange(1, leadScoreCol, 1, 2)
    .setBackground("#4CAF50")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");
  
  // Set column widths
  sheet.setColumnWidth(leadScoreCol, 100);
  sheet.setColumnWidth(leadStatusCol, 120);
  
  Logger.log(`Updated ${sheet.getName()} to 34-column schema`);
}

// ============================================================================
// LEAD SCORING FUNCTIONS
// ============================================================================

/**
 * Score a single arrest record
 * @param {Object} record - Record object with all fields
 * @returns {Object} - {score: number, status: string, breakdown: array}
 */
function scoreArrestRecord(record) {
  let score = 0;
  let breakdown = [];
  
  // 1. Bond Amount Scoring
  const bondAmount = parseBondAmount(record.Bond_Amount || "");
  if (bondAmount === 0) {
    score -= 50;
    breakdown.push("Bond amount: $0 (-50)");
  } else if (bondAmount < 500) {
    score -= 10;
    breakdown.push(`Bond amount: $${bondAmount} < $500 (-10)`);
  } else if (bondAmount <= 50000) {
    score += 30;
    breakdown.push(`Bond amount: $${bondAmount} in $500-$50K range (+30)`);
  } else if (bondAmount <= 100000) {
    score += 20;
    breakdown.push(`Bond amount: $${bondAmount} in $50K-$100K range (+20)`);
  } else {
    score += 10;
    breakdown.push(`Bond amount: $${bondAmount} > $100K (+10)`);
  }
  
  // 2. Bond Type Scoring
  const bondType = (record.Bond_Type || "").toUpperCase();
  if (bondType.includes("NO BOND") || bondType.includes("HOLD")) {
    score -= 50;
    breakdown.push(`Bond type: ${record.Bond_Type} (NO BOND/HOLD) (-50)`);
  } else if (bondType.includes("ROR") || bondType.includes("R.O.R")) {
    score -= 30;
    breakdown.push(`Bond type: ${record.Bond_Type} (ROR) (-30)`);
  } else if (bondType.includes("CASH") || bondType.includes("SURETY")) {
    score += 25;
    breakdown.push(`Bond type: ${record.Bond_Type} (CASH/SURETY) (+25)`);
  }
  
  // 3. Status Scoring
  const status = (record.Status || "").toUpperCase();
  if (status.includes("IN CUSTODY") || status.includes("INCUSTODY")) {
    score += 20;
    breakdown.push(`Status: ${record.Status} (IN CUSTODY) (+20)` );
  } else if (status.includes("RELEASED")) {
    score -= 30;
    breakdown.push(`Status: ${record.Status} (RELEASED) (-30)`);
  }
  
  // 4. Data Completeness
  const requiredFields = ["Full_Name", "Charges", "Bond_Amount", "Court_Date"];
  const missingFields = requiredFields.filter(field => !record[field] || record[field].toString().trim() === "");
  
  if (missingFields.length === 0) {
    score += 15;
    breakdown.push("Complete data (all required fields present) (+15)");
  } else {
    score -= 10;
    breakdown.push(`Missing data: ${missingFields.join(", ")} (-10)`);
  }
  
  // 5. Disqualifying Charges
  const charges = (record.Charges || "").toLowerCase();
  const disqualifyingKeywords = ["capital", "murder", "federal"];
  
  for (const keyword of disqualifyingKeywords) {
    if (charges.includes(keyword)) {
      score -= 100;
      breakdown.push(`DISQUALIFIED: Severe charge (${keyword}) (-100)`);
      break;
    }
  }
  
  // Determine status
  let leadStatus;
  if (score < 0) {
    leadStatus = "Disqualified";
  } else if (score >= HOT_THRESHOLD) {
    leadStatus = "Hot";
  } else if (score >= WARM_THRESHOLD) {
    leadStatus = "Warm";
  } else {
    leadStatus = "Cold";
  }
  
  return {
    score: score,
    status: leadStatus,
    breakdown: breakdown
  };
}

/**
 * Parse bond amount from string
 */
function parseBondAmount(bondStr) {
  if (!bondStr) return 0;
  const cleaned = bondStr.toString().replace(/[$,]/g, "").trim();
  const amount = parseFloat(cleaned);
  return isNaN(amount) ? 0 : amount;
}

/**
 * Score all records in a county sheet
 */
function scoreCountySheet(countyName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(countyName);
  
  if (!sheet) {
    throw new Error(`Sheet "${countyName}" not found`);
  }
  
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    Logger.log(`No data to score in ${countyName}`);
    return;
  }
  
  // Get all data
  const data = sheet.getRange(2, 1, lastRow - 1, TOTAL_COLUMNS).getValues();
  const headers = sheet.getRange(1, 1, 1, TOTAL_COLUMNS).getValues()[0];
  
  // Find column indices
  const colIndex = {};
  headers.forEach((header, index) => {
    colIndex[header] = index;
  });
  
  let scoredCount = 0;
  
  // Score each row
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    
    // Build record object
    const record = {};
    headers.forEach((header, index) => {
      record[header] = row[index];
    });
    
    // Score the record
    const result = scoreArrestRecord(record);
    
    // Update Lead_Score and Lead_Status columns
    row[colIndex["Lead_Score"]] = result.score;
    row[colIndex["Lead_Status"]] = result.status;
    
    scoredCount++;
  }
  
  // Write back to sheet
  sheet.getRange(2, 1, data.length, TOTAL_COLUMNS).setValues(data);
  
  Logger.log(`Scored ${scoredCount} records in ${countyName}`);
  
  return scoredCount;
}

/**
 * Score all county sheets
 */
function scoreAllSheets() {
  let results = {
    success: [],
    errors: [],
    totalScored: 0
  };
  
  COUNTY_TABS.forEach(countyName => {
    try {
      const count = scoreCountySheet(countyName);
      results.success.push(`${countyName}: ${count} records`);
      results.totalScored += count;
    } catch (error) {
      results.errors.push(`${countyName}: ${error.message}`);
      Logger.log(`Error scoring ${countyName}: ${error.message}`);
    }
  });
  
  const message = `Lead Scoring Complete!\n\n` +
    `✓ Total records scored: ${results.totalScored}\n` +
    `${results.success.join("\n")}\n\n` +
    (results.errors.length > 0 ? `✗ Errors:\n${results.errors.join("\n")}` : "");
  
  SpreadsheetApp.getUi().alert("Lead Scoring", message, SpreadsheetApp.getUi().ButtonSet.OK);
  
  return results;
}

// ============================================================================
// MENU INTEGRATION
// ============================================================================

/**
 * Add Lead Scoring menu items to the Bail Suite menu
 * Call this from onOpen() in ComprehensiveMenuSystem.gs
 */
function addLeadScoringMenuItems(menu) {
  menu.addSeparator();
  menu.addSubMenu(SpreadsheetApp.getUi().createMenu("🎯 Lead Scoring")
    .addItem("📊 Score All Sheets", "scoreAllSheets")
    .addItem("🔄 Update Schema to 34 Columns", "updateSchemaTo34Columns")
    .addSeparator()
    .addItem("📈 Score Lee County", "scoreLeeCounty")
    .addItem("📈 Score Collier County", "scoreCollierCounty")
    .addItem("📈 Score Hendry County", "scoreHendryCounty")
    .addItem("📈 Score Charlotte County", "scoreCharlotteCounty")
    .addItem("📈 Score Manatee County", "scoreManateeCounty")
    .addItem("📈 Score Sarasota County", "scoreSarasotaCounty")
    .addItem("📈 Score DeSoto County", "scoreDeSotoCounty"));
  
  return menu;
}

// Individual county scoring functions
function scoreLeeCounty() { scoreCountySheet("Lee"); SpreadsheetApp.getUi().alert("Scored Lee County"); }
function scoreCollierCounty() { scoreCountySheet("Collier"); SpreadsheetApp.getUi().alert("Scored Collier County"); }
function scoreHendryCounty() { scoreCountySheet("Hendry"); SpreadsheetApp.getUi().alert("Scored Hendry County"); }
function scoreCharlotteCounty() { scoreCountySheet("Charlotte"); SpreadsheetApp.getUi().alert("Scored Charlotte County"); }
function scoreManateeCounty() { scoreCountySheet("Manatee"); SpreadsheetApp.getUi().alert("Scored Manatee County"); }
function scoreSarasotaCounty() { scoreCountySheet("Sarasota"); SpreadsheetApp.getUi().alert("Scored Sarasota County"); }
function scoreDeSotoCounty() { scoreCountySheet("DeSoto"); SpreadsheetApp.getUi().alert("Scored DeSoto County"); }
```

**Then:**
1. Delete any placeholder code in the new file
2. Paste the code above
3. Click **Save** (💾 icon or Ctrl+S)

---

## Step 3: Run the Setup (2 minutes)

### 3a. Update Schema

1. In the Apps Script editor, find the function dropdown (top center)
2. Select `updateSchemaTo34Columns`
3. Click **Run** (▶️ button)
4. **Authorize** when prompted:
   - Click "Review Permissions"
   - Select your account
   - Click "Advanced" → "Go to shamrock-automations (unsafe)"
   - Click "Allow"
5. Wait for the popup: "Schema Update Complete!"

### 3b. Score All Records

1. Go back to your Google Sheet
2. Refresh the page (Ctrl+R or F5)
3. You should see a new menu: **🟩 Bail Suite**
4. Click **🟩 Bail Suite** → **🎯 Lead Scoring** → **📊 Score All Sheets**
5. Wait for the popup: "Lead Scoring Complete!"

---

## ✅ Verify It's Working

1. Open any county tab (e.g., "Lee")
2. Scroll all the way to the right
3. You should see two new columns:
   - **Column AG: Lead_Score** (numbers like 90, 45, -20)
   - **Column AH: Lead_Status** ("Hot", "Warm", "Cold", "Disqualified")

---

## 🎯 What the Scores Mean

- **Hot (Score ≥ 70)**: Best leads - good bond amount, in custody, complete data
- **Warm (40-69)**: Decent leads - moderate bond, some missing data
- **Cold (0-39)**: Poor leads - low bond, ROR, or incomplete data
- **Disqualified (< 0)**: Not worth pursuing - no bond, released, or severe charges

---

## 🔧 Troubleshooting

**Menu not showing?**
- Refresh the spreadsheet (Ctrl+R)
- Or run `onOpen()` function manually in Apps Script

**Authorization error?**
- Click "Advanced" → "Go to shamrock-automations (unsafe)" → "Allow"

**Columns not added?**
- Run `updateSchemaTo34Columns` again
- Check Execution Log in Apps Script for errors

---

## 📊 GitHub Repository

All code is backed up at:
**https://github.com/Shamrock2245/swfl-arrest-scrapers**

Location: `/apps_script/LeadScoringSystem.gs`

---

## 🎉 You're Done!

Once you complete these 3 steps, your lead scoring system is fully operational!

Every time new arrests are added, just click:
**🟩 Bail Suite** → **🎯 Lead Scoring** → **📊 Score All Sheets**
