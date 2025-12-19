/**
 * EmbeddedSigningLinks.gs
 * 
 * Functions for creating embedded signing links with redirect support
 * These are called from Dashboard.html to generate signing links for the Wix portal
 * 
 * USES EXISTING PROPERTY NAMES:
 * - SIGNNOW_ACCESS_TOKEN
 * - SIGNNOW_API_BASE_URL
 * - SIGNNOW_SENDER_EMAIL
 * - REDIRECT_URL
 * - GOOGLE_DRIVE_OUTPUT_FOLDER_ID
 */

/**
 * Get SignNow configuration from Script Properties
 * Uses the existing property names from your GAS project
 */
function getSignNowConfig_() {
  const props = PropertiesService.getScriptProperties();
  return {
    accessToken: props.getProperty('SIGNNOW_ACCESS_TOKEN'),
    baseUrl: props.getProperty('SIGNNOW_API_BASE_URL') || 'https://api.signnow.com',
    senderEmail: props.getProperty('SIGNNOW_SENDER_EMAIL') || 'admin@shamrockbailbonds.biz',
    redirectUrl: props.getProperty('REDIRECT_URL') || 'https://www.shamrockbailbonds.biz',
    outputFolderId: props.getProperty('GOOGLE_DRIVE_OUTPUT_FOLDER_ID')
  };
}

/**
 * Create an embedded signing link for a specific signer
 * 
 * @param {string} documentId - The SignNow document ID
 * @param {string} signerEmail - Email of the signer
 * @param {string} signerName - Name of the signer
 * @param {string} signerRole - Role: 'defendant', 'indemnitor', or 'agent'
 * @param {string} redirectUrl - URL to redirect to after signing (optional, uses REDIRECT_URL property if not provided)
 * @returns {Object} Result with signing link or error
 */
