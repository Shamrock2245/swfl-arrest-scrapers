/**
 * WixPortalIntegration.gs (UPDATED with Case Data Sync)
 * 
 * This module integrates the Dashboard.html/GAS workflow with the Wix portal.
 * When signing links are generated, they are automatically saved to the Wix
 * PendingDocuments collection so clients can see them when they log in.
 * 
 * NEW: When case data is saved to Google Sheets, it also syncs to Wix Cases collection
 * 
 * Add this file to your Google Apps Script project alongside SignNowAPI.gs
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

/**
 * Get Wix Portal configuration
 * Store your API key in Script Properties for security
 */
function getWixPortalConfig() {
  const scriptProps = PropertiesService.getScriptProperties();
  return {
    // Wix site API endpoints
    baseUrl: 'https://www.shamrockbailbonds.biz/_functions',
    
    // API key for authentication (set in Script Properties)
    apiKey: scriptProps.getProperty('WIX_API_KEY') || '',
    
    // Endpoints
    endpoints: {
      addDocument: '/documentsAdd',
      addDocumentsBatch: '/documentsBatch',
      updateStatus: '/documentsStatus',
      syncCaseData: '/api/syncCaseData'  // NEW ENDPOINT
    }
  };
}

/**
 * Set the Wix API key in Script Properties
 * Run this once to configure the API key
 */
function setWixApiKey(apiKey) {
  const scriptProps = PropertiesService.getScriptProperties();
  scriptProps.setProperty('WIX_API_KEY', apiKey);
  Logger.log('Wix API key set successfully');
}

// =============================================================================
// CASE DATA SYNC (NEW FUNCTIONALITY)
// =============================================================================

/**
 * Sync case data to Wix portal when a case is saved
 * This should be called from FormDataHandler.gs after saveBookingData()
 * 
 * @param {Object} caseData - The case data from the form
 * @param {number} sheetRow - The row number in the Google Sheet
 * @returns {Object} Result with success status
 */
