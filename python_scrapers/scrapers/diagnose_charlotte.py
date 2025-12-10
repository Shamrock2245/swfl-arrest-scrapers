from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys

def diagnose():
    co = ChromiumOptions()
    co.headless(False)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    page = ChromiumPage(co)
    
    url = 'https://inmates.charlottecountyfl.revize.com/bookings'
    print(f"Navigating to {url}...")
    page.get(url)
    
    # Cloudflare Check
    for i in range(15):
        time.sleep(2)
        title = page.title
        print(f"[{i}] Title: {title}")
        
        if "just a moment" not in title.lower() and "security" not in title.lower():
            links = page.eles('tag:a')
            if len(links) > 10:
                print("Cloudflare cleared!")
                break
    
    print("\n--- Detail Page Test ---")
    
    links = page.eles('tag:a')
    booking_links = [l for l in links if '/bookings/' in (l.attr('href') or '') and not l.attr('href').endswith('bookings')]
    
    if not booking_links:
        print("No booking links to test.")
        return

    # test 1: Click first link
    try:
        l1 = booking_links[0]
        txt1 = l1.text
        url1 = l1.attr('href')
        print(f"Testing CLICK on {txt1} ({url1})...")
        
        # Scroll to view
        # page.scroll.to_ele(l1) # Sometimes DrissionPage scroll is finicky if ele is hidden
        l1.click(by_js=True) # Force JS click
        time.sleep(5)
        print(f"Post-Click Title: {page.title}")
        
        if page.ele('#bookings-table') or page.ele('text:Charges') or page.ele('text:Bond'):
            print("✅ Data found via CLICK")
        else:
            print("❌ Data MISSING via CLICK")
            with open('debug_click_fail.html', 'w') as f: f.write(page.html)
            
        page.back()
        time.sleep(3)
        print("Back at list.")
    except Exception as e:
        print(f"❌ Click test failed entirely: {e}")
        # Ensure we go back to list if we navigated
        if '/bookings/' in page.url and not page.url.endswith('/bookings'):
             page.back()
    
    # Refresh links after backup
    links = page.eles('tag:a')
    booking_links = [l for l in links if '/bookings/' in (l.attr('href') or '') and not l.attr('href').endswith('bookings')]
    
    # test 2: Direct GET
    if len(booking_links) > 1:
        try:
            l2 = booking_links[1]
            txt2 = l2.text
            url2 = l2.attr('href')
            if not url2.startswith('http'):
                url2 = 'https://inmates.charlottecountyfl.revize.com' + url2
                
            print(f"Testing GET on {txt2} ({url2})...")
            page.get(url2)
            time.sleep(5)
            print(f"Post-GET Title: {page.title}")
            
            if page.ele('#bookings-table') or page.ele('text:Charges') or page.ele('text:Bond'):
                print("✅ Data found via GET")
            else:
                print("❌ Data MISSING via GET")
                with open('debug_get_fail.html', 'w') as f: f.write(page.html)
        except Exception as e:
             print(f"❌ GET test failed entirely: {e}")

    print("-----------------")
    page.quit()

if __name__ == "__main__":
    diagnose()
