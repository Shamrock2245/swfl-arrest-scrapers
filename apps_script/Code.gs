// ============================================================================
// Shamrock Bail Bonds - Unified Production Backend (Code.gs)
// Version: 3.2 - Integrated Advanced SignNow Workflows & Hardened API
// ============================================================================
/**
 * SINGLE ENTRY POINT for all GAS Web App requests.
 * * Features:
 * - Serves Form.html via doGet()
 * - Routes all API actions via doPost()
 * - Serves PDF templates as base64 for browser-side filling
 * - SignNow API integration (Standard + Advanced Workflows)
 * - Smart Signer Management (Defendant/Indemnitor)
 * - Email Delivery OR Kiosk Mode (Embedded Signing)
 * - Auto-incrementing Receipt numbers
 * - Status monitoring of completed documents
 * - Booking data persistence
 * - Google Drive integration with metadata
 * * CONFIGURATION: All sensitive values are stored in Script Properties
 */

// ============================================================================
// CONFIGURATION - Using Script Properties for security
// ============================================================================

function getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    SIGNNOW_API_BASE: props.getProperty('SIGNNOW_API_BASE_URL') || 'https://api.signnow.com',
    SIGNNOW_ACCESS_TOKEN: props.getProperty('SIGNNOW_API_TOKEN') || '',
    SIGNNOW_FOLDER_ID: props.getProperty('SIGNNOW_FOLDER_ID') || '79a05a382b38460b95a78d94a6d79a5ad55e89e6',
    GOOGLE_DRIVE_OUTPUT_FOLDER_ID: props.getProperty('GOOGLE_DRIVE_OUTPUT_FOLDER_ID') || '1ZyTCodt67UAxEbFdGqE3VNua-9TlblR3',
    CURRENT_RECEIPT_NUMBER: parseInt(props.getProperty('CURRENT_RECEIPT_NUMBER') || '201204')
  };
}

// ============================================================================
// GOOGLE DRIVE TEMPLATE IDS - Source of Truth for PDF Templates
// ============================================================================
const TEMPLATE_DRIVE_IDS = {
  'paperwork-header': '15sTaIIwhzHk96I8X3rxz7GtLMU-F5zo1',
  'faq-cosigners': '1bjmH2w-XS5Hhe828y_Jmv9DqaS_gSZM7',
  'faq-defendants': '16j9Z8eTii-J_p4o6A2LrzgzptGB8aOhR',
  'indemnity-agreement': '1p4bYIiZ__JnJHhlmVwLyPJZpsmSdGq12',
  'defendant-application': '1cokWm8qCDpiGxYD6suZEjm9i8MoABeVe',
  'promissory-note': '104-ArZiCm3cgfQcT5rIO0x_OWiaw6Ddt',
  'disclosure-form': '1qIIDudp7r3J7-6MHlL2US34RcrU9KZKY',
  'surety-terms': '1VfmyUTpchfwJTlENlR72JxmoE_NCF-uf',
  'master-waiver': '181mgKQN-VxvQOyzDquFs8cFHUN0tjrMs',
  'ssa-release': '1govKv_N1wl0FIePV8Xfa8mFmZ9JT8mNu',
  'collateral-receipt': '1IAYq4H2b0N0vPnJN7b2vZPaHg_RNKCmP',
  'payment-plan': '1v-qkaegm6MDymiaPK45JqfXXX2_KOj8A',
  'appearance-bond': '15SDM1oBysTw76bIL7Xt0Uhti8uRZKABs'
};

