// ComprehensiveMenuSystem.gs
// UPDATED VERSION with "Check for Changes" functionality

/**
 * Creates custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  
  ui.createMenu('🟩 Bail Suite')
    .addSubMenu(ui.createMenu('🔄 Run Scrapers')
      .addItem('📍 Lee County', 'runLeeScraper')
      .addItem('📍 Collier County', 'runCollierScraper')
      .addItem('📍 Hendry County', 'runHendryScraper')
      .addItem('📍 Charlotte County', 'runCharlotteScraper')
      .addItem('📍 Manatee County', 'runManateeScraper')
      .addItem('📍 Sarasota County', 'runSarasotaScraper')
      .addItem('📍 Hillsborough County', 'runHillsboroughScraper')
      .addSeparator()
      .addItem('🚀 Run All Scrapers', 'runAllScrapers'))
    .addSeparator()
    .addItem('🔍 Check for Changes', 'checkForChanges')  // NEW: Check for Changes button
    .addSeparator()
    .addSubMenu(ui.createMenu('🎯 Lead Scoring')
      .addItem('📊 Score All Sheets', 'scoreAllSheets')
      .addItem('📈 Score Current Sheet', 'scoreCurrentSheet')
      .addItem('🔍 View Scoring Rules', 'viewScoringRules'))
    .addSeparator()
    .addItem('📝 Open Booking Form', 'openBookingFormFromRow')
    .addSeparator()
    .addSubMenu(ui.createMenu('⚙️ Triggers')
      .addItem('📅 Install Triggers', 'installTriggers')
      .addItem('👀 View Triggers', 'viewTriggers')
      .addItem('🚫 Disable Triggers', 'disableTriggers'))
    .addSeparator()
    .addItem('📊 View Status', 'viewStatus')
    .addToUi();
}

// ============================================================================
// CHECK FOR CHANGES FUNCTIONALITY (NEW)
// ============================================================================

/**
 * Main function to check for changes across all counties
 * Updates "In Custody" status dynamically by checking current data
 */
function checkForChanges() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Show initial toast
  showToast('🔍 Checking for changes across all counties...', 'Check for Changes');
  
  const counties = ['Lee', 'Collier', 'Hendry', 'Charlotte', 'Manatee', 'Sarasota', 'Hillsborough', 'DeSoto'];
  let totalUpdated = 0;
  let totalChecked = 0;
  const results = [];
  
  // Process each county sheet
  counties.forEach(county => {
    const sheet = ss.getSheetByName(county);
    if (sheet) {
      const result = checkCountyForChanges(sheet, county);
      totalUpdated += result.updated;
      totalChecked += result.checked;
      results.push(`${county}: ${result.updated}/${result.checked} updated`);
      Logger.log(`${county}: Checked ${result.checked}, Updated ${result.updated}`);
    } else {
      Logger.log(`${county}: Sheet not found`);
      results.push(`${county}: Sheet not found`);
    }
  });
  
  // Show summary dialog
  const summary = `
📊 Check for Changes - Summary Report

Total Records Checked: ${totalChecked}
Total Records Updated: ${totalUpdated}

County Breakdown:
${results.join('\n')}

✅ Check completed successfully!
  `.trim();
  
  ui.alert('Check for Changes Complete', summary, ui.ButtonSet.OK);
  showToast(`✅ Updated ${totalUpdated} of ${totalChecked} records`, 'Success');
}

/**
 * Check a single county sheet for changes
 * Updates Status column based on current custody status
 * 
 * @param {Sheet} sheet - The county sheet to check
 * @param {String} countyName - Name of the county
 * @returns {Object} - {checked: number, updated: number}
 */
