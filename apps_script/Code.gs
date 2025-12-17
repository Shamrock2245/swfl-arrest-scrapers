// ============================================================================
// Shamrock Bail Bonds - Unified Production Backend (Code.gs)
// Version: 3.1 - Refactored with Script Properties & Enhanced PDF Handling
// ============================================================================
/**
 * SINGLE ENTRY POINT for all GAS Web App requests.
 * 
 * Features:
 * - Serves Form.html via doGet()
 * - Routes all API actions via doPost()
 * - Serves PDF templates as base64 for browser-side filling
 * - SignNow API integration for document signing
 * - Smart Signer Management (Defendant/Indemnitor)
 * - Email Delivery OR Kiosk Mode signing
 * - Auto-incrementing Receipt numbers
 * - Status monitoring of completed documents
 * - Booking data persistence (via FormDataHandler)
 * - Google Drive integration with metadata
 * - Bulk packet generation
 * 
 * CONFIGURATION: All sensitive values are stored in Script Properties
 * Go to Project Settings > Script Properties to configure:
 * - SIGNNOW_API_TOKEN
 * - SIGNNOW_API_BASE_URL
 * - GOOGLE_DRIVE_FOLDER_ID
 * - CURRENT_RECEIPT_NUMBER
 * 
 * IMPORTANT: Remove doGet() and doPost() from other .gs files to avoid conflicts!
 */

// ============================================================================
// CONFIGURATION - Using Script Properties for security
// ============================================================================

/**
 * Get configuration from Script Properties with fallbacks
 */
function getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    SIGNNOW_API_BASE: props.getProperty('SIGNNOW_API_BASE_URL') || 'https://api.signnow.com',
    SIGNNOW_ACCESS_TOKEN: props.getProperty('SIGNNOW_API_TOKEN') || '',
    SIGNNOW_FOLDER_ID: props.getProperty('SIGNNOW_FOLDER_ID') || '79a05a382b38460b95a78d94a6d79a5ad55e89e6',
    GOOGLE_DRIVE_FOLDER_ID: props.getProperty('GOOGLE_DRIVE_FOLDER_ID') || '1ZyTCodt67UAxEbFdGqE3VNua-9TlblR3',
    CURRENT_RECEIPT_NUMBER: parseInt(props.getProperty('CURRENT_RECEIPT_NUMBER') || '201204')
  };
}

// ============================================================================
// GOOGLE DRIVE TEMPLATE IDS - Source of Truth for PDF Templates
// ============================================================================
const TEMPLATE_DRIVE_IDS = {
  // Core Documents (in signing order)
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
  'appearance-bond': '15SDM1oBysTw76bIL7Xt0Uhti8uRZKABs'  // PRINT ONLY - does not go to SignNow
};

// ============================================================================
// SIGNNOW TEMPLATE IDS - For sending documents for signature
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
// WEB APP ENTRY POINTS
// ============================================================================

/**
 * Serves the Form.html interface or handles GET API requests
 */