function SN_createEmbeddedSigningLink(documentId, signerEmail, signerName, signerRole, redirectUrl) {
  try {
    const config = getSignNowConfig_();
    const accessToken = config.accessToken;
    const redirectUri = redirectUrl || config.redirectUrl;
    const baseUrl = config.baseUrl;
    
    if (!accessToken) {
      throw new Error('SIGNNOW_ACCESS_TOKEN not configured in Script Properties');
    }
    
    // First, create an invite for this signer
    const invitePayload = {
      to: [{
        email: signerEmail,
        role: signerRole,
        role_id: '',
        order: 1,
        reassign: '0',
        decline_by_signature: '0',
        reminder: 0,
        expiration_days: 7,
        subject: 'Shamrock Bail Bonds - Documents Ready for Signature',
        message: `Hello ${signerName},\n\nYour bail bond documents are ready for signature. Please click the link to review and sign.\n\nThank you,\nShamrock Bail Bonds`
      }],
      from: config.senderEmail,
      cc: [],
      subject: 'Shamrock Bail Bonds - Signature Required',
      message: 'Please sign the attached documents.',
      redirect_uri: redirectUri
    };
    
    // Create the field invite
    const inviteResponse = UrlFetchApp.fetch(
      `${baseUrl}/document/${documentId}/invite`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        payload: JSON.stringify(invitePayload),
        muteHttpExceptions: true
      }
    );
    
    const inviteResult = JSON.parse(inviteResponse.getContentText());
    
    if (inviteResponse.getResponseCode() !== 200 && inviteResponse.getResponseCode() !== 201) {
      console.error('Invite creation failed:', inviteResult);
      return { success: false, error: inviteResult.error || 'Failed to create invite' };
    }
    
    // Now create an embedded signing link
    const linkPayload = {
      document_id: documentId,
      email: signerEmail,
      auth_method: 'none',
      link_expiration: 45, // 45 minutes
      redirect_uri: redirectUri
    };
    
    const linkResponse = UrlFetchApp.fetch(
      `${baseUrl}/v2/documents/${documentId}/embedded-invites/${inviteResult.id}/link`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        payload: JSON.stringify(linkPayload),
        muteHttpExceptions: true
      }
    );
    
    // If the v2 endpoint doesn't work, try the legacy approach
    if (linkResponse.getResponseCode() !== 200 && linkResponse.getResponseCode() !== 201) {
      // Fallback: Create a simple signing link
      const simpleLinkResponse = UrlFetchApp.fetch(
        `${baseUrl}/link`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          payload: JSON.stringify({
            document_id: documentId
          }),
          muteHttpExceptions: true
        }
      );
      
      if (simpleLinkResponse.getResponseCode() === 200 || simpleLinkResponse.getResponseCode() === 201) {
        const simpleLinkResult = JSON.parse(simpleLinkResponse.getContentText());
        return {
          success: true,
          link: simpleLinkResult.url || simpleLinkResult.link,
          inviteId: inviteResult.id,
          signerEmail: signerEmail,
          signerName: signerName,
          signerRole: signerRole
        };
      }
    }
    
    const linkResult = JSON.parse(linkResponse.getContentText());
    
    return {
      success: true,
      link: linkResult.link || linkResult.url,
      inviteId: inviteResult.id,
      signerEmail: signerEmail,
      signerName: signerName,
      signerRole: signerRole
    };
    
  } catch (error) {
    console.error('Error creating embedded signing link:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Create embedded signing links for all signers in a document
 * 
 * @param {string} documentId - The SignNow document ID
 * @param {Array} signers - Array of signer objects with email, name, role
 * @param {string} redirectUrl - URL to redirect to after signing (optional)
 * @returns {Object} Result with array of signing links
 */
function SN_createMultipleEmbeddedLinks(documentId, signers, redirectUrl) {
  const results = [];
  
  for (const signer of signers) {
    const result = SN_createEmbeddedSigningLink(
      documentId,
      signer.email,
      signer.name,
      signer.role,
      redirectUrl
    );
    
    results.push({
      ...signer,
      ...result
    });
  }
  
  return {
    success: results.every(r => r.success),
    links: results,
    successCount: results.filter(r => r.success).length,
    failCount: results.filter(r => !r.success).length
  };
}

/**
 * Get the signing status of a document
 * 
 * @param {string} documentId - The SignNow document ID
 * @returns {Object} Document status information
 */
function SN_getDocumentStatus(documentId) {
  try {
    const config = getSignNowConfig_();
    const accessToken = config.accessToken;
    const baseUrl = config.baseUrl;
    
    const response = UrlFetchApp.fetch(
      `${baseUrl}/document/${documentId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        },
        muteHttpExceptions: true
      }
    );
    
    if (response.getResponseCode() !== 200) {
      return { success: false, error: 'Failed to get document status' };
    }
    
    const doc = JSON.parse(response.getContentText());
    
    // Check signature status
    const signatures = doc.signatures || [];
    const totalSigners = doc.field_invites?.length || 1;
    const signedCount = signatures.length;
    
    return {
      success: true,
      documentId: documentId,
      documentName: doc.document_name,
      status: signedCount >= totalSigners ? 'completed' : 'pending',
      totalSigners: totalSigners,
      signedCount: signedCount,
      signatures: signatures.map(sig => ({
        email: sig.email,
        signedAt: sig.created,
        ipAddress: sig.ip_address
      })),
      createdAt: doc.created,
      updatedAt: doc.updated
    };
    
  } catch (error) {
    console.error('Error getting document status:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Download a completed signed document
 * 
 * @param {string} documentId - The SignNow document ID
 * @param {string} folderId - Google Drive folder ID to save to (optional, uses GOOGLE_DRIVE_OUTPUT_FOLDER_ID if not provided)
 * @returns {Object} Result with file ID or error
 */
function SN_downloadSignedDocument(documentId, folderId) {
  try {
    const config = getSignNowConfig_();
    const accessToken = config.accessToken;
    const baseUrl = config.baseUrl;
    const outputFolderId = folderId || config.outputFolderId;
    
    // Download the document
    const response = UrlFetchApp.fetch(
      `${baseUrl}/document/${documentId}/download?type=collapsed`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        },
        muteHttpExceptions: true
      }
    );
    
    if (response.getResponseCode() !== 200) {
      return { success: false, error: 'Failed to download document' };
    }
    
    const pdfBlob = response.getBlob();
    
    // Get document info for naming
    const docInfo = SN_getDocumentStatus(documentId);
    const fileName = docInfo.documentName || `SignedDocument_${documentId}`;
    
    // Save to Google Drive
    let folder;
    if (outputFolderId) {
      folder = DriveApp.getFolderById(outputFolderId);
    } else {
      // Create or get the "Completed Bonds" folder
      const folders = DriveApp.getFoldersByName('Completed Bonds');
      folder = folders.hasNext() ? folders.next() : DriveApp.createFolder('Completed Bonds');
    }
    
    const file = folder.createFile(pdfBlob.setName(fileName + '.pdf'));
    
    return {
      success: true,
      fileId: file.getId(),
      fileUrl: file.getUrl(),
      fileName: file.getName()
    };
    
  } catch (error) {
    console.error('Error downloading signed document:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Update document status in Wix PendingDocuments collection
 * 
 * @param {string} documentId - The SignNow document ID
 * @param {string} status - New status ('signed', 'expired', 'cancelled')
 */
function updateWixDocumentStatus(documentId, status) {
  try {
    const props = PropertiesService.getScriptProperties();
    const wixApiKey = props.getProperty('WIX_API_KEY');
    const redirectUrl = props.getProperty('REDIRECT_URL') || 'https://www.shamrockbailbonds.biz';
    
    if (!wixApiKey) {
      console.log('WIX_API_KEY not configured, skipping Wix update');
      return;
    }
    
    const response = UrlFetchApp.fetch(
      redirectUrl + '/_functions/documentsStatus',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': wixApiKey
        },
        payload: JSON.stringify({
          documentId: documentId,
          status: status,
          signedAt: new Date().toISOString()
        }),
        muteHttpExceptions: true
      }
    );
    
    console.log('Wix status update response:', response.getContentText());
    
  } catch (error) {
    console.error('Error updating Wix status:', error);
  }
}