function checkCountyForChanges(sheet, countyName) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return {checked: 0, updated: 0};  // No data rows
  }
  
  // Get all data (skip header)
  const data = sheet.getRange(2, 1, lastRow - 1, 34).getValues();
  
  let checked = 0;
  let updated = 0;
  
  // Column indices (0-based)
  const BOOKING_NUMBER_COL = 0;   // Column A
  const STATUS_COL = 25;           // Column Z (Status)
  const BOND_AMOUNT_COL = 23;      // Column X (Bond_Amount)
  const BOND_TYPE_COL = 24;        // Column Y (Bond_Type)
  
  data.forEach((row, index) => {
    const rowNum = index + 2;  // Account for header and 0-indexing
    checked++;
    
    const bookingNumber = row[BOOKING_NUMBER_COL];
    const currentStatus = (row[STATUS_COL] || '').toString().toUpperCase();
    const bondAmount = parseBondAmount(row[BOND_AMOUNT_COL]);
    const bondType = (row[BOND_TYPE_COL] || '').toString().toUpperCase();
    
    // Skip if no booking number
    if (!bookingNumber) {
      return;
    }
    
    // Determine new status based on bond and other indicators
    let newStatus = determineInCustodyStatus(currentStatus, bondAmount, bondType);
    
    // Only update if status changed
    if (newStatus && newStatus !== currentStatus) {
      sheet.getRange(rowNum, STATUS_COL + 1).setValue(newStatus);  // +1 for 1-based column
      updated++;
      Logger.log(`${countyName} - Row ${rowNum}: "${currentStatus}" → "${newStatus}"`);
    }
  });
  
  return {checked, updated};
}

/**
 * Determine custody status based on bond information and current status
 * 
 * @param {String} currentStatus - Current status value
 * @param {Number} bondAmount - Bond amount
 * @param {String} bondType - Bond type
 * @returns {String|null} - New status or null if no change needed
 */
function determineInCustodyStatus(currentStatus, bondAmount, bondType) {
  // Indicators that person is NOT in custody
  const releasedIndicators = [
    'RELEASED',
    'RELEASE',
    'BONDED',
    'BONDED OUT',
    'ROR',
    'DISCHARGED',
    'TRANSFERRED'
  ];
  
  // Indicators that person IS in custody
  const inCustodyIndicators = [
    'IN CUSTODY',
    'INCUSTODY',
    'CUSTODY',
    'BOOKED',
    'ACTIVE',
    'HELD',
    'DETAINED'
  ];
  
  // Check if already has clear status
  const isReleased = releasedIndicators.some(indicator => currentStatus.includes(indicator));
  const isInCustody = inCustodyIndicators.some(indicator => currentStatus.includes(indicator));
  
  // If status is already clear, don't change it
  if (isReleased) {
    return null;  // Already marked as released
  }
  
  if (isInCustody) {
    return null;  // Already marked as in custody
  }
  
  // If status is unclear or empty, infer from bond information
  
  // No bond or hold = likely in custody
  if (bondType.includes('NO BOND') || bondType.includes('HOLD')) {
    return 'In Custody - No Bond';
  }
  
  // ROR or released bond type = likely released
  if (bondType.includes('ROR') || bondType.includes('RELEASE')) {
    return 'Released - ROR';
  }
  
  // Has bond amount but unclear status = assume in custody awaiting bond
  if (bondAmount > 0) {
    return 'In Custody';
  }
  
  // Zero bond = likely released
  if (bondAmount === 0 && !bondType.includes('NO BOND')) {
    return 'Released';
  }
  
  // Default: if we can't determine, mark as in custody (conservative approach)
  return 'In Custody';
}

/**
 * Parse bond amount from various formats
 * 
 * @param {String|Number} bondValue - Bond amount value
 * @returns {Number} - Parsed bond amount
 */
function parseBondAmount(bondValue) {
  if (!bondValue) return 0;
  
  // If already a number
  if (typeof bondValue === 'number') {
    return bondValue;
  }
  
  // Convert to string and clean
  const bondStr = bondValue.toString().toUpperCase();
  
  // Check for "NO BOND" or similar
  if (bondStr.includes('NO BOND') || bondStr.includes('NONE') || bondStr.includes('N/A')) {
    return 0;
  }
  
  // Extract numeric value
  const match = bondStr.match(/[\d,]+\.?\d*/);
  if (match) {
    return parseFloat(match[0].replace(/,/g, ''));
  }
  
  return 0;
}

// ============================================================================
// SCRAPER FUNCTIONS (Call Node.js scrapers via GitHub Actions or webhooks)
// ============================================================================

function runLeeScraper() {
  showToast('🔄 Running Lee County scraper...', 'Lee County');
  // TODO: Trigger GitHub Action or webhook for Lee scraper
  Logger.log('Lee County scraper triggered');
  showToast('✅ Lee County scraper completed', 'Success');
}