// ============================================================================
// SIGNNOW TEMPLATE IDS
// ============================================================================
const SIGNNOW_TEMPLATE_IDS = {
  'appearance-bond': '09719c685b074d5aae00664a0dcdf433c965a4aa',
  'defendant-application': '5ca8b3a3dbc748aa8e33201fcbe87f985850573f',
  'indemnity-agreement': '2c16525316f143338db14b4ef578aabe67bd47d8',
  'promissory-note': 'e01eb884a00a46408c056093ba0937e26715e3ae',
  'disclosure-form': '08f56f268b2c4b45a1de434b278c840936d09ad9',
  'surety-terms': '4cd02a2dcb334fcc89499d277763fb541820ff40',
  'defendant-waiver': 'd1d0113a16fa4fd5bc1636b0b1c7bdadac0dc4a5',
  'indemnitor-waiver': '642fed81e8314eb99a12ad414777a922145dc9f7',
  'master-waiver': 'cc7e8c7bd0c343088ecb55b965baee881dfd1950',
  'faq-defendant': '41ea80f5087f4bbca274f545b6e270748182e013',
  'faq-cosigners': '37725f4033cc4316a154a7edc2e0600da71f8938',
  'collateral-receipt': '903275f447284cce83e973253f2760c334eb3768',
  'payment-plan': 'ea13db9ec6e7462d963682e6b53f5ca0e46c892f',
  'ssa-release': '3aac5dd7cc03408594e56d4a7f1ddd9ccbdb8fe7'
};

// ============================================================================
// MENU SYSTEM
// ============================================================================

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

/**
 * Opens booking form with data from selected row
 */
function openBookingFormFromRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  const selection = sheet.getActiveRange();
  
  if (!selection) {
    ui.alert('No Selection', 'Please select a row to populate the booking form.', ui.ButtonSet.OK);
    return;
  }
  
  const row = selection.getRow();
  if (row === 1) {
    ui.alert('Invalid Selection', 'Please select a data row (not the header).', ui.ButtonSet.OK);
    return;
  }
  
  const data = sheet.getRange(row, 1, 1, 34).getValues()[0];
  const rowData = {
    scrapeTimestamp: data[0] || '',
    county: data[1] || '',
    bookingNumber: data[2] || '',
    personId: data[3] || '',
    fullName: data[4] || '',
    firstName: data[5] || '',
    middleName: data[6] || '',
    lastName: data[7] || '',
    dob: data[8] || '',
    bookingDate: data[9] || '',
    bookingTime: data[10] || '',
    status: data[11] || '',
    facility: data[12] || '',
    race: data[13] || '',
    sex: data[14] || '',
    height: data[15] || '',
    weight: data[16] || '',
    address: data[17] || '',
    city: data[18] || '',
    state: data[19] || '',
    zip: data[20] || '',
    mugshotUrl: data[21] || '',
    charges: data[22] || '',
    bondAmount: data[23] || '',
    bondPaid: data[24] || '',
    bondType: data[25] || '',
    courtType: data[26] || '',
    caseNumber: data[27] || '',
    courtDate: data[28] || '',
    courtTime: data[29] || '',
    courtLocation: data[30] || '',
    detailUrl: data[31] || '',
    leadScore: data[32] || '',
    leadStatus: data[33] || ''
  };

  const html = HtmlService.createTemplateFromFile('Dashboard');
  html.data = rowData;
  
  const output = html.evaluate()
    .setTitle('Booking Form - ' + (rowData.fullName || 'New Record'))
    .setWidth(1200)
    .setHeight(900);
    
  ui.showModalDialog(output, 'Shamrock Bail Bonds - Booking System');
}

// ============================================================================
// WEB APP ENTRY POINTS
// ============================================================================

function doGet(e) {
  if (!e) e = { parameter: {} };
  
  // Handle mode=scrape for Lee County trigger
  if (e.parameter && e.parameter.mode === 'scrape') {
    return runLeeCountyScraper();
  }
  
  if (e.parameter && e.parameter.action) {
    return handleGetAction(e);
  }
  
  const page = (e.parameter && e.parameter.page) || 'Dashboard';
  
  try {
    return HtmlService.createHtmlOutputFromFile(page)
      .setTitle('Shamrock Bail Bonds - Booking System')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  } catch (error) {
    Logger.log('doGet Error: ' + error.toString());
    return HtmlService.createHtmlOutput('<h1>Error loading page</h1><p>' + error.toString() + '</p>');
  }
}

