# Google Apps Script - Check for Changes

This directory contains Google Apps Script code to add custom functionality to your arrest tracking spreadsheet.

## Features

### "Check for Changes" Button
- Adds a custom "Arrest Tools" menu to your Google Sheets
- Automatically checks all county websites to update "In Custody" status
- Works across all counties: Collier, Hendry, DeSoto, Charlotte, Sarasota, Manatee, Lee, and Hillsborough

## Installation Instructions

### Step 1: Open Your Google Sheets
1. Navigate to your primary spreadsheet:
   - https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit

### Step 2: Open Apps Script Editor
1. Click **Extensions** in the menu bar
2. Select **Apps Script**
3. This will open the Apps Script editor in a new tab

### Step 3: Add the Code
1. Delete any existing code in the editor
2. Copy the entire contents of `CheckForChanges.gs`
3. Paste it into the Apps Script editor
4. Click **File** > **Save** (or press Ctrl+S / Cmd+S)
5. Name your project: "Arrest Tools"

### Step 4: Authorize the Script
1. Close the Apps Script tab
2. Refresh your Google Sheets page
3. You should see a new menu called **"Arrest Tools"** appear
4. Click **Arrest Tools** > **Check for Changes**
5. Google will ask you to authorize the script:
   - Click "Continue"
   - Select your account (`admin@shamrockbailbonds.biz`)
   - Click "Advanced" if you see a warning
   - Click "Go to Arrest Tools (unsafe)" - this is safe, it's your own script
   - Click "Allow"

### Step 5: Test It
1. Click **Arrest Tools** > **Check for Changes**
2. The script will check all counties and update "In Custody" statuses
3. You'll see a progress dialog, then a summary of updates

## Menu Options

Once installed, you'll have these options in the "Arrest Tools" menu:

### Check for Changes
- Checks ALL counties for status updates
- Updates "In Custody" vs "Released" status
- Shows summary of how many records were updated

### Update In Custody Status
- Updates only the currently active sheet (county)
- Faster if you only need to check one county

### Refresh All Counties
- (Future feature) Will trigger scrapers to collect new data
- Currently shows a placeholder message

## How It Works

### Status Update Logic

For each arrest record in each county sheet:
1. Extracts the booking number
2. Checks the county website to see if the inmate is still listed
3. Updates the "Status" column:
   - **"In Custody"** - Still in jail
   - **"Released"** - No longer in jail

### County-Specific Checks

The script uses county-specific URLs to check status:

- **Collier**: https://www2.colliersheriff.org/arrestsearch/Report.aspx
- **Hendry**: https://hendrysheriff.org/inmate-search/
- **DeSoto**: https://jail.desotosheriff.org/DCN/inmates
- **Charlotte**: https://apps.charlottecountyfl.gov/ArrestInquiry/
- **Sarasota**: https://sarasotasheriff.org/arrest-inquiry/
- **Manatee**: https://manatee-sheriff.revize.com/bookings/{booking_number}
- **Lee**: https://www.leeclerk.org/our-services/public-records/arrest-inquiry
- **Hillsborough**: https://webapps.hcso.tampa.fl.us/arrestinquiry

## Troubleshooting

### Menu Doesn't Appear
- Refresh the spreadsheet page
- Make sure you saved the script
- Check that you're using the correct Google account

### Script Runs Slowly
- This is normal! Checking hundreds of records across 8 counties takes time
- The script may take 2-5 minutes to complete
- You'll see a progress dialog while it runs

### "Authorization Required" Error
- Follow Step 4 above to authorize the script
- Make sure you're logged in as `admin@shamrockbailbonds.biz`

### Status Not Updating
- Some counties may block automated checks
- The script defaults to "In Custody" if it can't verify
- You can manually update individual records if needed

## Future Enhancements

Planned features:
- Trigger GitHub Actions to run scrapers
- Email notifications when high-value leads are released
- Automated daily status checks
- Integration with SignNow for automated bond applications

## Support

For issues or questions:
- Check the execution log: **Extensions** > **Apps Script** > **Executions**
- Review error messages in the log
- Contact your development team for assistance
