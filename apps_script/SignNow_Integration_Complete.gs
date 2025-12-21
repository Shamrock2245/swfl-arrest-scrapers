/**
 * ============================================================================
 * SignNow_Integration_Complete.gs
 * ============================================================================
 * Shamrock Bail Bonds - admin@shamrockbailbonds.biz
 * 
 * COMPLETE INTEGRATION FILE - Add this to your existing GAS project
 * 
 * This file provides:
 * 1. Multi-signer embedded signing (uses existing indemnitors from Dashboard.html)
 * 2. Redirect URIs to shamrockbailbonds.biz after signing
 * 3. Webhook handler for document completion
 * 4. Automatic Google Drive saving of completed documents
 * 
 * SETUP INSTRUCTIONS:
 * 1. Add this file to your Google Apps Script project
 * 2. Deploy as web app for webhook endpoint
 * 3. Register webhook URL with SignNow
 * 4. Configure Wix signing page (optional)
 * ============================================================================
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const INTEGRATION_CONFIG = {
  // Wix site URLs for redirects after signing
  REDIRECT_URI: 'https://www.shamrockbailbonds.biz',
  DECLINE_REDIRECT_URI: 'https://www.shamrockbailbonds.biz',
  CLOSE_REDIRECT_URI: 'https://www.shamrockbailbonds.biz',
  
  // Wix signing page URL (where embedded iFrame can be shown)
  WIX_SIGNING_PAGE: 'https://www.shamrockbailbonds.biz/sign',
  
  // Link expiration in minutes
  LINK_EXPIRATION_MINUTES: 45,
  
  // Google Drive folder for completed bonds
  COMPLETED_BONDS_FOLDER_ID: '1WnjwtxoaoXVW8_B6s-0ftdCPf_5WfKgs'
};

// ============================================================================
// MULTI-SIGNER EMBEDDED SIGNING
// ============================================================================

/**
 * Create embedded signing links for all signers (defendant + all indemnitors)
 * Called from Dashboard.html after document upload
 * 
 * @param {string} documentId - SignNow document ID
 * @param {Object} formData - Complete form data from Dashboard.html including indemnitors array
 * @param {Object} options - Optional settings
 * @returns {Object} - { success, signingLinks: [{role, name, email, phone, link, inviteId}] }
 */
