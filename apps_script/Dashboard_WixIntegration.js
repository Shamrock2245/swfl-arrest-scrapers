/**
 * Dashboard.html - Wix Portal Integration Module
 * 
 * This code should be added to Dashboard.html to enable:
 * 1. Saving signing links to Wix PendingDocuments collection
 * 2. Clients can view and sign from their Wix member portal
 * 3. Automatic status updates when documents are signed
 * 
 * Add this script block before the closing </body> tag in Dashboard.html
 */

// =========================================================
// WIX PORTAL INTEGRATION
// =========================================================

/**
 * Configuration for Wix Portal Integration
 */
const WIX_PORTAL_CONFIG = {
    // Your Wix site URL
    siteUrl: 'https://www.shamrockbailbonds.biz',
    
    // HTTP function endpoints (these are created by http-functions.js in Wix)
    endpoints: {
        addDocument: '/_functions/documentsAdd',
        batchAdd: '/_functions/documentsBatch',
        updateStatus: '/_functions/documentsStatus'
    },
    
    // Enable/disable portal integration
    enabled: true,
    
    // Redirect URL after signing
    redirectUrl: 'https://www.shamrockbailbonds.biz'
};

/**
 * Save a signing link to the Wix portal for a specific signer
 * 
 * @param {Object} params
 * @param {string} params.signerEmail - Email of the signer
 * @param {string} params.signerName - Name of the signer
 * @param {string} params.signerPhone - Phone of the signer
 * @param {string} params.signerRole - 'defendant', 'indemnitor', or 'agent'
 * @param {string} params.signingLink - The SignNow signing link
 * @param {string} params.documentId - The SignNow document ID
 * @param {string} params.defendantName - Full defendant name
 * @param {string} params.caseNumber - Case number
 * @param {string} params.documentName - Name of the document packet
 * @returns {Promise<Object>} Result of the save operation
 */