function handleGetAction(e) {
  const action = e.parameter.action;
  const callback = e.parameter.callback;
  
  let result;
  
  try {
    switch(action) {
      case 'getTemplate':
        result = getPdfTemplateBase64(e.parameter.templateId);
        break;
      case 'getTemplateList':
        result = getTemplateList();
        break;
      case 'getNextReceiptNumber':
        result = getNextReceiptNumber();
        break;
      case 'getPdf':
        if (!e.parameter.fileId) {
          result = { success: false, error: 'Missing fileId parameter' };
        } else {
          result = getPdfByFileId(e.parameter.fileId);
        }
        break;
      case 'health':
        result = { 
          success: true, 
          message: 'GAS backend is running', 
          timestamp: new Date().toISOString(),
          driveAccess: testDriveAccess()
        };
        break;
      default:
        result = { success: false, error: 'Unknown action: ' + action };
    }
  } catch (error) {
    result = { success: false, error: 'Server Error: ' + error.toString() };
  }
  
  const jsonString = JSON.stringify(result);
  if (callback) {
    return ContentService.createTextOutput(callback + '(' + jsonString + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  
  return ContentService.createTextOutput(jsonString)
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Routes all POST requests.
 * INTEGRATED: Now includes Partner's Advanced SignNow workflows.
 */
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      throw new Error("No POST data received");
    }

    const data = JSON.parse(e.postData.contents);
    const action = data.action;
    
    let result;
    
    switch(action) {
      // --- Standard Template Operations ---
      case 'getTemplate':
        result = getPdfTemplateBase64(data.templateId);
        break;
      case 'getMultipleTemplates':
        result = getMultipleTemplates(data.templateIds);
        break;
      case 'getPdf':
        result = getPdfByFileId(data.fileId);
        break;
      
      // --- Standard SignNow Operations ---
      case 'uploadToSignNow':
        // Uses existing robust uploader
        result = uploadFilledPdfToSignNow(data.pdfBase64, data.fileName);
        break;
      case 'createSigningRequest':
        result = createSigningRequest(data);
        break;
      case 'sendForSignature':
        result = sendForSignature(data);
        break;
      case 'getDocumentStatus':
        result = getDocumentStatus(data.documentId);
        break;
      
      // === ADVANCED SIGNNOW WORKFLOWS (Unified) ===
      
      case 'validateSignNowToken':
        result = SN_validateToken();
        break;
      
      case 'addSignatureFields':
        result = SN_addFields(data.documentId, data.fields);
        break;
      
      case 'addFieldsForDocType':
        result = SN_addFieldsForDocType(data.documentId, data.documentType, data.options);
        break;
      
      case 'sendEmailInvite':
        result = SN_sendEmailInvite(data.documentId, data.signers, data.options);
        break;
      
      case 'sendSmsInvite':
        result = SN_sendSmsInvite(data.documentId, data.signers, data.options);
        break;
      
      case 'createEmbeddedLink':
        result = SN_createEmbeddedLink(data.documentId, data.signerEmail, data.signerRole, data.linkExpiration);
        break;
      
      case 'sendPacketForSignature':
        result = SN_sendPacketForSignature(data);
        break;
      
      case 'downloadCompletedDocument':
        const blob = SN_downloadDocument(data.documentId, data.type);
        if (blob) {
          result = {
            success: true,
            pdfBase64: Utilities.base64Encode(blob.getBytes()),
            fileName: blob.getName()
          };
        } else {
          result = { success: false, error: 'Download failed' };
        }
        break;
      
      case 'saveCompletedToDrive':
        result = SN_saveCompletedToDrive(data.documentId, data.defendantName, data.bondDate);
        break;
      
      case 'cancelInvite':
        result = { success: SN_cancelInvite(data.documentId) };
        break;
      
      case 'sendReminder':
        result = SN_sendReminder(data.documentId);
        break;

      case 'sendPaymentEmail':
        result = sendPaymentEmail(data);
        break;

      // --- Booking Data Operations ---
      case 'saveBooking':
        result = saveBookingData(data.bookingData);
        break;
      case 'getBooking':
        result = getBookingData(data.bookingId);
        break;
      
      // --- Receipt Number ---
      case 'getNextReceiptNumber':
        result = getNextReceiptNumber();
        break;
      case 'incrementReceiptNumber':
        result = incrementReceiptNumber();
        break;
      
      // --- Google Drive Operations ---
      case 'saveToGoogleDrive':
        result = saveFilledPacketToDrive(data);
        break;
      
      case 'runLeeScraper':
        result = runLeeCountyScraper();
        break;
      
      default:
        result = { success: false, error: 'Unknown action: ' + action };
    }
    
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    Logger.log('doPost Error: ' + error.toString());
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * CLIENT HELPER: Allows Form.html to trigger doPost actions via google.script.run
 */
function doPostFromClient(data) {
  // Simulate a POST request from the client
  const fakeEvent = {
    postData: {
      contents: JSON.stringify(data)
    }
  };
  
  // Call doPost and parse the result
  const response = doPost(fakeEvent);
  return JSON.parse(response.getContent());
}

// ============================================================================
// PDF TEMPLATE FUNCTIONS
// ============================================================================

function getPdfTemplateBase64(templateId) {
  try {
    const driveId = TEMPLATE_DRIVE_IDS[templateId];
    
    if (!driveId) {
      return { 
        success: false, 
        error: 'Template not found: ' + templateId,
        availableTemplates: Object.keys(TEMPLATE_DRIVE_IDS)
      };
    }
    return getPdfByFileId(driveId);
  } catch (error) {
    Logger.log('Error in getPdfTemplateBase64: ' + error.toString());
    return { success: false, error: 'Error fetching template: ' + error.toString() };
  }
}

function getPdfByFileId(fileId) {
  try {
    if (!fileId) return { success: false, error: 'No file ID provided' };
    
    const file = DriveApp.getFileById(fileId);
    if (!file) return { success: false, error: 'File not found: ' + fileId };
    
    const blob = file.getBlob();
    const bytes = blob.getBytes();
    const base64 = Utilities.base64Encode(bytes);
    
    return {
      success: true,
      pdfBase64: base64,
      fileName: file.getName(),
      filename: file.getName(),
      mimeType: blob.getContentType(),
      fileId: fileId,
      size: bytes.length
    };
  } catch (error) {
    Logger.log('getPdfByFileId Error: ' + error.toString());
    return { success: false, error: 'Failed to fetch PDF: ' + error.toString() };
  }
}

function getMultipleTemplates(templateIds) {
  const results = { success: true, templates: {}, errors: [] };
  
  if (!Array.isArray(templateIds)) {
    return { success: false, error: "templateIds must be an array" };
  }

  for (const templateId of templateIds) {
    const result = getPdfTemplateBase64(templateId);
    if (result.success) {
      results.templates[templateId] = result;
    } else {
      results.errors.push({ templateId: templateId, error: result.error });
    }
  }
  results.success = results.errors.length === 0;
  return results;
}

function getTemplateList() {
  const templates = [];
  for (const [id, driveId] of Object.entries(TEMPLATE_DRIVE_IDS)) {
    try {
      const file = DriveApp.getFileById(driveId);
      templates.push({ id: id, driveId: driveId, name: file.getName(), accessible: true });
    } catch (error) {
      templates.push({ id: id, driveId: driveId, name: 'Unknown', accessible: false, error: error.toString() });
    }
  }
  return { success: true, templates: templates, count: templates.length };
}

// ============================================================================
// STANDARD SIGNNOW API FUNCTIONS
// ============================================================================

function uploadFilledPdfToSignNow(pdfBase64, fileName) {
  const config = getConfig();
  try {
    if (!config.SIGNNOW_ACCESS_TOKEN) return { success: false, error: 'SignNow API token not configured.' };
    
    const pdfBytes = Utilities.base64Decode(pdfBase64);
    const boundary = '----WebKitFormBoundary' + Utilities.getUuid();
    
    let payload = '';
    payload += '--' + boundary + '\r\n';
    payload += 'Content-Disposition: form-data; name="file"; filename="' + fileName + '"\r\n';
    payload += 'Content-Type: application/pdf\r\n\r\n';
    
    const payloadBytes = Utilities.newBlob(payload).getBytes();
    const endBytes = Utilities.newBlob('\r\n--' + boundary + '--\r\n').getBytes();
    const allBytes = [...payloadBytes, ...pdfBytes, ...endBytes];
    
    const options = {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN,
        'Content-Type': 'multipart/form-data; boundary=' + boundary
      },
      payload: Utilities.newBlob(allBytes).getBytes(),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(config.SIGNNOW_API_BASE + '/document', options);
    const responseCode = response.getResponseCode();
    const result = JSON.parse(response.getContentText());
    
    if (responseCode === 200 || responseCode === 201) {
      return { success: true, documentId: result.id, documentName: fileName };
    } else {
      return { success: false, error: 'SignNow upload failed: ' + (result.error || result.message), responseCode: responseCode };
    }
  } catch (error) {
    return { success: false, error: 'Error uploading to SignNow: ' + error.toString() };
  }
}

function createSigningRequest(data) {
  const config = getConfig();
  try {
    if (!config.SIGNNOW_ACCESS_TOKEN) return { success: false, error: 'SignNow API token not configured' };
    
    const invitePayload = {
      to: data.signers.map(signer => ({
        email: signer.email,
        role: signer.role || 'Signer',
        order: signer.order || 1
      })),
      from: data.fromEmail || 'admin@shamrockbailbonds.biz',
      subject: data.subject || 'Documents Ready for Signature',
      message: data.message || 'Please review and sign.'
    };
    
    const options = {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN, 'Content-Type': 'application/json' },
      payload: JSON.stringify(invitePayload),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(config.SIGNNOW_API_BASE + '/document/' + data.documentId + '/invite', options);
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      return { success: true, inviteId: result.id || result.result, documentId: data.documentId };
    } else {
      return { success: false, error: 'SignNow invite failed: ' + (result.error || result.message) };
    }
  } catch (error) {
    return { success: false, error: 'Error creating signing request: ' + error.toString() };
  }
}

function sendForSignature(data) {
  const uploadResult = uploadFilledPdfToSignNow(data.pdfBase64, data.fileName);
  if (!uploadResult.success) return uploadResult;
  
  const signingResult = createSigningRequest({
    documentId: uploadResult.documentId,
    signers: data.signers,
    subject: data.subject,
    message: data.message,
    fromEmail: data.fromEmail
  });
  
  return {
    success: signingResult.success,
    documentId: uploadResult.documentId,
    inviteId: signingResult.inviteId,
    error: signingResult.error
  };
}

function getDocumentStatus(documentId) {
  const config = getConfig();
  try {
    const options = {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN },
      muteHttpExceptions: true
    };
    const response = UrlFetchApp.fetch(config.SIGNNOW_API_BASE + '/document/' + documentId, options);
    const result = JSON.parse(response.getContentText());
    
    return {
      success: true,
      documentId: documentId,
      status: result.status,
      signers: result.field_invites || [],
      updated: result.updated
    };
  } catch (error) {
    return { success: false, error: 'Error getting status: ' + error.toString() };
  }
}

