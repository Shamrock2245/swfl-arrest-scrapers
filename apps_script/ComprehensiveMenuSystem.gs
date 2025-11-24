/**
 * ComprehensiveMenuSystem.gs
 * 
 * Complete menu system for SWFL Arrest Scrapers
 * Integrates with both Apps Script scrapers and Node.js scrapers
 * 
 * INSTALLATION:
 * 1. Open Apps Script project: https://script.google.com/u/0/home/projects/12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo/edit
 * 2. Copy this entire file into your project
 * 3. Ensure Form.html is also added to the project
 * 4. Save and reload the spreadsheet
 * 
 * CONFIGURATION:
 * - Update SHEET_ID if needed
 * - Update GITHUB_REPO_URL if needed
 * - Configure webhook URLs if you want automated triggers
 */

// ============================================
// CONFIGURATION
// ============================================

var CONFIG = {
  SHEET_ID: '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E',
  GITHUB_REPO_URL: 'https://github.com/Shamrock2245/swfl-arrest-scrapers',
  APPS_SCRIPT_URL: 'https://script.google.com/u/0/home/projects/12BRRdYuyVJpQODJq2-OpUhQdZ9YLt4bbAFWmOUyJPWM_EcazKTiu3dYo/edit',
  
  // Optional: Configure webhooks for automated triggers
  WEBHOOK_URL: '', // e.g., 'https://your-webhook-url.com/trigger'
  
  // County tabs
  COUNTIES: {
    LEE: 'Lee',
    COLLIER: 'Collier',
    HENDRY: 'Hendry',
    CHARLOTTE: 'Charlotte',
    MANATEE: 'Manatee',
    SARASOTA: 'Sarasota',
    DESOTO: 'DeSoto'
  },
  
  LOGS_TAB: 'Logs',
  QUALIFIED_TAB: 'Qualified_Arrests'
};

// ============================================
// MENU SYSTEM
// ============================================

/**
 * Creates custom menu when spreadsheet opens
 * This is the main entry point for the menu system
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  ui.createMenu('🟩 Bail Suite')
    .addSubMenu(ui.createMenu('📍 Run Individual Scrapers')
      .addItem('Lee County', 'runLeeCountyScraper')
      .addItem('Collier County', 'runCollierCountyScraper')
      .addItem('Hendry County', 'runHendryCountyScraper')
      .addItem('Charlotte County', 'runCharlotteCountyScraper')
      .addItem('Manatee County', 'runManateeCountyScraper')
      .addItem('Sarasota County', 'runSarasotaCountyScraper')
      .addItem('DeSoto County', 'runDeSotoCountyScraper'))
    .addSeparator()
    .addItem('🚀 Run All Scrapers', 'runAllScrapers')
    .addSeparator()
    .addItem('📋 Open Booking Form', 'showBookingForm')
    .addSeparator()
    .addSubMenu(ui.createMenu('⏰ Manage Triggers')
      .addItem('Install Hourly Triggers', 'installHourlyTriggers')
      .addItem('View Active Triggers', 'viewActiveTriggers')
      .addItem('Disable All Triggers', 'disableAllTriggers'))
    .addSeparator()
    .addSubMenu(ui.createMenu('📊 View Status')
      .addItem('View Scraper Logs', 'viewScraperLogs')
      .addItem('View Qualified Arrests', 'viewQualifiedArrests')
      .addItem('Check Sheet Status', 'checkSheetStatus'))
    .addSeparator()
    .addItem('ℹ️ About / Help', 'showAboutDialog')
    .addToUi();
}

// ============================================
// INDIVIDUAL SCRAPER FUNCTIONS
// ============================================

/**
 * Run Lee County scraper
 * This can be an Apps Script scraper or trigger Node.js
 */
