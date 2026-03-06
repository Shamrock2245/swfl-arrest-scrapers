import sys
from curl_cffi import requests

def test_collier_curl():
    url = 'https://www2.colliersheriff.org/arrestsearch/Report.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, impersonate="chrome120")
        if response.status_code == 200:
            print("Successfully fetched the page!")
            
            # Print title looking for Cloudflare or the actual title
            import re
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
            if title_match:
                print(f"Title: {title_match.group(1)}")
                
            print(f"HTML Preview:\n{response.text[:1000]}")
        else:
            print(f"Failed with status: {response.status_code}")
    except Exception as e:
        print(f"Error fetching page: {e}", file=sys.stderr)

if __name__ == "__main__":
    test_collier_curl()