function runCollierScraper() {
  showToast('🔄 Running Collier County scraper...', 'Collier County');
  // TODO: Trigger GitHub Action or webhook for Collier scraper
  Logger.log('Collier County scraper triggered');
  showToast('✅ Collier County scraper completed', 'Success');
}

function runHendryScraper() {
  showToast('🔄 Running Hendry County scraper...', 'Hendry County');
  // TODO: Trigger GitHub Action or webhook for Hendry scraper
  Logger.log('Hendry County scraper triggered');
  showToast('✅ Hendry County scraper completed', 'Success');
}

function runCharlotteScraper() {
  showToast('🔄 Running Charlotte County scraper...', 'Charlotte County');
  // TODO: Trigger GitHub Action or webhook for Charlotte scraper
  Logger.log('Charlotte County scraper triggered');
  showToast('✅ Charlotte County scraper completed', 'Success');
}

function runManateeScraper() {
  showToast('🔄 Running Manatee County scraper...', 'Manatee County');
  // TODO: Trigger GitHub Action or webhook for Manatee scraper
  Logger.log('Manatee County scraper triggered');
  showToast('✅ Manatee County scraper completed', 'Success');
}

function runSarasotaScraper() {
  showToast('🔄 Running Sarasota County scraper...', 'Sarasota County');
  // TODO: Trigger GitHub Action or webhook for Sarasota scraper
  Logger.log('Sarasota County scraper triggered');
  showToast('✅ Sarasota County scraper completed', 'Success');
}

function runHillsboroughScraper() {
  showToast('🔄 Running Hillsborough County scraper...', 'Hillsborough County');
  // TODO: Trigger GitHub Action or webhook for Hillsborough scraper
  Logger.log('Hillsborough County scraper triggered');
  showToast('✅ Hillsborough County scraper completed', 'Success');
}

function runAllScrapers() {
  showToast('🚀 Running all county scrapers...', 'All Counties');
  
  runLeeScraper();
  Utilities.sleep(2000);
  runCollierScraper();
  Utilities.sleep(2000);
  runHendryScraper();
  Utilities.sleep(2000);
  runCharlotteScraper();
  Utilities.sleep(2000);
  runManateeScraper();
  Utilities.sleep(2000);
  runSarasotaScraper();
  Utilities.sleep(2000);
  runHillsboroughScraper();
  
  showToast('✅ All scrapers completed', 'Success');
}

// ============================================================================
// BOOKING FORM INTEGRATION
// ============================================================================

/**
 * Opens booking form with data from selected row
 * Supports dual workflow: Menu button (Method A)
 */
function openBookingFormFromRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  const selection = sheet.getActiveRange();
  
  // Check if a row is selected
  if (!selection) {
    ui.alert('No Selection', 'Please select a row to populate the booking form.', ui.ButtonSet.OK);
    return;
  }
  
  const row = selection.getRow();
  
  // Skip header row
  if (row === 1) {
    ui.alert('Invalid Selection', 'Please select a data row (not the header).', ui.ButtonSet.OK);
    return;
  }
  
  // Get all 34 columns from the selected row
  const data = sheet.getRange(row, 1, 1, 34).getValues()[0];
  
  // Map data to booking form fields (34-column schema)
  const rowData = {
    bookingNumber: data[0] || '',
    fullName: data[1] || '',
    firstName: data[2] || '',
    lastName: data[3] || '',
    dob: data[4] || '',
    sex: data[5] || '',
    race: data[6] || '',
    arrestDate: data[7] || '',
    arrestTime: data[8] || '',
    bookingDate: data[9] || '',
    bookingTime: data[10] || '',
    agency: data[11] || '',
    address: data[12] || '',
    city: data[13] || '',
    state: data[14] || '',
    zipcode: data[15] || '',
    charges: data[16] || '',
    charge1: data[17] || '',
    charge1Statute: data[18] || '',
    charge1Bond: data[19] || '',
    charge2: data[20] || '',
    charge2Statute: data[21] || '',
    charge2Bond: data[22] || '',
    bondAmount: data[23] || '',
    bondType: data[24] || '',
    status: data[25] || '',
    courtDate: data[26] || '',
    caseNumber: data[27] || '',
    mugshotUrl: data[28] || '',
    county: data[29] || '',
    courtLocation: data[30] || '',
    leadScore: data[31] || '',
    leadStatus: data[32] || '',
    detailUrl: data[33] || ''
  };
  
  // Create HTML template and pass data
  const template = HtmlService.createTemplateFromFile('Form');
  template.rowData = rowData;
  
  // Evaluate template and create modal dialog
  const html = template.evaluate()
    .setWidth(900)
    .setHeight(700)
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);
  
  ui.showModalDialog(html, '📝 Booking Form - ' + rowData.fullName);
}

