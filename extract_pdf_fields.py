#!/usr/bin/env python3
"""Extract form field names from PDF files"""

import subprocess
import sys

# Try to use pdfinfo and pdftk if available, otherwise use pdftoppm
def extract_with_pdftk(pdf_path):
    """Use pdftk to dump form fields"""
    try:
        result = subprocess.run(
            ['pdftk', pdf_path, 'dump_data_fields'],
            capture_output=True, text=True
        )
        return result.stdout
    except FileNotFoundError:
        return None

def extract_with_pdftotext(pdf_path):
    """Use pdftotext to get text content"""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', pdf_path, '-'],
            capture_output=True, text=True
        )
        return result.stdout
    except FileNotFoundError:
        return None

def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else '/home/ubuntu/shamrock-bail-bonds/pdf_analysis/shamrock-defendant-application.pdf'
    
    print(f"Analyzing: {pdf_path}")
    print("=" * 60)
    
    # Try pdftk first
    fields = extract_with_pdftk(pdf_path)
    if fields:
        print("Form Fields (from pdftk):")
        print(fields)
    else:
        print("pdftk not available, trying pdftotext...")
        text = extract_with_pdftotext(pdf_path)
        if text:
            print("PDF Text Content (first 5000 chars):")
            print(text[:5000])
        else:
            print("No tools available to analyze PDF")

if __name__ == '__main__':
    main()
