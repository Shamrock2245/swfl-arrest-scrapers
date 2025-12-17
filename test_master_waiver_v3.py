#!/usr/bin/env python3
"""
Test Script v3: Master-waiver - moving signatures UP one space (~22px)
"""

import requests
import os

API_BASE = "https://api.signnow.com"
ACCESS_TOKEN = "0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d"

# v2 values: 490, 512, 534, 556 -> v3: subtract ~22px each
# New values: 468, 490, 512, 534
MASTER_WAIVER_FIELDS = [
    # Page 1-4 initials - UNCHANGED (these were correct)
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p1", "page_number": 0, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p1", "page_number": 0, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p2", "page_number": 1, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p2", "page_number": 1, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p3", "page_number": 2, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p3", "page_number": 2, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Defendant", "name": "initials-defendant-p4", "page_number": 3, "x": 60, "y": 30, "width": 50, "height": 22, "required": True },
    { "type": "initials", "role": "Indemnitor", "name": "initials-indemnitor-p4", "page_number": 3, "x": 502, "y": 30, "width": 50, "height": 22, "required": True },
    
    # Page 4 signatures - MOVED UP 22px from v2
    { "type": "signature", "role": "Bail Agent", "name": "signature-surety-representative", "page_number": 3, "x": 195, "y": 468, "width": 145, "height": 26, "required": True },
    { "type": "signature", "role": "Defendant", "name": "signature-defendant", "page_number": 3, "x": 155, "y": 490, "width": 185, "height": 26, "required": True },
    { "type": "signature", "role": "Indemnitor", "name": "signature-indemnitor", "page_number": 3, "x": 165, "y": 512, "width": 175, "height": 26, "required": True },
    { "type": "signature", "role": "Co-Indemnitor", "name": "signature-co-indemnitor", "page_number": 3, "x": 175, "y": 534, "width": 165, "height": 26, "required": False }
]

def main():
    print("=" * 70)
    print("Master-Waiver Test v3 - Signatures moved UP 22px")
    print("=" * 70)
    print("\nChanges from v2:")
    print("  - Surety Representative: y: 490 -> 468")
    print("  - Defendant: y: 512 -> 490")
    print("  - Indemnitor: y: 534 -> 512")
    print("  - Co-Indemnitor: y: 556 -> 534")
    
    pdf_path = "/home/ubuntu/shamrock-bail-bonds/pdf_analysis/shamrock-master-waiver.pdf"
    
    # Upload
    print(f"\n=== Uploading ===")
    with open(pdf_path, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/document",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            files={'file': ('master-waiver-test-v3.pdf', f, 'application/pdf')}
        )
    
    if response.status_code not in [200, 201]:
        print(f"✗ Upload failed: {response.text}")
        return
    
    doc_id = response.json().get('id')
    print(f"✓ Document ID: {doc_id}")
    
    # Add fields
    print(f"\n=== Adding 12 fields ===")
    formatted_fields = []
    for field in MASTER_WAIVER_FIELDS:
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
    
    response = requests.put(
        f"{API_BASE}/document/{doc_id}",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"fields": formatted_fields}
    )
    
    if response.status_code == 200:
        print(f"✓ All fields added!")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"\nDocument ID: {doc_id}")
    print(f"\n🔗 View in SignNow Dashboard:")
    print(f"   https://app.signnow.com/webapp/document/{doc_id}")

if __name__ == "__main__":
    main()