// Note: SN_ methods are now defined in SignNowAPI.gs

// ============================================================================
// UTILITIES & DATA
// ============================================================================

function sendPaymentEmail(data) {
  try {
    const to = data.email;
    const amount = data.amount;
    const name = data.name;
    
    if (!to) return { success: false, error: 'No email address provided' };
    
    const subject = 'Payment Due - Shamrock Bail Bonds';
    const body = `Dear ${name},\n\n This is a reminder that a payment of $${amount} is due for your bail bond premium.\n\n Please contact us to make a payment or use the payment link provided.\n\n Thank you,\n Shamrock Bail Bonds`;
    
    MailApp.sendEmail({
      to: to,
      subject: subject,
      body: body
    });
    
    return { success: true };
  } catch (e) {
    return { success: false, error: e.toString() };
  }
}


function getNextReceiptNumber() {
  try {
    const props = PropertiesService.getScriptProperties();
    let current = parseInt(props.getProperty('CURRENT_RECEIPT_NUMBER') || '201204');
    return {
      success: true,
      receiptNumber: current.toString().padStart(6, '0'),
      collateralReceiptNumber: 'C-' + current
    };
  } catch (e) { return { success: false, error: e.toString() }; }
}

function incrementReceiptNumber() {
  try {
    const props = PropertiesService.getScriptProperties();
    let current = parseInt(props.getProperty('CURRENT_RECEIPT_NUMBER') || '201204');
    current++;
    props.setProperty('CURRENT_RECEIPT_NUMBER', current.toString());
    return { success: true, newReceiptNumber: current.toString().padStart(6, '0') };
  } catch (e) { return { success: false, error: e.toString() }; }
}

