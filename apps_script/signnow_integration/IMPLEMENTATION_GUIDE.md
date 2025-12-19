# SignNow + Wix Integration Implementation Guide

**Shamrock Bail Bonds - admin@shamrockbailbonds.biz**

This guide explains how to integrate SignNow embedded signing with your existing Dashboard.html workflow, with automatic saving to Google Drive and redirect to your Wix site.

---

## Overview

The integration provides:

1. **Multi-signer embedded signing** - Defendant + all indemnitors you add in Dashboard.html
2. **Redirect to shamrockbailbonds.biz** - After signing, users are redirected to your homepage
3. **Automatic Google Drive saving** - Completed signed documents are automatically saved
4. **Wix signing page** - Optional embedded signing experience on your website

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │ Dashboard.html│────▶│ Google Apps  │────▶│   SignNow    │        │
│  │ (Control     │     │ Script       │     │   API        │        │
│  │  Center)     │     │              │     │              │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│         │                    │                    │                 │
│         │                    │                    │                 │
│         ▼                    ▼                    ▼                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │ Add Defendant│     │ Fill PDFs    │     │ Upload &     │        │
│  │ + Indemnitors│     │ Merge Docs   │     │ Add Fields   │        │
│  │ (+ button)   │     │              │     │              │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                   │                 │
│                                                   ▼                 │
│                              ┌─────────────────────────────────┐   │
│                              │  Generate Signing Links         │   │
│                              │  (One per signer)               │   │
│                              └─────────────────────────────────┘   │
│                                          │                         │
│                    ┌─────────────────────┼─────────────────────┐   │
│                    ▼                     ▼                     ▼   │
│             ┌───────────┐         ┌───────────┐         ┌─────────┐│
│             │ Direct    │         │ Wix Page  │         │ SMS/    ││
│             │ Link      │         │ Embed     │         │ Email   ││
│             └───────────┘         └───────────┘         └─────────┘│
│                    │                     │                     │   │
│                    └─────────────────────┼─────────────────────┘   │
│                                          ▼                         │
│                              ┌─────────────────────────────────┐   │
│                              │  Signer Signs Document          │   │
│                              │  (Redirects to shamrockbailbonds│   │
│                              │   .biz after completion)        │   │
│                              └─────────────────────────────────┘   │
│                                          │                         │
│                                          ▼                         │
│                              ┌─────────────────────────────────┐   │
│                              │  Webhook Triggered              │   │
│                              │  (document.complete)            │   │
│                              └─────────────────────────────────┘   │
│                                          │                         │
│                                          ▼                         │
│                              ┌─────────────────────────────────┐   │
│                              │  Auto-Save to Google Drive      │   │
│                              │  Completed Bonds folder         │   │
│                              └─────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Files Included

| File | Purpose |
|------|---------|
| `SignNow_Integration_Complete.gs` | Main GAS file with all SignNow integration functions |
| `wix-signing-page.js` | Velo code for Wix signing page |
| `wix-signing-page.html` | HTML structure reference for Wix page |
| `signnow-integration-notes.md` | API documentation notes |

---

## Step-by-Step Setup

### Step 1: Add the GAS Integration File

1. Open your Google Apps Script project
2. Create a new file: `SignNow_Integration_Complete.gs`
3. Copy the contents from the provided file
4. Save the project

### Step 2: Configure Script Properties

In your GAS project, go to **Project Settings > Script Properties** and ensure these are set:

| Property | Value |
|----------|-------|
| `SIGNNOW_API_BASE_URL` | `https://api.signnow.com` |
| `SIGNNOW_API_TOKEN` | Your SignNow access token |
| `SIGNNOW_FOLDER_ID` | Your SignNow folder ID (optional) |

### Step 3: Deploy as Web App (for Webhooks)

1. In GAS, click **Deploy > New deployment**
2. Select type: **Web app**
3. Settings:
   - Execute as: **Me**
   - Who has access: **Anyone**
4. Click **Deploy**
5. Copy the Web app URL

### Step 4: Register Webhook with SignNow

Run this function once in GAS to register the webhook:

```javascript
function setupWebhook() {
  const webAppUrl = 'YOUR_DEPLOYED_WEB_APP_URL';
  const result = SN_registerCompletionWebhook(webAppUrl);
  Logger.log(result);
}
```

### Step 5: Update Dashboard.html Generate Function

In your `Dashboard.html`, update the generate function to use the new workflow:

