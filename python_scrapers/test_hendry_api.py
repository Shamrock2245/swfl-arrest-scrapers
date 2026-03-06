import re
from curl_cffi import requests

def find_api():
    url = "https://www.hendrysheriff.org/static/js/main.3c62118a.js"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    resp = requests.get(url, headers=headers, impersonate="chrome120")
    print(f"JS Length: {len(resp.text)}")
    
    # Try to find typical fetch or axios urls
    urls = re.findall(r'https?://[^\s"\']+', resp.text)
    for u in set(urls):
        if 'api' in u.lower() or 'inmate' in u.lower() or 'myocv' in u.lower() or 'scraper' in u.lower():
            print("Found URL:", u)
            
    # Also find any endpoint paths like "/api/..."
    paths = re.findall(r'\"/api/[^\"]+\"', resp.text)
    for p in set(paths):
        print("Found Path:", p)

if __name__ == "__main__":
    find_api()
