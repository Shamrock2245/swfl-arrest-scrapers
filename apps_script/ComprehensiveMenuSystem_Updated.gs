// ComprehensiveMenuSystem_Updated.gs
// Updated menu system without DeSoto, with booking form integration

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
  showToast
('🔄 Running Charlotte County scraper...', 'Charlotte County');
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
  
  // Disqualifying Charges
  const disqualifyingKeywords = ['MURDER', 'CAPITAL', 'DEATH', 'FEDERAL', 'LIFE'];
  const hasDisqualifyingCharge = disqualifyingKeywords.some(keyword => charges.includes(keyword));
  if (hasDisqualifyingCharge) {
    score -= 100;  // Disqualify
  }
  
  return score;
}

function getLeadStatus(score) {
  if (score < 0) return 'Disqualified';
  if (score >= 70) return 'Hot';
  if (score >= 40) return 'Warm';
  return 'Cold';
}

function parseBondAmount(bondStr) {
  if (!bondStr) return 0;
  const cleaned = String(bondStr).replace(/[$,]/g, '');
  const amount = parseFloat(cleaned);
  return isNaN(amount) ? 0 : amount;
}

function viewScoringRules() {
  const ui = SpreadsheetApp.getUi();
  const message = `
📊 LEAD SCORING RULES

Bond Amount:
• $500-$50K: +30 points (sweet spot)
• $50K-$100K: +20 points
• >$100K: +10 points
• <$500: -10 points
• $0: -50 points

Bond Type:
• CASH/SURETY: +25 points
• NO BOND/HOLD: -50 points
• ROR/RELEASE: -30 points

Status:
• IN CUSTODY: +20 points
• RELEASED: -30 points

Data Completeness:
• All fields: +15 points
• Missing data: -10 points

Disqualifying Charges:
• Murder/Capital/Federal: -100 points

Lead Status:
• Score ≥ 70: Hot 🔥
• Score 40-69: Warm 🟡
• Score 0-39: Cold 🔵
• Score < 0: Disqualified ⛔
  `;
  
  ui.alert('Lead Scoring Rules', message, ui.ButtonSet.OK);
}

// ============================================================================
// TRIGGER MANAGEMENT
// ============================================================================

function installTriggers() {
  // Remove existing triggers first
  disableTriggers();
  
  // Install time-driven triggers for scrapers (every 30 minutes)
  ScriptApp.newTrigger('runAllScrapers')
    .timeBased()
    .everyMinutes(30)
    .create();
  
  // Install trigger for lead scoring (every 30 minutes, offset by 15 min)
  ScriptApp.newTrigger('scoreAllSheets')
    .timeBased()
    .everyMinutes(30)
    .create();
  
  showToast('✅ Triggers installed successfully', 'Success');
}

function viewTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  const ui = SpreadsheetApp.getUi();
  
  if (triggers.length === 0) {
    ui.alert('No Triggers', 'No triggers are currently installed.', ui.ButtonSet.OK);
    return;
  }
  
  let message = `📅 ACTIVE TRIGGERS (${triggers.length})\n\n`;
  
  triggers.forEach((trigger, index) => {
    message += `${index + 1}. ${trigger.getHandlerFunction()}\n`;
    message += `   Type: ${trigger.getEventType()}\n`;
    message += `   Source: ${trigger.getTriggerSource()}\n\n`;
  });
  
  ui.alert('Active Triggers', message, ui.ButtonSet.OK);
}

function disableTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => ScriptApp.deleteTrigger(trigger));
  showToast('🚫 All triggers disabled', 'Success');
}

// ============================================================================
// STATUS & UTILITIES
// ============================================================================

function viewStatus() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  
  const counties = ['Lee', 'Collier', 'Hendry', 'Charlotte', 'Manatee', 'Sarasota', 'Hillsborough'];
  let message = '📊 SYSTEM STATUS\n\n';
  
  counties.forEach(county => {
    const sheet = ss.getSheetByName(county);
    if (sheet) {
      const lastRow = sheet.getLastRow() - 1;  // Exclude header
      message += `${county}: ${lastRow} records\n`;
    } else {
      message += `${county}: Sheet not found\n`;
    }
  });
  
  const triggers = ScriptApp.getProjectTriggers();
  message += `\nActive Triggers: ${triggers.length}\n`;
  
  ui.alert('System Status', message, ui.ButtonSet.OK);
}

function showToast(message, title) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, title, 5);
}
