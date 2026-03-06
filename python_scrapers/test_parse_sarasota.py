import sys
import datetime
from scrapling import Fetcher

def test_sarasota_search():
    page = Fetcher()
    # Let's search for arrest date yesterday 
    date_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    url = "https://cms.revize.com/revize/apps/sarasota/personSearch.php"
    
    payload = {
        'type': 'date',
        'date': date_str
    }
    
    print(f"Submitting to {url} with {payload}")
    # scrapling typically supports pass-through params or data
    # We will try passing as form data via POST
    
    try:
        # Fetcher might not have a direct post method, but let's try
        # Actually Fetcher uses iterators etc. Let's see if we can perform a POST
        res = page.post(url, data=payload)
        
        print(f"Status: {getattr(res, 'status', 'Unknown')}")
        
        links = res.css('a[href*="viewInmate.php"]')
        print(f"Found {len(links)} inmate links")
        if links:
            for link in links[:3]:
                print(f"  Link: {link.attrib.get('href')}")
                
        # Save HTML for review
        html_text = res.html_content if hasattr(res, 'html_content') else (res.body.decode('utf-8', errors='ignore') if hasattr(res, 'body') else '')
        with open('test_sarasota_results_body.html', 'w') as f:
            f.write(html_text)
        print("Saved html to test_sarasota_results_body.html")
        
    except Exception as e:
        print(f"Error fetching: {e}")

if __name__ == "__main__":
    test_sarasota_search()
