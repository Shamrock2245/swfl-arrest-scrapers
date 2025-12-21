/**
 * WebhookHandler.gs
 * 
 * Google Apps Script Web App for handling webhooks from SignNow and Wix
 */

/**
 * Handle GET requests (for testing/health check)
 * Renamed from doGet to avoid conflict with Code.gs
 */
function webhookHealthCheck(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: 'ok',
    message: 'Shamrock Bail Bonds Webhook Handler',
    timestamp: new Date().toISOString(),
    id: 'shamrock-sync-20251219'
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Handle POST requests (webhooks from SignNow and Wix)
 */
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const source = detectWebhookSource(payload, e);
    
    console.log(`Webhook received from ${source}:`, JSON.stringify(payload).substring(0, 500));
    
    let result;
    
    switch (source) {
      case 'signnow':
        result = handleSignNowWebhook(payload);
        break;
      case 'wix':
        result = handleWixWebhook(payload);
        break;
      default:
        result = { success: false, error: 'Unknown webhook source' };
    }
    
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    console.error('Webhook error:', error);
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.message
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Detect the source of the webhook
 */
function detectWebhookSource(payload, e) {
  if (payload.event || payload.meta?.event || payload.document_id) {
    return 'signnow';
  }
  if (payload.action || e.parameter?.source === 'wix') {
    return 'wix';
  }
  return 'unknown';
}

/**
 * Handle SignNow webhooks
 */
function handleSignNowWebhook(payload) {
  const event = payload.event || payload.meta?.event;
  const documentId = payload.document_id || payload.content?.document_id;
  
  console.log(`SignNow event: ${event}, Document: ${documentId}`);
  
  switch (event) {
    case 'document.complete':
    case 'document_complete':
      return handleDocumentComplete(documentId, payload);
      
    case 'document.update':
    case 'document_update':
      return handleDocumentUpdate(documentId, payload);
      
    case 'invite.sent':
    case 'invite_sent':
      return handleInviteSent(documentId, payload);
      
    default:
      console.log(`Unhandled SignNow event: ${event}`);
      return { success: true, message: `Event ${event} acknowledged` };
  }
}

/**
 * Handle document completion - download and save to Google Drive
 */
function handleDocumentComplete(documentId, payload) {
  try {
    console.log(`Document ${documentId} completed, downloading...`);
    
    // Get document info
    const docInfo = SN_getDocumentStatus(documentId);
    if (!docInfo.success) {
      throw new Error('Failed to get document info');
    }
    
    const defendantName = extractDefendantName(docInfo.documentName) || 'Unknown';
    const dateStr = new Date().toISOString().split('T')[0];
    const folderName = `${defendantName} - ${dateStr}`;
    
    const props = PropertiesService.getScriptProperties();
    const outputFolderId = props.getProperty('GOOGLE_DRIVE_OUTPUT_FOLDER_ID');
    let completedBondsFolder;
    if (outputFolderId) {
      completedBondsFolder = DriveApp.getFolderById(outputFolderId);
    } else {
      completedBondsFolder = getOrCreateFolder('Completed Bonds');
    }
    const defendantFolder = getOrCreateFolder(folderName, completedBondsFolder);
    
    const downloadResult = SN_downloadSignedDocument(documentId, defendantFolder.getId());
    
    if (!downloadResult.success) {
      throw new Error('Failed to download signed document');
    }
    
    // Update status in Wix (if integrated)
    try { updateWixDocumentStatus(documentId, 'signed'); } catch(e) {}
    
    logCompletion(documentId, defendantName, downloadResult.fileUrl);
    
    return {
      success: true,
      message: 'Document saved to Google Drive',
      fileUrl: downloadResult.fileUrl
    };
    
  } catch (error) {
    console.error('Error handling document completion:', error);
    return { success: false, error: error.message };
  }
}

// ... (remaining utility functions like getOrCreateFolder, getFileExtension, logCompletion) ...
// NOTE: These are already in your other script files, so you only need the functions above.