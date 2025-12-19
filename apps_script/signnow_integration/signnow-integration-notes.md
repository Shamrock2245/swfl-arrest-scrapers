# SignNow Integration Notes for Wix Site

## Key Findings from Documentation

### Embedded Signing Overview
- API users can embed SignNow into their website/app to allow customers to sign documents without sending emails
- No additional registration required, no email interruptions
- Works by adding a link that opens a document in SignNow iFrame directly in the app

### Two-Step Process
1. Prepare document for signature OR create embedded invite to sign
2. Generate a link for the invite that can be built into your app

### Prerequisites for Embedded Signing
- Must be owner of the Document or Document group
- Create invite for a document, NOT a template
- Document must contain fields
- Document must NOT be in pending or signed status
- All roles/role IDs must be assigned to signers

### Key API Endpoints Needed

#### Step 1: Upload Document
```
POST /document
```

#### Step 2: Add Fields
```
PUT /document/{document_id}
```

#### Step 3: Get Role ID
```
GET /document/{document_id}
```

#### Step 4: Create Embedded Invite
```
POST /v2/documents/{document_id}/embedded-invites
```

#### Step 5: Generate Signing Link
```
POST /v2/documents/{document_id}/embedded-invites/{invite_id}/link
```

### Signing Features Available
- Multiple signers with specific order
- Different fields assigned to separate signer roles
- Auto-generated document names using name_formula
- Three authentication methods:
  - SMS verification
  - Phone call verification  
  - Password verification

### Redirect URIs
- `redirect_uri`: After signing complete
- `decline_redirect_uri`: When signer declines
- `close_redirect_uri`: When signer saves progress/closes
- `redirect_target`: "blank" (new tab) or "self" (same tab)

### Language Support
- en (English), es (Spanish), fr (French)

### Signature Options
- `prefill_signature_name`: Prefill text, signer can edit
- `required_preset_signature_name`: Prefill text, disabled for editing
- `force_new_signature`: 0 = use saved, 1 = new signature required

## Wix Integration Architecture

### Option 1: Wix Velo Backend (Recommended)
- Use Wix Velo (JavaScript) for backend API calls
- Store SignNow credentials in Wix Secrets Manager
- Create backend web modules (.jsw files) for SignNow API calls
- Frontend calls backend modules, backend calls SignNow

### Option 2: External Backend Service
- Host a Node.js/Python backend separately
- Wix frontend calls external API
- External API handles SignNow integration

### Workflow for Wix Integration
1. User fills form on Wix site (similar to Dashboard.html)
2. Form data sent to Wix backend
3. Backend:
   - Fetches PDF templates from Google Drive
   - Pre-fills PDFs with form data
   - Uploads to SignNow
   - Adds signature fields
   - Creates embedded invite
   - Returns signing link
4. Frontend displays signing link or embeds in iframe
5. After signing, webhook notifies completion
6. Backend downloads signed docs and saves to Google Drive

### Existing Access Token
```
0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d
```

## Next Steps
1. Create SignNow application in API dashboard (if not already done)
2. Set up OAuth 2.0 for production use
3. Build Wix Velo backend modules
4. Migrate Dashboard.html functionality to Wix
5. Set up webhooks for signing completion
6. Implement Google Drive integration for completed docs


## Complete Embedded Signing API Workflow

### Step 1: Upload Document
```bash
curl --request POST \
  --url https://api.signnow.com/document \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer {{access_token}}' \
  --header 'Content-Type: multipart/form-data' \
  --form file=@/path/to/your/file.pdf
```

Alternative: Upload from URL
```bash
curl --request POST \
  --url https://api.signnow.com/v2/documents/url \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer {{access_token}}' \
  --header 'Content-Type: application/json' \
  --data '{
    "url": "https://file.com"
  }'
```

### Step 2: Add Fields
```bash
curl --location --request PUT 'https://api.signnow.com/document/{{document_id}}' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer {{access_token}}' \
  --data '{
    "fields": [
      {
        "page_number": 1,
        "type": "signature",
        "name": "signature_1",
        "role": "Signer 1",
        "required": true,
        "height": 40,
        "width": 50,
        "x": 260,
        "y": 60
      },
      {
        "page_number": 0,
        "type": "text",
        "name": "signer_name",
        "role": "Signer 1",
        "required": true,
        "height": 40
      }
    ]
  }'
```

### Step 3: Get Role ID
Make a GET document request to extract the role ID from the roles array:
```json
"roles": [
  {
    "unique_id": "26XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "signing_order": "1",
    "name": "Signer 1"
  }
]
```

### Step 4: Create Embedded Invite
```bash
curl --request POST \
  --url https://api.signnow.com/v2/documents/{{document_id}}/embedded-invites \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer {{access_token}}' \
  --header 'Content-Type: application/json' \
  --data '{
    "name_formula": "Contract|signer_name|signed_date",
    "invites": [
      {
        "email": "signer@email.com",
        "role_id": "26XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "order": 1,
        "auth_method": "none",
        "first_name": "Jane",
        "last_name": "Doe"
      }
    ]
  }'
```

### Step 5: Generate Signing Link
```bash
curl --request POST \
  --url https://api.signnow.com/v2/documents/{{document_id}}/embedded-invites/{{field_invite_id}}/link \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer {{access_token}}' \
  --header 'Content-Type: application/json' \
  --data '{
    "auth_method": "none",
    "link_expiration": 45
  }'
```

Note: The `auth_method` should match the one used when creating the embedded invite.

### Step 6: Open the Embedded Link
The generated link opens the SignNow signing interface where the signer can:
- Select language
- View the document
- Click "Get Started" to begin signing
- Complete all required fields
- Click "Finish" to complete

## Key Integration Points for Wix

### Wix Velo HTTP Functions
Wix Velo supports backend HTTP functions that can call external APIs. Create a backend file like:

```javascript
// backend/signnow.jsw
import { fetch } from 'wix-fetch';
import { getSecret } from 'wix-secrets-backend';

export async function uploadDocument(pdfBase64, filename) {
  const accessToken = await getSecret('SIGNNOW_ACCESS_TOKEN');
  // Implementation here
}

export async function createEmbeddedInvite(documentId, signerInfo) {
  const accessToken = await getSecret('SIGNNOW_ACCESS_TOKEN');
  // Implementation here
}

export async function getSigningLink(documentId, inviteId) {
  const accessToken = await getSecret('SIGNNOW_ACCESS_TOKEN');
  // Implementation here
}
```

### Wix Secrets Manager
Store SignNow credentials securely:
- SIGNNOW_ACCESS_TOKEN
- SIGNNOW_CLIENT_ID
- SIGNNOW_CLIENT_SECRET

### Wix HTML Component (iFrame)
Use Wix HTML Component to embed the SignNow signing interface:
```javascript
$w('#htmlComponent').src = signingLink;
```

### Webhooks for Completion
Set up SignNow webhooks to notify your Wix backend when documents are signed:
- document.complete
- document.update
- invite.complete