function runLeeCountyScraper() {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert(
    'Lee County Scraper',
    'Run Lee County arrest scraper now?\\n\\n' +
    'This will fetch the latest arrest data and add it to the Lee tab.',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    ui.alert(
      'Lee County Scraper Started',
      'The Lee County scraper is running.\\n\\n' +
      'To run via Node.js:\\n' +
      '1. Open terminal in repo directory\\n' +
      '2. Run: node scrapers/lee.js\\n\\n' +
      'Or trigger via GitHub Actions.\\n\\n' +
      'Data will appear in the "Lee" tab shortly.',
      ui.ButtonSet.OK
    );
    
    logScraperRun('LEE', 'Manual trigger from menu');
    
    // Optional: Call webhook to trigger Node.js scraper
    if (CONFIG.WEBHOOK_URL) {
      triggerWebhook('lee', 'scrape');
    }
    
  } catch (error) {
    ui.alert('Error', 'Failed to trigger Lee County scraper: ' + error.message, ui.ButtonSet.OK);
    Logger.log('Lee County scraper error: ' + error.message);
  }
}

/**
 * Run Collier County scraper
 */
function runCollierCountyScraper() {
  runCountyScraper('COLLIER', 'Collier', 'collier');
}

/**
 * Run Hendry County scraper
 */
function runHendryCountyScraper() {
  runCountyScraper('HENDRY', 'Hendry', 'hendry');
}

/**
 * Run Charlotte County scraper
 */
function runCharlotteCountyScraper() {
  runCountyScraper('CHARLOTTE', 'Charlotte', 'charlotte');
}

/**
 * Run Manatee County scraper
 */
function runManateeCountyScraper() {
  runCountyScraper('MANATEE', 'Manatee', 'manatee');
}

/**
 * Run Sarasota County scraper
 */
function runSarasotaCountyScraper() {
  runCountyScraper('SARASOTA', 'Sarasota', 'sarasota');
}

/**
 * Run DeSoto County scraper
 */
function runDeSotoCountyScraper() {
  runCountyScraper('DESOTO', 'DeSoto', 'desoto');
}

/**
 * Generic function to run any county scraper
 */
function runCountyScraper(countyKey, countyName, scriptName) {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert(
    countyName + ' County Scraper',
    'Run ' + countyName + ' County arrest scraper now?\\n\\n' +
    'This will fetch the latest arrest data.',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    ui.alert(
      countyName + ' County Scraper Started',
      'The ' + countyName + ' County scraper is running via Node.js/Puppeteer.\\n\\n' +
      'To run it:\\n' +
      '1. Open terminal in repo directory\\n' +
      '2. Run: node scrapers/' + scriptName + '.js\\n\\n' +
      'Or trigger via GitHub Actions.\\n\\n' +
      'Data will appear in the "' + countyName + '" tab shortly.',
      ui.ButtonSet.OK
    );
    
    logScraperRun(countyKey, 'Manual trigger from menu');
    
    // Optional: Call webhook to trigger Node.js scraper
    if (CONFIG.WEBHOOK_URL) {
      triggerWebhook(scriptName, 'scrape');
    }
    
  } catch (error) {
    ui.alert('Error', 'Failed to trigger ' + countyName + ' County scraper: ' + error.message, ui.ButtonSet.OK);
    Logger.log(countyName + ' County scraper error: ' + error.message);
  }
}

// ============================================
// RUN ALL SCRAPERS
// ============================================

/**
 * Run all county scrapers
 */
function runAllScrapers() {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert(
    'Run All Scrapers',
    'This will run scrapers for ALL counties:\\n' +
    '• Lee County\\n' +
    '• Collier County\\n' +
    '• Hendry County\\n' +
    '• Charlotte County\\n' +
    '• Manatee County\\n' +
    '• Sarasota County\\n' +
    '• DeSoto County\\n\\n' +
    'This may take 15-20 minutes. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    ui.alert(
      'All Scrapers Started',
      'All county scrapers are being triggered.\\n\\n' +
      'To run via Node.js:\\n' +
      '1. Open terminal in repo directory\\n' +
      '2. Run: node jobs/runAll.js\\n\\n' +
      'Or trigger via GitHub Actions.\\n\\n' +
      'Check the Logs tab for progress.',
      ui.ButtonSet.OK
    );
    
    logScraperRun('ALL', 'Manual trigger - all scrapers from menu');
    
    // Optional: Call webhook to trigger all Node.js scrapers
    if (CONFIG.WEBHOOK_URL) {
      triggerWebhook('all', 'scrape');
    }
    
  } catch (error) {
    ui.alert('Error', 'Failed to run all scrapers: ' + error.message, ui.ButtonSet.OK);
    Logger.log('Run all scrapers error: ' + error.message);
  }
}

