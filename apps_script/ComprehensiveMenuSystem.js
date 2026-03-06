// ComprehensiveMenuSystem.gs
// CLEAN + CONGRUENT VERSION (Dec 14, 2025)
// - Single onOpen() owner
// - Bail Suite menu + submenus
// - Lead Scoring submenu uses LeadScoringSystem.gs functions (no duplicates here)
// - Preserves Send to Form + Check for Changes + Triggers + Status
// - Court email menu placeholders preserved

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  const menu = ui.createMenu('🟩 Bail Suite')
    .addItem('📝 Send to Form', 'sendSelectedRowToForm')
    .addSeparator()
    .addItem('🔍 Check for Changes', 'checkForChanges')
    .addItem('🔄 Update In Custody Status (Active Sheet)', 'updateInCustodyStatus')
    .addSeparator()
    .addSubMenu(ui.createMenu('📧 Court Emails')
      .addItem('▶️ Process New Emails', 'processCourtEmails')
      .addSeparator()
      .addItem('🔄 Process Historical Emails (Jan 2025 - Now)', 'processHistoricalEmails')
      .addItem('📅 Process Custom Date Range', 'processDateRange')
      .addSeparator()
      .addItem('⚙️ Configure Slack Webhooks', 'showSlackConfig')
      .addItem('📊 View Processing Log', 'showProcessingLog'))
    .addSeparator();

  // Lead scoring submenu is built by LeadScoringSystem.gs (safe)
  if (typeof addLeadScoringMenuItems === "function") {
    addLeadScoringMenuItems(menu);
  } else {
    menu.addSubMenu(
      ui.createMenu('🎯 Lead Scoring')
        .addItem('⚠️ LeadScoringSystem.gs not loaded', 'noop_')
    );
  }

  menu
    .addSeparator()
    .addSubMenu(ui.createMenu('⚙️ Triggers')
      .addItem('📅 Install Triggers', 'installTriggers')
      .addItem('👀 View Triggers', 'viewTriggers')
      .addItem('🚫 Disable Triggers', 'disableTriggers'))
    .addSeparator()
    .addItem('📊 View Status', 'viewStatus')
    .addToUi();
}

function noop_() {
  SpreadsheetApp.getUi().alert("Missing file", "LeadScoringSystem.gs wasn’t found/loaded in this project.", SpreadsheetApp.getUi().ButtonSet.OK);
}

// ============================================================================
// SEND TO FORM FUNCTIONALITY
// ============================================================================

function sendSelectedRowToForm() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  const activeRange = sheet.getActiveRange();

  if (!activeRange) {
    ui.alert('No Selection', 'Please select a row to send to the form.', ui.ButtonSet.OK);
    return;
  }

  const row = activeRange.getRow();
  if (row === 1) {
    ui.alert('Invalid Selection', 'Cannot send header row. Please select a data row.', ui.ButtonSet.OK);
    return;
  }

  const lastCol = sheet.getLastColumn();
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const rowData = sheet.getRange(row, 1, 1, lastCol).getValues()[0];

  const data = {};
  headers.forEach((header, index) => {
    if (header) data[header.toString().trim()] = rowData[index];
  });

  const formData = mapSheetDataToForm_(data);

  const props = PropertiesService.getScriptProperties();
  props.setProperty('FORM_PREFILL_DATA', JSON.stringify(formData));

  const formUrl = props.getProperty('FORM_URL') || getFormUrl_();

  const html = HtmlService.createHtmlOutput(`
    <script>
      window.open('${formUrl}?prefill=true', '_blank');
      google.script.host.close();
    </script>
  `).setWidth(200).setHeight(100);

  ui.showModalDialog(html, 'Opening Form...');
  showToast_('✅ Data sent to form. Opening in new tab...', 'Success');
}

function mapSheetDataToForm_(sheetData) {
  return {
    defendantFullName: sheetData['Full_Name'] || '',
    defendantFirstName: sheetData['First_Name'] || '',
    defendantLastName: sheetData['Last_Name'] || '',
    defendantDOB: formatDate_(sheetData['DOB']),
    defendantSex: sheetData['Sex'] || '',
    defendantRace: sheetData['Race'] || '',
    defendantHeight: sheetData['Height'] || '',
    defendantWeight: sheetData['Weight'] || '',
    defendantArrestNumber: sheetData['Booking_Number'] || '',

    defendantStreetAddress: sheetData['Address'] || '',
    defendantCity: sheetData['City'] || '',
    defendantState: sheetData['State'] || 'FL',
    defendantZip: sheetData['Zipcode'] || '',

    defendantPhone: sheetData['Phone'] || '',
    defendantEmail: sheetData['Email'] || '',

    charges: parseChargesFromSheet_(sheetData),

    source: sheetData['County'] || 'spreadsheet',
    scrapedAt: new Date().toISOString(),
    leadScore: sheetData['Lead_Score'] || '',
    leadStatus: sheetData['Lead_Status'] || ''
  };
}

