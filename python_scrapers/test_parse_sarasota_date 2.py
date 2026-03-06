import time
import urllib.parse
from datetime import datetime, timedelta
from scrapling import Fetcher

fetcher = Fetcher()

print("Fetching index.php...")
fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')

# Search for yesterday
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f"Fetching personSearch.php for date {yesterday}...")
payload = {'type': 'date', 'date': yesterday}

# It seems the form names are: type='date', date='YYYY-MM-DD' (wait, let me check the HTML for date format expected)
# In test_parse_sarasota_forms, date type is 'date'. Usually 'YYYY-MM-DD'
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)

links = r2.css('a[href*="viewInmate.php"]')
print(f"Found {len(links)} inmates for {yesterday}")

if links:
    href = links[0].attrib.get('href')
    url1 = f"https://cms.revize.com/revize/apps/sarasota/{href}"
    r3 = fetcher.get(url1, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    
    parsed = urllib.parse.urlparse(href)
    qs = urllib.parse.parse_qs(parsed.query)
    clean_id = qs['id'][0].strip()
    url2 = f"https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id={clean_id}"
    
    r4 = fetcher.get(url2, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    
    title = r4.css('title')
    print("Page Title:", getattr(title[0], 'text', '') if title else 'No Title')
    
    h1 = r4.css('h1.page-title')
    print("H1 (Name):", getattr(h1[0], 'text', '').strip() if h1 else 'No H1')
