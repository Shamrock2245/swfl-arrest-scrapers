from DrissionPage import ChromiumPage, ChromiumOptions
import time

def diagnose():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        print("Navigating to list page...")
        page.get("https://manatee-sheriff.revize.com/bookings")
        time.sleep(5)
        
        # Get first link
        link = page.ele('xpath://a[contains(@href, "/bookings/")]')
        if not link:
            print("No links found on list page.")
            with open("manatee_list.html", "w") as f:
                f.write(page.html)
            return
            
        href = link.attr('href')
        print(f"Found link: {href}")
        
        if not href.startswith('http'):
            href = f"https://manatee-sheriff.revize.com{href}"
            
        print(f"Navigating to detail page: {href}")
        page.get(href)
        time.sleep(3)
        
        with open("manatee_detail.html", "w") as f:
            f.write(page.html)
            
        print("Saved manatee_detail.html")
        
        # Try to print some text dump to see structure
        print("\n--- PAGE TEXT DUMP ---")
        print(page.ele('tag:body').text[:1000])
        print("----------------------")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        page.quit()

if __name__ == "__main__":
    diagnose()