function parseChargesFromSheet_(sheetData) {
  const charges = [];
  const chargesField = sheetData['Charges'] || '';

  if (chargesField) {
    try {
      const parsed = JSON.parse(chargesField);
      if (Array.isArray(parsed)) return parsed;
    } catch (e) { }

    const chargesList = chargesField.split(/[;,\n]/).map(c => c.trim()).filter(Boolean);
    chargesList.forEach(charge => {
      charges.push({
        description: charge,
        bondAmount: sheetData['Bond_Amount'] || '',
        bondType: sheetData['Bond_Type'] || '',
        caseNumber: sheetData['Case_Number'] || '',
        courtLocation: sheetData['Court_Location'] || '',
        courtDate: formatDate_(sheetData['Court_Date'])
      });
    });
  }

  if (charges.length === 0 && sheetData['Bond_Amount']) {
    charges.push({
      description: sheetData['Charges'] || 'See booking details',
      bondAmount: sheetData['Bond_Amount'] || '',
      bondType: sheetData['Bond_Type'] || '',
      caseNumber: sheetData['Case_Number'] || '',
      courtLocation: sheetData['Court_Location'] || '',
      courtDate: formatDate_(sheetData['Court_Date'])
    });
  }

  return charges;
}

function formatDate_(dateValue) {
  if (!dateValue) return '';
  try {
    let date;
    if (dateValue instanceof Date) date = dateValue;
    else if (typeof dateValue === 'string') date = new Date(dateValue);
    else return '';

    if (isNaN(date.getTime())) return '';

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  } catch (e) {
    return '';
  }
}

function getFormUrl_() {
  // Replace with your deployed web app URL (or store it in Script Properties as FORM_URL)
  return 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec';
}

function getPrefillData() {
  const props = PropertiesService.getScriptProperties();
  const dataJson = props.getProperty('FORM_PREFILL_DATA');
  if (dataJson) {
    props.deleteProperty('FORM_PREFILL_DATA');
    return JSON.parse(dataJson);
  }
  return null;
}

// ============================================================================
// CHECK FOR CHANGES (kept from your version)
// ============================================================================

function checkForChanges() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const modeResponse = ui.alert(
    'Check for Changes',
    'Choose mode:\n\nYes = Full web-check (queries county sites)\nNo = Quick local inference\nCancel = Abort',
    ui.ButtonSet.YES_NO_CANCEL
  );

  if (modeResponse === ui.Button.CANCEL) {
    ui.alert('Check cancelled', 'No changes performed.', ui.ButtonSet.OK);
    return;
  }

  const fullWebCheck = (modeResponse === ui.Button.YES);
  showToast_(fullWebCheck ? '🔎 Running full web-check...' : '🔍 Running quick inference...', 'Check for Changes');

  const counties = ['Lee', 'Collier', 'Hendry', 'Charlotte', 'Manatee', 'Sarasota', 'Hillsborough', 'DeSoto'];
  let totalUpdated = 0;
  let totalChecked = 0;
  const results = [];

  counties.forEach(county => {
    const sheet = ss.getSheetByName(county);
    if (sheet) {
      const result = updateCountyInCustodyStatus(sheet, county, fullWebCheck);
      totalUpdated += result.updated;
      totalChecked += result.checked;
      results.push(`${county}: ${result.updated}/${result.checked} updated`);
    } else {
      results.push(`${county}: Sheet not found`);
    }
  });

  ui.alert(
    'Check for Changes Complete',
    `Total Checked: ${totalChecked}\nTotal Updated: ${totalUpdated}\n\n${results.join('\n')}`,
    ui.ButtonSet.OK
  );
  showToast_(`✅ Updated ${totalUpdated} of ${totalChecked} records`, 'Success');
}

function updateInCustodyStatus() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const countyName = sheet.getName();
  showToast_(`🔄 Updating ${countyName} custody status...`, 'Update Status');

  const result = updateCountyInCustodyStatus(sheet, countyName, false);
  showToast_(`✅ Updated ${result.updated} of ${result.checked} records`, 'Success');
}

