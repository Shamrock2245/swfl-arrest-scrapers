# SignNow Integration - Complete Implementation Guide

## Shamrock Bail Bonds - admin@shamrockbailbonds.biz

---

## Executive Summary

This guide provides a complete solution for integrating SignNow with your bail bond workflow. The key insight is that **your PDFs already have form fields** - you just need to:

1. **Pre-fill the PDFs** with data from Form.html (using pdf-lib in browser)
2. **Upload the pre-filled PDF** to SignNow
3. **Add signature fields** programmatically
4. **Send for signing** via SMS, email, or embedded link (kiosk mode)

---

## Issues Identified in Current Implementation

### 1. Missing SMS Invite Support
**Problem:** Current `createSigningRequest()` only supports email invites.
**Solution:** New `SN_sendSmsInvite()` function with proper phone formatting.

### 2. No Signature Field Placement
**Problem:** After uploading a PDF, signature fields aren't being added.
**Solution:** New `SN_addFields()` and `SN_addFieldsForDocType()` functions.

### 3. Missing Role ID Retrieval
**Problem:** SignNow requires role IDs for invites, but they weren't being fetched.
**Solution:** `SN_getDocument()` retrieves roles, and invite functions now map them automatically.

### 4. No Embedded Signing Link
**Problem:** Kiosk mode requires embedded links, which weren't implemented.
**Solution:** New `SN_createEmbeddedLink()` function for in-person signing.

### 5. Preview Function Gap
**Problem:** Preview wasn't showing pre-filled PDFs.
**Solution:** Updated workflow fills PDFs client-side before preview/send.

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FORM.HTML                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ Defendant   │  │ Indemnitor  │  │ Documents   │                  │
│  │ Tab         │  │ Tab         │  │ Tab         │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Generate & Send Tab                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │    │
│  │  │ Preview      │  │ Send Email   │  │ Send SMS     │       │    │
│  │  │ Packet       │  │              │  │              │       │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │    │
│  │                    ┌──────────────┐                          │    │
│  │                    │ Kiosk Mode   │                          │    │
│  │                    │ (Embedded)   │                          │    │
│  │                    └──────────────┘                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BROWSER (pdf-lib)                                 │
│  1. Fetch PDF template from Google Drive                            │
│  2. Fill form fields with data from Form.html                       │
│  3. Generate pre-filled PDF as base64                               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GOOGLE APPS SCRIPT                                │
│  1. Receive pre-filled PDF base64                                   │
│  2. Upload to SignNow (POST /document)                              │
│  3. Add signature fields (PUT /document/{id})                       │
│  4. Send invite (POST /document/{id}/invite)                        │
│     - Email: to[].email                                             │
│     - SMS: to[].phone_invite                                        │
│     - Embedded: /v2/documents/{id}/embedded-invites                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SIGNNOW                                           │
│  1. Stores document                                                  │
│  2. Sends invite (email/SMS/link)                                   │
│  3. Collects signatures                                             │
│  4. Webhook notifies completion                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GOOGLE DRIVE                                      │
│  "Completed Bonds" folder                                           │
│  Filename: LastName, FirstInitial - MM-DD-YYYY.pdf                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Files to Update

### 1. SignNowAPI.gs (Replace Entirely)
Copy the contents of `SignNowAPI_Refactored.gs` to replace the existing `SignNowAPI.gs` in your GAS project.

### 2. Code.gs (Add Cases)
Add the new switch cases from `Code_SignNow_Updates.gs` to your existing `doPost()` function.

### 3. Form.html (Add Functions)
Add the JavaScript functions from `Code_SignNow_Updates.gs` to your Form.html.

---

## API Reference

### Upload Document
```javascript
SN_uploadDocument(pdfBase64, fileName)
// Returns: { success: true, documentId: "xxx" }
```

### Add Signature Fields
```javascript
SN_addFields(documentId, [
  { type: 'signature', role: 'Defendant', page: 0, x: 100, y: 600, width: 200, height: 50 },
  { type: 'initials', role: 'Indemnitor', page: 0, x: 400, y: 600, width: 80, height: 30 }
])
```

### Send Email Invite
```javascript
SN_sendEmailInvite(documentId, [
  { email: 'defendant@email.com', role: 'Defendant', name: 'John Doe' },
  { email: 'indemnitor@email.com', role: 'Indemnitor', name: 'Jane Doe' }
], {
  subject: 'Documents Ready for Signature',
  message: 'Please sign your bail bond documents.'
})
```

### Send SMS Invite
```javascript
SN_sendSmsInvite(documentId, [
  { phone: '(239) 555-1234', role: 'Defendant', name: 'John Doe' }
], {
  fromEmail: 'admin@shamrockbailbonds.biz'
})
// Note: SMS only works for US/Canada numbers
```

