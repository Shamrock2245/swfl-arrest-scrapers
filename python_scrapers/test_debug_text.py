import urllib.parse
from scrapling import Fetcher

fetcher = Fetcher()
fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')

payload = {'type': 'name', 'lname': 'Smith', 'fname': ''}
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)

links = r2.css('a[href*="viewInmate.php"]')
if links:
    href = links[0].attrib.get('href')
    
    url1 = f"https://cms.revize.com/revize/apps/sarasota/{href}"
    fetcher.get(url1, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    
    parsed = urllib.parse.urlparse(href)
    qs = urllib.parse.parse_qs(parsed.query)
    clean_id = qs['id'][0].strip()
    url2 = f"https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id={clean_id}"
    
    r4 = fetcher.get(url2, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    
    print("r4.text type:", type(r4.text))
    print("dir(r4.text):", dir(r4.text))
    # Let's try to get the raw string
    try:
        print("str(r4.text) length:", len(str(r4.text)))
        print(str(r4.text)[:100])
    except Exception as e:
        print("str(r4.text) failed:", e)

    try:
        if hasattr(r4, 'body'):
            print("r4.body length:", len(r4.body))
    except Exception as e:
         print("r4.body failed:", e)
    
    try:
         print("r4.html length:", len(r4.html) if hasattr(r4, 'html') else "NO HTML ATTR")
    except Exception as e:
         pass
