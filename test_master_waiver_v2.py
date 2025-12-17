#!/usr/bin/env python3
"""
Test Script v2: Master-waiver with ADJUSTED signature Y coordinates
Moving signatures down ~200 pixels to align with actual signature lines
"""

import requests
import json
import os

# Configuration
API_BASE = "https://api.signnow.com"
ACCESS_TOKEN = "0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d"

# Master-waiver field configuration - ADJUSTED SIGNATURE Y VALUES
MASTER_WAIVER_FIELDS = [
    # Page 1 initials (page 0 in API) - THESE WERE CORRECT
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
    
    # Page 4 signatures (page 3 in API) - ADJUSTED Y VALUES (+187 pixels)
    # Original: 303, 275, 247, 219 -> New: 490, 462 (wait, need to maintain spacing)
    # Looking at the form, the lines are evenly spaced about 22px apart
    { "type": "signature", "role": "Bail Agent", "name": "signature-surety-representative", "page_number": 3, "x": 195, "y": 490, "width": 145, "height": 26, "required": True },
    { "type": "signature", "role": "Defendant", "name": "signature-defendant", "page_number": 3, "x": 155, "y": 512, "width": 185, "height": 26, "required": True },
    { "type": "signature", "role": "Indemnitor", "name": "signature-indemnitor", "page_number": 3, "x": 165, "y": 534, "width": 175, "height": 26, "required": True },
    { "type": "signature", "role": "Co-Indemnitor", "name": "signature-co-indemnitor", "page_number": 3, "x": 175, "y": 556, "width": 165, "height": 26, "required": False }
]

def upload_document(pdf_path):
    """Upload a PDF to SignNow"""
    print(f"\n=== Uploading {os.path.basename(pdf_path)} ===")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('master-waiver-test-v2.pdf', f, 'application/pdf')}
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
            print(f"    - {role.get('name', 'Unnamed')}")
        
        return doc
    else:
        print(f"✗ Failed to get document")
        return None

def main():
    print("=" * 70)
    print("Master-Waiver Test v2 - ADJUSTED Signature Y Coordinates")
    print("=" * 70)
    print("\nChanges from v1:")
    print("  - Surety Representative: y: 303 -> 490")
    print("  - Defendant: y: 275 -> 512")
    print("  - Indemnitor: y: 247 -> 534")
    print("  - Co-Indemnitor: y: 219 -> 556")
    
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
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"\nDocument ID: {doc_id}")
    print(f"\n🔗 View in SignNow Dashboard:")
    print(f"   https://app.signnow.com/webapp/document/{doc_id}")
    print("\nPlease check if the signature fields are now aligned with the signature lines.")

if __name__ == "__main__":
    main()