function syncCaseDataToWix(caseData, sheetRow) {
  const config = getWixPortalConfig();
  
  if (!config.apiKey) {
    Logger.log('Warning: Wix API key not configured. Run setWixApiKey() first.');
    return { success: false, message: 'Wix API key not configured' };
  }
  
  // Build the payload for Wix
  const payload = {
    apiKey: config.apiKey,
    caseData: {
      caseNumber: caseData.Case_Number || caseData.Booking_Number || '',
      defendantName: caseData.Full_Name || '',
      defendantEmail: caseData.Email || '',
      defendantPhone: caseData.Phone || '',
      indemnitorName: caseData.Indemnitor_Name || '',
      indemnitorEmail: caseData.Indemnitor_Email || '',
      indemnitorPhone: caseData.Indemnitor_Phone || '',
      bondAmount: caseData.Bond_Amount || '',
      county: caseData.County || '',
      arrestDate: caseData.Arrest_Date || caseData.Booking_Date || '',
      charges: caseData.Charges || '',
      status: caseData.Status || 'pending',
      receiptNumber: caseData.Receipt_Number || '',
      gasSheetRow: sheetRow || null
    }
  };
  
  try {
    const response = UrlFetchApp.fetch(config.baseUrl + config.endpoints.syncCaseData, {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    const responseCode = response.getResponseCode();
    const result = JSON.parse(response.getContentText());
    
    if (responseCode === 200) {
      Logger.log('✅ Case data synced to Wix successfully: ' + JSON.stringify(result));
      return result;
    } else {
      Logger.log('⚠️ Wix sync returned status ' + responseCode + ': ' + JSON.stringify(result));
      return { success: false, message: 'HTTP ' + responseCode, details: result };
    }
    
  } catch (error) {
    Logger.log('❌ Error syncing case data to Wix: ' + error.message);
    return { success: false, message: error.message };
  }
}

/**
 * Enhanced version of saveBookingData that also syncs to Wix
 * This wraps the existing FormDataHandler.saveBookingData function
 * 
 * @param {Object} payload - The booking data payload
 * @returns {Object} Result with both Sheet save and Wix sync status
 */
function saveBookingDataWithWixSync(payload) {
  // First, save to Google Sheets using the existing function
  const sheetResult = saveBookingData(payload);
  
  if (!sheetResult.success) {
    return sheetResult;
  }
  
  // Now sync to Wix portal
  const wixResult = syncCaseDataToWix(payload, sheetResult.row);
  
  // Return combined result
  return {
    success: true,
    message: sheetResult.message,
    bookingNumber: sheetResult.bookingNumber,
    row: sheetResult.row,
    timestamp: sheetResult.timestamp,
    wixSync: wixResult,
    wixSyncMessage: wixResult.success 
      ? 'Case synced to Wix portal' 
      : 'Sheet saved but Wix sync failed: ' + wixResult.message
  };
}

// =============================================================================
// SIGNING LINK INTEGRATION (EXISTING FUNCTIONALITY)
// =============================================================================

/**
 * Save a single signing link to the Wix portal
 * Called after generating a signing link in SignNowAPI.gs
 * 
 * @param {Object} signerData - The signer information
 * @param {string} signerData.email - Signer's email
 * @param {string} signerData.phone - Signer's phone
 * @param {string} signerData.name - Signer's name
 * @param {string} signerData.role - Role: defendant, indemnitor, agent
 * @param {Object} documentData - The document information
 * @param {string} documentData.defendantName - Defendant's full name
 * @param {string} documentData.caseNumber - Case number
 * @param {string} documentData.documentName - Name of the document packet
 * @param {string} documentData.signingLink - The SignNow signing link
 * @param {string} documentData.signNowDocumentId - SignNow document ID
 * @param {Date} documentData.expiresAt - When the link expires
 * @returns {Object} Result with success status and message
 */
function saveSigningLinkToWix(signerData, documentData) {
  const config = getWixPortalConfig();
  
  if (!config.apiKey) {
    Logger.log('Warning: Wix API key not configured. Run setWixApiKey() first.');
    return { success: false, message: 'Wix API key not configured' };
  }
  
  const payload = {
    apiKey: config.apiKey,
    document: {
      memberEmail: signerData.email || '',
      memberPhone: signerData.phone || '',
      defendantName: documentData.defendantName || '',
      caseNumber: documentData.caseNumber || '',
      documentName: documentData.documentName || 'Bail Bond Document',
      signingLink: documentData.signingLink,
      signerRole: signerData.role || 'signer',
      signNowDocumentId: documentData.signNowDocumentId || '',
      expiresAt: documentData.expiresAt ? documentData.expiresAt.toISOString() : null
    }
  };
  
  try {
    const response = UrlFetchApp.fetch(config.baseUrl + config.endpoints.addDocument, {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    Logger.log('Wix portal response: ' + JSON.stringify(result));
    return result;
    
  } catch (error) {
    Logger.log('Error saving to Wix portal: ' + error.message);
    return { success: false, message: error.message };
  }
}

/**
 * Save multiple signing links to the Wix portal (batch operation)
 * Called after generating signing links for all signers
 * 
 * @param {Array<Object>} signers - Array of signer objects with their signing links
 * @param {Object} caseData - Common case data
 * @returns {Object} Result with success status and results array
 */
function saveSigningLinksToWixBatch(signers, caseData) {
  const config = getWixPortalConfig();
  
  if (!config.apiKey) {
    Logger.log('Warning: Wix API key not configured. Run setWixApiKey() first.');
    return { success: false, message: 'Wix API key not configured' };
  }
  
  const documents = signers.map(signer => ({
    memberEmail: signer.email || '',
    memberPhone: signer.phone || '',
    defendantName: caseData.defendantName || '',
    caseNumber: caseData.caseNumber || '',
    documentName: caseData.documentName || 'Bail Bond Document',
    signingLink: signer.signingLink,
    signerRole: signer.role || 'signer',
    signNowDocumentId: signer.signNowDocumentId || caseData.signNowDocumentId || '',
    expiresAt: caseData.expiresAt ? caseData.expiresAt.toISOString() : null
  }));
  
  const payload = {
    apiKey: config.apiKey,
    documents: documents
  };
  
  try {
    const response = UrlFetchApp.fetch(config.baseUrl + config.endpoints.addDocumentsBatch, {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    Logger.log('Wix portal batch response: ' + JSON.stringify(result));
    return result;
    
  } catch (error) {
    Logger.log('Error saving batch to Wix portal: ' + error.message);
    return { success: false, message: error.message };
  }
}

/**
 * Update document status in the Wix portal
 * Called when a document is signed (via webhook) or expires
 * 
 * @param {string} signNowDocumentId - The SignNow document ID
 * @param {string} status - New status: signed, expired, cancelled
 * @returns {Object} Result with success status
 */
function updateWixDocumentStatus(signNowDocumentId, status) {
  const config = getWixPortalConfig();
  
  if (!config.apiKey) {
    return { success: false, message: 'Wix API key not configured' };
  }
  
  const payload = {
    apiKey: config.apiKey,
    signNowDocumentId: signNowDocumentId,
    status: status
  };
  
  try {
    const response = UrlFetchApp.fetch(config.baseUrl + config.endpoints.updateStatus, {
      method: 'POST',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    Logger.log('Wix status update response: ' + JSON.stringify(result));
    return result;
    
  } catch (error) {
    Logger.log('Error updating Wix status: ' + error.message);
    return { success: false, message: error.message };
  }
}

// =============================================================================
// INTEGRATION WITH EXISTING SIGNNOW WORKFLOW
// =============================================================================

/**
 * Enhanced version of generateAndSendForSigning that also saves to Wix
 * This wraps the existing SignNow functionality and adds Wix portal integration
 * 
 * @param {Object} formData - All form data from Dashboard.html
 * @returns {Object} Result with signing links and Wix portal status
 */
function generateAndSendWithWixPortal(formData) {
  // First, generate the signing links using existing SignNow functions
  // (This assumes SN_generateMultiSignerLinks exists in SignNow_Integration_Complete.gs)
  
  const signingResult = SN_generateMultiSignerLinks(formData);
  
  if (!signingResult.success) {
    return signingResult;
  }
  
  // Now save all signing links to the Wix portal
  const caseData = {
    defendantName: formData.defendantName || 
                   (formData.defendantFirstName + ' ' + formData.defendantLastName),
    caseNumber: formData.caseNumber || '',
    documentName: 'Bail Bond Packet - ' + (formData.defendantName || 
                   (formData.defendantFirstName + ' ' + formData.defendantLastName)),
    signNowDocumentId: signingResult.documentId || '',
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days from now
  };
  
  // Prepare signers array with their links
  const signersWithLinks = signingResult.signers.map(signer => ({
    email: signer.email,
    phone: signer.phone,
    role: signer.role,
    signingLink: signer.signingLink,
    signNowDocumentId: signingResult.documentId
  }));
  
  // Save to Wix portal
  const wixResult = saveSigningLinksToWixBatch(signersWithLinks, caseData);
  
  // Return combined result
  return {
    success: true,
    signingLinks: signingResult.signers,
    documentId: signingResult.documentId,
    wixPortal: wixResult,
    message: wixResult.success 
      ? 'Documents generated and saved to client portal' 
      : 'Documents generated but portal save failed: ' + wixResult.message
  };
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Test the Wix portal connection
 * Run this to verify the integration is working
 */
function testWixPortalConnection() {
  const config = getWixPortalConfig();
  
  try {
    const response = UrlFetchApp.fetch(config.baseUrl.replace('/_functions', '') + '/_functions/health', {
      method: 'GET',
      muteHttpExceptions: true
    });
    
    Logger.log('Wix portal health check: ' + response.getContentText());
    return JSON.parse(response.getContentText());
    
  } catch (error) {
    Logger.log('Wix portal connection failed: ' + error.message);
    return { success: false, message: error.message };
  }
}

/**
 * Test the case data sync endpoint
 * Run this to verify the new syncCaseData endpoint is working
 */
function testWixCaseDataSync() {
  const testData = {
    Case_Number: 'TEST-2024-001',
    Full_Name: 'John Test Doe',
    Email: 'john.test@example.com',
    Phone: '2395551234',
    Bond_Amount: '10000',
    County: 'Collier',
    Arrest_Date: '2024-01-15',
    Charges: 'DUI',
    Status: 'pending'
  };
  
  Logger.log('Testing Wix case data sync with test data...');
  const result = syncCaseDataToWix(testData, 999);
  
  Logger.log('Test result: ' + JSON.stringify(result));
  return result;
}

/**
 * Generate a secure API key for Wix portal authentication
 * Run this once and save the key in both GAS Script Properties and Wix Secrets
 */
function generateWixApiKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let key = '';
  for (let i = 0; i < 32; i++) {
    key += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  
  Logger.log('Generated API Key: ' + key);
  Logger.log('Save this key in:');
  Logger.log('1. GAS Script Properties as WIX_API_KEY');
  Logger.log('2. Wix Secrets Manager as GAS_API_KEY');
  
  return key;
}
