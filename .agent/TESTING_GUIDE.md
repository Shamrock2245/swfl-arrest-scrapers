# 🧪 Testing Guide

## Test Structure
```
tests/
├── unit/           ← Tests for core/ modules
├── parsers/        ← Per-county parser tests (fixture-based)
├── integration/    ← Pipeline tests
├── smoke/          ← Site reachability checks
└── regression/     ← Tests for known past issues
```

## Running Tests
```bash
# All tests
pytest tests/

# Just unit tests
pytest tests/unit/

# Just parser tests for one county
pytest tests/parsers/test_charlotte.py

# Smoke tests (actually hits the sites — use sparingly)
pytest tests/smoke/ -v
```

## Writing a Parser Test
Every county should have a parser test that uses saved HTML fixtures:

```python
# tests/parsers/test_charlotte.py
import json
from pathlib import Path

FIXTURES = Path(__file__).parent.parent.parent / "counties" / "charlotte" / "fixtures"

def test_parse_listing():
    """Verify we can extract booking links from a listing page."""
    html = (FIXTURES / "listing_page.html").read_text()
    # Import the parsing function from the solver
    from counties.charlotte.solver import parse_listing
    links = parse_listing(html)
    assert len(links) > 0
    assert all(link.startswith("http") for link in links)

def test_parse_detail():
    """Verify we can extract fields from a detail page."""
    html = (FIXTURES / "detail_page.html").read_text()
    expected = json.loads((FIXTURES / "expected_output.json").read_text())
    from counties.charlotte.solver import parse_detail
    record = parse_detail(html)
    assert record["Booking_Number"] == expected["Booking_Number"]
    assert record["Full_Name"] == expected["Full_Name"]
```

## Writing a Unit Test
```python
# tests/unit/test_normalizer.py
from core.normalizer import normalize_bond_amount, normalize_date

def test_bond_amount_parsing():
    assert normalize_bond_amount("$5,000.00") == "5000.0"
    assert normalize_bond_amount("5000") == "5000.0"
    assert normalize_bond_amount("") == "0"
    assert normalize_bond_amount(None) == "0"

def test_date_normalization():
    assert normalize_date("03/15/2024") == "2024-03-15"
    assert normalize_date("2024-03-15") == "2024-03-15"
    assert normalize_date("") == ""
```

## Smoke Test Template
```python
# tests/smoke/test_sites_reachable.py
import requests

SITES = {
    "charlotte": "https://inmates.charlottecountyfl.revize.com/bookings",
    "collier": "https://www2.colliersheriff.org/arrestsearch/Report.aspx",
}

def test_sites_respond():
    for county, url in SITES.items():
        resp = requests.get(url, timeout=15)
        assert resp.status_code < 500, f"{county} returned {resp.status_code}"
```

## Fixture Guidelines
- Save FULL HTML pages, not fragments
- Include at least 3 sample records in listing fixtures
- Include all field variations in detail fixtures (empty bonds, multiple charges, etc.)
- Name files: `listing_page.html`, `detail_page.html`, `expected_output.json`
- **NEVER** include real personal information — redact names, DOBs, etc.
