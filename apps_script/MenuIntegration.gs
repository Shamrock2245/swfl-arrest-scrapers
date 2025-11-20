/**
 * MenuIntegration.gs
 * 
 * Adds Collier County scraper to the Bail Suite menu in Google Sheets
 * 
 * INSTALLATION:
 * 1. Open your Apps Script project: https://script.google.com/u/0/home/projects/1-AidUbJivXw_t2eUw4mMX5GiJjvWtqL8SGuHDLaBCYFKYt8Pcba6uZIt/edit
 * 2. Create a new file called "CollierCountyScraper.gs"
 * 3. Paste this code into that file
 * 4. Update the onOpen() function in your main Code.gs to include the Collier menu item
 */

/**
 * Add Collier County menu items to the Bail Suite menu
 * 
 * Add this to your existing onOpen() function:
 * 
 * function onOpen() {
 *   var ui = SpreadsheetApp.getUi();
 *   ui.createMenu('Bail Suite')
 *     .addItem('Run Lee County Scraper', 'runLeeCountyScraper')
 *     .addItem('Run Collier County Scraper', 'runCollierCountyScraper')
 *     .addItem('Backfill Collier County (10 days)', 'backfillCollierCounty')
 *     .addSeparator()
 *     .addItem('Run All Scrapers', 'runAllScrapers')
 *     .addToUi();
 * }
 */

/**
 * Run Collier County scraper via the Node.js scraper
 * 
 * This triggers the GitHub Actions workflow or calls a webhook
 */
function runCollierCountyScraper() {
  var ui = SpreadsheetApp.getUi();
  
  try {
    ui.alert('Collier County Scraper', 
             'The Collier County scraper runs via Node.js/Puppeteer.\n\n' +
             'To run it now:\n' +
             '1. Go to GitHub Actions\n' +
             '2. Click "Run workflow"\n\n' +
             'Or run locally: node -r dotenv/config scrapers/collier.js\n\n' +
             'Data will appear in the "Collier" tab shortly.',
             ui.ButtonSet.OK);
    
    // Optional: Call a webhook to trigger the scraper
    // var webhookUrl = 'YOUR_WEBHOOK_URL_HERE';
    // var response = UrlFetchApp.fetch(webhookUrl, {
    //   method: 'post',
    //   payload: JSON.stringify({ county: 'collier', action: 'scrape' }),
    //   contentType: 'application/json'
    // });
    
  } catch (error) {
    ui.alert('Error', 'Failed to trigger Collier County scraper: ' + error.message, ui.ButtonSet.OK);
  }
}

/**
 * Backfill Collier County data for the last 10 days
 */
function backfillCollierCounty() {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert('Backfill Collier County', 
                          'This will scrape Collier County arrest data for the last 10 days.\n\n' +
                          'This may take 5-10 minutes. Continue?',
                          ui.ButtonSet.YES_NO);
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    ui.alert('Backfill Started', 
             'The Collier County backfill has been triggered.\n\n' +
             'To run it:\n' +
             '1. Open terminal in the repo directory\n' +
             '2. Run: node backfill_collier.js\n\n' +
             'Data will appear in the "Collier" tab shortly.',
             ui.ButtonSet.OK);
    
    // Optional: Call a webhook to trigger the backfill
    // var webhookUrl = 'YOUR_WEBHOOK_URL_HERE';
    // var response = UrlFetchApp.fetch(webhookUrl, {
    //   method: 'post',
    //   payload: JSON.stringify({ county: 'collier', action: 'backfill', days: 10 }),
    //   contentType: 'application/json'
    // });
    
  } catch (error) {
    ui.alert('Error', 'Failed to trigger backfill: ' + error.message, ui.ButtonSet.OK);
  }
}

/**
 * Run all county scrapers
 */
function runAllScrapers() {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert('Run All Scrapers', 
                          'This will run scrapers for all counties:\n' +
                          '• Lee County (Apps Script)\n' +
                          '• Collier County (Node.js)\n' +
                          '• Hendry County (Node.js)\n' +
                          '• Charlotte County (Node.js)\n\n' +
                          'Continue?',
                          ui.ButtonSet.YES_NO);
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    // Run Lee County (Apps Script)
    if (typeof runLeeCountyScraper === 'function') {
      Logger.log('Running Lee County scraper...');
      runLeeCountyScraper();
    }
    
    // Trigger Node.js scrapers
    ui.alert('All Scrapers Started', 
             'Lee County scraper completed.\n\n' +
             'To run other counties:\n' +
             '1. Open terminal in the repo directory\n' +
             '2. Run: node jobs/runAll.js\n\n' +
             'Or trigger via GitHub Actions.',
             ui.ButtonSet.OK);
    
  } catch (error) {
    ui.alert('Error', 'Failed to run all scrapers: ' + error.message, ui.ButtonSet.OK);
  }
}

/**
 * View Collier County scraper status
 */
function viewCollierStatus() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logsSheet = ss.getSheetByName('Logs');
  
  if (!logsSheet) {
    SpreadsheetApp.getUi().alert('Error', 'Logs sheet not found', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // Get last 10 log entries for Collier
  var data = logsSheet.getDataRange().getValues();
  var collierLogs = data.filter(function(row) {
    return row[0] === 'COLLIER'; // Assuming county is in first column
  }).slice(-10);
  
  if (collierLogs.length === 0) {
    SpreadsheetApp.getUi().alert('Collier Status', 'No logs found for Collier County', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  var message = 'Last 10 Collier County scraper runs:\n\n';
  collierLogs.forEach(function(log) {
    message += log.join(' | ') + '\n';
  });
  
  SpreadsheetApp.getUi().alert('Collier Status', message, SpreadsheetApp.getUi().ButtonSet.OK);
}
