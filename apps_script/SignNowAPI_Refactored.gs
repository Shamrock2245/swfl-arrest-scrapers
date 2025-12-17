/**
 * ============================================================================
 * SignNowAPI.gs - REFACTORED for Complete Workflow
 * ============================================================================
 * Shamrock Bail Bonds - admin@shamrockbailbonds.biz
 * 
 * WORKFLOW SUPPORTED:
 * 1. Pre-fill PDFs locally (via pdf-lib in browser or Python backend)
 * 2. Upload pre-filled PDF to SignNow
 * 3. Add signature/initials fields programmatically
 * 4. Send invite via EMAIL, SMS, or get EMBEDDED LINK (kiosk mode)
 * 5. Monitor signing status
 * 6. Download completed document
 * 7. Save to Google Drive "Completed Bonds" folder
 * 
 * All functions prefixed with SN_ to avoid conflicts
 * ============================================================================
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Get SignNow configuration from Script Properties
 */
function SN_getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    API_BASE: props.getProperty('SIGNNOW_API_BASE_URL') || 'https://api.signnow.com',
    ACCESS_TOKEN: props.getProperty('SIGNNOW_API_TOKEN') || '',
    FOLDER_ID: props.getProperty('SIGNNOW_FOLDER_ID') || '',
    SENDER_EMAIL: 'admin@shamrockbailbonds.biz'
  };
}

/**
 * Signature field positions for each document type
 * These define WHERE signatures/initials go on each PDF
 * Coordinates are in pixels from top-left of page
 * Page numbers are 1-indexed (page 1 = 1) as provided, converted to 0-indexed for API
 * 
 * Roles: 'Defendant', 'Indemnitor', 'Co-Indemnitor', 'Bail Agent'
 */