// NOTE: This function stays as-is from your current project.
// If you want, we can harden it further next (header mapping + batching + strict status rules).
function updateCountyInCustodyStatus(sheet, countyName, fullWebCheck = false) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return { checked: 0, updated: 0 };

  let lastCol = sheet.getLastColumn();
  let headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(h => (h || '').toString().trim());

  let bookingCol = headers.indexOf('Booking_Number');
  let statusCol = headers.indexOf('Status');
  let bondAmountCol = headers.indexOf('Bond_Amount');
  let bondTypeCol = headers.indexOf('Bond_Type');
  let lastCheckedCol = headers.indexOf('LastChecked');
  let lastCheckedModeCol = headers.indexOf('LastCheckedMode');

  if (lastCheckedCol === -1 || lastCheckedModeCol === -1) {
    let appendIndex = lastCol + 1;
    if (lastCheckedCol === -1) { sheet.getRange(1, appendIndex).setValue('LastChecked'); appendIndex++; }
    if (lastCheckedModeCol === -1) { sheet.getRange(1, appendIndex).setValue('LastCheckedMode'); appendIndex++; }
    lastCol = sheet.getLastColumn();
    headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(h => (h || '').toString().trim());
    bookingCol = headers.indexOf('Booking_Number');
    statusCol = headers.indexOf('Status');
    bondAmountCol = headers.indexOf('Bond_Amount');
    bondTypeCol = headers.indexOf('Bond_Type');
    lastCheckedCol = headers.indexOf('LastChecked');
    lastCheckedModeCol = headers.indexOf('LastCheckedMode');
  }

  if (bookingCol === -1 || statusCol === -1) {
    bookingCol = (bookingCol === -1) ? 0 : bookingCol;
    bondAmountCol = (bondAmountCol === -1) ? 23 : bondAmountCol;
    bondTypeCol = (bondTypeCol === -1) ? 24 : bondTypeCol;
    statusCol = (statusCol === -1) ? 25 : statusCol;
  }

  const numRows = lastRow - 1;
  const data = sheet.getRange(2, 1, numRows, lastCol).getValues();
  const statusValues = sheet.getRange(2, statusCol + 1, numRows, 1).getValues();
  const lastCheckedValues = sheet.getRange(2, lastCheckedCol + 1, numRows, 1).getValues();
  const lastCheckedModeValues = sheet.getRange(2, lastCheckedModeCol + 1, numRows, 1).getValues();

  let checked = 0;
  let updated = 0;
  const now = new Date();
  const modeText = fullWebCheck ? 'web' : 'local';

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    const bookingNumber = row[bookingCol];
    if (!bookingNumber) continue;

    checked++;
    const currentStatus = (row[statusCol] || '').toString();
    const bondAmount = parseBondAmount_(row[bondAmountCol]);
    const bondType = (row[bondTypeCol] || '').toString();

    let inferredStatus = determineInCustodyStatus_(currentStatus, bondAmount, bondType);

    if (fullWebCheck) {
      try {
        const inCustody = checkIfInCustody_(countyName, String(bookingNumber));
        inferredStatus = inCustody ? 'In Custody' : 'Released';
      } catch (err) { }
    }

    if (inferredStatus && inferredStatus !== currentStatus) {
      statusValues[i][0] = inferredStatus;
      updated++;
    }

    lastCheckedValues[i][0] = now;
    lastCheckedModeValues[i][0] = modeText;
  }

  sheet.getRange(2, statusCol + 1, numRows, 1).setValues(statusValues);
  sheet.getRange(2, lastCheckedCol + 1, numRows, 1).setValues(lastCheckedValues);
  sheet.getRange(2, lastCheckedModeCol + 1, numRows, 1).setValues(lastCheckedModeValues);

  return { checked, updated };
}

function determineInCustodyStatus_(currentStatus, bondAmount, bondType) {
  currentStatus = (currentStatus || '').toString().toUpperCase();
  bondType = (bondType || '').toString().toUpperCase();

  const releasedIndicators = ['RELEASED', 'RELEASE', 'BONDED', 'BONDED OUT', 'ROR', 'DISCHARGED', 'TRANSFERRED'];
  const inCustodyIndicators = ['IN CUSTODY', 'INCUSTODY', 'CUSTODY', 'BOOKED', 'ACTIVE', 'HELD', 'DETAINED'];

  const isReleased = releasedIndicators.some(ind => currentStatus.includes(ind));
  const isInCustody = inCustodyIndicators.some(ind => currentStatus.includes(ind));

  if (isReleased) return null;
  if (isInCustody) return null;

  if (bondAmount === 0 || bondType.includes('NO BOND') || bondType.includes('HOLD')) return 'In Custody';
  if (bondType.includes('ROR') || bondType.includes('RELEASE')) return 'Released';

  return null;
}

