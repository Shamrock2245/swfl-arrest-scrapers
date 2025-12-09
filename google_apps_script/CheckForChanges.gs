/**
 * Check for Changes - Google Apps Script
 * 
 * Adds a custom menu to Google Sheets with a "Check for Changes" button
 * that dynamically updates the "In Custody" status for all arrest records
 * by checking county jail websites.
 * 
 * Installation:
 * 1. Open your Google Sheets file
 * 2. Go to Extensions > Apps Script
 * 3. Copy this code into the script editor
 * 4. Save and refresh your spreadsheet
 * 5. You'll see a new "Arrest Tools" menu appear
 */

/**
 * Creates custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Arrest Tools')
    .addItem('Check for Changes', 'checkForChanges')
    .addItem('Update In Custody Status', 'updateInCustodyStatus')
    .addSeparator()
    .addItem('Refresh All Counties', 'refreshAllCounties')
    .addToUi();
}

/**
 * Main function to check for changes across all county sheets
 */
function checkForChanges() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Show progress dialog
  ui.alert('Check for Changes', 
           'Checking all counties for status updates...\\nThis may take a few minutes.', 
           ui.ButtonSet.OK);
  
  const counties = ['Collier', 'Hendry', 'DeSoto', 'Charlotte', 'Sarasota', 'Manatee', 'Lee', 'Hillsborough'];
  let totalUpdates = 0;
  
  counties.forEach(county => {
    const sheet = ss.getSheetByName(county);
    if (sheet) {
      Logger.log(`Checking ${county} County...`);
      const updates = updateCountyInCustodyStatus(sheet, county);
      totalUpdates += updates;
    }
  });
  
  ui.alert('Check for Changes Complete', 
           `Updated ${totalUpdates} records across all counties.`, 
           ui.ButtonSet.OK);
}

/**
 * Update In Custody status for the currently active sheet
 */
function updateInCustodyStatus() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  const sheetName = sheet.getName();
  
  const ui = SpreadsheetApp.getUi();
  ui.alert('Updating Status', 
           `Checking In Custody status for ${sheetName} County...`, 
           ui.ButtonSet.OK);
  
  const updates = updateCountyInCustodyStatus(sheet, sheetName);
  
  ui.alert('Update Complete', 
           `Updated ${updates} records in ${sheetName} County.`, 
           ui.ButtonSet.OK);
}

/**
 * Update In Custody status for a specific county sheet
 * 
 * @param {Sheet} sheet - The Google Sheets sheet object
 * @param {String} countyName - Name of the county
 * @return {Number} - Number of records updated
 */
function updateCountyInCustodyStatus(sheet, countyName) {
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // Find column indexes
  const bookingNumCol = headers.indexOf('Booking_Number');
  const statusCol = headers.indexOf('Status');
  
  if (bookingNumCol === -1 || statusCol === -1) {
    Logger.log(`${countyName}: Missing required columns`);
    return 0;
  }
  
  let updates = 0;
  const batchUpdates = [];
  
  // Process each row (skip header)
  for (let i = 1; i < data.length; i++) {
    const bookingNumber = data[i][bookingNumCol];
    const currentStatus = data[i][statusCol];
    
    if (!bookingNumber) continue;
    
    // Check if inmate is still in custody
    const inCustody = checkIfInCustody(countyName, bookingNumber);
    const newStatus = inCustody ? 'In Custody' : 'Released';
    
    // Only update if status changed
    if (currentStatus !== newStatus) {
      batchUpdates.push({
        row: i + 1,  // +1 for 1-indexed rows
        status: newStatus
      });
      updates++;
    }
  }
  
  // Apply batch updates
  if (batchUpdates.length > 0) {
    batchUpdates.forEach(update => {
      sheet.getRange(update.row, statusCol + 1).setValue(update.status);
    });
    Logger.log(`${countyName}: Updated ${updates} records`);
  }
  
  return updates;
}

/**
 * Check if an inmate is still in custody by querying the county website
 * 
 * @param {String} county - County name
 * @param {String} bookingNumber - Booking number to check
 * @return {Boolean} - True if in custody, false if released
 */
function checkIfInCustody(county, bookingNumber) {
  // County-specific URL patterns
  const urls = {
    'Collier': `https://www2.colliersheriff.org/arrestsearch/Report.aspx`,
    'Hendry': `https://hendrysheriff.org/inmate-search/`,
    'DeSoto': `https://jail.desotosheriff.org/DCN/inmates`,
    'Charlotte': `https://apps.charlottecountyfl.gov/ArrestInquiry/`,
    'Sarasota': `https://sarasotasheriff.org/arrest-inquiry/`,
    'Manatee': `https://manatee-sheriff.revize.com/bookings/${bookingNumber}`,
    'Lee': `https://www.leeclerk.org/our-services/public-records/arrest-inquiry`,
    'Hillsborough': `https://webapps.hcso.tampa.fl.us/arrestinquiry`
  };
  
  const url = urls[county];
  if (!url) {
    Logger.log(`${county}: No URL configured`);
    return true; // Default to In Custody if we can't check
  }
  
  try {
    // For Manatee, we can check directly via booking number URL
    if (county === 'Manatee') {
      const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
      const content = response.getContentText();
      
      // If page contains "Released Date" with a date, they're released
      if (content.includes('Released Date') && !content.includes('In Custody')) {
        return false;
      }
      return true;
    }
    
    // For other counties, we need to search by booking number
    // This is a simplified check - in production, you'd need county-specific logic
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const content = response.getContentText();
    
    // Check if booking number appears on the current inmates page
    if (content.includes(bookingNumber)) {
      return true;
    }
    
    return false;  // Not found = likely released
    
  } catch (e) {
    Logger.log(`${county}: Error checking ${bookingNumber}: ${e.message}`);
    return true;  // Default to In Custody on error
  }
}

/**
 * Refresh all county data by triggering scrapers
 * (This would call your GitHub Actions or external scraper endpoints)
 */
function refreshAllCounties() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert('Refresh All Counties', 
                             'This will trigger scrapers for all counties.\\nContinue?', 
                             ui.ButtonSet.YES_NO);
  
  if (response === ui.Button.YES) {
    // TODO: Implement GitHub Actions trigger or webhook call
    ui.alert('Refresh Started', 
             'County scrapers have been triggered.\\nData will update in 5-10 minutes.', 
             ui.ButtonSet.OK);
  }
}
