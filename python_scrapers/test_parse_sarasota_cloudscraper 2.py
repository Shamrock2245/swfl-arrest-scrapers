import sys
try:
    import cloudscraper
except ImportError:
    print("cloudscraper not installed")
    sys.exit(1)

scraper = cloudscraper.create_scraper()

print("Fetching index.php...")
r1 = scraper.get('https://cms.revize.com/revize/apps/sarasota/index.php')
print(f"Status: {r1.status_code}")

print("\nFetching viewInmate.php...")
r2 = scraper.get('https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id=0201029792%20%20%20%20%20')
print(f"Status: {r2.status_code}")

if r1.status_code == 403 or r2.status_code == 403:
    print("Cloudflare still blocking cloudscraper.")
