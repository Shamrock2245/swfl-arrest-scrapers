/**
 * ============================================================================
 * Code.gs - ADDITIONAL doPost HANDLERS for SignNow Integration
 * ============================================================================
 * ADD THESE CASES to the existing doPost switch statement in Code.gs
 * These enable the new SignNow workflow from Form.html
 * ============================================================================
 */

// ============================================================================
// ADD THESE CASES TO doPost() switch statement
// ============================================================================

/*
Add these cases to the existing doPost() function in Code.gs:

      // === NEW SIGNNOW WORKFLOW CASES ===
      
      // Validate SignNow token
      case 'validateSignNowToken':
        result = SN_validateToken();
        break;
      
      // Upload pre-filled PDF to SignNow
      case 'uploadToSignNow':
        result = SN_uploadDocument(data.pdfBase64, data.fileName);
        break;
      
      // Add signature fields to uploaded document
      case 'addSignatureFields':
        result = SN_addFields(data.documentId, data.fields);
        break;
      
      // Add predefined fields for document type
      case 'addFieldsForDocType':
        result = SN_addFieldsForDocType(data.documentId, data.documentType);
        break;
      
      // Send email invite
      case 'sendEmailInvite':
        result = SN_sendEmailInvite(data.documentId, data.signers, data.options);
        break;
      
      // Send SMS invite
      case 'sendSmsInvite':
        result = SN_sendSmsInvite(data.documentId, data.signers, data.options);
        break;
      
      // Create embedded signing link (kiosk mode)
      case 'createEmbeddedLink':
        result = SN_createEmbeddedLink(data.documentId, data.signerEmail, data.signerRole, data.linkExpiration);
        break;
      
      // Complete workflow: upload + fields + invite
      case 'sendForSignature':
        result = SN_sendForSignature(data);
        break;
      
      // Send packet (multiple documents)
      case 'sendPacketForSignature':
        result = SN_sendPacketForSignature(data);
        break;
      
      // Get document status
      case 'getDocumentStatus':
        result = SN_getDocumentStatus(data.documentId);
        break;
      
      // Download completed document
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
      
      // Save completed document to Google Drive
      case 'saveCompletedToDrive':
        result = SN_saveCompletedToDrive(data.documentId, data.defendantName, data.bondDate);
        break;
      
      // Cancel pending invite
      case 'cancelInvite':
        result = { success: SN_cancelInvite(data.documentId) };
        break;
      
      // Send reminder
      case 'sendReminder':
        result = SN_sendReminder(data.documentId);
        break;

*/

// ============================================================================
// FORM.HTML INTEGRATION - JavaScript Functions
// ============================================================================

/**
 * These functions should be added to Form.html to call the new SignNow API
 * 
 * Example usage in Form.html:
 */

