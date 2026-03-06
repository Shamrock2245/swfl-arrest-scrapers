from playwright.sync_api import sync_playwright
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    def handle_response(response):
        if "api" in response.url.lower() or "inmate" in response.url.lower() or "search" in response.url.lower():
            print(f"[{response.status}] {response.request.method} {response.url}")
            if "application/json" in response.headers.get("content-type", ""):
                print("JSON Payload Start:", response.text()[:200])

    page.on("response", handle_response)
    print("Navigating to Hendry...")
    page.goto("https://www.hendrysheriff.org/inmateSearch", wait_until="networkidle")
    print("Waiting 10s for data to load...")
    time.sleep(10)
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
