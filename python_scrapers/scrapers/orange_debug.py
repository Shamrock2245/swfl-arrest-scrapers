import pdfplumber
import requests
import io
import sys

def debug_pdf():
    url = "https://netapps.ocfl.net/BestJail/PDF/bookings.pdf"
    print(f"Downloading {url}...")
    response = requests.get(url)
    
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            print(f"--- Page {i+1} ---")
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                print(f"Table {t_idx}:")
                for row in table[:5]: # Print first 5 rows
                    print(row)
            
            # extract_text usually helpful too
            text = page.extract_text()
            print(f"Text Snippet:\n{text[:500]}")
            
            if i >= 1: break # Just check first 2 pages

if __name__ == "__main__":
    debug_pdf()