function parseBondAmount_(value) {
  if (!value) return 0;
  const str = value.toString().replace(/[$,]/g, '');
  const num = parseFloat(str);
  return isNaN(num) ? 0 : num;
}

function checkIfInCustody_(countyName, bookingNumber) {
  // Placeholder for your per-county web check logic
  return false;
}

// ============================================================================
// COURT EMAIL PLACEHOLDERS
// ============================================================================

function processCourtEmails() { showToast_('📧 Processing court emails...', 'Court Emails'); }
function processHistoricalEmails() { showToast_('📧 Processing historical emails...', 'Court Emails'); }
function processDateRange() { SpreadsheetApp.getUi().alert('Date Range', 'Coming soon.', SpreadsheetApp.getUi().ButtonSet.OK); }
function showSlackConfig() {
  if (typeof openConfigModal === 'function') {
    openConfigModal();
  } else {
    SpreadsheetApp.getUi().alert('Config module not found. Deploy newest code version.');
  }
}
function showProcessingLog() { SpreadsheetApp.getUi().alert('Processing Log', 'Coming soon.', SpreadsheetApp.getUi().ButtonSet.OK); }

// ============================================================================
// TRIGGER MANAGEMENT
// ============================================================================

function installTriggers() {
  const ui = SpreadsheetApp.getUi();

  // Confirm Intent
  const response = ui.alert(
    'Factory Reset Triggers',
    'This will DELETE all existing triggers and re-install the standard automation suite:\n\n' +
    '1. 🚓 Lee County Arrests (Hourly)\n' +
    '2. 📧 Court Email Processor (Daily: 7am, 10am, 2pm, 5pm)\n' +
    '3. 🔍 Custody Status Checks (Every 6 hours)\n\n' +
    'Proceed?',
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) return;

  // 1. Clear All
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => ScriptApp.deleteTrigger(t));

  // 2. Install Lee Scraper
  if (typeof runLeeArrestsNow === 'function') {
    ScriptApp.newTrigger('runLeeArrestsNow').timeBased().everyHours(1).create();
  } else {
    console.warn('runLeeArrestsNow not found. Skipping.');
  }

  // 3. Install Court Email Processor
  if (typeof processCourtEmails === 'function') {
    // 7am, 10am, 2pm (14), 5pm (17)
    [7, 10, 14, 17].forEach(h => {
      ScriptApp.newTrigger('processCourtEmails').timeBased().atHour(h).everyDays(1).create();
    });
  } else {
    console.warn('processCourtEmails not found. Skipping.');
  }

  // 4. Install Status Checker
  ScriptApp.newTrigger('checkForChanges').timeBased().everyHours(6).create();

  ui.alert('✅ Automation Factory Reset Complete.', 'All 6 triggers have been installed.', ui.ButtonSet.OK);
}

function viewTriggers() {
  const ui = SpreadsheetApp.getUi();
  const triggers = ScriptApp.getProjectTriggers();
  if (triggers.length === 0) {
    ui.alert('No Triggers', 'No triggers are currently installed.', ui.ButtonSet.OK);
    return;
  }

  const triggerList = triggers.map((t, i) => `${i + 1}. ${t.getHandlerFunction()} (${t.getEventType()})`).join('\n');
  ui.alert('Active Triggers', `Found ${triggers.length} trigger(s):\n\n${triggerList}`, ui.ButtonSet.OK);
}

function disableTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => ScriptApp.deleteTrigger(t));
  SpreadsheetApp.getUi().alert('Triggers Disabled', `✅ Removed ${triggers.length} trigger(s).`, SpreadsheetApp.getUi().ButtonSet.OK);
}

// ============================================================================
// STATUS & UTILITY
// ============================================================================

function viewStatus() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const counties = ['Lee', 'Collier', 'Hendry', 'Charlotte', 'Manatee', 'Sarasota', 'Hillsborough', 'DeSoto'];
  const status = counties.map(county => {
    const sheet = ss.getSheetByName(county);
    if (!sheet) return `${county}: Sheet not found`;
    const recordCount = Math.max(0, sheet.getLastRow() - 1);
    return `${county}: ${recordCount} records`;
  }).join('\n');

  const triggers = ScriptApp.getProjectTriggers();
  const triggerStatus = triggers.length > 0 ? `✅ ${triggers.length} active` : '❌ None';

  ui.alert(
    'System Status',
    `County Records:\n${status}\n\nTriggers: ${triggerStatus}\n\nLast Updated: ${new Date().toLocaleString()}`,
    ui.ButtonSet.OK
  );
}

function showToast_(message, title) {
  SpreadsheetApp.getActiveSpreadsheet().toast(message, title, 3);
}