const SN_SIGNATURE_FIELDS = {
  // paperwork-header (15sTaIIwhzHk96I8X3rxz7GtLMU-F5zo1) - No signature fields
  'paperwork-header': {
    driveId: '15sTaIIwhzHk96I8X3rxz7GtLMU-F5zo1',
    pageCount: 1,
    fields: []
  },

  // faq-cosigners (1bjmH2w-XS5Hhe828y_Jmv9DqaS_gSZM7)
  'faq-cosigners': {
    driveId: '1bjmH2w-XS5Hhe828y_Jmv9DqaS_gSZM7',
    pageCount: 2,
    fields: [
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p1', page: 0, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p1', page: 0, x: 502, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p2', page: 1, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p2', page: 1, x: 502, y: 30, width: 50, height: 22, required: true }
    ]
  },

  // faq-defendants (16j9Z8eTii-J_p4o6A2LrzgzptGB8aOhR)
  'faq-defendants': {
    driveId: '16j9Z8eTii-J_p4o6A2LrzgzptGB8aOhR',
    pageCount: 2,
    fields: [
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p1', page: 0, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p1', page: 0, x: 502, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p2', page: 1, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p2', page: 1, x: 502, y: 30, width: 50, height: 22, required: true }
    ]
  },

  // indemnity-agreement (1p4bYIiZ__JnJHhlmVwLyPJZpsmSdGq12)
  'indemnity-agreement': {
    driveId: '1p4bYIiZ__JnJHhlmVwLyPJZpsmSdGq12',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor', page: 0, x: 330, y: 95, width: 230, height: 34, required: true }
    ]
  },

  // defendant-application (1cokWm8qCDpiGxYD6suZEjm9i8MoABeVe)
  'defendant-application': {
    driveId: '1cokWm8qCDpiGxYD6suZEjm9i8MoABeVe',
    pageCount: 2,
    fields: [
      { type: 'signature', role: 'Bail Agent', name: 'signature-agent', page: 0, x: 85, y: 95, width: 210, height: 34, required: true },
      { type: 'signature', role: 'Defendant', name: 'signature-defendant', page: 0, x: 335, y: 95, width: 210, height: 34, required: true },
      { type: 'signature', role: 'Defendant', name: 'signature-defendant-page-2', page: 1, x: 155, y: 110, width: 300, height: 34, required: true }
    ]
  },

  // promissory-note (104-ArZiCm3cgfQcT5rIO0x_OWiaw6Ddt)
  'promissory-note': {
    driveId: '104-ArZiCm3cgfQcT5rIO0x_OWiaw6Ddt',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Defendant', name: 'signature-defendant', page: 0, x: 85, y: 95, width: 210, height: 34, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor', page: 0, x: 325, y: 95, width: 210, height: 34, required: true }
    ]
  },

  // disclosure-form (1qIIDudp7r3J7-6MHlL2US34RcrU9KZKY)
  'disclosure-form': {
    driveId: '1qIIDudp7r3J7-6MHlL2US34RcrU9KZKY',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Defendant', name: 'signature-defendant', page: 0, x: 85, y: 515, width: 180, height: 35, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor', page: 0, x: 315, y: 515, width: 180, height: 35, required: true },
      { type: 'signature', role: 'Co-Indemnitor', name: 'signature-co-indemnitor', page: 0, x: 85, y: 470, width: 180, height: 35, required: false },
      { type: 'signature', role: 'Bail Agent', name: 'signature-agent', page: 0, x: 315, y: 470, width: 180, height: 35, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor-2', page: 0, x: 85, y: 395, width: 180, height: 35, required: false },
      { type: 'signature', role: 'Co-Indemnitor', name: 'signature-co-indemnitor-2', page: 0, x: 315, y: 395, width: 180, height: 35, required: false }
    ]
  },

  // surety-terms (1VfmyUTpchfwJTlENlR72JxmoE_NCF-uf)
  'surety-terms': {
    driveId: '1VfmyUTpchfwJTlENlR72JxmoE_NCF-uf',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Defendant', name: 'signature-defendant', page: 0, x: 85, y: 140, width: 200, height: 34, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor-1', page: 0, x: 325, y: 140, width: 200, height: 34, required: true },
      { type: 'signature', role: 'Co-Indemnitor', name: 'signature-indemnitor-2', page: 0, x: 85, y: 95, width: 200, height: 34, required: false },
      { type: 'signature', role: 'Co-Indemnitor', name: 'signature-indemnitor-3', page: 0, x: 325, y: 95, width: 200, height: 34, required: false }
    ]
  },

  // master-waiver (181mgKQN-VxvQOyzDquFs8cFHUN0tjrMs)
  'master-waiver': {
    driveId: '181mgKQN-VxvQOyzDquFs8cFHUN0tjrMs',
    pageCount: 4,
    fields: [
      // Page 1 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p1', page: 0, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p1', page: 0, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 2 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p2', page: 1, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p2', page: 1, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 3 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p3', page: 2, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p3', page: 2, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 4 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p4', page: 3, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p4', page: 3, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 4 signatures
      { type: 'signature', role: 'Bail Agent', name: 'signature-surety-representative', page: 3, x: 195, y: 303, width: 145, height: 26, required: true },
      { type: 'signature', role: 'Defendant', name: 'signature-defendant', page: 3, x: 155, y: 275, width: 185, height: 26, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor', page: 3, x: 165, y: 247, width: 175, height: 26, required: true },
      { type: 'signature', role: 'Co-Indemnitor', name: 'signature-co-indemnitor', page: 3, x: 175, y: 219, width: 165, height: 26, required: false }
    ]
  },

  // ssa-release (1govKv_N1wl0FIePV8Xfa8mFmZ9JT8mNu)
  'ssa-release': {
    driveId: '1govKv_N1wl0FIePV8Xfa8mFmZ9JT8mNu',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Defendant', name: 'signature-authorizing-party', page: 0, x: 140, y: 145, width: 330, height: 40, required: true }
    ]
  },

  // collateral-receipt (1IAYq4H2b0N0vPnJN7b2vZPaHg_RNKCmP)
  'collateral-receipt': {
    driveId: '1IAYq4H2b0N0vPnJN7b2vZPaHg_RNKCmP',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Bail Agent', name: 'signature-bail-agent-received-by-top', page: 0, x: 95, y: 355, width: 200, height: 32, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-depositor', page: 0, x: 350, y: 305, width: 210, height: 32, required: true },
      { type: 'signature', role: 'Bail Agent', name: 'signature-bail-agent-bottom', page: 0, x: 90, y: 165, width: 210, height: 32, required: true }
    ]
  },

  // payment-plan (1v-qkaegm6MDymiaPK45JqfXXX2_KOj8A)
  'payment-plan': {
    driveId: '1v-qkaegm6MDymiaPK45JqfXXX2_KOj8A',
    pageCount: 4,
    fields: [
      // Page 1 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p1', page: 0, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p1', page: 0, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 2 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p2', page: 1, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p2', page: 1, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 3 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p3', page: 2, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p3', page: 2, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 4 initials
      { type: 'initials', role: 'Defendant', name: 'initials-defendant-p4', page: 3, x: 60, y: 30, width: 50, height: 22, required: true },
      { type: 'initials', role: 'Indemnitor', name: 'initials-indemnitor-p4', page: 3, x: 502, y: 30, width: 50, height: 22, required: true },
      // Page 4 signatures
      { type: 'signature', role: 'Defendant', name: 'signature-defendant', page: 3, x: 180, y: 658, width: 185, height: 28, required: true },
      { type: 'signature', role: 'Indemnitor', name: 'signature-indemnitor', page: 3, x: 186, y: 630, width: 185, height: 28, required: true }
    ]
  },

  // appearance-bond (15SDM1oBysTw76bIL7Xt0Uhti8uRZKABs) - PRINT ONLY but included for completeness
  'appearance-bond': {
    driveId: '15SDM1oBysTw76bIL7Xt0Uhti8uRZKABs',
    pageCount: 1,
    fields: [
      { type: 'signature', role: 'Bail Agent', name: 'signature-agent-attorney-in-fact', page: 0, x: 95, y: 250, width: 230, height: 30, required: false },
      { type: 'signature', role: 'Bail Agent', name: 'signature-agent-bondsman', page: 0, x: 70, y: 55, width: 220, height: 28, required: false }
    ]
  }
};

