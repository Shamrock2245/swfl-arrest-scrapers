import time
from scrapling.engines._browsers._stealth import StealthySession

print("Starting StealthySession...")
with StealthySession(headless=True) as engine:
    print("1. GET index.php to init session...")
    r1 = engine.fetch('https://cms.revize.com/revize/apps/sarasota/index.php')
    print('Fetched index.php', r1.status)
    
    # Wait, can we script the browser? StealthySession returns a Response object, which has .page?
    # Actually, Scrapling `Response` from `StealthySession` doesn't expose the underlying Playwright Page directly for interaction.
    # StealthySession is just for a single fetch?
    # Let's see what methods it has.
    print(dir(r1))
