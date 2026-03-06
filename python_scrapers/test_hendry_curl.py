import sys
from curl_cffi import requests

def test_hendry():
    url = "https://www.hendrysheriff.org/inmateSearch"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    print("Fetching Hendry...", url)
    try:
        response = requests.get(url, headers=headers, impersonate="chrome120", timeout=30)
        print("Status code:", response.status_code)
        
        # Save first 500 chars to see if it's cloudflare or the app
        print("Response start:", response.text[:500])
        
        with open('debug_hendry.html', 'w') as f:
            f.write(response.text)
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_hendry()