function saveFilledPacketToDrive(data) {
  const config = getConfig();
  try {
    const parentFolder = DriveApp.getFolderById(config.GOOGLE_DRIVE_OUTPUT_FOLDER_ID);
    const folderName = data.defendantName + ' - ' + data.caseNumber + ' - ' + 
                       Utilities.formatDate(new Date(), 'America/New_York', 'yyyy-MM-dd');
    let caseFolder;
    const existing = parentFolder.getFoldersByName(folderName);
    if (existing.hasNext()) caseFolder = existing.next();
    else caseFolder = parentFolder.createFolder(folderName);
    
    const bytes = Utilities.base64Decode(data.pdfBase64);
    const blob = Utilities.newBlob(bytes, 'application/pdf', data.fileName);
    const file = caseFolder.createFile(blob);
    
    return {
      success: true,
      fileId: file.getId(),
      folderUrl: caseFolder.getUrl(),
      fileUrl: file.getUrl()
    };
  } catch (e) { return { success: false, error: e.toString() }; }
}

// --- Persistence Placeholders (Connect to FormDataHandler.gs) ---
// --- Persistence Functions ---
function saveBookingData(formData) {
  try {
    if (!formData || typeof formData !== 'object') {
      throw new Error('Invalid form data: formData is ' + typeof formData);
    }
    
    Logger.log('Received form data: ' + JSON.stringify(formData));
    
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    // Determine sheet to use
    var isBondWritten = formData['status'] === 'Bond Written' || formData['status'] === 'Active';
    var sheetName = isBondWritten ? "Shamrock's Bonds" : "Qualified";
    var sheet = ss.getSheetByName(sheetName);
    
    if (!sheet) {
      if (isBondWritten) {
          sheet = ss.insertSheet(sheetName);
          // Gid: 1351721696 requested - we can't set GID via script for new sheet but we name it correctly
          var headers = [
            'Scrape_Timestamp', 'Agent_Name', 'Defendant_Full_Name', 'Booking_Number', 'DOB', 
            'Defendant_Phone', 'Defendant_Email', 'Defendant_Address', 'Defendant_City', 'Defendant_Zip',
            'Indemnitor_1_Name', 'Indemnitor_1_Phone', 'Indemnitor_1_Email', 'Indemnitor_1_Address', 'Indemnitor_1_City',
            'Indemnitor_2_Name', 'Indemnitor_2_Phone', 'Indemnitor_2_Email', 'Indemnitor_2_Address', 'Indemnitor_2_City',
            'Total_Bond_Amount', 'Premium_Owed', 'Premium_Paid', 'Balance_Due', 'Payment_Method',
            'Court_Date', 'Court_Time', 'Court_Location', 'Court_Type', 'County',
            'Case_Number', 'Facility', 'Charges', 'Mugshot_URL', 'Detail_URL',
            'SignNow_Document_IDs', 'SignNow_Invite_IDs', 'SignNow_Status', 'Lead_Score', 'Lead_Status',
            'Notes'
          ];
          sheet.appendRow(headers);
          var headerRange = sheet.getRange(1, 1, 1, headers.length);
          headerRange.setBackground('#2e7d32').setFontColor('#ffffff').setFontWeight('bold');
          sheet.setFrozenRows(1);
      } else {
          sheet = ss.insertSheet(sheetName);
          // Gid: 1799498945
          var headers = [
            'Scrape_Timestamp', 'County', 'Booking_Number', 'Person_ID', 'Full_Name',
            'First_Name', 'Middle_Name', 'Last_Name', 'DOB', 'Booking_Date',
            'Booking_Time', 'Status', 'Facility', 'Race', 'Sex', 'Height', 'Weight',
            'Address', 'City', 'State', 'ZIP', 'Mugshot_URL', 'Charges',
            'Bond_Amount', 'Bond_Paid', 'Bond_Type', 'Court_Type', 'Case_Number',
            'Court_Date', 'Court_Time', 'Court_Location', 'Detail_URL',
            'Lead_Score', 'Lead_Status'
          ];
          sheet.appendRow(headers);
          var headerRange = sheet.getRange(1, 1, 1, headers.length);
          headerRange.setBackground('#1565c0').setFontColor('#ffffff').setFontWeight('bold');
          sheet.setFrozenRows(1);
      }
    }
    
    var timestamp = new Date();
    var rowData = [];
    
    if (isBondWritten) {
      // Indemnitors processing
      var ind1 = formData.indemnitors && formData.indemnitors[0] ? formData.indemnitors[0] : {};
      var ind2 = formData.indemnitors && formData.indemnitors[1] ? formData.indemnitors[1] : {};
      
      rowData = [
        timestamp.toISOString(),
        formData['agent-name'] || 'Shamrock Bail Bonds',
        (formData['defendant-first-name'] + ' ' + formData['defendant-last-name']).trim(),
        formData['defendant-booking-number'] || '',
        formData['defendant-dob'] || '',
        formData['defendant-phone'] || '',
        formData['defendant-email'] || '',
        formData['defendant-street-address'] || '',
        formData['defendant-city'] || '',
        formData['defendant-zipcode'] || '',
        ind1.name || '', ind1.phone || '', ind1.email || '', ind1.address || '', ind1.city || '',
        ind2.name || '', ind2.phone || '', ind2.email || '', ind2.address || '', ind2.city || '',
        formData['payment-total-bond'] || '0',
        formData['payment-premium-due'] || '0',
        formData['payment-down'] || '0',
        formData['payment-balance'] || '0',
        formData['payment-method'] || '',
        formData['court-date'] || '',
        formData['court-time'] || '',
        formData['court-location'] || '',
        formData['defendant-court-type'] || '',
        formData['defendant-county'] || '',
        formData['case-number'] || '',
        formData['defendant-jail-facility'] || '',
        (formData.charges || []).map(c => c.charge).join(' | '),
        formData['mugshot-url'] || '',
        formData['detail-url'] || '',
        formData['signnow_doc_ids'] || '',
        formData['signnow_invite_ids'] || '',
        formData['signnow_status'] || 'Pending Signing',
        formData['lead_score'] || 0,
        formData['lead_status'] || 'Closed',
        formData['defendant-notes'] || ''
      ];
    } else {
      rowData = [
        timestamp.toISOString(),
        formData['defendant-county'] || 'Manual',
        formData['defendant-booking-number'] || '',
        formData['defendant-person-id'] || '',
        (formData['defendant-first-name'] + ' ' + formData['defendant-last-name']).trim(),
        formData['defendant-first-name'] || '',
        formData['defendant-middle-name'] || '',
        formData['defendant-last-name'] || '',
        formData['defendant-dob'] || '',
        formData['defendant-booking-date'] || '',
        formData['defendant-booking-time'] || '',
        formData['status'] || 'Pending',
        formData['defendant-facility'] || '',
        formData['defendant-race'] || '',
        formData['defendant-sex'] || '',
        formData['defendant-height'] || '',
        formData['defendant-weight'] || '',
        formData['defendant-street-address'] || '',
        formData['defendant-city'] || '',
        formData['defendant-state'] || 'FL',
        formData['defendant-zipcode'] || '',
        formData['mugshot-url'] || '',
        (formData.charges || []).map(c => c.charge).join(' | '),
        formData['payment-total-bond'] || '0',
        formData['bond-paid'] || 'NO',
        formData['payment-method'] || '',
        formData['defendant-court-type'] || '',
        formData['case-number'] || '',
        formData['court-date'] || '',
        formData['court-time'] || '',
        formData['court-location'] || '',
        formData['detail-url'] || '',
        formData['lead_score'] || 0,
        formData['lead_status'] || 'Qualified'
      ];
    }
    
    sheet.appendRow(rowData);
    for (var i = 1; i <= rowData.length; i++) {
      sheet.autoResizeColumn(i);
    }
    
    return {
      success: true,
      message: 'Booking data saved successfully',
      bookingNumber: formData['booking-number'] || 'N/A',
      timestamp: timestamp.toISOString()
    };
  } catch (error) {
    Logger.log('Error saving booking data: ' + error.message);
    return { success: false, message: 'Failed to save booking data: ' + error.message };
  }
}
function getBookingData(id) { return { success: true, data: null }; }

