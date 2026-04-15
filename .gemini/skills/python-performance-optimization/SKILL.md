---
name: python-performance-optimization
description: Performance optimization patterns for Python scraper pipelines — connection pooling, memory efficiency, async I/O, and batch operations for high-throughput data ingestion.
---

# Python Performance Optimization for Scrapers

## Connection Pooling
```python
# Reuse sessions across requests — don't create new connections per page
session = requests.Session()
session.headers.update(HEADERS)
# Session persists TCP connections, cookies, and auth
```

## Memory Efficiency
```python
# Process records in streams, not full lists
def process_records(records):
    for record in records:
        yield normalize(record)  # Generator, not list comprehension

# Use __slots__ for high-volume record objects
class ArrestRecord:
    __slots__ = ['name', 'booking_number', 'dob', 'charges', 'bond']
```

## Batch Google Sheets Writes
```python
# ❌ Bad: One API call per record
for record in records:
    sheet.append_row(record)

# ✅ Good: Batch all records in single API call
sheet.batch_update([{
    'range': f'{tab}!A2',
    'values': [record_to_row(r) for r in records]
}])
```

## Deduplication with Sets
```python
# O(1) lookup instead of O(n) scan
existing_ids = set(sheet.col_values(booking_number_col))
new_records = [r for r in records if r['Booking_Number'] not in existing_ids]
```

## Parallel Scraping (When Safe)
```python
from concurrent.futures import ThreadPoolExecutor

def scrape_detail_page(url):
    return session.get(url, timeout=30).text

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(scrape_detail_page, detail_urls))
```

## Profiling
```bash
# Time the entire pipeline
time python counties/lee/runner.py --days-back 1

# Profile bottlenecks
python -m cProfile -s cumulative counties/lee/runner.py
```

## Key Metrics to Monitor
- Scrape duration (target: <2 min per county)
- Records per run (compare against historical average)
- API quota usage (Sheets API: 300 req/min)
- Memory usage (target: <256MB per scraper)