const FORM_HTML_SIGNNOW_FUNCTIONS = `
// ============================================================================
// SignNow Integration Functions for Form.html
// ============================================================================

/**
 * Send documents for signature via the selected delivery method
 * @param {string} deliveryMethod - 'email', 'sms', or 'embedded'
 */
async function sendToSignNow(deliveryMethod) {
  const formData = collectFormData();
  
  // Validate required fields
  if (!formData.defendantName || !formData.bookingNumber) {
    showError('Please fill in Defendant Name and Booking Number');
    return;
  }
  
  // Get selected documents
  const selectedDocs = getSelectedDocuments();
  if (selectedDocs.length === 0) {
    showError('Please select at least one document');
    return;
  }
  
  // Build signers array based on delivery method
  let signers = [];
  
  if (deliveryMethod === 'sms') {
    // Validate phone numbers
    if (!formData.defendantPhone) {
      showError('Defendant phone number is required for SMS delivery');
      return;
    }
    
    signers.push({
      phone: formData.defendantPhone,
      role: 'Defendant',
      name: formData.defendantName
    });
    
    if (formData.indemnitorPhone) {
      signers.push({
        phone: formData.indemnitorPhone,
        role: 'Indemnitor',
        name: formData.indemnitorName
      });
    }
  } else if (deliveryMethod === 'email') {
    // Validate emails
    if (!formData.defendantEmail) {
      showError('Defendant email is required for email delivery');
      return;
    }
    
    signers.push({
      email: formData.defendantEmail,
      role: 'Defendant',
      name: formData.defendantName
    });
    
    if (formData.indemnitorEmail) {
      signers.push({
        email: formData.indemnitorEmail,
        role: 'Indemnitor',
        name: formData.indemnitorName
      });
    }
  } else {
    // Embedded/Kiosk mode - use placeholder
    signers.push({
      email: 'signer@shamrockbailbonds.biz',
      role: 'Defendant',
      name: formData.defendantName
    });
  }
  
  showLoading('Preparing documents...');
  
  try {
    // Step 1: Pre-fill each selected document
    const filledDocuments = [];
    
    for (const docType of selectedDocs) {
      showLoading('Filling ' + docType + '...');
      
      // Get template
      const templateResult = await callGAS('getTemplate', { templateId: docType });
      if (!templateResult.success) {
        throw new Error('Failed to get template: ' + docType);
      }
      
      // Fill the PDF with form data (using pdf-lib)
      const filledPdf = await fillPdfWithData(templateResult.pdfBase64, formData, docType);
      
      filledDocuments.push({
        pdfBase64: filledPdf,
        fileName: docType + '-' + formData.bookingNumber + '.pdf',
        documentType: docType
      });
    }
    
    showLoading('Sending to SignNow...');
    
    // Step 2: Send to SignNow
    const result = await callGAS('sendPacketForSignature', {
      documents: filledDocuments,
      deliveryMethod: deliveryMethod,
      signers: signers,
      options: {
        subject: 'Bail Bond Documents - ' + formData.defendantName,
        message: 'Please review and sign the attached bail bond documents for ' + formData.defendantName + '.',
        fromEmail: formData.agentEmail || 'admin@shamrockbailbonds.biz'
      }
    });
    
    hideLoading();
    
    if (result.success) {
      if (deliveryMethod === 'embedded' && result.links && result.links.length > 0) {
        // Show signing link for kiosk mode
        showSigningLink(result.links[0]);
      } else {
        showSuccess('Documents sent successfully! ' + 
          (deliveryMethod === 'sms' ? 'SMS sent to signers.' : 'Email sent to signers.'));
      }
      
      // Store document IDs for status tracking
      storeDocumentIds(result.documentIds);
    } else {
      showError('Failed to send documents: ' + result.error);
    }
    
  } catch (error) {
    hideLoading();
    showError('Error: ' + error.message);
  }
}

/**
 * Preview filled documents before sending
 */
async function previewDocuments() {
  const formData = collectFormData();
  const selectedDocs = getSelectedDocuments();
  
  if (selectedDocs.length === 0) {
    showError('Please select at least one document');
    return;
  }
  
  showLoading('Generating preview...');
  
  try {
    const previewPdfs = [];
    
    for (const docType of selectedDocs) {
      // Get template
      const templateResult = await callGAS('getTemplate', { templateId: docType });
      if (!templateResult.success) {
        throw new Error('Failed to get template: ' + docType);
      }
      
      // Fill the PDF
      const filledPdf = await fillPdfWithData(templateResult.pdfBase64, formData, docType);
      
      previewPdfs.push({
        docType: docType,
        pdfBase64: filledPdf,
        fileName: templateResult.fileName
      });
    }
    
    hideLoading();
    
    // Show preview modal with all filled PDFs
    showPreviewModal(previewPdfs);
    
  } catch (error) {
    hideLoading();
    showError('Preview error: ' + error.message);
  }
}

/**
 * Show preview modal with PDF viewer
 */
function showPreviewModal(previewPdfs) {
  const modal = document.getElementById('previewModal');
  const container = document.getElementById('previewContainer');
  
  container.innerHTML = '';
  
  previewPdfs.forEach((pdf, index) => {
    const section = document.createElement('div');
    section.className = 'preview-section';
    section.innerHTML = \`
      <h4>\${pdf.docType.replace(/-/g, ' ').toUpperCase()}</h4>
      <iframe 
        src="data:application/pdf;base64,\${pdf.pdfBase64}" 
        style="width: 100%; height: 500px; border: 1px solid #ccc;">
      </iframe>
    \`;
    container.appendChild(section);
  });
  
  modal.style.display = 'block';
}

/**
 * Show embedded signing link for kiosk mode
 */
function showSigningLink(link) {
  const modal = document.getElementById('signingLinkModal');
  const linkContainer = document.getElementById('signingLinkContainer');
  
  linkContainer.innerHTML = \`
    <div class="signing-link-box">
      <h3>Ready for Signing</h3>
      <p>Open this link on the signing device (iPad/tablet):</p>
      <a href="\${link}" target="_blank" class="signing-link">\${link}</a>
      <button onclick="copyToClipboard('\${link}')" class="btn btn-secondary">Copy Link</button>
      <button onclick="openInNewTab('\${link}')" class="btn btn-primary">Open Signing Page</button>
      <p class="expiry-note">This link expires in 45 minutes.</p>
    </div>
  \`;
  
  modal.style.display = 'block';
}

/**
 * Helper to call GAS functions
 */
function callGAS(action, data) {
  return new Promise((resolve, reject) => {
    google.script.run
      .withSuccessHandler(resolve)
      .withFailureHandler(reject)
      .doPostFromClient({ action: action, ...data });
  });
}

/**
 * Collect all form data into a single object
 */
function collectFormData() {
  return {
    // Defendant Info
    defendantName: document.getElementById('defendantFullName')?.value || '',
    defendantFirstName: document.getElementById('defendantFirstName')?.value || '',
    defendantLastName: document.getElementById('defendantLastName')?.value || '',
    defendantDOB: document.getElementById('defendantDOB')?.value || '',
    defendantSSN: document.getElementById('defendantSSN')?.value || '',
    defendantAddress: document.getElementById('defendantAddress')?.value || '',
    defendantCity: document.getElementById('defendantCity')?.value || '',
    defendantState: document.getElementById('defendantState')?.value || '',
    defendantZip: document.getElementById('defendantZip')?.value || '',
    defendantPhone: document.getElementById('defendantPhone')?.value || '',
    defendantEmail: document.getElementById('defendantEmail')?.value || '',
    
    // Booking Info
    bookingNumber: document.getElementById('bookingNumber')?.value || '',
    bondAmount: document.getElementById('bondAmount')?.value || '',
    premiumAmount: document.getElementById('premiumAmount')?.value || '',
    charges: document.getElementById('charges')?.value || '',
    caseNumber: document.getElementById('caseNumber')?.value || '',
    courtDate: document.getElementById('courtDate')?.value || '',
    courtType: document.getElementById('courtType')?.value || '',
    county: document.getElementById('county')?.value || '',
    powerNumber: document.getElementById('powerNumber')?.value || '',
    
    // Indemnitor Info
    indemnitorName: document.getElementById('indemnitorFullName')?.value || '',
    indemnitorPhone: document.getElementById('indemnitorPhone')?.value || '',
    indemnitorEmail: document.getElementById('indemnitorEmail')?.value || '',
    indemnitorAddress: document.getElementById('indemnitorAddress')?.value || '',
    indemnitorRelationship: document.getElementById('indemnitorRelationship')?.value || '',
    
    // Agent Info
    agentName: document.getElementById('agentName')?.value || 'Shamrock Bail Bonds',
    agentEmail: document.getElementById('agentEmail')?.value || 'admin@shamrockbailbonds.biz',
    
    // Receipt Numbers
    receiptNumber: document.getElementById('receiptNumber')?.value || '',
    collateralReceiptNumber: document.getElementById('collateralReceiptNumber')?.value || '',
    
    // Execution Date
    executionDate: new Date().toLocaleDateString('en-US')
  };
}

/**
 * Get list of selected document checkboxes
 */
function getSelectedDocuments() {
  const checkboxes = document.querySelectorAll('.doc-checkbox:checked');
  return Array.from(checkboxes).map(cb => cb.value);
}
`;

// ============================================================================
// HELPER FUNCTION for Form.html to call doPost
// ============================================================================

/**
 * This function should be added to Code.gs to allow Form.html to call doPost actions
 * Add this near the doPost function
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
