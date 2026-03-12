# 🆕 Adding a New County Scraper — Step by Step

## Pre-Work
1. Confirm the jail website URL is live and publicly accessible
2. Determine: pagination type, anti-bot protections, CMS platform
3. Check if the site requires JavaScript rendering

## Steps

### 1. Copy the Template
```bash
cp -r counties/_template counties/{county_name}
```

### 2. Create County Config
Create `config/counties/{county_name}.yaml`:
```yaml
name: {County Name}
code: {COUNTY_CODE}
sheet_name: {County Name}
base_url: "https://..."
search_url: "https://..."
pagination_type: links  # or: form_submit, date_iteration, roster, api
cloudflare_protected: false
schedule_cron: "0 7,13,19,1 * * *"
notes: "Brief description of the site"
```

### 3. Implement `solver.py`
Open `counties/{county_name}/solver.py` and:
- Replace the TODOs with real scraping logic
- Use `core.browser.create_browser(config)` for the browser
- Use `core.stealth.wait_for_cloudflare(page)` if Cloudflare-protected
- Return a list of raw dicts (one per booking)
- Each dict MUST include at minimum: `Booking_Number`, `Full_Name`, `County`

### 4. Update `runner.py`
Edit `counties/{county_name}/runner.py`:
- Change the import: `from counties.{county_name}.solver import scrape`
- Change `COUNTY_NAME = "{county_name}"`

### 5. Save Test Fixtures
Save sample HTML in `counties/{county_name}/fixtures/`:
- `listing_page.html` — the search results / roster page
- `detail_page.html` — a single booking detail page
- `expected_output.json` — expected parsed records from the fixture

### 6. Write Parser Test
Create `tests/parsers/test_{county_name}.py`:
```python
import json
from pathlib import Path

FIXTURES = Path(__file__).parent.parent.parent / "counties" / "{county_name}" / "fixtures"

def test_parse_detail():
    with open(FIXTURES / "detail_page.html") as f:
        html = f.read()
    with open(FIXTURES / "expected_output.json") as f:
        expected = json.load(f)
    # Parse html and compare to expected
    # ...
```

### 7. Test End-to-End
```bash
python scripts/run_county.py {county_name} --dry-run --days-back 1
```

### 8. Document
- Update `counties/{county_name}/README.md` with real status and details
- Fill in `counties/{county_name}/quirks.md` with site-specific notes
- Update `docs/COUNTY_STATUS.md`

### 9. Create GitHub Actions Workflow
Create `.github/workflows/scrape_{county_name}.yml` (copy from an existing one, update county name)

### 10. Create `__init__.py`
```bash
touch counties/{county_name}/__init__.py
```

## Checklist
- [ ] County folder exists with all files
- [ ] Config YAML exists
- [ ] `solver.py` implements real scraping logic
- [ ] `runner.py` imports updated
- [ ] Fixtures saved
- [ ] Parser test written and passing
- [ ] `--dry-run` completes without error
- [ ] `README.md` and `quirks.md` filled in
- [ ] GitHub Actions workflow created
- [ ] `docs/COUNTY_STATUS.md` updated