// ============================================================================
// CORE API FUNCTIONS
// ============================================================================

/**
 * Validate the SignNow access token
 * @returns {Object} - { valid: boolean, user?: Object, error?: string }
 */
function SN_validateToken() {
  const config = SN_getConfig();
  
  if (!config.ACCESS_TOKEN) {
    return { valid: false, error: 'No access token configured' };
  }
  
  try {
    const response = UrlFetchApp.fetch(config.API_BASE + '/user', {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + config.ACCESS_TOKEN },
      muteHttpExceptions: true
    });
    
    const data = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      return { valid: true, user: data };
    } else {
      return { valid: false, error: data.message || 'Token validation failed' };
    }
  } catch (error) {
    return { valid: false, error: error.toString() };
  }
}

/**
 * Upload a pre-filled PDF to SignNow
 * @param {string} pdfBase64 - Base64 encoded PDF
 * @param {string} fileName - Name for the document
 * @returns {Object} - { success: boolean, documentId?: string, error?: string }
 */
function SN_uploadDocument(pdfBase64, fileName) {
  const config = SN_getConfig();
  
  if (!config.ACCESS_TOKEN) {
    return { success: false, error: 'SignNow API token not configured' };
  }
  
  try {
    const pdfBytes = Utilities.base64Decode(pdfBase64);
    const boundary = '----WebKitFormBoundary' + Utilities.getUuid();
    
    // Build multipart form data
    let payload = '--' + boundary + '\r\n';
    payload += 'Content-Disposition: form-data; name="file"; filename="' + fileName + '"\r\n';
    payload += 'Content-Type: application/pdf\r\n\r\n';
    
    const payloadBytes = Utilities.newBlob(payload).getBytes();
    const endBytes = Utilities.newBlob('\r\n--' + boundary + '--\r\n').getBytes();
    const allBytes = [...payloadBytes, ...pdfBytes, ...endBytes];
    
    const response = UrlFetchApp.fetch(config.API_BASE + '/document', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
        'Content-Type': 'multipart/form-data; boundary=' + boundary
      },
      payload: Utilities.newBlob(allBytes).getBytes(),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200 || response.getResponseCode() === 201) {
      SN_log('uploadDocument', { success: true, documentId: result.id, fileName: fileName });
      return { success: true, documentId: result.id, fileName: fileName };
    } else {
      SN_log('uploadDocument', { success: false, error: result });
      return { success: false, error: result.error || result.message || 'Upload failed' };
    }
  } catch (error) {
    SN_log('uploadDocument', { success: false, error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Get document details including roles
 * @param {string} documentId - SignNow document ID
 * @returns {Object} - Document details including roles array
 */
function SN_getDocument(documentId) {
  const config = SN_getConfig();
  
  try {
    const response = UrlFetchApp.fetch(config.API_BASE + '/document/' + documentId, {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + config.ACCESS_TOKEN },
      muteHttpExceptions: true
    });
    
    return JSON.parse(response.getContentText());
  } catch (error) {
    return { error: error.toString() };
  }
}

/**
 * Add signature/initials fields to an uploaded document
 * @param {string} documentId - SignNow document ID
 * @param {Array} fields - Array of field objects
 * @returns {Object} - { success: boolean, error?: string }
 */
function SN_addFields(documentId, fields) {
  const config = SN_getConfig();
  
  if (!fields || fields.length === 0) {
    return { success: true, message: 'No fields to add' };
  }
  
  try {
    // Format fields for SignNow API
    const formattedFields = fields.map(field => ({
      type: field.type,
      required: field.required !== false,
      role: field.role,
      name: field.name || '',
      page_number: field.page || 0,
      x: field.x,
      y: field.y,
      width: field.width,
      height: field.height,
      ...(field.lock_to_sign_date && {
        lock_to_sign_date: true,
        validator_id: '13435fa6c2a17f83177fcbb5c4a9376ce85befeb' // MM/DD/YYYY format
      }),
      ...(field.type === 'signature' && {
        allowed_types: ['draw', 'type', 'upload']
      })
    }));
    
    const response = UrlFetchApp.fetch(config.API_BASE + '/document/' + documentId, {
      method: 'PUT',
      headers: {
        'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify({ fields: formattedFields }),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      SN_log('addFields', { success: true, documentId: documentId, fieldCount: fields.length });
      return { success: true, documentId: result.id };
    } else {
      SN_log('addFields', { success: false, error: result });
      return { success: false, error: result.error || result.message || 'Failed to add fields' };
    }
  } catch (error) {
    SN_log('addFields', { success: false, error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Add predefined signature fields for a specific document type
 * @param {string} documentId - SignNow document ID
 * @param {string} documentType - Document type key (e.g., 'defendant-application')
 * @param {Object} options - { includeCoIndemnitor: boolean } - whether to include co-indemnitor fields
 * @returns {Object} - { success: boolean, error?: string }
 */
function SN_addFieldsForDocType(documentId, documentType, options) {
  const fieldConfig = SN_SIGNATURE_FIELDS[documentType];
  options = options || {};
  
  if (!fieldConfig) {
    return { success: true, message: 'No predefined fields for document type: ' + documentType };
  }
  
  // Filter fields based on options
  let fieldsToAdd = fieldConfig.fields;
  
  // If no co-indemnitor, filter out co-indemnitor fields
  if (!options.includeCoIndemnitor) {
    fieldsToAdd = fieldsToAdd.filter(f => f.role !== 'Co-Indemnitor');
  }
  
  // Filter out optional fields if not needed
  if (!options.includeOptional) {
    fieldsToAdd = fieldsToAdd.filter(f => f.required !== false);
  }
  
  return SN_addFields(documentId, fieldsToAdd);
}

/**
 * Get the signature field configuration for a document type
 * @param {string} documentType - Document type key
 * @returns {Object} - Field configuration or null
 */
function SN_getFieldConfig(documentType) {
  return SN_SIGNATURE_FIELDS[documentType] || null;
}

/**
 * Get all available document types with their field configurations
 * @returns {Object} - All document types and their configs
 */
function SN_getAllFieldConfigs() {
  return SN_SIGNATURE_FIELDS;
}

// ============================================================================
// INVITE FUNCTIONS - EMAIL, SMS, AND EMBEDDED
// ============================================================================

/**
 * Send signing invite via EMAIL
 * @param {string} documentId - SignNow document ID
 * @param {Array} signers - Array of { email, role, name, order }
 * @param {Object} options - { subject, message, fromEmail }
 * @returns {Object} - { success: boolean, inviteId?: string }
 */
function SN_sendEmailInvite(documentId, signers, options) {
  const config = SN_getConfig();
  options = options || {};
  
  try {
    // First get the document to retrieve role IDs
    const doc = SN_getDocument(documentId);
    const roleMap = {};
    
    if (doc.roles) {
      doc.roles.forEach(role => {
        roleMap[role.name] = role.unique_id;
      });
    }
    
    const invitePayload = {
      to: signers.map((signer, index) => ({
        email: signer.email,
        role: signer.role,
        role_id: roleMap[signer.role] || '',
        order: signer.order || (index + 1)
      })),
      from: options.fromEmail || config.SENDER_EMAIL,
      subject: options.subject || 'Documents Ready for Signature - Shamrock Bail Bonds',
      message: options.message || 'Please review and sign the attached bail bond documents. If you have any questions, please contact us.'
    };
    
    const response = UrlFetchApp.fetch(config.API_BASE + '/document/' + documentId + '/invite', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(invitePayload),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200 || response.getResponseCode() === 201) {
      SN_log('sendEmailInvite', { success: true, documentId: documentId });
      return { success: true, inviteId: result.id || result.result, documentId: documentId };
    } else {
      SN_log('sendEmailInvite', { success: false, error: result });
      return { success: false, error: result.error || result.message || 'Email invite failed' };
    }
  } catch (error) {
    SN_log('sendEmailInvite', { success: false, error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Send signing invite via SMS (US/Canada only)
 * @param {string} documentId - SignNow document ID
 * @param {Array} signers - Array of { phone, role, name, order, smsMessage }
 * @param {Object} options - { fromEmail }
 * @returns {Object} - { success: boolean, inviteId?: string }
 */
function SN_sendSmsInvite(documentId, signers, options) {
  const config = SN_getConfig();
  options = options || {};
  
  try {
    // First get the document to retrieve role IDs
    const doc = SN_getDocument(documentId);
    const roleMap = {};
    
    if (doc.roles) {
      doc.roles.forEach(role => {
        roleMap[role.name] = role.unique_id;
      });
    }
    
    const invitePayload = {
      to: signers.map((signer, index) => ({
        phone_invite: SN_formatPhoneE164(signer.phone),
        role: signer.role,
        role_id: roleMap[signer.role] || '',
        order: signer.order || (index + 1),
        sms_message: signer.smsMessage || 'Shamrock Bail Bonds: Please sign your bail bond documents.'
      })),
      from: options.fromEmail || config.SENDER_EMAIL
    };
    
    const response = UrlFetchApp.fetch(config.API_BASE + '/document/' + documentId + '/invite', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(invitePayload),
      muteHttpExceptions: true
    });
    
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200 || response.getResponseCode() === 201) {
      SN_log('sendSmsInvite', { success: true, documentId: documentId });
      return { success: true, inviteId: result.id || result.result, documentId: documentId };
    } else {
      SN_log('sendSmsInvite', { success: false, error: result });
      return { success: false, error: result.error || result.message || 'SMS invite failed' };
    }
  } catch (error) {
    SN_log('sendSmsInvite', { success: false, error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

/**
 * Create an embedded signing link for kiosk/in-person signing
 * @param {string} documentId - SignNow document ID
 * @param {string} signerEmail - Email for the signer (can be placeholder)
 * @param {string} signerRole - Role name
 * @param {number} linkExpiration - Link expiration in minutes (default 45)
 * @returns {Object} - { success: boolean, link?: string, inviteId?: string }
 */
function SN_createEmbeddedLink(documentId, signerEmail, signerRole, linkExpiration) {
  const config = SN_getConfig();
  linkExpiration = linkExpiration || 45;
  
  try {
    // Step 1: Create embedded invite
    const invitePayload = {
      invites: [{
        email: signerEmail,
        role: signerRole,
        order: 1,
        auth_method: 'none',
        force_new_signature: 1
      }]
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
      return { success: false, error: 'Failed to create embedded invite: ' + (inviteResult.error || inviteResult.message) };
    }
    
    const inviteId = inviteResult.data[0].id;
    
    // Step 2: Generate signing link
    const linkPayload = {
      auth_method: 'none',
      link_expiration: linkExpiration
    };
    
    const linkResponse = UrlFetchApp.fetch(
      config.API_BASE + '/v2/documents/' + documentId + '/embedded-invites/' + inviteId + '/link',
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
    
    if (linkResponse.getResponseCode() !== 200 && linkResponse.getResponseCode() !== 201) {
      return { success: false, error: 'Failed to generate signing link: ' + (linkResult.error || linkResult.message) };
    }
    
    SN_log('createEmbeddedLink', { success: true, documentId: documentId, inviteId: inviteId });
    return {
      success: true,
      link: linkResult.link,
      inviteId: inviteId,
      documentId: documentId,
      expiresIn: linkExpiration + ' minutes'
    };
    
  } catch (error) {
    SN_log('createEmbeddedLink', { success: false, error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

// ============================================================================
// COMPLETE WORKFLOW FUNCTIONS
// ============================================================================

/**
 * MAIN WORKFLOW: Upload pre-filled PDF, add fields, and send for signature
 * @param {Object} params - {
 *   pdfBase64: string,
 *   fileName: string,
 *   documentType: string (e.g., 'defendant-application'),
 *   deliveryMethod: 'email' | 'sms' | 'embedded',
 *   signers: Array of { email?, phone?, role, name, order },
 *   options: { subject?, message?, fromEmail?, includeCoIndemnitor? }
 * }
 * @returns {Object} - { success, documentId, inviteId?, link?, error? }
 */
function SN_sendForSignature(params) {
  const { pdfBase64, fileName, documentType, deliveryMethod, signers, options } = params;
  
  // Step 1: Upload the pre-filled PDF
  const uploadResult = SN_uploadDocument(pdfBase64, fileName);
  if (!uploadResult.success) {
    return { success: false, error: 'Upload failed: ' + uploadResult.error, step: 'upload' };
  }
  
  const documentId = uploadResult.documentId;
  
  // Step 2: Add signature fields for this document type
  if (documentType && SN_SIGNATURE_FIELDS[documentType]) {
    const fieldsResult = SN_addFieldsForDocType(documentId, documentType, options);
    if (!fieldsResult.success) {
      return { success: false, error: 'Add fields failed: ' + fieldsResult.error, step: 'addFields', documentId: documentId };
    }
  }
  
  // Step 3: Send invite based on delivery method
  let inviteResult;
  
  switch (deliveryMethod) {
    case 'sms':
      inviteResult = SN_sendSmsInvite(documentId, signers, options);
      break;
      
    case 'embedded':
      // For embedded, create link for first signer
      const firstSigner = signers[0];
      inviteResult = SN_createEmbeddedLink(
        documentId,
        firstSigner.email || 'signer@shamrockbailbonds.biz',
        firstSigner.role,
        45
      );
      break;
      
    case 'email':
    default:
      inviteResult = SN_sendEmailInvite(documentId, signers, options);
      break;
  }
  
  if (!inviteResult.success) {
    return {
      success: false,
      error: 'Invite failed: ' + inviteResult.error,
      step: 'invite',
      documentId: documentId
    };
  }
  
  return {
    success: true,
    documentId: documentId,
    inviteId: inviteResult.inviteId,
    link: inviteResult.link,
    deliveryMethod: deliveryMethod
  };
}

/**
 * Send a complete document packet (multiple documents) for signature
 * @param {Object} params - {
 *   documents: Array of { pdfBase64, fileName, documentType },
 *   deliveryMethod: 'email' | 'sms' | 'embedded',
 *   signers: Array of { email?, phone?, role, name },
 *   options: { subject?, message?, fromEmail?, includeCoIndemnitor? }
 * }
 * @returns {Object} - { success, documentIds: [], errors: [] }
 */
function SN_sendPacketForSignature(params) {
  const { documents, deliveryMethod, signers, options } = params;
  const results = {
    success: true,
    documentIds: [],
    inviteIds: [],
    links: [],
    errors: []
  };
  
  // Process each document
  for (let i = 0; i < documents.length; i++) {
    const doc = documents[i];
    const result = SN_sendForSignature({
      pdfBase64: doc.pdfBase64,
      fileName: doc.fileName,
      documentType: doc.documentType,
      deliveryMethod: deliveryMethod,
      signers: signers.map((s, idx) => ({ ...s, order: idx + 1 })),
      options: options
    });
    
    if (result.success) {
      results.documentIds.push(result.documentId);
      if (result.inviteId) results.inviteIds.push(result.inviteId);
      if (result.link) results.links.push(result.link);
    } else {
      results.errors.push({ document: doc.fileName, error: result.error });
      results.success = false;
    }
  }
  
  return results;
}

// ============================================================================
// DOCUMENT STATUS AND DOWNLOAD
// ============================================================================

/**
 * Get signing status for a document
 * @param {string} documentId - SignNow document ID
 * @returns {Object} - Document status with signing progress
 */
function SN_getDocumentStatus(documentId) {
  const doc = SN_getDocument(documentId);
  
  if (doc.error) {
    return { success: false, error: doc.error };
  }
  
  // Parse signing status
  const signatures = doc.signatures || [];
  const fields = doc.fields || [];
  const requiredSignatures = fields.filter(f => f.type === 'signature' && f.required).length;
  const completedSignatures = signatures.length;
  
  return {
    success: true,
    documentId: documentId,
    documentName: doc.document_name,
    status: completedSignatures >= requiredSignatures ? 'completed' : 'pending',
    requiredSignatures: requiredSignatures,
    completedSignatures: completedSignatures,
    created: doc.created,
    updated: doc.updated,
    signers: doc.field_invites || []
  };
}

/**
 * Download a completed document
 * @param {string} documentId - SignNow document ID
 * @param {string} type - 'collapsed' (flattened) or 'zip' (with history)
 * @returns {Blob} - PDF blob
 */
function SN_downloadDocument(documentId, type) {
  const config = SN_getConfig();
  type = type || 'collapsed';
  
  try {
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/document/' + documentId + '/download?type=' + type,
      {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + config.ACCESS_TOKEN },
        muteHttpExceptions: true
      }
    );
    
    if (response.getResponseCode() === 200) {
      return response.getBlob();
    } else {
      throw new Error('Download failed: ' + response.getContentText());
    }
  } catch (error) {
    SN_log('downloadDocument', { success: false, error: error.toString() });
    return null;
  }
}

/**
 * Download completed document and save to Google Drive
 * @param {string} documentId - SignNow document ID
 * @param {string} defendantName - For folder/file naming (LastName, FirstInitial)
 * @param {string} bondDate - Date of bond (MM-DD-YYYY)
 * @returns {Object} - { success, driveFileId, driveUrl }
 */
function SN_saveCompletedToDrive(documentId, defendantName, bondDate) {
  const COMPLETED_FOLDER_ID = '1WnjwtxoaoXVW8_B6s-0ftdCPf_5WfKgs'; // Completed Bonds folder
  
  try {
    // Download the document
    const pdfBlob = SN_downloadDocument(documentId, 'collapsed');
    
    if (!pdfBlob) {
      return { success: false, error: 'Failed to download document' };
    }
    
    // Create filename: LastName, FirstInitial - MM-DD-YYYY.pdf
    const fileName = defendantName + ' - ' + bondDate + '.pdf';
    pdfBlob.setName(fileName);
    
    // Get the Completed Bonds folder
    const folder = DriveApp.getFolderById(COMPLETED_FOLDER_ID);
    
    // Save the file
    const file = folder.createFile(pdfBlob);
    
    SN_log('saveCompletedToDrive', { success: true, fileName: fileName, fileId: file.getId() });
    
    return {
      success: true,
      driveFileId: file.getId(),
      driveUrl: file.getUrl(),
      fileName: fileName
    };
    
  } catch (error) {
    SN_log('saveCompletedToDrive', { success: false, error: error.toString() });
    return { success: false, error: error.toString() };
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format phone number to E.164 format for SMS
 * @param {string} phone - Phone number in any format
 * @returns {string} - Phone in +1XXXXXXXXXX format
 */
function SN_formatPhoneE164(phone) {
  if (!phone) return '';
  
  // Remove all non-digits
  const cleaned = String(phone).replace(/\D/g, '');
  
  // Add +1 if US number without country code
  if (cleaned.length === 10) {
    return '+1' + cleaned;
  } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return '+' + cleaned;
  }
  
  return '+' + cleaned;
}

/**
 * Format phone for display
 * @param {string} phone - Phone number
 * @returns {string} - Formatted as (XXX) XXX-XXXX
 */
function SN_formatPhoneDisplay(phone) {
  if (!phone) return '';
  const cleaned = String(phone).replace(/\D/g, '');
  if (cleaned.length === 10) {
    return '(' + cleaned.slice(0, 3) + ') ' + cleaned.slice(3, 6) + '-' + cleaned.slice(6);
  }
  return phone;
}

/**
 * Log SignNow operations
 * @param {string} action - Action name
 * @param {Object} data - Data to log
 */
function SN_log(action, data) {
  Logger.log('[SignNow:' + action + '] ' + JSON.stringify(data));
}

/**
 * Cancel a pending invite
 * @param {string} documentId - SignNow document ID
 * @returns {boolean} - Success status
 */
function SN_cancelInvite(documentId) {
  const config = SN_getConfig();
  
  try {
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/document/' + documentId + '/fieldinvitecancel',
      {
        method: 'PUT',
        headers: {
          'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
          'Content-Type': 'application/json'
        },
        muteHttpExceptions: true
      }
    );
    
    return response.getResponseCode() === 200;
  } catch (error) {
    SN_log('cancelInvite', { success: false, error: error.toString() });
    return false;
  }
}

/**
 * Delete a document from SignNow
 * @param {string} documentId - SignNow document ID
 * @returns {boolean} - Success status
 */
function SN_deleteDocument(documentId) {
  const config = SN_getConfig();
  
  try {
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/document/' + documentId,
      {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + config.ACCESS_TOKEN },
        muteHttpExceptions: true
      }
    );
    
    return response.getResponseCode() === 200;
  } catch (error) {
    SN_log('deleteDocument', { success: false, error: error.toString() });
    return false;
  }
}

/**
 * Send a reminder for pending signatures
 * @param {string} documentId - SignNow document ID
 * @returns {Object} - API response
 */
function SN_sendReminder(documentId) {
  const config = SN_getConfig();
  
  try {
    const response = UrlFetchApp.fetch(
      config.API_BASE + '/document/' + documentId + '/remind',
      {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + config.ACCESS_TOKEN,
          'Content-Type': 'application/json'
        },
        muteHttpExceptions: true
      }
    );
    
    return JSON.parse(response.getContentText());
  } catch (error) {
    return { error: error.toString() };
  }
}

// ============================================================================
// TEST FUNCTIONS
// ============================================================================

/**
 * Test SignNow connection and token validity
 */
function SN_testConnection() {
  const result = SN_validateToken();
  Logger.log('SignNow Connection Test: ' + JSON.stringify(result));
  return result;
}

/**
 * Test the complete workflow with a sample document
 */
function SN_testWorkflow() {
  // This would be called with actual PDF data from Form.html
  Logger.log('SignNow Workflow Test - Use Form.html to test with actual documents');
  return { message: 'Use Form.html to test the complete workflow' };
}

/**
 * List all document types and their field counts
 */
function SN_listDocumentTypes() {
  const types = [];
  for (const [key, config] of Object.entries(SN_SIGNATURE_FIELDS)) {
    types.push({
      documentType: key,
      driveId: config.driveId,
      pageCount: config.pageCount,
      signatureFields: config.fields.filter(f => f.type === 'signature').length,
      initialsFields: config.fields.filter(f => f.type === 'initials').length,
      totalFields: config.fields.length
    });
  }
  Logger.log('Document Types: ' + JSON.stringify(types, null, 2));
  return types;
}
