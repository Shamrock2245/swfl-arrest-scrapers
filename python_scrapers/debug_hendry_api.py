import json
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def on_response(response):
            if response.request.resource_type in ["fetch", "xhr"]:
                if "json" in response.headers.get("content-type", "") and "paginatedBlog" in response.url:
                    try:
                        data = response.json()
                        with open("debug_hendry_api.json", "w") as f:
                            json.dump(data, f, indent=2)
                        print("✅ Dumped JSON to debug_hendry_api.json")
                    except Exception as e:
                        print("Failed to parse JSON:", e)
        
        page.on("response", on_response)
        page.goto("https://www.hendrysheriff.org/inmateSearch", wait_until="networkidle")
        
        try:
            page.wait_for_selector('.chakra-card', state='attached', timeout=10000)
        except:
            pass
            
        browser.close()

if __name__ == "__main__":
    run()
