# Check for Changes - Quick Start Guide

## 🚀 Installation in 3 Steps

### Step 1: Open Apps Script
1. Open your Google Sheet
2. Click **Extensions** → **Apps Script**

### Step 2: Replace the Code
1. Click **ComprehensiveMenuSystem** in the left sidebar
2. **Select All** (Ctrl+A) and **Delete**
3. Copy ALL code from `ComprehensiveMenuSystem_UPDATED.gs`
4. Paste into the editor
5. Click **Save** (💾)

### Step 3: Test It
1. Go back to your Google Sheet
2. **Refresh the page** (F5)
3. Click **🟩 Bail Suite** → **🔍 Check for Changes**
4. Done! ✅

---

## 📋 What It Does

Updates the **Status** column (Column Z) for all counties based on:

- ✅ Bond Amount
- ✅ Bond Type  
- ✅ Current Status

**Smart Detection**:
- Has bond → "In Custody"
- No bond/hold → "In Custody - No Bond"
- ROR → "Released - ROR"
- Zero bond → "Released"

---

## 🎯 Counties Covered

✅ Lee  
✅ Collier  
✅ Hendry  
✅ Charlotte  
✅ Manatee  
✅ Sarasota  
✅ Hillsborough  
✅ DeSoto  

---

## 📊 Example Output

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

---

## 🔧 Troubleshooting

**Menu doesn't appear?**
- Refresh the page (F5)
- Wait 10-15 seconds

**Button missing?**
- Verify you saved the script
- Check line 23 has: `.addItem('🔍 Check for Changes', 'checkForChanges')`

**No updates?**
- Check Status column exists (Column Z)
- Verify bond data is populated

---

## 📖 Full Documentation

See `CHECK_FOR_CHANGES_INSTALLATION.md` for:
- Detailed installation steps
- How the logic works
- Automated trigger setup
- Advanced troubleshooting

---

**Ready to go? Follow the 3 steps above!** 🎉