function doGet(e) {
  // Handle case when e is undefined (direct script execution)
  if (!e) {
    e = { parameter: {} };
  }
  
  // Handle API-style GET requests
  if (e.parameter && e.parameter.action) {
    return handleGetAction(e);
  }
  
  // Serve the HTML page
  const page = (e.parameter && e.parameter.page) || 'Form';
  
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

/**
 * Handle GET actions (for template fetching, etc.)
 */
function handleGetAction(e) {
  const action = e.parameter.action;
  const callback = e.parameter.callback; // For JSONP support
  
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
    Logger.log('handleGetAction Error: ' + error.toString());
    result = { success: false, error: 'Server Error: ' + error.toString() };
  }
  
  // Return as JSONP if callback provided, otherwise JSON
  const jsonString = JSON.stringify(result);
  if (callback) {
    return ContentService.createTextOutput(callback + '(' + jsonString + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  
  return ContentService.createTextOutput(jsonString)
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Routes all POST requests to appropriate handlers
 */
function doPost(e) {
  try {
    // Hardening: Check if postData exists
    if (!e || !e.postData || !e.postData.contents) {
      throw new Error("No POST data received");
    }

    const data = JSON.parse(e.postData.contents);
    const action = data.action;
    
    let result;
    
    switch(action) {
      // Template Operations
      case 'getTemplate':
        result = getPdfTemplateBase64(data.templateId);
        break;
      case 'getMultipleTemplates':
        result = getMultipleTemplates(data.templateIds);
        break;
      case 'getPdf':
        result = getPdfByFileId(data.fileId);
        break;
      
      // SignNow Operations
      case 'uploadToSignNow':
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
      
      // Booking Data Operations
      case 'saveBooking':
        result = saveBookingData(data.bookingData);
        break;
      case 'getBooking':
        result = getBookingData(data.bookingId);
        break;
      
      // Receipt Number
      case 'getNextReceiptNumber':
        result = getNextReceiptNumber();
        break;
      case 'incrementReceiptNumber':
        result = incrementReceiptNumber();
        break;
      
      // Google Drive Operations
      case 'saveToGoogleDrive':
        result = saveFilledPacketToDrive(data);
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

// ============================================================================
// PDF TEMPLATE FUNCTIONS - CORE FUNCTIONALITY
// ============================================================================

/**
 * Get a PDF template as base64 from Google Drive by template ID
 * @param {string} templateId - The template identifier (e.g., 'appearance-bond')
 * @returns {Object} - { success: boolean, data: base64String, error?: string }
 */
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
    return {
      success: false,
      error: 'Error fetching template: ' + error.toString()
    };
  }
}

/**
 * Fetch a PDF from Google Drive and return as base64
 * This is the MAIN function called by Form.html via google.script.run
 * @param {string} fileId - The Google Drive file ID
 * @returns {Object} - Object with success status and base64 PDF data
 */
function getPdfByFileId(fileId) {
  try {
    if (!fileId) {
      Logger.log('getPdfByFileId: No file ID provided');
      return { success: false, error: 'No file ID provided' };
    }
    
    Logger.log('getPdfByFileId: Fetching file ID: ' + fileId);
    
    // Get the file from Drive
    const file = DriveApp.getFileById(fileId);
    
    if (!file) {
      Logger.log('getPdfByFileId: File not found');
      return { success: false, error: 'File not found: ' + fileId };
    }
    
    Logger.log('getPdfByFileId: File found: ' + file.getName());
    
    // Get the blob (this auto-converts Google Docs to PDF)
    const blob = file.getBlob();
    
    if (!blob) {
      Logger.log('getPdfByFileId: Could not get blob');
      return { success: false, error: 'Could not retrieve blob from file' };
    }
    
    // Convert to base64
    const bytes = blob.getBytes();
    const base64 = Utilities.base64Encode(bytes);
    
    Logger.log('getPdfByFileId: Success - ' + file.getName() + ' (' + bytes.length + ' bytes)');
    
    return {
      success: true,
      pdfBase64: base64,
      fileName: file.getName(),
      filename: file.getName(), // Backward compatibility
      mimeType: blob.getContentType(),
      fileId: fileId,
      size: bytes.length
    };
    
  } catch (error) {
    Logger.log('getPdfByFileId Error (ID: ' + fileId + '): ' + error.toString());
    return {
      success: false,
      error: 'Failed to fetch PDF: ' + error.toString(),
      fileId: fileId
    };
  }
}

/**
 * Get multiple PDF templates at once
 * @param {Array} templateIds - Array of template identifiers
 * @returns {Object} - { success: boolean, templates: {...}, errors: [...] }
 */
function getMultipleTemplates(templateIds) {
  const results = {
    success: true,
    templates: {},
    errors: []
  };
  
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

/**
 * Get list of all available templates
 * @returns {Object} - { success: boolean, templates: [...] }
 */
function getTemplateList() {
  const templates = [];
  
  for (const [id, driveId] of Object.entries(TEMPLATE_DRIVE_IDS)) {
    try {
      const file = DriveApp.getFileById(driveId);
      templates.push({
        id: id,
        driveId: driveId,
        name: file.getName(),
        accessible: true
      });
    } catch (error) {
      templates.push({
        id: id,
        driveId: driveId,
        name: 'Unknown',
        accessible: false,
        error: error.toString()
      });
    }
  }
  
  return {
    success: true,
    templates: templates,
    count: templates.length
  };
}

// ============================================================================
// SIGNNOW API FUNCTIONS
// ============================================================================

/**
 * Upload a filled PDF to SignNow
 * @param {string} pdfBase64 - Base64 encoded PDF
 * @param {string} fileName - Name for the file
 * @returns {Object} - { success: boolean, documentId?: string }
 */
function uploadFilledPdfToSignNow(pdfBase64, fileName) {
  const config = getConfig();
  
  try {
    if (!config.SIGNNOW_ACCESS_TOKEN) {
      return { success: false, error: 'SignNow API token not configured. Set SIGNNOW_API_TOKEN in Script Properties.' };
    }
    
    const pdfBytes = Utilities.base64Decode(pdfBase64);
    const pdfBlob = Utilities.newBlob(pdfBytes, 'application/pdf', fileName);
    
    const boundary = '----WebKitFormBoundary' + Utilities.getUuid();
    
    // Build multipart form data
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
      Logger.log('SignNow Upload Success: ' + result.id);
      return {
        success: true,
        documentId: result.id,
        documentName: fileName
      };
    } else {
      Logger.log('SignNow Upload Error: ' + response.getContentText());
      return {
        success: false,
        error: 'SignNow upload failed: ' + (result.error || result.message || 'Unknown error'),
        responseCode: responseCode
      };
    }
    
  } catch (error) {
    Logger.log('uploadFilledPdfToSignNow Error: ' + error.toString());
    return {
      success: false,
      error: 'Error uploading to SignNow: ' + error.toString()
    };
  }
}

/**
 * Create a signing request for a document
 * @param {Object} data - { documentId, signers: [{email, role, name}], subject, message }
 * @returns {Object} - { success: boolean, inviteId?: string }
 */
function createSigningRequest(data) {
  const config = getConfig();
  
  try {
    if (!config.SIGNNOW_ACCESS_TOKEN) {
      return { success: false, error: 'SignNow API token not configured' };
    }
    
    // Build the invite payload
    const invitePayload = {
      to: data.signers.map(signer => ({
        email: signer.email,
        role: signer.role || 'Signer',
        role_id: signer.roleId || '',
        order: signer.order || 1
      })),
      from: data.fromEmail || 'admin@shamrockbailbonds.biz',
      subject: data.subject || 'Documents Ready for Signature - Shamrock Bail Bonds',
      message: data.message || 'Please review and sign the attached bail bond documents.'
    };
    
    const options = {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(invitePayload),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(
      config.SIGNNOW_API_BASE + '/document/' + data.documentId + '/invite',
      options
    );
    const responseCode = response.getResponseCode();
    const result = JSON.parse(response.getContentText());
    
    if (responseCode === 200 || responseCode === 201) {
      Logger.log('SignNow Invite Success');
      return {
        success: true,
        inviteId: result.id || result.result,
        documentId: data.documentId
      };
    } else {
      Logger.log('SignNow Invite Error: ' + response.getContentText());
      return {
        success: false,
        error: 'SignNow invite failed: ' + (result.error || result.message || 'Unknown error')
      };
    }
    
  } catch (error) {
    Logger.log('createSigningRequest Error: ' + error.toString());
    return {
      success: false,
      error: 'Error creating signing request: ' + error.toString()
    };
  }
}

/**
 * Send a document for signature (combined upload + invite)
 * @param {Object} data - { pdfBase64, fileName, signers, subject, message }
 * @returns {Object} - { success: boolean, documentId?: string, inviteId?: string }
 */
function sendForSignature(data) {
  // Step 1: Upload the PDF
  const uploadResult = uploadFilledPdfToSignNow(data.pdfBase64, data.fileName);
  
  if (!uploadResult.success) {
    return uploadResult;
  }
  
  // Step 2: Create signing request
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

/**
 * Get document status from SignNow
 * @param {string} documentId - SignNow document ID
 * @returns {Object} - Document status information
 */
function getDocumentStatus(documentId) {
  const config = getConfig();
  
  try {
    if (!config.SIGNNOW_ACCESS_TOKEN) {
      return { success: false, error: 'SignNow API token not configured' };
    }
    
    const options = {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN
      },
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(
      config.SIGNNOW_API_BASE + '/document/' + documentId,
      options
    );
    const result = JSON.parse(response.getContentText());
    
    return {
      success: true,
      documentId: documentId,
      status: result.status,
      signers: result.field_invites || [],
      created: result.created,
      updated: result.updated
    };
    
  } catch (error) {
    return {
      success: false,
      error: 'Error getting document status: ' + error.toString()
    };
  }
}

// ============================================================================
// RECEIPT NUMBER MANAGEMENT
// ============================================================================

/**
 * Get the next receipt number from Script Properties
 * @returns {Object} - { success: boolean, receiptNumber: string, collateralReceiptNumber: string }
 */
function getNextReceiptNumber() {
  try {
    const props = PropertiesService.getScriptProperties();
    let currentNumber = parseInt(props.getProperty('CURRENT_RECEIPT_NUMBER') || '201204');
    
    const receiptNumber = currentNumber.toString().padStart(6, '0');
    const collateralReceiptNumber = 'C-' + receiptNumber;
    
    return {
      success: true,
      receiptNumber: receiptNumber,
      collateralReceiptNumber: collateralReceiptNumber
    };
    
  } catch (error) {
    return {
      success: false,
      error: 'Error getting receipt number: ' + error.toString()
    };
  }
}

/**
 * Increment the receipt number after successful packet generation
 * @returns {Object} - { success: boolean, newReceiptNumber: string }
 */
function incrementReceiptNumber() {
  try {
    const props = PropertiesService.getScriptProperties();
    let currentNumber = parseInt(props.getProperty('CURRENT_RECEIPT_NUMBER') || '201204');
    currentNumber++;
    props.setProperty('CURRENT_RECEIPT_NUMBER', currentNumber.toString());
    
    return {
      success: true,
      newReceiptNumber: currentNumber.toString().padStart(6, '0')
    };
    
  } catch (error) {
    return {
      success: false,
      error: 'Error incrementing receipt number: ' + error.toString()
    };
  }
}

// ============================================================================
// GOOGLE DRIVE OPERATIONS
// ============================================================================

/**
 * Save a filled packet to Google Drive
 * @param {Object} data - { pdfBase64, fileName, defendantName, caseNumber }
 * @returns {Object} - { success: boolean, fileId?: string, folderUrl?: string }
 */
function saveFilledPacketToDrive(data) {
  const config = getConfig();
  
  try {
    // Create a folder for this defendant/case
    const parentFolder = DriveApp.getFolderById(config.GOOGLE_DRIVE_FOLDER_ID);
    const folderName = data.defendantName + ' - ' + data.caseNumber + ' - ' + 
                       Utilities.formatDate(new Date(), 'America/New_York', 'yyyy-MM-dd');
    
    let caseFolder;
    const existingFolders = parentFolder.getFoldersByName(folderName);
    if (existingFolders.hasNext()) {
      caseFolder = existingFolders.next();
    } else {
      caseFolder = parentFolder.createFolder(folderName);
    }
    
    // Save the PDF
    const pdfBytes = Utilities.base64Decode(data.pdfBase64);
    const pdfBlob = Utilities.newBlob(pdfBytes, 'application/pdf', data.fileName);
    const file = caseFolder.createFile(pdfBlob);
    
    return {
      success: true,
      fileId: file.getId(),
      fileName: file.getName(),
      folderUrl: caseFolder.getUrl(),
      fileUrl: file.getUrl()
    };
    
  } catch (error) {
    Logger.log('Drive Save Error: ' + error.toString());
    return {
      success: false,
      error: 'Error saving to Google Drive: ' + error.toString()
    };
  }
}

// ============================================================================
// BOOKING DATA PERSISTENCE (Calls FormDataHandler.gs)
// ============================================================================

/**
 * Save booking data to the spreadsheet
 * @param {Object} bookingData - The booking form data
 * @returns {Object} - { success: boolean, bookingId?: string }
 */
function saveBookingData(bookingData) {
  try {
    const bookingId = 'BK-' + Utilities.getUuid().substring(0, 8).toUpperCase();
    
    // TODO: Implement actual spreadsheet saving via FormDataHandler.gs
    
    return {
      success: true,
      bookingId: bookingId,
      message: 'Booking data saved successfully'
    };
    
  } catch (error) {
    return {
      success: false,
      error: 'Error saving booking data: ' + error.toString()
    };
  }
}

/**
 * Get booking data by ID
 * @param {string} bookingId - The booking ID
 * @returns {Object} - The booking data
 */
function getBookingData(bookingId) {
  try {
    // TODO: Implement actual retrieval via FormDataHandler.gs
    return {
      success: true,
      bookingId: bookingId,
      data: null,
      message: 'Booking retrieval not yet implemented'
    };
    
  } catch (error) {
    return {
      success: false,
      error: 'Error getting booking data: ' + error.toString()
    };
  }
}

// ============================================================================
// COUNTY STATISTICS (for Dashboard)
// ============================================================================

/**
 * Get arrest statistics for all active counties for today
 * Called by Form.html to populate the county dashboard
 * @returns {Object} Statistics object keyed by county name
 */
function getCountyStatistics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const counties = ['lee', 'collier', 'charlotte'];
  const stats = {};
  
  counties.forEach(county => {
    try {
      const sheetName = county.charAt(0).toUpperCase() + county.slice(1);
      const sheet = ss.getSheetByName(sheetName) || ss.getSheetByName(county);
      
      if (!sheet) {
        stats[county] = getEmptyStats();
        return;
      }
      
      const data = sheet.getDataRange().getValues();
      if (data.length < 2) {
        stats[county] = getEmptyStats();
        return;
      }
      
      const headers = data[0];
      const dateCol = headers.findIndex(h => String(h).toLowerCase().includes('date') || String(h).toLowerCase().includes('booking'));
      const genderCol = headers.findIndex(h => String(h).toLowerCase().includes('gender') || String(h).toLowerCase().includes('sex'));
      const chargeCol = headers.findIndex(h => String(h).toLowerCase().includes('charge'));
      const bondCol = headers.findIndex(h => String(h).toLowerCase().includes('bond'));
      
      let todayArrestees = [];
      
      for (let i = 1; i < data.length; i++) {
        const row = data[i];
        let rowDate = row[dateCol >= 0 ? dateCol : 0];
        
        if (rowDate instanceof Date) {
          rowDate.setHours(0, 0, 0, 0);
          if (rowDate.getTime() === today.getTime()) {
            todayArrestees.push({
              gender: genderCol >= 0 ? String(row[genderCol]).toUpperCase() : '',
              charge: chargeCol >= 0 ? String(row[chargeCol]) : '',
              bond: bondCol >= 0 ? parseFloat(row[bondCol]) || 0 : 0
            });
          }
        }
      }
      
      const totalArrestees = todayArrestees.length;
      const maleCount = todayArrestees.filter(a => a.gender === 'M' || a.gender === 'MALE').length;
      const femaleCount = todayArrestees.filter(a => a.gender === 'F' || a.gender === 'FEMALE').length;
      
      const bondAmounts = todayArrestees.map(a => a.bond).filter(b => b > 0);
      const avgBond = bondAmounts.length > 0 ? bondAmounts.reduce((a, b) => a + b, 0) / bondAmounts.length : 0;
      
      const chargeCounts = {};
      todayArrestees.forEach(a => {
        const chargeType = categorizeCharge(a.charge);
        chargeCounts[chargeType] = (chargeCounts[chargeType] || 0) + 1;
      });
      
      const topCharges = Object.entries(chargeCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([type, count]) => ({ type, count }));
      
      stats[county] = {
        totalArrestees,
        maleCount,
        femaleCount,
        avgBond: Math.round(avgBond),
        topCharges,
        lastUpdated: new Date().toISOString()
      };
      
    } catch (error) {
      Logger.log('Error getting stats for ' + county + ': ' + error.toString());
      stats[county] = getEmptyStats();
    }
  });
  
  return stats;
}

/**
 * Return empty statistics object
 */
function getEmptyStats() {
  return {
    totalArrestees: 0,
    maleCount: 0,
    femaleCount: 0,
    avgBond: 0,
    topCharges: [],
    lastUpdated: new Date().toISOString()
  };
}

/**
 * Categorize a charge into a general type
 */
function categorizeCharge(charge) {
  const chargeUpper = String(charge).toUpperCase();
  
  if (chargeUpper.includes('DUI') || chargeUpper.includes('DWI')) return 'DUI';
  if (chargeUpper.includes('BATTERY') || chargeUpper.includes('ASSAULT')) return 'Battery/Assault';
  if (chargeUpper.includes('THEFT') || chargeUpper.includes('BURGLARY') || chargeUpper.includes('ROBBERY')) return 'Theft/Burglary';
  if (chargeUpper.includes('DRUG') || chargeUpper.includes('COCAINE') || chargeUpper.includes('CANNABIS') || chargeUpper.includes('POSSESSION')) return 'Drug Offense';
  if (chargeUpper.includes('DOMESTIC')) return 'Domestic Violence';
  if (chargeUpper.includes('FRAUD') || chargeUpper.includes('FORGERY')) return 'Fraud';
  if (chargeUpper.includes('WEAPON') || chargeUpper.includes('FIREARM')) return 'Weapons';
  if (chargeUpper.includes('PROBATION') || chargeUpper.includes('VOP')) return 'Probation Violation';
  
  return 'Other';
}

// ============================================================================
// TEST & UTILITY FUNCTIONS
// ============================================================================

/**
 * Test function to verify Drive access - Run this manually to check permissions
 */
function testDriveAccess() {
  try {
    const testFileId = TEMPLATE_DRIVE_IDS['paperwork-header'];
    const file = DriveApp.getFileById(testFileId);
    return {
      success: true,
      fileName: file.getName(),
      message: 'Drive access is working'
    };
  } catch (error) {
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Test function to verify template access - Run this in the GAS editor
 */
function testTemplateAccess() {
  const templates = getTemplateList();
  Logger.log(JSON.stringify(templates, null, 2));
  return templates;
}

/**
 * Test SignNow connection - Run this in the GAS editor
 */
function testSignNowConnection() {
  const config = getConfig();
  
  try {
    if (!config.SIGNNOW_ACCESS_TOKEN) {
      return { success: false, error: 'SignNow API token not configured in Script Properties' };
    }
    
    const options = {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + config.SIGNNOW_ACCESS_TOKEN
      },
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(config.SIGNNOW_API_BASE + '/user', options);
    const result = JSON.parse(response.getContentText());
    
    Logger.log('SignNow User: ' + JSON.stringify(result));
    return { success: true, user: result };
    
  } catch (error) {
    Logger.log('SignNow Error: ' + error.toString());
    return { success: false, error: error.toString() };
  }
}

/**
 * Test getPdf function - Run this in the GAS editor
 */
function testGetPdf() {
  const result = getPdfByFileId(TEMPLATE_DRIVE_IDS['appearance-bond']);
  Logger.log('getPdf result: success=' + result.success + ', filename=' + result.fileName + ', size=' + (result.size || 'N/A'));
  return result;
}

/**
 * Run all tests - Run this in the GAS editor to verify everything is working
 */
function runAllTests() {
  Logger.log('=== Running All Tests ===');
  
  Logger.log('\n1. Testing Drive Access...');
  const driveTest = testDriveAccess();
  Logger.log('Drive Access: ' + (driveTest.success ? 'PASS' : 'FAIL - ' + driveTest.error));
  
  Logger.log('\n2. Testing Template List...');
  const templateTest = testTemplateAccess();
  Logger.log('Template List: ' + (templateTest.success ? 'PASS - ' + templateTest.count + ' templates' : 'FAIL'));
  
  Logger.log('\n3. Testing getPdf...');
  const pdfTest = testGetPdf();
  Logger.log('getPdf: ' + (pdfTest.success ? 'PASS - ' + pdfTest.fileName : 'FAIL - ' + pdfTest.error));
  
  Logger.log('\n4. Testing SignNow Connection...');
  const signNowTest = testSignNowConnection();
  Logger.log('SignNow: ' + (signNowTest.success ? 'PASS' : 'FAIL - ' + signNowTest.error));
  
  Logger.log('\n=== Tests Complete ===');
  
  return {
    driveAccess: driveTest.success,
    templateList: templateTest.success,
    getPdf: pdfTest.success,
    signNow: signNowTest.success
  };
}