function SN_createAllSignerLinks(documentId, formData, options) {
  const config = SN_getConfig();
  options = options || {};
  
  try {
    // Build signers array from form data
    const signers = buildSignersFromFormData(formData);
    
    if (signers.length === 0) {
      return { success: false, error: 'No signers found in form data' };
    }
    
    SN_log('createAllSignerLinks', { documentId: documentId, signerCount: signers.length });
    
    // First, get document to check for existing roles
    const docInfo = SN_getDocumentInfo(documentId);
    if (!docInfo.success) {
      return { success: false, error: 'Failed to get document info: ' + docInfo.error };
    }
    
    // Build the embedded invite payload
    const invites = signers.map((signer, index) => ({
      email: signer.email || `signer${index + 1}_${Date.now()}@shamrockbailbonds.biz`,
      role: signer.role,
      order: signer.order,
      auth_method: 'none',
      first_name: signer.firstName || '',
      last_name: signer.lastName || '',
      prefill_signature_name: `${signer.firstName || ''} ${signer.lastName || ''}`.trim(),
      force_new_signature: 1,
      redirect_uri: options.redirectUri || INTEGRATION_CONFIG.REDIRECT_URI,
      decline_redirect_uri: options.declineRedirectUri || INTEGRATION_CONFIG.DECLINE_REDIRECT_URI,
      close_redirect_uri: options.closeRedirectUri || INTEGRATION_CONFIG.CLOSE_REDIRECT_URI,
      redirect_target: 'self',
      language: 'en'
    }));
    
    // Create the embedded invite
    const invitePayload = {
      invites: invites,
      name_formula: `Shamrock_Bond_${formData['defendant-last-name'] || 'Unknown'}|date`
    };
    
    const inviteResponse = UrlFetchApp.fetch(
      config.API_BASE + '/v2/documents/' + documentId + '/embedded-invites',
      {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
          'Content-Type': 'application/json'
        },
        payload: JSON.stringify(invitePayload),
        muteHttpExceptions: true
      }
    );
    
    const inviteResult = JSON.parse(inviteResponse.getContentText());
    
    if (inviteResponse.getResponseCode() !== 200 && inviteResponse.getResponseCode() !== 201) {
      SN_log('createAllSignerLinks', { error: inviteResult });
      return { 
        success: false, 
        error: 'Failed to create embedded invite: ' + (inviteResult.error || inviteResult.message || JSON.stringify(inviteResult))
      };
    }
    
    // Generate signing links for each invite
    const signingLinks = [];
    const inviteData = inviteResult.data || [];
    
    for (let i = 0; i < inviteData.length; i++) {
      const invite = inviteData[i];
      const signer = signers[i];
      
      const linkPayload = {
        auth_method: 'none',
        link_expiration: options.linkExpiration || INTEGRATION_CONFIG.LINK_EXPIRATION_MINUTES
      };
      
      const linkResponse = UrlFetchApp.fetch(
        config.API_BASE + '/v2/documents/' + documentId + '/embedded-invites/' + invite.id + '/link',
        {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
            'Content-Type': 'application/json'
          },
          payload: JSON.stringify(linkPayload),
          muteHttpExceptions: true
        }
      );
      
      const linkResult = JSON.parse(linkResponse.getContentText());
      
      if (linkResponse.getResponseCode() === 200 || linkResponse.getResponseCode() === 201) {
        // Build Wix signing page URL with parameters
        const wixSigningUrl = buildWixSigningUrl(linkResult.link, signer);
        
        signingLinks.push({
          role: signer.role,
          firstName: signer.firstName,
          lastName: signer.lastName,
          fullName: `${signer.firstName} ${signer.lastName}`.trim(),
          email: signer.email,
          phone: signer.phone,
          order: signer.order,
          link: linkResult.link,
          wixLink: wixSigningUrl,
          inviteId: invite.id,
          expiresIn: (options.linkExpiration || INTEGRATION_CONFIG.LINK_EXPIRATION_MINUTES) + ' minutes'
        });
      } else {
        signingLinks.push({
          role: signer.role,
          firstName: signer.firstName,
          lastName: signer.lastName,
          error: 'Failed to generate link: ' + (linkResult.error || linkResult.message)
        });
      }
    }
    
    SN_log('createAllSignerLinks', { 
      success: true, 
      linksGenerated: signingLinks.filter(l => l.link).length 
    });
    
    return {
      success: true,
      documentId: documentId,
      signingLinks: signingLinks,
      wixSigningPageBase: INTEGRATION_CONFIG.WIX_SIGNING_PAGE
    };
    
  } catch (error) {
    SN_log('createAllSignerLinks', { error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Build signers array from Dashboard.html form data
 * Extracts defendant and all indemnitors
 * 
 * @param {Object} formData - Form data from collectFormData()
 * @returns {Array} - Array of signer objects
 */
function buildSignersFromFormData(formData) {
  const signers = [];
  let order = 1;
  
  // 1. Add Defendant (always first)
  if (formData['defendant-first-name'] || formData['defendant-last-name']) {
    signers.push({
      role: 'Defendant',
      firstName: formData['defendant-first-name'] || '',
      lastName: formData['defendant-last-name'] || '',
      email: formData['defendant-email'] || '',
      phone: formData['defendant-phone'] || '',
      order: order++
    });
  }
  
  // 2. Add all Indemnitors from the indemnitors array
  if (formData.indemnitors && Array.isArray(formData.indemnitors)) {
    formData.indemnitors.forEach((ind, index) => {
      if (ind.firstName || ind.lastName) {
        signers.push({
          role: index === 0 ? 'Indemnitor' : 'Co-Indemnitor',
          firstName: ind.firstName || '',
          lastName: ind.lastName || '',
          email: ind.email || '',
          phone: ind.phone || '',
          order: order++
        });
      }
    });
  }
  
  // 3. Add Bail Agent (always last - signs in office)
  signers.push({
    role: 'Bail Agent',
    firstName: 'Shamrock',
    lastName: 'Bail Bonds',
    email: 'admin@shamrockbailbonds.biz',
    phone: '',
    order: order++
  });
  
  return signers;
}

/**
 * Build Wix signing page URL with signer info as query parameters
 * 
 * @param {string} signingLink - Raw SignNow signing link
 * @param {Object} signer - Signer info
 * @returns {string} - Wix signing page URL
 */
function buildWixSigningUrl(signingLink, signer) {
  const params = new URLSearchParams();
  params.append('link', encodeURIComponent(signingLink));
  params.append('signer', encodeURIComponent(`${signer.firstName} ${signer.lastName}`.trim()));
  params.append('role', encodeURIComponent(signer.role));
  
  return INTEGRATION_CONFIG.WIX_SIGNING_PAGE + '?' + params.toString();
}

// ============================================================================
// COMPLETE WORKFLOW FUNCTION
// ============================================================================

/**
 * MAIN WORKFLOW: Generate documents, upload to SignNow, and create signing links
 * Called from Dashboard.html "Generate & Send" button
 * 
 * @param {Object} params - {
 *   formData: Object (from collectFormData()),
 *   selectedDocs: Array of document type strings,
 *   deliveryMethod: 'embedded' | 'email' | 'sms',
 *   pdfBase64: string (merged PDF as base64),
 *   fileName: string
 * }
 * @returns {Object} - { success, documentId, signingLinks?, error? }
 */
function SN_processCompleteWorkflow(params) {
  const { formData, selectedDocs, deliveryMethod, pdfBase64, fileName } = params;
  
  try {
    // Step 1: Upload the merged PDF to SignNow
    SN_log('processCompleteWorkflow', { step: 'upload', fileName: fileName });
    const uploadResult = SN_uploadDocument(pdfBase64, fileName);
    
    if (!uploadResult.success) {
      return { success: false, error: 'Upload failed: ' + uploadResult.error, step: 'upload' };
    }
    
    const documentId = uploadResult.documentId;
    
    // Step 2: Add signature fields based on selected documents
    SN_log('processCompleteWorkflow', { step: 'addFields', documentId: documentId });
    const fieldsResult = SN_addFieldsForSelectedDocs(documentId, selectedDocs, {
      includeCoIndemnitor: (formData.indemnitors && formData.indemnitors.length > 1)
    });
    
    if (!fieldsResult.success) {
      return { 
        success: false, 
        error: 'Add fields failed: ' + fieldsResult.error, 
        step: 'addFields',
        documentId: documentId 
      };
    }
    
    // Step 3: Handle delivery based on method
    if (deliveryMethod === 'embedded') {
      // Create embedded signing links for all signers
      SN_log('processCompleteWorkflow', { step: 'createLinks' });
      const linksResult = SN_createAllSignerLinks(documentId, formData);
      
      if (!linksResult.success) {
        return {
          success: false,
          error: 'Create signing links failed: ' + linksResult.error,
          step: 'createLinks',
          documentId: documentId
        };
      }
      
      return {
        success: true,
        documentId: documentId,
        deliveryMethod: 'embedded',
        signingLinks: linksResult.signingLinks,
        wixSigningPageBase: linksResult.wixSigningPageBase
      };
      
    } else if (deliveryMethod === 'email') {
      // Send email invites
      const signers = buildSignersFromFormData(formData).filter(s => s.email && s.role !== 'Bail Agent');
      const emailResult = SN_sendEmailInvite(documentId, signers, {
        subject: `Shamrock Bail Bonds - Documents for ${formData['defendant-first-name']} ${formData['defendant-last-name']}`,
        message: 'Please review and sign the attached bail bond documents.'
      });
      
      return {
        success: emailResult.success,
        documentId: documentId,
        deliveryMethod: 'email',
        error: emailResult.error
      };
      
    } else if (deliveryMethod === 'sms') {
      // Send SMS invites
      const signers = buildSignersFromFormData(formData).filter(s => s.phone && s.role !== 'Bail Agent');
      const smsResult = SN_sendSmsInvite(documentId, signers, {});
      
      return {
        success: smsResult.success,
        documentId: documentId,
        deliveryMethod: 'sms',
        error: smsResult.error
      };
    }
    
    return { success: false, error: 'Invalid delivery method: ' + deliveryMethod };
    
  } catch (error) {
    SN_log('processCompleteWorkflow', { error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Add signature fields for all selected documents
 * Calculates cumulative page offsets for merged PDF
 * 
 * @param {string} documentId - SignNow document ID
 * @param {Array} selectedDocs - Array of document type strings
 * @param {Object} options - { includeCoIndemnitor: boolean }
 * @returns {Object} - { success, fieldsAdded, error? }
 */
function SN_addFieldsForSelectedDocs(documentId, selectedDocs, options) {
  options = options || {};
  let totalFieldsAdded = 0;
  let currentPageOffset = 0;
  
  try {
    for (const docType of selectedDocs) {
      const docConfig = SN_SIGNATURE_FIELDS[docType];
      if (!docConfig || !docConfig.fields || docConfig.fields.length === 0) {
        // No fields for this document, just add page count to offset
        if (docConfig && docConfig.pageCount) {
          currentPageOffset += docConfig.pageCount;
        }
        continue;
      }
      
      // Filter fields based on options
      let fieldsToAdd = docConfig.fields.filter(field => {
        if (field.role === 'Co-Indemnitor' && !options.includeCoIndemnitor) {
          return field.required !== false; // Only skip if explicitly optional
        }
        return true;
      });
      
      // Adjust page numbers for merged PDF
      fieldsToAdd = fieldsToAdd.map(field => ({
        ...field,
        page: field.page + currentPageOffset
      }));
      
      // Add fields to document
      const result = SN_addFields(documentId, fieldsToAdd);
      if (result.success) {
        totalFieldsAdded += fieldsToAdd.length;
      }
      
      // Update page offset for next document
      currentPageOffset += docConfig.pageCount || 1;
    }
    
    return { success: true, fieldsAdded: totalFieldsAdded };
    
  } catch (error) {
    return { success: false, error: error.toString(), fieldsAdded: totalFieldsAdded };
  }
}

// ============================================================================
// WEBHOOK HANDLER - Document Completion
// ============================================================================

/**
 * Web App doPost handler for SignNow webhooks
 * Deploy this GAS project as a web app with "Anyone" access
 */
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    
    SN_log('webhook', { 
      event: payload.event, 
      documentId: payload.document_id,
      timestamp: new Date().toISOString()
    });
    
    // Handle document completion
    if (payload.event === 'document.complete') {
      const result = handleDocumentComplete(payload);
      return ContentService.createTextOutput(JSON.stringify(result))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Handle other events as needed
    if (payload.event === 'document.update') {
      // Document was updated (signature added)
      SN_log('webhook', { event: 'document.update', documentId: payload.document_id });
    }
    
    return ContentService.createTextOutput(JSON.stringify({ received: true }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    SN_log('webhook_error', { error: error.toString() });
    return ContentService.createTextOutput(JSON.stringify({ error: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Handle document completion - download and save to Google Drive
 * 
 * @param {Object} payload - Webhook payload from SignNow
 * @returns {Object} - Result
 */
function handleDocumentComplete(payload) {
  const documentId = payload.document_id;
  
  try {
    // Get document details
    const docInfo = SN_getDocumentInfo(documentId);
    if (!docInfo.success) {
      return { success: false, error: 'Failed to get document info' };
    }
    
    // Extract defendant name from document name
    // Expected format: "Shamrock_Bond_LastName|date" or similar
    let defendantName = 'Unknown';
    const docName = docInfo.document_name || '';
    const nameMatch = docName.match(/Bond_([^|_]+)/i);
    if (nameMatch) {
      defendantName = nameMatch[1];
    }
    
    // Get current date
    const bondDate = Utilities.formatDate(new Date(), 'America/New_York', 'MM-dd-yyyy');
    
    // Download the signed document
    const pdfBlob = SN_downloadDocument(documentId, 'collapsed');
    if (!pdfBlob) {
      return { success: false, error: 'Failed to download signed document' };
    }
    
    // Create folder name and file name
    const folderName = `${defendantName} - ${bondDate}`;
    const fileName = `${defendantName} - Signed Bond Package - ${bondDate}.pdf`;
    pdfBlob.setName(fileName);
    
    // Get or create defendant folder in Completed Bonds
    const completedFolder = DriveApp.getFolderById(INTEGRATION_CONFIG.COMPLETED_BONDS_FOLDER_ID);
    let defendantFolder;
    
    const existingFolders = completedFolder.getFoldersByName(folderName);
    if (existingFolders.hasNext()) {
      defendantFolder = existingFolders.next();
    } else {
      defendantFolder = completedFolder.createFolder(folderName);
    }
    
    // Save the signed PDF
    const savedFile = defendantFolder.createFile(pdfBlob);
    
    // Log completion to spreadsheet
    logCompletedBond({
      documentId: documentId,
      defendantName: defendantName,
      bondDate: bondDate,
      driveFileId: savedFile.getId(),
      driveUrl: savedFile.getUrl(),
      folderUrl: defendantFolder.getUrl(),
      completedAt: new Date().toISOString()
    });
    
    SN_log('documentComplete', {
      success: true,
      documentId: documentId,
      defendantName: defendantName,
      driveFileId: savedFile.getId()
    });
    
    return {
      success: true,
      driveFileId: savedFile.getId(),
      driveUrl: savedFile.getUrl(),
      folderUrl: defendantFolder.getUrl(),
      fileName: fileName
    };
    
  } catch (error) {
    SN_log('documentComplete_error', { error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Log completed bond to tracking sheet
 */
function logCompletedBond(data) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName('Completed Bonds Log');
    
    if (!sheet) {
      sheet = ss.insertSheet('Completed Bonds Log');
      sheet.appendRow([
        'Completed At',
        'Defendant Name',
        'Bond Date',
        'SignNow Doc ID',
        'Drive File ID',
        'Drive URL',
        'Folder URL'
      ]);
      sheet.getRange(1, 1, 1, 7).setFontWeight('bold');
    }
    
    sheet.appendRow([
      data.completedAt,
      data.defendantName,
      data.bondDate,
      data.documentId,
      data.driveFileId,
      data.driveUrl,
      data.folderUrl
    ]);
    
  } catch (error) {
    SN_log('logCompletedBond_error', { error: error.toString() });
  }
}

// ============================================================================
// WEBHOOK REGISTRATION
// ============================================================================

/**
 * Register webhook with SignNow for document completion events
 * Run this once after deploying the web app
 * 
 * @param {string} webhookUrl - Your deployed web app URL
 */
function SN_registerCompletionWebhook(webhookUrl) {
  const config = SN_getConfig();
  
  if (!webhookUrl) {
    // Try to get the deployed web app URL
    const scriptUrl = ScriptApp.getService().getUrl();
    if (scriptUrl) {
      webhookUrl = scriptUrl;
    } else {
      return { success: false, error: 'Please provide webhook URL or deploy as web app first' };
    }
  }
  
  try {
    const payload = {
      event: 'document.complete',
      callback_url: webhookUrl
    };
    
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/api/v2/events',
      {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
          'Content-Type': 'application/json'
        },
        payload: JSON.stringify(payload),
        muteHttpExceptions: true
      }
    );
    
    const result = JSON.parse(response.getContentText());
    const success = response.getResponseCode() === 200 || response.getResponseCode() === 201;
    
    SN_log('registerWebhook', { success: success, result: result });
    
    return { success: success, result: result };
    
  } catch (error) {
    return { success: false, error: error.toString() };
  }
}

/**
 * List all registered webhooks
 */
function SN_listRegisteredWebhooks() {
  const config = SN_getConfig();
  
  try {
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/api/v2/events',
      {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + config.ACCESS_TOKEN },
        muteHttpExceptions: true
      }
    );
    
    return JSON.parse(response.getContentText());
    
  } catch (error) {
    return { error: error.toString() };
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get document info from SignNow
 */
function SN_getDocumentInfo(documentId) {
  const config = SN_getConfig();
  
  try {
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/document/' + documentId,
      {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + config.ACCESS_TOKEN },
        muteHttpExceptions: true
      }
    );
    
    if (response.getResponseCode() === 200) {
      return { success: true, ...JSON.parse(response.getContentText()) };
    } else {
      return { success: false, error: response.getContentText() };
    }
    
  } catch (error) {
    return { success: false, error: error.toString() };
  }
}

/**
 * Send a single SMS with signing link
 * Called from Dashboard.html for individual signer
 */
function SN_sendSingleSigningLinkSms(phone, signingLink, signerName, role) {
  // Format phone number
  const formattedPhone = SN_formatPhoneE164(phone);
  if (!formattedPhone) {
    return { success: false, error: 'Invalid phone number' };
  }
  
  // Build message
  const message = `Shamrock Bail Bonds: ${signerName}, please sign your bail bond documents as the ${role}: ${signingLink}`;
  
  // Use existing SMS sending mechanism
  // This would integrate with your SMS provider (Twilio, etc.)
  // For now, return the message to be sent
  return {
    success: true,
    phone: formattedPhone,
    message: message,
    note: 'Integrate with your SMS provider'
  };
}

// ============================================================================
// TEST FUNCTIONS
// ============================================================================

/**
 * Test the complete workflow with sample data
 */
function testCompleteWorkflow() {
  const sampleFormData = {
    'defendant-first-name': 'John',
    'defendant-last-name': 'Doe',
    'defendant-email': 'john.doe@test.com',
    'defendant-phone': '239-555-1234',
    indemnitors: [
      {
        firstName: 'Jane',
        lastName: 'Smith',
        email: 'jane.smith@test.com',
        phone: '239-555-5678'
      }
    ]
  };
  
  const signers = buildSignersFromFormData(sampleFormData);
  Logger.log('Built signers: ' + JSON.stringify(signers, null, 2));
  
  return signers;
}

/**
 * Test webhook registration
 */
function testWebhookRegistration() {
  const result = SN_listRegisteredWebhooks();
  Logger.log('Registered webhooks: ' + JSON.stringify(result, null, 2));
  return result;
}
