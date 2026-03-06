import time
from scrapling import Fetcher
import urllib.parse

fetcher = Fetcher()

print("Fetching index.php...")
r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')

payload = {'type': 'name', 'lname': 'Smith', 'fname': ''}
print("\nFetching personSearch.php...")
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)

links = r2.css('a[href*="viewInmate.php"]')

if links:
    href = links[0].attrib.get('href')
    
    # Clean ID
    parsed = urllib.parse.urlparse(href)
    qs = urllib.parse.parse_qs(parsed.query)
    clean_id = qs['id'][0].strip()
    url2 = f"https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id={clean_id}"
    
    print(f"\n2. Trying clean URL: {url2}")
    r4 = fetcher.get(url2, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 2: {r4.status}")
    print(f"URL loaded: {r4.url}")
    
    title = r4.css('title')
    print("Page Title:", getattr(title[0], 'text', '') if title else 'No Title')
    
    h1 = r4.css('h1.page-title')
    print("H1:", getattr(h1[0], 'text', '') if h1 else 'No H1')