### Create Embedded Link (Kiosk Mode)
```javascript
SN_createEmbeddedLink(documentId, 'signer@email.com', 'Defendant', 45)
// Returns: { success: true, link: 'https://app.signnow.com/...', expiresIn: '45 minutes' }
```

### Complete Workflow
```javascript
SN_sendForSignature({
  pdfBase64: 'base64...',
  fileName: 'defendant-application-123456.pdf',
  documentType: 'defendant-application',
  deliveryMethod: 'sms', // or 'email' or 'embedded'
  signers: [
    { phone: '2395551234', role: 'Defendant', name: 'John Doe' }
  ],
  options: {
    subject: 'Bail Bond Documents',
    message: 'Please sign your documents.'
  }
})
```

---

## Signature Field Positions

The `SN_SIGNATURE_FIELDS` object in `SignNowAPI_Refactored.gs` contains predefined positions for each document type. **You will need to calibrate these** based on your actual PDF layouts.

### How to Find Coordinates:
1. Open a PDF in Adobe Acrobat
2. Go to Tools > Prepare Form
3. Note the X, Y coordinates of existing signature fields
4. Update `SN_SIGNATURE_FIELDS` with correct positions

### Current Definitions (Need Calibration):
```javascript
const SN_SIGNATURE_FIELDS = {
  'defendant-application': {
    fields: [
      { type: 'signature', role: 'Defendant', page: 1, x: 100, y: 680, width: 200, height: 50 }
    ]
  },
  // ... etc
};
```

---

## Contact Input Design

For the "Generate & Send" tab, here's the recommended layout:

```
┌─────────────────────────────────────────────────────────────────┐
│  SEND DOCUMENTS FOR SIGNATURE                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Defendant Contact:                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ Phone: (239) 555-   │  │ Email: john@...     │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                  │
│  Indemnitor Contact:                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ Phone: (239) 555-   │  │ Email: jane@...     │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                  │
│  Delivery Method:                                                │
│  ○ Email    ○ SMS (Text)    ○ In-Person (Kiosk)                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Preview      │  │ Send Now     │                             │
│  └──────────────┘  └──────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Script Properties Required

Set these in your GAS project (Project Settings > Script Properties):

| Property | Value |
|----------|-------|
| `SIGNNOW_API_TOKEN` | `0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d` |
| `SIGNNOW_API_BASE_URL` | `https://api.signnow.com` |
| `GOOGLE_DRIVE_FOLDER_ID` | `1ZyTCodt67UAxEbFdGqE3VNua-9TlblR3` |
| `CURRENT_RECEIPT_NUMBER` | `201204` |

---

## Testing Checklist

### Phase 1: Token Validation
- [ ] Run `SN_testConnection()` in GAS editor
- [ ] Verify token is valid and returns user info

### Phase 2: Document Upload
- [ ] Upload a test PDF via Form.html
- [ ] Verify document appears in SignNow account

### Phase 3: Field Placement
- [ ] Add signature fields to uploaded document
- [ ] Verify fields appear in correct positions

### Phase 4: Email Invite
- [ ] Send email invite to test email
- [ ] Verify email received with signing link

### Phase 5: SMS Invite
- [ ] Send SMS invite to test phone
- [ ] Verify SMS received with signing link

### Phase 6: Embedded Link
- [ ] Generate embedded signing link
- [ ] Verify link opens signing interface

### Phase 7: Complete Workflow
- [ ] Fill Form.html with test data
- [ ] Preview documents
- [ ] Send for signature
- [ ] Complete signing
- [ ] Verify saved to Google Drive

---

## Troubleshooting

### "Token validation failed"
- Check that `SIGNNOW_API_TOKEN` is set in Script Properties
- Token may have expired - regenerate in SignNow dashboard

### "Upload failed"
- Check file size (max 50MB)
- Verify PDF is not corrupted
- Check API token permissions

### "SMS invite failed"
- SMS only works for US/Canada numbers
- Phone must be in E.164 format (+1XXXXXXXXXX)
- Check organization settings for electronic consent

### "Fields not appearing"
- Verify page_number is correct (0-indexed)
- Check x/y coordinates are within page bounds
- Ensure role names match exactly

---

## Next Steps

1. **Copy `SignNowAPI_Refactored.gs`** to your GAS project
2. **Add new cases** to `doPost()` in Code.gs
3. **Update Form.html** with new JavaScript functions
4. **Calibrate signature field positions** for each document
5. **Test each delivery method** (email, SMS, embedded)
6. **Set up webhook** for completion notifications (optional)

---

## Support

For SignNow API issues: https://docs.signnow.com
For this implementation: Check the GitHub repo issues

---

*Document generated: December 17, 2025*
*Account: shamrock2245 / admin@shamrockbailbonds.biz*