async function saveSigningLinkToWixPortal(params) {
    if (!WIX_PORTAL_CONFIG.enabled) {
        console.log('Wix Portal integration disabled');
        return { success: false, reason: 'disabled' };
    }
    
    try {
        const payload = {
            signerEmail: params.signerEmail,
            signerName: params.signerName,
            signerPhone: params.signerPhone,
            signerRole: params.signerRole,
            signingLink: params.signingLink,
            documentId: params.documentId,
            defendantName: params.defendantName,
            caseNumber: params.caseNumber || '',
            documentName: params.documentName || 'Bail Bond Packet',
            expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 7 days
        };
        
        const response = await fetch(WIX_PORTAL_CONFIG.siteUrl + WIX_PORTAL_CONFIG.endpoints.addDocument, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Signing link saved to Wix portal:', result.documentId);
        } else {
            console.error('Failed to save to Wix portal:', result.error);
        }
        
        return result;
        
    } catch (error) {
        console.error('Error saving to Wix portal:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Save multiple signing links to Wix portal at once
 * 
 * @param {Array<Object>} documents - Array of document objects (same structure as saveSigningLinkToWixPortal params)
 * @returns {Promise<Object>} Result with counts of successful/failed saves
 */
async function batchSaveToWixPortal(documents) {
    if (!WIX_PORTAL_CONFIG.enabled) {
        console.log('Wix Portal integration disabled');
        return { success: false, reason: 'disabled' };
    }
    
    try {
        const response = await fetch(WIX_PORTAL_CONFIG.siteUrl + WIX_PORTAL_CONFIG.endpoints.batchAdd, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ documents })
        });
        
        const result = await response.json();
        console.log('Batch save to Wix portal:', result);
        return result;
        
    } catch (error) {
        console.error('Error batch saving to Wix portal:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Enhanced generateAndSend function that also saves to Wix portal
 * This wraps the existing generateAndSend functionality
 */
async function generateAndSendWithWixPortal() {
    const formData = collectFormData();

    if (!formData['defendant-first-name'] || !formData['defendant-last-name']) {
        showToast('Please enter defendant name', 'error');
        return;
    }

    if (formData.charges.length === 0) {
        showToast('Please add at least one charge', 'error');
        return;
    }

    const signingMethod = document.getElementById('signing-method').value;

    // Validate signing method inputs
    if (signingMethod === 'email') {
        const defendantEmail = document.getElementById('signer-defendant-email').value;
        const indemnitorEmail = document.getElementById('signer-indemnitor-email').value;
        if (!defendantEmail && !indemnitorEmail) {
            showToast('Please enter at least one email address for signing', 'error');
            return;
        }
    } else if (signingMethod === 'sms') {
        const defendantPhone = document.getElementById('signer-defendant-phone').value;
        const indemnitorPhone = document.getElementById('signer-indemnitor-phone').value;
        if (!defendantPhone && !indemnitorPhone) {
            showToast('Please enter at least one phone number for SMS signing', 'error');
            return;
        }
    }

    // Add Wix portal step to progress
    showProgress('Generating Bail Packet', [
        'Collecting form data',
        'Fetching PDF templates',
        'Filling documents',
        'Merging packet',
        'Uploading to SignNow',
        'Adding signature fields',
        'Sending for signatures',
        'Saving to client portal'  // New step
    ]);

    try {
        updateProgress(1, 'Collecting form data...');
        await sleep(300);

        updateProgress(2, 'Fetching PDF templates from Google Drive...');
        const selectedDocs = getSelectedDocuments();
        if (selectedDocs.length === 0) throw new Error('No documents selected');

        const pdfBytes = await fetchPDFsFromDrive(selectedDocs);

        updateProgress(3, 'Filling documents with defendant data...');
        const filledPdfs = await fillPDFsWithData(pdfBytes, formData);

        updateProgress(4, 'Merging all documents into packet...');
        const mergedPdf = await mergePDFs(filledPdfs);

        updateProgress(5, 'Uploading to SignNow...');
        const documentId = await uploadToSignNow(mergedPdf, formData);

        if (!documentId) throw new Error('Failed to upload document to SignNow');

        // Add signature/initials fields to the uploaded document
        updateProgress(6, 'Adding signature fields...');
        await addSignatureFields(documentId, selectedDocs);

        updateProgress(7, 'Sending for signatures...');

        let result;
        let signingLinks = [];
        
        if (signingMethod === 'email' || signingMethod === 'sms') {
            result = await sendSignNowInvite(documentId, formData, signingMethod);
        } else if (signingMethod === 'kiosk' || signingMethod === 'embedded') {
            // For embedded/kiosk, create individual signing links for each signer
            signingLinks = await createMultiSignerLinks(documentId, formData);
            result = { success: true, mode: 'embedded', links: signingLinks };
        } else {
            result = { success: true, mode: 'download' };
            downloadFilledPdf(mergedPdf, formData);
        }

        // NEW: Save signing links to Wix portal
        updateProgress(8, 'Saving to client portal...');
        if (WIX_PORTAL_CONFIG.enabled && signingLinks.length > 0) {
            const defendantName = `${formData['defendant-first-name']} ${formData['defendant-last-name']}`;
            const caseNumber = formData.charges[0]?.['case-number'] || '';
            
            const portalDocuments = signingLinks.map(link => ({
                signerEmail: link.email,
                signerName: link.name,
                signerPhone: link.phone,
                signerRole: link.role,
                signingLink: link.url,
                documentId: documentId,
                defendantName: defendantName,
                caseNumber: caseNumber,
                documentName: 'Bail Bond Packet'
            }));
            
            await batchSaveToWixPortal(portalDocuments);
        }

        currentReceiptNumber++;
        updateReceiptDisplay();
        saveFormToLocalStorage();

        sentPackets.push({
            id: Date.now(),
            documentId: documentId,
            defendant: `${formData['defendant-first-name']} ${formData['defendant-last-name']}`,
            date: new Date().toISOString(),
            status: signingMethod === 'download' ? 'downloaded' : 'sent',
            receiptNumber: currentReceiptNumber - 1,
            signingMethod: signingMethod,
            portalEnabled: WIX_PORTAL_CONFIG.enabled
        });
        localStorage.setItem(LS_KEY_PACKETS, JSON.stringify(sentPackets));

        hideProgress();
        showSuccessResult(result, formData, signingMethod);

    } catch (err) {
        hideProgress();
        showToast('Error generating packet: ' + err.message, 'error');
        console.error('Generation error:', err);
    }
}

/**
 * Create embedded signing links for multiple signers
 * 
 * @param {string} documentId - SignNow document ID
 * @param {Object} formData - Form data with signer information
 * @returns {Promise<Array>} Array of signing link objects
 */
async function createMultiSignerLinks(documentId, formData) {
    const signers = [];
    
    // Add defendant
    const defendantEmail = document.getElementById('signer-defendant-email')?.value || '';
    const defendantPhone = document.getElementById('signer-defendant-phone')?.value || '';
    if (defendantEmail || defendantPhone) {
        signers.push({
            name: `${formData['defendant-first-name']} ${formData['defendant-last-name']}`,
            email: defendantEmail,
            phone: defendantPhone,
            role: 'defendant',
            order: 1
        });
    }
    
    // Add indemnitors from the dynamic indemnitor list
    const indemnitorContainers = document.querySelectorAll('.indemnitor-entry, [data-indemnitor-index]');
    indemnitorContainers.forEach((container, index) => {
        const firstName = container.querySelector('[name*="first-name"], [id*="first-name"]')?.value || '';
        const lastName = container.querySelector('[name*="last-name"], [id*="last-name"]')?.value || '';
        const email = container.querySelector('[name*="email"], [id*="email"]')?.value || '';
        const phone = container.querySelector('[name*="phone"], [id*="phone"]')?.value || '';
        
        if ((firstName || lastName) && (email || phone)) {
            signers.push({
                name: `${firstName} ${lastName}`.trim(),
                email: email,
                phone: phone,
                role: 'indemnitor',
                order: index + 2
            });
        }
    });
    
    // Also check for primary indemnitor fields
    const primaryIndemnitorEmail = document.getElementById('signer-indemnitor-email')?.value || '';
    const primaryIndemnitorPhone = document.getElementById('signer-indemnitor-phone')?.value || '';
    const primaryIndemnitorName = formData['indemnitor-first-name'] 
        ? `${formData['indemnitor-first-name']} ${formData['indemnitor-last-name'] || ''}`.trim()
        : '';
    
    if (primaryIndemnitorName && (primaryIndemnitorEmail || primaryIndemnitorPhone)) {
        // Check if not already added
        const alreadyAdded = signers.some(s => s.email === primaryIndemnitorEmail && s.role === 'indemnitor');
        if (!alreadyAdded) {
            signers.push({
                name: primaryIndemnitorName,
                email: primaryIndemnitorEmail,
                phone: primaryIndemnitorPhone,
                role: 'indemnitor',
                order: 2
            });
        }
    }
    
    // Create embedded signing links for each signer via GAS
    const links = [];
    for (const signer of signers) {
        try {
            const linkResult = await new Promise((resolve, reject) => {
                google.script.run
                    .withSuccessHandler(resolve)
                    .withFailureHandler(reject)
                    .SN_createEmbeddedSigningLink(documentId, signer.email, signer.name, signer.role, WIX_PORTAL_CONFIG.redirectUrl);
            });
            
            if (linkResult && linkResult.link) {
                links.push({
                    ...signer,
                    url: linkResult.link,
                    wixUrl: `${WIX_PORTAL_CONFIG.siteUrl}/sign?link=${encodeURIComponent(linkResult.link)}`
                });
            }
        } catch (error) {
            console.error(`Error creating signing link for ${signer.name}:`, error);
        }
    }
    
    return links;
}

/**
 * Show enhanced success result with Wix portal links
 */
function showSuccessResultWithPortal(result, formData, signingMethod) {
    // Call original success handler
    showSuccessResult(result, formData, signingMethod);
    
    // If we have portal links, add them to the success modal
    if (result.links && result.links.length > 0) {
        const linksHtml = result.links.map(link => `
            <div style="margin: 10px 0; padding: 10px; background: var(--surface-2); border-radius: 8px;">
                <strong>${link.name}</strong> (${link.role})<br>
                <a href="${link.wixUrl}" target="_blank" style="color: var(--accent); word-break: break-all;">
                    ${link.wixUrl}
                </a>
                <button onclick="navigator.clipboard.writeText('${link.wixUrl}'); showToast('Link copied!', 'success');" 
                        style="margin-left: 10px; padding: 4px 8px; cursor: pointer;">
                    Copy
                </button>
            </div>
        `).join('');
        
        // Append to success modal if it exists
        const successContent = document.querySelector('.success-modal-content, .modal-content');
        if (successContent) {
            const portalSection = document.createElement('div');
            portalSection.innerHTML = `
                <h4 style="margin-top: 20px;">Client Portal Signing Links</h4>
                <p style="font-size: 14px; color: var(--muted);">
                    These links are also saved to each client's portal account.
                </p>
                ${linksHtml}
            `;
            successContent.appendChild(portalSection);
        }
    }
}

// =========================================================
// OPTIONAL: Replace the default generateAndSend with portal version
// =========================================================

// Uncomment the line below to automatically use the Wix portal version
// window.generateAndSend = generateAndSendWithWixPortal;

console.log('Wix Portal Integration module loaded');
