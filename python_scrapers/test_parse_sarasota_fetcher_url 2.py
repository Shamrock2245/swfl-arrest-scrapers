import time
from scrapling import Fetcher

fetcher = Fetcher()

print("Fetching index.php...")
r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')
print(f"Status: {r1.status}")

payload = {'type': 'name', 'lname': 'Smith', 'fname': ''}
print("\nFetching personSearch.php...")
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)
print(f"Status: {r2.status}")

links = r2.css('a[href*="viewInmate.php"]')
print(f"Links found: {len(links)}")

if links:
    href = links[0].attrib.get('href')
    print(f"Raw href: '{href}'")
    
    # 1. Exact as returned
    url1 = f"https://cms.revize.com/revize/apps/sarasota/{href}"
    print(f"\n1. Trying exact URL: {url1}")
    r3 = fetcher.get(url1, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 1: {r3.status}")
    
    # 2. Stripped trailing spaces
    import urllib.parse
    parsed = urllib.parse.urlparse(url1)
    qs = urllib.parse.parse_qs(parsed.query)
    clean_id = qs['id'][0].strip()
    url2 = f"https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id={clean_id}"
    print(f"\n2. Trying clean URL: {url2}")
    r4 = fetcher.get(url2, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 2: {r4.status}")