```javascript
async function generateAndSend() {
  // ... existing validation code ...
  
  const formData = collectFormData();
  const selectedDocs = getSelectedDocuments();
  const deliveryMethod = document.querySelector('input[name="delivery-method"]:checked')?.value || 'embedded';
  
  showProgress('Generating documents...');
  
  try {
    // Step 1: Generate and merge PDFs (existing code)
    updateProgress(30, 'Filling PDF forms...');
    const pdfResult = await callGAS('generateAndMergePdfs', {
      formData: formData,
      selectedDocs: selectedDocs
    });
    
    if (!pdfResult.success) throw new Error(pdfResult.error);
    
    // Step 2: Process complete workflow with SignNow
    updateProgress(60, 'Processing with SignNow...');
    const result = await callGAS('SN_processCompleteWorkflow', {
      formData: formData,
      selectedDocs: selectedDocs,
      deliveryMethod: deliveryMethod,
      pdfBase64: pdfResult.pdfBase64,
      fileName: pdfResult.fileName
    });
    
    if (!result.success) throw new Error(result.error);
    
    // Step 3: Display signing links (for embedded method)
    if (deliveryMethod === 'embedded' && result.signingLinks) {
      displaySigningLinks(result.signingLinks);
    }
    
    updateProgress(100, 'Complete!');
    hideProgress();
    showToast('Documents ready!', 'success');
    
  } catch (error) {
    hideProgress();
    showToast('Error: ' + error.message, 'error');
  }
}

function displaySigningLinks(links) {
  // Create a modal or section to display the links
  let html = '<div class="signing-links-modal">';
  html += '<h3>Signing Links Generated</h3>';
  html += '<p>Share these links with each signer:</p>';
  
  links.forEach(link => {
    if (link.error) {
      html += `<div class="link-item error">
        <strong>${link.role}</strong>: Error - ${link.error}
      </div>`;
    } else {
      html += `<div class="link-item">
        <strong>${link.role}</strong>: ${link.fullName}<br>
        <small>Expires in ${link.expiresIn}</small><br>
        <button onclick="copyToClipboard('${link.link}')">Copy Link</button>
        <button onclick="window.open('${link.link}', '_blank')">Open</button>
        ${link.phone ? `<button onclick="sendSms('${link.phone}', '${link.link}')">Send SMS</button>` : ''}
      </div>`;
    }
  });
  
  html += '</div>';
  
  // Display in your preferred way (modal, section, etc.)
  document.getElementById('signing-links-container').innerHTML = html;
  document.getElementById('signing-links-container').style.display = 'block';
}
```

### Step 6: (Optional) Create Wix Signing Page

If you want signers to have a branded experience on your Wix site:

1. In Wix Editor, create a new page at `/sign`
2. Add an HTML iFrame component (ID: `signingFrame`)
3. Add loading, success, and error message containers
4. Enable Velo (Dev Mode)
5. Paste the code from `wix-signing-page.js`

The signing links will include query parameters that the Wix page uses to load the correct SignNow document.

---

## How It Works

### Adding Signers

You already have the **+ Add Indemnitor** button in Dashboard.html. When you click "Generate & Send":

1. The system automatically collects all indemnitors you've added
2. Creates a signing link for each person:
   - Defendant (always first)
   - Primary Indemnitor
   - Co-Indemnitors (any additional indemnitors)
   - Bail Agent (always last)

### Signing Flow

1. Each signer receives their unique link (via SMS, email, or copy/paste)
2. They click the link and sign their portions
3. After signing, they're redirected to `shamrockbailbonds.biz`
4. When ALL signers complete, the webhook fires

### Auto-Save to Google Drive

When the document is fully signed:

1. SignNow sends a webhook to your GAS web app
2. The webhook handler downloads the signed PDF
3. Creates a folder: `{Defendant Name} - {Date}`
4. Saves the PDF to that folder
5. Logs the completion to "Completed Bonds Log" sheet

---

## Configuration Options

### Redirect URLs

In `SignNow_Integration_Complete.gs`, update the `INTEGRATION_CONFIG` object:

```javascript
const INTEGRATION_CONFIG = {
  REDIRECT_URI: 'https://www.shamrockbailbonds.biz',
  DECLINE_REDIRECT_URI: 'https://www.shamrockbailbonds.biz',
  CLOSE_REDIRECT_URI: 'https://www.shamrockbailbonds.biz',
  WIX_SIGNING_PAGE: 'https://www.shamrockbailbonds.biz/sign',
  LINK_EXPIRATION_MINUTES: 45,
  COMPLETED_BONDS_FOLDER_ID: '1WnjwtxoaoXVW8_B6s-0ftdCPf_5WfKgs'
};
```

### Link Expiration

Default is 45 minutes. Change `LINK_EXPIRATION_MINUTES` to adjust.

### Google Drive Folder

Update `COMPLETED_BONDS_FOLDER_ID` to your preferred folder ID.

---

## Troubleshooting

### Signing links not generating

1. Check SignNow API token is valid: Run `SN_testConnection()`
2. Verify document uploaded successfully
3. Check GAS logs for errors

### Webhook not firing

1. Verify web app is deployed with "Anyone" access
2. Check webhook is registered: Run `SN_listRegisteredWebhooks()`
3. Re-register if needed: Run `SN_registerCompletionWebhook(url)`

### Documents not saving to Drive

1. Check folder ID is correct
2. Verify GAS has Drive permissions
3. Check "Completed Bonds Log" sheet for errors

---

## API Reference

### Main Functions

| Function | Description |
|----------|-------------|
| `SN_processCompleteWorkflow(params)` | Main workflow: upload, add fields, create links |
| `SN_createAllSignerLinks(documentId, formData)` | Generate embedded links for all signers |
| `SN_registerCompletionWebhook(url)` | Register webhook for auto-save |
| `buildSignersFromFormData(formData)` | Extract signers from form data |

### Webhook Events

| Event | Handler |
|-------|---------|
| `document.complete` | `handleDocumentComplete()` - Downloads and saves to Drive |

---

## Support

For issues with this integration:
- Check GAS execution logs
- Review SignNow API documentation
- Contact admin@shamrockbailbonds.biz
