import json
from scrapling import Fetcher

fetcher = Fetcher()
response = fetcher.get("https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id=0201082895")

with open("test_sarasota_detail.html", "w") as f:
    f.write(response.body.decode('utf-8', errors='ignore'))
print("Saved html")

# Test Name
h1 = response.css('h1.page-title')
print(f"H1 length: {len(h1)}")
if h1:
    print(f"H1 content: {getattr(h1[0], 'text', '')}")

# Test Demographics
label_divs = response.css('div.text-right')
print(f"Label divs found: {len(label_divs)}")
for ld in label_divs:
    key = getattr(ld, 'text', '').replace(':', '').strip()
    val_div = ld.xpath('./following-sibling::*[1]')
    if val_div:
        val = getattr(val_div[0], 'text', '').strip()
        print(f"Key: {key} -> Val: {val}")

# Test Charges
rows = response.css('#data-table tr')
print(f"Charge rows: {len(rows)}")
for r_idx, row in enumerate(rows):
    cells = row.css('td')
    if len(cells) > 6:
        print(f"Row {r_idx} Intake: {getattr(cells[6], 'text', '').strip()}")
