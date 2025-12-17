#!/usr/bin/env python3
"""
SignNow API Test Script
Tests the API connection and basic operations for Shamrock Bail Bonds
"""

import requests
import json
import os

# Configuration
API_BASE = "https://api.signnow.com"
ACCESS_TOKEN = "0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d"

def test_token_validation():
    """Test if the access token is valid"""
    print("\n=== Testing Token Validation ===")
    
    response = requests.get(
        f"{API_BASE}/user",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✓ Token is VALID")
        print(f"  User Email: {user_data.get('primary_email', 'N/A')}")
        print(f"  User ID: {user_data.get('id', 'N/A')}")
        return True
    else:
        print(f"✗ Token validation FAILED")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_list_documents():
    """List documents in the account"""
    print("\n=== Listing Documents ===")
    
    response = requests.get(
        f"{API_BASE}/user/documentsv2",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Handle both list and dict responses
        if isinstance(data, list):
            docs = data
        else:
            docs = data.get('data', data.get('documents', []))
        print(f"✓ Found {len(docs)} documents")
        for doc in docs[:5]:  # Show first 5
            doc_name = doc.get('document_name', doc.get('name', 'Unnamed'))
            doc_id = doc.get('id', 'N/A')
            print(f"  - {doc_name} (ID: {doc_id[:20] if len(doc_id) > 20 else doc_id}...)")
        return True
    else:
        print(f"✗ Failed to list documents")
        print(f"  Status Code: {response.status_code}")
        return False

def test_list_templates():
    """List templates in the account"""
    print("\n=== Listing Templates ===")
    
    response = requests.get(
        f"{API_BASE}/user/templates",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✓ Found {len(templates)} templates")
        for tmpl in templates[:5]:  # Show first 5
            print(f"  - {tmpl.get('template_name', 'Unnamed')} (ID: {tmpl.get('id', 'N/A')[:20]}...)")
        return True
    else:
        print(f"✗ Failed to list templates")
        print(f"  Status Code: {response.status_code}")
        return False

def test_upload_document():
    """Test uploading a simple PDF"""
    print("\n=== Testing Document Upload ===")
    
    # Check if we have a test PDF
    test_pdf_path = "/home/ubuntu/shamrock-bail-bonds/pdf_analysis/shamrock-master-waiver.pdf"
    
    if not os.path.exists(test_pdf_path):
        print("✗ Test PDF not found, skipping upload test")
        return False
    
    with open(test_pdf_path, 'rb') as f:
        files = {'file': ('test-upload.pdf', f, 'application/pdf')}
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

def test_add_signature_field(document_id):
    """Test adding a signature field to a document"""
    print("\n=== Testing Add Signature Field ===")
    
    if not document_id:
        print("✗ No document ID provided, skipping")
        return False
    
    payload = {
        "fields": [
            {
                "type": "signature",
                "required": True,
                "role": "Signer 1",
                "page_number": 0,
                "x": 100,
                "y": 600,
                "width": 200,
                "height": 50
            }
        ]
    }
    
    response = requests.put(
        f"{API_BASE}/document/{document_id}",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        print(f"✓ Signature field added successfully")
        return True
    else:
        print(f"✗ Failed to add signature field")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_get_document(document_id):
    """Get document details including roles"""
    print("\n=== Testing Get Document Details ===")
    
    if not document_id:
        print("✗ No document ID provided, skipping")
        return None
    
    response = requests.get(
        f"{API_BASE}/document/{document_id}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 200:
        doc = response.json()
        print(f"✓ Document retrieved successfully")
        print(f"  Name: {doc.get('document_name', 'N/A')}")
        print(f"  Pages: {doc.get('page_count', 'N/A')}")
        
        roles = doc.get('roles', [])
        print(f"  Roles: {len(roles)}")
        for role in roles:
            print(f"    - {role.get('name', 'Unnamed')} (ID: {role.get('unique_id', 'N/A')[:20]}...)")
        
        return doc
    else:
        print(f"✗ Failed to get document")
        print(f"  Status Code: {response.status_code}")
        return None

def test_delete_document(document_id):
    """Clean up - delete test document"""
    print("\n=== Cleaning Up Test Document ===")
    
    if not document_id:
        print("✗ No document ID provided, skipping")
        return False
    
    response = requests.delete(
        f"{API_BASE}/document/{document_id}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    if response.status_code == 200:
        print(f"✓ Test document deleted successfully")
        return True
    else:
        print(f"✗ Failed to delete document (may already be deleted)")
        return False

def main():
    print("=" * 60)
    print("SignNow API Test Suite - Shamrock Bail Bonds")
    print("=" * 60)
    
    # Test 1: Token validation
    if not test_token_validation():
        print("\n❌ Token validation failed. Cannot proceed with other tests.")
        return
    
    # Test 2: List documents
    test_list_documents()
    
    # Test 3: List templates
    test_list_templates()
    
    # Test 4: Upload document
    doc_id = test_upload_document()
    
    if doc_id:
        # Test 5: Add signature field
        test_add_signature_field(doc_id)
        
        # Test 6: Get document details
        test_get_document(doc_id)
        
        # Test 7: Clean up
        test_delete_document(doc_id)
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