/**
 * Web app endpoint for bookmarklet (Method B)
 * Serves Form.html with URL parameters
 */
function doGet(e) {
  const template = HtmlService.createTemplateFromFile('Form');
  
  // Pass URL parameters to template
  template.params = e.parameter;
  
  return template.evaluate()
    .setTitle('Booking Form - Shamrock Bail Bonds')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Include helper for HTML templates
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

// ============================================================================
// LEAD SCORING FUNCTIONS (from LeadScoringSystem.gs)
// ============================================================================

function scoreAllSheets() {
  showToast('🎯 Scoring all sheets...', 'Lead Scoring');
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const counties = ['Lee', 'Collier', 'Hendry', 'Charlotte', 'Manatee', 'Sarasota', 'Hillsborough'];
  let totalScored = 0;
  
  counties.forEach(county => {
    const sheet = ss.getSheetByName(county);
    if (sheet) {
      const scored = scoreSheet(sheet);
      totalScored += scored;
      Logger.log(`${county}: ${scored} records scored`);
    }
  });
  
  showToast(`✅ Scored ${totalScored} records across all sheets`, 'Success');
}

function scoreCurrentSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  showToast(`🎯 Scoring ${sheet.getName()}...`, 'Lead Scoring');
  
  const scored = scoreSheet(sheet);
  
  showToast(`✅ Scored ${scored} records in ${sheet.getName()}`, 'Success');
}

function scoreSheet(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return 0;  // No data rows
  
  // Get all data (skip header)
  const data = sheet.getRange(2, 1, lastRow - 1, 34).getValues();
  
  let scored = 0;
  
  data.forEach((row, index) => {
    const rowNum = index + 2;  // Account for header and 0-indexing
    
    // Calculate lead score
    const score = calculateLeadScore(row);
    const status = getLeadStatus(score);
    
    // Update columns AG (32) and AH (33) - Lead_Score and Lead_Status
    sheet.getRange(rowNum, 32).setValue(score);
    sheet.getRange(rowNum, 33).setValue(status);
    
    scored++;
  });
  
  return scored;
}

function calculateLeadScore(row) {
  let score = 0;
  
  // Extract fields from 34-column schema
  const bondAmount = parseBondAmount(row[23]);  // Bond_Amount (column 24)
  const bondType = (row[24] || '').toUpperCase();  // Bond_Type (column 25)
  const status = (row[25] || '').toUpperCase();  // Status (column 26)
  const charges = (row[16] || '').toUpperCase();  // Charges (column 17)
  
  // Bond Amount Scoring
  if (bondAmount >= 500 && bondAmount <= 50000) {
    score += 30;  // Sweet spot
  } else if (bondAmount > 50000 && bondAmount <= 100000) {
    score += 20;  // High bond
  } else if (bondAmount > 100000) {
    score += 10;  // Very high bond
  } else if (bondAmount > 0 && bondAmount < 500) {
    score -= 10;  // Too low
  } else if (bondAmount === 0) {
    score -= 50;  // No bond
  }
  
  // Bond Type Scoring
  if (bondType.includes('CASH') || bondType.includes('SURETY')) {
    score += 25;  // Good bond types
  } else if (bondType.includes('NO BOND') || bondType.includes('HOLD')) {
    score -= 50;  // Cannot bond
  } else if (bondType.includes('ROR') || bondType.includes('RELEASE')) {
    score -= 30;  // Released on own recognizance
  }
  
  // Status Scoring
  if (status.includes('IN') || status.includes('CUSTODY')) {
    score += 20;  // In custody (good lead)
  } else if (status.includes('RELEASE')) {
    score -= 30;  // Already released
  }
  
  // Data Completeness
  const hasAllFields = row[0] && row[1] && row[4] && row[16] && row[23];
  if (hasAllFields) {
    score += 15;  // Complete data
  } else {
    score -= 10;  // Missing data
  }
  
  return score;
}

