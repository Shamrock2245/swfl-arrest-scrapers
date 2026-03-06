import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
}

session = requests.Session()
session.headers.update(headers)

# 1. Get index to get PHP session
print("Fetching index.php...")
r1 = session.get('https://cms.revize.com/revize/apps/sarasota/index.php')
print(f"Status: {r1.status_code}")
print(f"Cookies: {session.cookies.get_dict()}")

# 2. Fetch specific detail page
print("\nFetching viewInmate.php...")
detail_url = 'https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id=0201029792%20%20%20%20%20'
r2 = session.get(detail_url)
print(f"Status: {r2.status_code}")

if r2.status_code == 200:
    soup = BeautifulSoup(r2.text, 'html.parser')
    h1 = soup.find('h1', class_='page-title')
    print(f"H1 Text: {h1.text if h1 else 'None'}")
    
    # Are we getting a Cloudflare captcha page?
    title = soup.find('title')
    print(f"Page Title: {title.text if title else 'None'}")
