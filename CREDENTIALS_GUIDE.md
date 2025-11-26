# Google Sheets Credentials Setup Guide

## 🔑 Quick Setup (5 minutes)

### Step 1: Pull Latest Code

```bash
cd ~/Desktop/swfl-arrest-scrapers
git pull origin main
```

### Step 2: Run Setup Script

```bash
node setup_credentials.js
```

The script will guide you through the process!

---

## 📋 Creating a Google Service Account

### 1. Go to Google Cloud Console
https://console.cloud.google.com/

### 2. Create/Select Project
- Click "Select a project" → "New Project"
- Name: "SWFL Arrest Scrapers"
- Click "Create"

### 3. Enable Google Sheets API
- Go to: APIs & Services → Library
- Search: "Google Sheets API"
- Click "Enable"

### 4. Create Service Account
- Go to: APIs & Services → Credentials
- Click "Create Credentials" → "Service Account"
- Name: "arrest-scraper"
- Click "Create and Continue"
- Skip optional steps → "Done"

### 5. Create JSON Key
- Click on the service account you just created
- Go to "Keys" tab
- Click "Add Key" → "Create new key"
- Choose "JSON"
- Click "Create"
- **File downloads automatically** (keep it safe!)

### 6. Share Google Sheet with Service Account
- Open your Google Sheet: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
- Click "Share" button
- Paste the service account email (from the JSON file, looks like: `arrest-scraper@project-id.iam.gserviceaccount.com`)
- Give "Editor" permission
- Click "Send"

---

## 🚀 Using the Setup Script

### Option A: Paste JSON Directly

```bash
node setup_credentials.js
# Choose option A
# Paste the entire JSON content
# Press Ctrl+D when done
```

### Option B: Provide File Path

```bash
node setup_credentials.js
# Choose option B
# Enter path to downloaded JSON file
# Example: ~/Downloads/arrest-scraper-key.json
```

### Option C: Manual Setup

1. Save the downloaded JSON as `service-account-key.json` in project root
2. Create `.env` file with:
   ```
   GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
   GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
   ```

---

## ✅ Verify Setup

After setup, your project should have:

```
swfl-arrest-scrapers/
├── service-account-key.json    ← Created by setup script
├── .env                         ← Created/updated by setup script
├── .gitignore                   ← Already excludes above files
└── ...
```

**Check .env file:**
```bash
cat .env
```

Should contain:
```
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
```

**Test credentials:**
```bash
node run_all_counties.js
```

Should start scraping without "GOOGLE_SERVICE_ACCOUNT_KEY_PATH not set" error!

---

## 🔒 Security Notes

1. **Never commit credentials to Git**
   - `.gitignore` already excludes `service-account-key.json` and `.env`
   - These files stay only on your computer

2. **Keep the JSON key safe**
   - It grants access to your Google Sheets
   - Don't share it publicly
   - Don't email it

3. **Rotate keys if compromised**
   - Delete old key in Google Cloud Console
   - Create new key
   - Run setup script again

---

## 🐛 Troubleshooting

### Error: "GOOGLE_SERVICE_ACCOUNT_KEY_PATH not set"

**Solution:**
```bash
# Check if .env exists
cat .env

# If missing, create it:
echo "GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E" > .env
echo "GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json" >> .env
```

### Error: "Cannot read file"

**Solution:**
```bash
# Check if service-account-key.json exists
ls -la service-account-key.json

# If missing, run setup script:
node setup_credentials.js
```

### Error: "Permission denied"

**Solution:**
1. Open Google Sheet: https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
2. Click "Share"
3. Add service account email (from JSON file)
4. Give "Editor" permission

### Error: "Invalid JSON"

**Solution:**
- Make sure you copied the entire JSON file
- Check for missing braces `{` or `}`
- Re-download from Google Cloud Console

---

## 🎯 Next Steps

After credentials are set up:

1. **Test scrapers:**
   ```bash
   node run_all_counties.js
   ```

2. **Check Google Sheets** for populated data

3. **Run lead scoring** in Apps Script

4. **Set up automated scheduling** (cron/PM2)

---

## 📞 Need Help?

If you're stuck:
1. Check the error message carefully
2. Verify service account email is shared with the sheet
3. Confirm JSON file is valid
4. Try running setup script again

---

**Ready to set up credentials?** 🔑

```bash
node setup_credentials.js
```