// --- Tests ---
function testDriveAccess() {
  try {
    const f = DriveApp.getFileById(TEMPLATE_DRIVE_IDS['paperwork-header']);
    return { success: true, fileName: f.getName() };
  } catch (e) { return { success: false, error: e.toString() }; }
}

function testSignNowConnection() {
  const config = getConfig();
  try {
    const options = { headers: { 'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN }, muteHttpExceptions: true };
    const res = UrlFetchApp.fetch(config.SIGNNOW_API_BASE + '/user', options);
    const json = JSON.parse(res.getContentText());
    return { success: true, user: json };
  } catch (e) { return { success: false, error: e.toString() }; }
}

// ============================================================================
// PARTNER CLIENT SCRIPTS (Storage only, unused by server)
// ============================================================================
const FORM_HTML_SIGNNOW_FUNCTIONS = `
// Client-side JS stored here for reference or injection if needed.
// See Form.html for implementation.
`;
/**
 * Get County Statistics
 * Currently returns mock data or calculated real data if sheets are connected
 */
function getCountyStatistics() {
  // In a real implementation, this would query the master spreadsheet
  // For now, we return the structure the frontend expects
  const stats = {
    lee: { val: 0, total: 0, male: 0, female: 0, avgBond: 0, crimes: {} },
    collier: { val: 0, total: 0, male: 0, female: 0, avgBond: 0, crimes: {} },
    charlotte: { val: 0, total: 0, male: 0, female: 0, avgBond: 0, crimes: {} },
    hendry: { val: 0, total: 0, male: 0, female: 0, avgBond: 0, crimes: {} },
    sarasota: { val: 0, total: 0, male: 0, female: 0, avgBond: 0, crimes: {} },
    manatee: { val: 0, total: 0, male: 0, female: 0, avgBond: 0, crimes: {} }
  };

  try {
    // If you have the Sheet ID, we could implement real stats fetching here
    // const sheet = SpreadsheetApp.openById('121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E');
    // ... logic to count rows ...
  } catch (e) {
    console.error('Error fetching stats:', e);
  }

  return stats;
}
// ============================================================================
// COUNTY SCRAPER INTEGRATION
// ============================================================================

/**
 * Run Lee County scraper (Wrapper for google.script.run)
 */
function runLeeScraper() {
  const result = runLeeCountyScraper();
  // Parse ContentService result for google.script.run
  try {
    return JSON.parse(result.getContent());
  } catch (e) {
    return { success: false, error: 'Failed to trigger scraper' };
  }
}

/**
 * Run Lee County scraper
 * This can be an Apps Script scraper or trigger Node.js
 */
function runLeeCountyScraper() {
  try {
    Logger.log('Lee County Scraper Triggered');
    logScraperRun('LEE', 'Manual trigger / WebApp call');
    
    // Check for webhook to trigger Node.js scraper
    const props = PropertiesService.getScriptProperties();
    const webhookUrl = props.getProperty('WEBHOOK_URL');
    
    if (webhookUrl) {
      triggerWebhook('lee', 'scrape', webhookUrl);
      return ContentService.createTextOutput(JSON.stringify({ 
        success: true, 
        message: 'Lee County scraper triggered via webhook' 
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({ 
      success: true, 
      message: 'Lee County scraper call logged (webhook not configured)' 
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    Logger.log('Lee County scraper error: ' + error.message);
    return ContentService.createTextOutput(JSON.stringify({ 
      success: false, 
      error: error.message 
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Log a scraper run to the Logs sheet
 */
function logScraperRun(county, message) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var logsSheet = ss.getSheetByName('Logs');
    
    if (!logsSheet) {
      logsSheet = ss.insertSheet('Logs');
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
function triggerWebhook(county, action, webhookUrl) {
  if (!webhookUrl) return;
  
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
    
    var response = UrlFetchApp.fetch(webhookUrl, options);
    Logger.log('Webhook triggered for ' + county + ': ' + response.getResponseCode());
    
  } catch (error) {
    Logger.log('Webhook trigger failed: ' + error.message);
  }
}
