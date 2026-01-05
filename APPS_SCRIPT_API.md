# Google Apps Script Web App API

This API is exposed via `doPost` in `Code.gs`. It serves as the backend for the Wix website to perform server-side actions like uploading to SignNow, sending invites, and saving data.

**Base URL**: `[YOUR_GAS_WEB_APP_URL]` (Get this from the GAS Deployment "Web App URL")

## Authentication
Currently, the API is public (open) if deployed as "Anyone". For security, we recommend:
1.  Deploy as "Anyone" (if needed for webhooks) but implement a token check in `doPost`.
2.  Or deploy as "Me" and use an execution API token (more complex).

*Refinement needed: Ensure `doPost` checks for a shared secret if accessed from outside systems.*

## Endpoints (via `action` parameter)

All requests should be `POST` requests with a JSON body.

### 1. `getTemplate`
Fetches a PDF template as Base64.
```json
{
  "action": "getTemplate",
  "templateId": "indemnity-agreement"
}
```
**Response**:
```json
{
  "success": true,
  "pdfBase64": "...",
  "fileName": "Indemnity Agreement.pdf"
}
```

### 2. `uploadToSignNow`
Uploads a generated PDF to SignNow.
```json
{
  "action": "uploadToSignNow",
  "pdfBase64": "...",
  "fileName": "Smith_John_Bond_Packet.pdf"
}
```
**Response**:
```json
{
  "success": true,
  "documentId": "signnow_doc_id_123"
}
```

### 3. `sendForSignature`
Sends a document for signature via Email or SMS.
```json
{
  "action": "sendForSignature",
  "pdfBase64": "...", // Optional if already uploaded and you have documentId, but mostly this function handles both upload and invite
  "fileName": "...",
  "signers": [
    { "email": "client@example.com", "role": "Defendant", "order": 1 }
  ],
  "subject": "Sign your bond",
  "message": "Please sign."
}
```
*Note: `sendForSignature` in `Code.gs` currently wraps `uploadFilledPdfToSignNow` and `createSigningRequest`.*

### 4. `createEmbeddedLink`
Creates a signing link for "Kiosk Mode" or immediate redirect signing.
```json
{
  "action": "createEmbeddedLink",
  "documentId": "signnow_doc_id_123",
  "signerEmail": "client@example.com",
  "signerRole": "Defendant",
  "linkExpiration": 45
}
```
**Response**:
```json
{
  "success": true,
  "link": "https://signnow.com/...",
  "inviteId": "..."
}
```

### 5. `saveBooking`
Saves booking data to the Google Sheet.
```json
{
  "action": "saveBooking",
  "bookingData": {
    "defendant-first-name": "John",
    "defendant-last-name": "Doe",
    ...
  }
}
```

## Wix Implementation Guide

To implement "Populate and Send" from Wix:

1.  **Backend Module (`.jsw`)**: Create a centralized module in Wix backend (e.g., `backend/gasService.jsw`).
2.  **PDF Generation**: Use `pdf-lib` (npm package) in Wix Node.js environment to fill templates.
    *   Call `getTemplate` from GAS to get the blank PDF.
    *   Fill it with Wix data.
    *   Convert to Base64.
3.  **Upload & Send**:
    *   Call `uploadToSignNow` on GAS with the filled Base64.
    *   Call `addSignatureFields` (via `doPost` - typically `addFieldsForDocType` in GAS).
    *   Call `sendEmailInvite` or `createEmbeddedLink` on GAS.

This keeps all SignNow tokens and logic in GAS, treating GAS as a microservice.
