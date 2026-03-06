import time
import urllib.parse
from scrapling import Fetcher

fetcher = Fetcher()

print("Fetching index.php...")
fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')

payload = {'type': 'name', 'lname': 'Smith', 'fname': ''}
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)

links = r2.css('a[href*="viewInmate.php"]')
if links:
    href = links[0].attrib.get('href')
    
    url1 = f"https://cms.revize.com/revize/apps/sarasota/{href}"
    print(f"\n1. Trying exact URL: {url1}")
    r3 = fetcher.get(url1, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 1: {r3.status} URL: {r3.url}")
    
    parsed = urllib.parse.urlparse(href)
    qs = urllib.parse.parse_qs(parsed.query)
    clean_id = qs['id'][0].strip()
    url2 = f"https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id={clean_id}"
    
    print(f"\n2. Trying clean URL: {url2}")
    r4 = fetcher.get(url2, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 2: {r4.status} URL: {r4.url}")
    
    title = r4.css('title')
    print("Page Title from CSS:", getattr(title[0], 'text', '') if title else 'No Title')
    
    h1 = r4.css('h1.page-title')
    print("H1 from CSS:", getattr(h1[0], 'text', '') if h1 else 'No H1')

    print("\nr4.text type:", type(r4.text))
    print("r4.text length:", len(r4.text) if r4.text else "None or 0")
    if r4.text:
        print("Starts with:", r4.text[:100])
