#!/usr/bin/env python3
"""
Test Script: Upload master-waiver PDF and add signature/initials fields
Tests the exact coordinates provided for the master-waiver document
"""

import requests
import json
import os

# Configuration
API_BASE = "https://api.signnow.com"
ACCESS_TOKEN = "0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d"

# Master-waiver field configuration (from SignNowAPI_Refactored.gs)
MASTER_WAIVER_FIELDS = [
    # Page 1 initials (page 0 in API)
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p1", "page_number": 0, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p1", "page_number": 0, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    # Page 2 initials (page 1 in API)
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p2", "page_number": 1, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p2", "page_number": 1, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    # Page 3 initials (page 2 in API)
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p3", "page_number": 2, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p3", "page_number": 2, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    # Page 4 initials (page 3 in API)
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p4", "page_number": 3, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p4", "page_number": 3, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    # Page 4 signatures (page 3 in API)
    { "type": "signature", "role": "Bail Agent", "name": "signature-surety-representative", "page_number": 3, "x": 195, "y": 303, "width": 145, "height": 26, "required": True },
    { "type": "signature", "role": "Defendant", "name": "signature-defendant", "page_number": 3, "x": 155, "y": 275, "width": 185, "height": 26, "required": True },
    { "type": "signature", "role": "Indemnitor", "name": "signature-indemnitor", "page_number": 3, "x": 165, "y": 247, "width": 175, "height": 26, "required": True },
    { "type": "signature", "role": "Co-Indemnitor", "name": "signature-co-indemnitor", "page_number": 3, "x": 175, "y": 219, "width": 165, "height": 26, "required": False }
]

def upload_document(pdf_path):
    """Upload a PDF to SignNow"""
    print(f"\n=== Uploading {os.path.basename(pdf_path)} ===")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('master-waiver-test.pdf', f, 'application/pdf')}
        response = requests.post(
            f"{API_BASE}/document",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            files=files
        )
    
    if response.status_code in [200, 201]:
        result = response.json()
        doc_id = result.get('id')
        print(f"✓ Document uploaded successfully")
        print(f"  Document ID: {doc_id}")
        return doc_id
    else:
        print(f"✗ Upload FAILED")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def add_fields(document_id, fields):
    """Add signature/initials fields to a document"""
    print(f"\n=== Adding {len(fields)} fields to document ===")
    
    # Format fields for SignNow API
    formatted_fields = []
    for field in fields:
        formatted = {
            "type": field["type"],
            "required": field.get("required", True),
            "role": field["role"],
            "name": field.get("name", ""),
            "page_number": field["page_number"],
            "x": field["x"],
            "y": field["y"],
            "width": field["width"],
            "height": field["height"]
        }
        if field["type"] == "signature":
            formatted["allowed_types"] = ["draw", "type", "upload"]
        formatted_fields.append(formatted)
    
    payload = {"fields": formatted_fields}
    
    response = requests.put(
        f"{API_BASE}/document/{document_id}",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        print(f"✓ All {len(fields)} fields added successfully!")
        return True
    else:
        print(f"✗ Failed to add fields")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def get_document_details(document_id):
    """Get document details to verify fields"""
    print(f"\n=== Verifying document fields ===")
    
    response = requests.get(
        f"{API_BASE}/document/{document_id}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 200:
        doc = response.json()
        print(f"✓ Document retrieved: {doc.get('document_name', 'N/A')}")
        print(f"  Pages: {doc.get('page_count', 'N/A')}")
        
        # Count fields
        fields = doc.get('fields', [])
        signatures = [f for f in fields if f.get('type') == 'signature']
        initials = [f for f in fields if f.get('type') == 'initials']
        
        print(f"  Total fields: {len(fields)}")
        print(f"  Signature fields: {len(signatures)}")
        print(f"  Initials fields: {len(initials)}")
        
        # Show roles
        roles = doc.get('roles', [])
        print(f"  Roles: {len(roles)}")
        for role in roles:
            print(f"    - {role.get('name', 'Unnamed')} (ID: {role.get('unique_id', 'N/A')[:20]}...)")
        
        return doc
    else:
        print(f"✗ Failed to get document")
        return None

def create_embedded_link(document_id, role="Defendant"):
    """Create an embedded signing link for testing"""
    print(f"\n=== Creating embedded signing link for {role} ===")
    
    # Step 1: Create embedded invite
    invite_payload = {
        "invites": [{
            "email": "test@shamrockbailbonds.biz",
            "role": role,
            "order": 1,
            "auth_method": "none",
            "force_new_signature": 1
        }]
    }
    
    response = requests.post(
        f"{API_BASE}/v2/documents/{document_id}/embedded-invites",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=invite_payload
    )
    
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create embedded invite")
        print(f"  Response: {response.text}")
        return None
    
    invite_data = response.json()
    invite_id = invite_data['data'][0]['id']
    
    # Step 2: Generate signing link
    link_payload = {
        "auth_method": "none",
        "link_expiration": 45
    }
    
    response = requests.post(
        f"{API_BASE}/v2/documents/{document_id}/embedded-invites/{invite_id}/link",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=link_payload
    )
    
    if response.status_code in [200, 201]:
        link_data = response.json()
        print(f"✓ Signing link created!")
        print(f"  Link: {link_data.get('link', 'N/A')}")
        print(f"  Expires in: 45 minutes")
        return link_data.get('link')
    else:
        print(f"✗ Failed to generate signing link")
        print(f"  Response: {response.text}")
        return None

def main():
    print("=" * 70)
    print("Master-Waiver Test - SignNow Field Placement")
    print("=" * 70)
    
    # Path to the master-waiver PDF
    pdf_path = "/home/ubuntu/shamrock-bail-bonds/pdf_analysis/shamrock-master-waiver.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"✗ PDF not found at {pdf_path}")
        return
    
    # Step 1: Upload the document
    doc_id = upload_document(pdf_path)
    if not doc_id:
        return
    
    # Step 2: Add all signature/initials fields
    success = add_fields(doc_id, MASTER_WAIVER_FIELDS)
    if not success:
        return
    
    # Step 3: Verify the document
    doc = get_document_details(doc_id)
    
    # Step 4: Create a signing link so you can visually verify field placement
    signing_link = create_embedded_link(doc_id, "Defendant")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"\nDocument ID: {doc_id}")
    if signing_link:
        print(f"\n🔗 SIGNING LINK (open this to verify field placement):")
        print(f"   {signing_link}")
        print(f"\n   This link expires in 45 minutes.")
    print("\nYou can also view this document in your SignNow dashboard.")

if __name__ == "__main__":
    main()