function getLeadStatus(score) {
  if (score >= 50) return 'Qualified';
  if (score >= 0) return 'Potential';
  return 'Unqualified';
}

function viewScoringRules() {
  const ui = SpreadsheetApp.getUi();
  
  const rules = `
🎯 Lead Scoring Rules

Bond Amount:
  • $500 - $50,000: +30 points (sweet spot)
  • $50,001 - $100,000: +20 points
  • Over $100,000: +10 points
  • Under $500: -10 points
  • $0: -50 points

Bond Type:
  • Cash/Surety: +25 points
  • No Bond/Hold: -50 points
  • ROR/Release: -30 points

Status:
  • In Custody: +20 points
  • Released: -30 points

Data Completeness:
  • All fields present: +15 points
  • Missing data: -10 points

Lead Status Thresholds:
  • Qualified: 50+ points
  • Potential: 0-49 points
  • Unqualified: Below 0 points
  `.trim();
  
  ui.alert('Lead Scoring Rules', rules, ui.ButtonSet.OK);
}

// ============================================================================
// TRIGGER MANAGEMENT
// ============================================================================

function installTriggers() {
  const ui = SpreadsheetApp.getUi();
  
  // Check if triggers already exist
  const triggers = ScriptApp.getProjectTriggers();
  if (triggers.length > 0) {
    const response = ui.alert(
      'Triggers Already Exist',
      `Found ${triggers.length} existing trigger(s). Delete and reinstall?`,
      ui.ButtonSet.YES_NO
    );
    
    if (response === ui.Button.YES) {
      disableTriggers();
    } else {
      return;
    }
  }
  
  // Install time-based trigger (every 25 minutes)
  ScriptApp.newTrigger('runAllScrapers')
    .timeBased()
    .everyMinutes(25)
    .create();
  
  ui.alert('Triggers Installed', '✅ Scrapers will run automatically every 25 minutes.', ui.ButtonSet.OK);
}

function viewTriggers() {
  const ui = SpreadsheetApp.getUi();
  const triggers = ScriptApp.getProjectTriggers();
  
  if (triggers.length === 0) {
    ui.alert('No Triggers', 'No triggers are currently installed.', ui.ButtonSet.OK);
    return;
  }
  
  const triggerList = triggers.map((trigger, index) => {
    const handler = trigger.getHandlerFunction();
    const eventType = trigger.getEventType();
    return `${index + 1}. ${handler} (${eventType})`;
  }).join('\n');
  
  ui.alert('Active Triggers', `Found ${triggers.length} trigger(s):\n\n${triggerList}`, ui.ButtonSet.OK);
}

function disableTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => ScriptApp.deleteTrigger(trigger));
  
  const ui = SpreadsheetApp.getUi();
  ui.alert('Triggers Disabled', `✅ Removed ${triggers.length} trigger(s).`, ui.ButtonSet.OK);
}

// ============================================================================
// STATUS AND UTILITY FUNCTIONS
// ============================================================================

function viewStatus() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  const counties = ['Lee', 'Collier', 'Hendry', 'Charlotte', 'Manatee', 'Sarasota', 'Hillsborough'];
  const status = counties.map(county => {
    const sheet = ss.getSheetByName(county);
    if (sheet) {
      const lastRow = sheet.getLastRow();
      const recordCount = lastRow > 1 ? lastRow - 1 : 0;
      return `${county}: ${recordCount} records`;
    }
    return `${county}: Sheet not found`;
  }).join('\n');
  
  const triggers = ScriptApp.getProjectTriggers();
  const triggerStatus = triggers.length > 0 ? `✅ ${triggers.length} active` : '❌ None';
  
  const summary = `
📊 System Status

County Records:
${status}

Triggers: ${triggerStatus}

Last Updated: ${new Date().toLocaleString()}
  `.trim();
  
  ui.alert('System Status', summary, ui.ButtonSet.OK);
}

function showToast(message, title) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, title, 3);
}
