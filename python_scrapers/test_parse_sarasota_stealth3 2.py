import os
import time
from scrapling.engines._browsers._stealth import StealthySession

os.makedirs('./tmp_scrapling', exist_ok=True)
user_data_path = os.path.abspath('./tmp_scrapling')

print(f"Starting StealthySession with data dir: {user_data_path}")

try:
    with StealthySession(headless=True, user_data_dir=user_data_path) as engine:
        print("1. GET index.php to init session...")
        r1 = engine.fetch('https://cms.revize.com/revize/apps/sarasota/index.php')
        print('Fetched index.php', r1.status)
        
        print("\n2. POST personSearch.php...")
        # Since engine is StealthySession, it only provides `fetch` according to the class methods in _stealth.py.
        # Wait, StealthySession only provides `fetch(url, **kwargs)`. Does it support POST?
        # StealthFetchParams documentation or scrapling docs might indicate how to pass POST data.
except Exception as e:
    print(f"Error: {e}")
