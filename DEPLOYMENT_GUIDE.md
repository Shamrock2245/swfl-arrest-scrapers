# Lead Scoring System Deployment Guide

## ✅ What's Been Completed

1. ✓ Created Python lead scoring module in `/python_scrapers/`
2. ✓ Created Google Apps Script lead scoring system in `/apps_script/LeadScoringSystem.gs`
3. ✓ Pushed all code to GitHub: https://github.com/Shamrock2245/swfl-arrest-scrapers
4. ✓ Updated README with new Google account and sheet information

---

## 📋 Next Steps: Deploy to Google Sheets

### Step 1: Add LeadScoringSystem.gs to Apps Script

1. **Open Apps Script Editor**
   - Go to your Google Sheet: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
   - Click **Extensions** → **Apps Script**

2. **Create New Script File**
   - Click the **+** button next to "Files"
   - Select **Script**
   - Name it: `LeadScoringSystem`
   - Click **OK**

3. **Copy the Code**
   - Open this file: https://github.com/Shamrock2245/swfl-arrest-scrapers/blob/main/apps_script/LeadScoringSystem.gs
   - Click **Raw** button
   - Copy ALL the code (Ctrl+A, Ctrl+C)
   - Paste into the new LeadScoringSystem.gs file in Apps Script
   - Click **Save** (Ctrl+S)

---

### Step 2: Update Schema to 34 Columns

1. **Run the Schema Update Function**
   - In Apps Script editor, select `updateSchemaTo34Columns` from the function dropdown
   - Click **Run** (▶️ button)
   - **Authorize** the script when prompted (click "Review Permissions" → Select your account → "Allow")

2. **Verify the Update**
   - You'll see a popup: "Schema Update Complete!"
   - It will show which sheets were updated
   - Go back to your spreadsheet and check any county tab
   - Scroll to the right - you should now see columns **AG (Lead_Score)** and **AH (Lead_Status)**

---

### Step 3: Score All Existing Records

1. **Reload the Spreadsheet**
   - Close and reopen the Google Sheet, OR
   - Press **Ctrl+R** to refresh

2. **Access the Lead Scoring Menu**
   - You should see a new menu: **🟩 Bail Suite** → **🎯 Lead Scoring**
   - If you don't see it, run the `onOpen` function manually in Apps Script

3. **Score All Sheets**
   - Click **🟩 Bail Suite** → **🎯 Lead Scoring** → **📊 Score All Sheets**
   - Wait for the process to complete
   - You'll see a popup showing how many records were scored

---

### Step 4: Verify the Results

1. **Check Any County Sheet**
   - Open the "Lee" tab (or any county)
   - Scroll to columns AG and AH
   - You should see:
     - **Lead_Score**: Numbers (e.g., 90, 45, -20)
     - **Lead_Status**: "Hot", "Warm", "Cold", or "Disqualified"

2. **Example Expected Results**
   - **Hot Lead** (Score ≥ 70): Bond $5K-$50K, SURETY, IN CUSTODY, complete data
   - **Warm Lead** (Score 40-69): Bond $1K-$5K, CASH, some missing data
   - **Cold Lead** (Score 0-39): Low bond, ROR, or incomplete data
   - **Disqualified** (Score < 0): NO BOND, RELEASED, or severe charges

---

## 🎯 Lead Scoring Menu Options

After deployment, you'll have these menu items under **🟩 Bail Suite** → **🎯 Lead Scoring**:

- **📊 Score All Sheets** - Score all county sheets at once
- **🔄 Update Schema to 34 Columns** - Re-run schema update if needed
- **📈 Score Lee County** - Score only Lee County
- **📈 Score Collier County** - Score only Collier County
- **📈 Score Hendry County** - Score only Hendry County
- **📈 Score Charlotte County** - Score only Charlotte County
- **📈 Score Manatee County** - Score only Manatee County
- **📈 Score Sarasota County** - Score only Sarasota County
- **📈 Score DeSoto County** - Score only DeSoto County

---

## 📊 Scoring Rules Summary

### Bond Amount
- **$500 - $50,000**: +30 points (Sweet spot)
- **$50,000 - $100,000**: +20 points
- **> $100,000**: +10 points
- **< $500**: -10 points
- **$0**: -50 points

### Bond Type
- **CASH or SURETY**: +25 points
- **ROR (Release on Recognizance)**: -30 points
- **NO BOND or HOLD**: -50 points

### Status
- **IN CUSTODY**: +20 points
- **RELEASED**: -30 points

### Data Completeness
- **All required fields present**: +15 points
- **Missing data**: -10 points

### Disqualifying Charges
- **Capital, Murder, or Federal charges**: -100 points (Auto-disqualified)

---

## 🔧 Troubleshooting

### Menu Not Showing
- Refresh the spreadsheet (Ctrl+R)
- Or manually run `onOpen()` function in Apps Script

### Authorization Error
- Click "Review Permissions"
- Select your Google account
- Click "Advanced" → "Go to shamrock-automations (unsafe)"
- Click "Allow"

### Scoring Not Working
- Check that columns AG and AH exist (run `updateSchemaTo34Columns` again)
- Check the Execution Log in Apps Script for errors
- Verify you have data in the sheets

### Need to Re-Score
- Just run the scoring function again - it will overwrite existing scores

---

## 📁 GitHub Repository Structure

```
swfl-arrest-scrapers/
├── apps_script/
│   ├── LeadScoringSystem.gs          ← NEW: Lead scoring for Apps Script
│   ├── ComprehensiveMenuSystem.gs    ← Existing menu system
│   ├── Form.html                     ← Booking form
│   ├── FormDataHandler.gs            ← Form handler
│   └── INSTALLATION.md               ← Installation guide
├── python_scrapers/
│   ├── models/
│   │   └── arrest_record.py          ← NEW: 34-column model
│   ├── scoring/
│   │   └── lead_scorer.py            ← NEW: Python scoring logic
│   ├── writers/
│   │   └── sheets_writer.py          ← NEW: 34-column writer
│   └── LEAD_SCORING_SPEC.md          ← NEW: Detailed spec
└── README.md                          ← Updated with new info
```

---

## 🎉 Success Criteria

You'll know everything is working when:

1. ✅ All county sheets have 34 columns (including Lead_Score and Lead_Status)
2. ✅ The "🎯 Lead Scoring" submenu appears in "🟩 Bail Suite"
3. ✅ Running "Score All Sheets" populates Lead_Score and Lead_Status columns
4. ✅ You can see "Hot", "Warm", "Cold", and "Disqualified" statuses
5. ✅ Scores make sense based on bond amount, type, and status

---

## 📞 Need Help?

If you encounter any issues:

1. Check the **Execution Log** in Apps Script (View → Logs)
2. Verify the **schema** has 34 columns
3. Ensure you have **data** in the sheets to score
4. Try running functions **one county at a time** first

---

## 🚀 Ready to Go Live!

Once you complete Steps 1-4 above, your lead scoring system will be fully operational and integrated into your Google Sheets workflow!
