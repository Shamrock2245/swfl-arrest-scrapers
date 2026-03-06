import sys
from scrapling import Fetcher

def test_scrapling():
    print("Testing Scrapling Fetcher with Charlotte County...")
    try:
        page = Fetcher()
        response = page.get('https://inmates.charlottecountyfl.revize.com/bookings')
        
        print(f"Response object attributes: {dir(response)}")
        print(f"Response status: {getattr(response, 'status', None) or getattr(response, 'status_code', None)}")
        
        # Try finding links using css selectors
        try:
            links = response.css('a[href*="/bookings/"]')
            print(f"Found {len(links)} booking links")
        except Exception as css_e:
            print(f"Error using css selectors: {css_e}")
            
        # Try to find cloudflare turnstile
        try:
            cf = response.css('#turnstile-wrapper')
            if cf:
                print("Cloudflare Turnstile found!")
        except Exception:
            pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrapling()
