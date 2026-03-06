import time
from scrapling import Fetcher

fetcher = Fetcher()

print("Fetching index.php...")
r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')

# print all forms and inputs
forms = r1.css('form')
print(f"Forms found: {len(forms)}")

for i, f in enumerate(forms):
    print(f"\nForm {i} action: {f.attrib.get('action')}")
    inputs = f.css('input, select')
    for inp in inputs:
        print(f"  Input: name='{inp.attrib.get('name')}', type='{inp.attrib.get('type')}', value='{inp.attrib.get('value', '')}'")