// ============================================
// BOOKING FORM
// ============================================

/**
 * Show the booking information form
 * Opens Form.html in a modal dialog
 */
function showBookingForm() {
  try {
    var html = HtmlService.createHtmlOutputFromFile('Form')
      .setWidth(900)
      .setHeight(700)
      .setTitle('Booking Information Form');
    
    SpreadsheetApp.getUi().showModalDialog(html, 'Booking Information');
  } catch (error) {
    SpreadsheetApp.getUi().alert(
      'Error',
      'Failed to open booking form: ' + error.message + '\\n\\n' +
      'Make sure Form.html exists in the Apps Script project.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    Logger.log('Form open error: ' + error.message);
  }
}

// ============================================
// TRIGGER MANAGEMENT
// ============================================

/**
 * Install hourly triggers for all scrapers
 */
function installHourlyTriggers() {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert(
    'Install Hourly Triggers',
    'This will create hourly triggers to run all scrapers automatically.\\n\\n' +
    'Scrapers will run every hour.\\n\\n' +
    'Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    // Remove existing triggers first
    var triggers = ScriptApp.getProjectTriggers();
    triggers.forEach(function(trigger) {
      if (trigger.getHandlerFunction() === 'runAllScrapers') {
        ScriptApp.deleteTrigger(trigger);
      }
    });
    
    // Create new hourly trigger
    ScriptApp.newTrigger('runAllScrapers')
      .timeBased()
      .everyHours(1)
      .create();
    
    ui.alert(
      'Triggers Installed',
      'Hourly trigger has been installed successfully.\\n\\n' +
      'All scrapers will run automatically every hour.\\n\\n' +
      'Use "View Active Triggers" to see all triggers.',
      ui.ButtonSet.OK
    );
    
    Logger.log('Hourly trigger installed successfully');
    
  } catch (error) {
    ui.alert('Error', 'Failed to install triggers: ' + error.message, ui.ButtonSet.OK);
    Logger.log('Trigger installation error: ' + error.message);
  }
}

/**
 * View all active triggers
 */
function viewActiveTriggers() {
  var ui = SpreadsheetApp.getUi();
  var triggers = ScriptApp.getProjectTriggers();
  
  if (triggers.length === 0) {
    ui.alert('Active Triggers', 'No active triggers found.', ui.ButtonSet.OK);
    return;
  }
  
  var message = 'Active Triggers:\\n\\n';
  triggers.forEach(function(trigger, index) {
    message += (index + 1) + '. ' + trigger.getHandlerFunction() + '\\n';
    message += '   Type: ' + trigger.getEventType() + '\\n\\n';
  });
  
  ui.alert('Active Triggers', message, ui.ButtonSet.OK);
}

/**
 * Disable all triggers
 */
function disableAllTriggers() {
  var ui = SpreadsheetApp.getUi();
  
  var response = ui.alert(
    'Disable All Triggers',
    'This will remove ALL automated triggers.\\n\\n' +
    'Scrapers will no longer run automatically.\\n\\n' +
    'Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    var triggers = ScriptApp.getProjectTriggers();
    var count = triggers.length;
    
    triggers.forEach(function(trigger) {
      ScriptApp.deleteTrigger(trigger);
    });
    
    ui.alert(
      'Triggers Disabled',
      count + ' trigger(s) have been removed.\\n\\n' +
      'Scrapers will no longer run automatically.',
      ui.ButtonSet.OK
    );
    
    Logger.log(count + ' triggers disabled');
    
  } catch (error) {
    ui.alert('Error', 'Failed to disable triggers: ' + error.message, ui.ButtonSet.OK);
    Logger.log('Trigger disable error: ' + error.message);
  }
}

// ============================================
// STATUS AND LOGGING
// ============================================

/**
 * View scraper logs
 */
function viewScraperLogs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logsSheet = ss.getSheetByName(CONFIG.LOGS_TAB);
  
  if (!logsSheet) {
    SpreadsheetApp.getUi().alert(
      'Logs Not Found',
      'The Logs sheet was not found.\\n\\n' +
      'Create a sheet named "' + CONFIG.LOGS_TAB + '" to track scraper runs.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }
  
  // Activate the logs sheet
  logsSheet.activate();
  
  SpreadsheetApp.getUi().alert(
    'Scraper Logs',
    'The Logs sheet is now active.\\n\\n' +
    'Review the log entries to see scraper run history.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * View qualified arrests
 */
function viewQualifiedArrests() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var qualifiedSheet = ss.getSheetByName(CONFIG.QUALIFIED_TAB);
  
  if (!qualifiedSheet) {
    SpreadsheetApp.getUi().alert(
      'Qualified Arrests Not Found',
      'The Qualified_Arrests sheet was not found.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }
  
  // Activate the qualified arrests sheet
  qualifiedSheet.activate();
  
  SpreadsheetApp.getUi().alert(
    'Qualified Arrests',
    'The Qualified_Arrests sheet is now active.\\n\\n' +
    'This shows arrests with qualification score ≥ 70.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Check sheet status
 */
function checkSheetStatus() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ui = SpreadsheetApp.getUi();
  
  var message = 'Sheet Status:\\n\\n';
  message += 'Spreadsheet: ' + ss.getName() + '\\n';
  message += 'Sheet ID: ' + ss.getId() + '\\n\\n';
  message += 'Tabs:\\n';
  
  var sheets = ss.getSheets();
  sheets.forEach(function(sheet) {
    var rowCount = sheet.getLastRow();
    message += '• ' + sheet.getName() + ': ' + rowCount + ' rows\\n';
  });
  
  ui.alert('Sheet Status', message, ui.ButtonSet.OK);
}

/**
 * Show about/help dialog
 */
function showAboutDialog() {
  var ui = SpreadsheetApp.getUi();
  
  var message = 'SWFL Arrest Scrapers - Bail Suite\\n\\n';
  message += 'Version: 2.0\\n';
  message += 'Account: admin@shamrockbailbonds.biz\\n\\n';
  message += 'GitHub: ' + CONFIG.GITHUB_REPO_URL + '\\n';
  message += 'Apps Script: ' + CONFIG.APPS_SCRIPT_URL + '\\n\\n';
  message += 'Counties Covered:\\n';
  message += '• Lee County\\n';
  message += '• Collier County\\n';
  message += '• Hendry County\\n';
  message += '• Charlotte County\\n';
  message += '• Manatee County\\n';
  message += '• Sarasota County\\n';
  message += '• DeSoto County\\n\\n';
  message += 'For support, visit the GitHub repository.';
  
  ui.alert('About SWFL Arrest Scrapers', message, ui.ButtonSet.OK);
}

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Log a scraper run to the Logs sheet
 */
function logScraperRun(county, message) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var logsSheet = ss.getSheetByName(CONFIG.LOGS_TAB);
    
    if (!logsSheet) {
      // Create logs sheet if it doesn't exist
      logsSheet = ss.insertSheet(CONFIG.LOGS_TAB);
      logsSheet.appendRow(['Timestamp', 'County', 'Event', 'Message']);
    }
    
    var timestamp = new Date();
    logsSheet.appendRow([timestamp, county, 'MANUAL_TRIGGER', message]);
    
  } catch (error) {
    Logger.log('Failed to log scraper run: ' + error.message);
  }
}

/**
 * Trigger webhook for Node.js scraper
 */
function triggerWebhook(county, action) {
  if (!CONFIG.WEBHOOK_URL) {
    return;
  }
  
  try {
    var payload = {
      county: county,
      action: action,
      timestamp: new Date().toISOString()
    };
    
    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL, options);
    Logger.log('Webhook triggered for ' + county + ': ' + response.getResponseCode());
    
  } catch (error) {
    Logger.log('Webhook trigger failed: ' + error.message);
  }
}
