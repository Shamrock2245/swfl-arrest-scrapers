# 🔍 Debugging Scrapers

## Symptom → Diagnosis Flowchart

### 1. Scraper returns 0 records
```
Did the page load?
├── No → Check site URL manually. Try: page.get(URL), check page.title
│   ├── 403/503 → ScraperBlocked (Cloudflare, IP ban)
│   ├── Connection refused → SiteDown
│   └── Page loads but wrong content → URL changed, check quirks.md
├── Yes → Check selectors
│   ├── Elements not found → Site redesigned, update selectors
│   ├── Elements found but empty → Check JavaScript rendering
│   └── Elements found with data → Check pagination logic
```

### 2. Scraper returns records but Sheets has no new rows
```
Check the writer log
├── "Duplicate" messages → Records already exist (expected behavior)
├── "Auth error" → Check GOOGLE_SERVICE_ACCOUNT_KEY_PATH
├── "Sheet not found" → Check sheet_name in county config
├── No write attempted → Check writers.sheets_enabled in config
```

### 3. Cloudflare blocks the scraper
```
1. Check if the site actually uses Cloudflare: curl -I {site_url}
2. Try increasing the wait: config cloudflare wait > 20s
3. Try disabling headless mode: headless: false
4. Check if you're being rate limited (too fast)
5. Try a different user-agent
```

### 4. Scraper works locally but fails in CI
```
1. Docker environment differs from local
2. Check Chrome/Chromium version in Docker vs local
3. Check headless mode (CI should always be headless)
4. Check environment variables are set in GitHub Secrets
5. Network restrictions in CI environment
```

## Debugging Commands
```bash
# Run with verbose logging
python scripts/run_county.py charlotte --dry-run 2>&1 | tee debug.log

# Test just the solver
python -c "from counties.charlotte.solver import scrape; from core.config_loader import load_config; print(scrape(load_config('charlotte')))"

# Check if a site is up
curl -I https://inmates.charlottecountyfl.revize.com/bookings

# View recent logs
cat logs/charlotte/$(date +%Y-%m-%d).jsonl | python -m json.tool
```

## Common Fixes

| Problem | Fix |
|---------|-----|
| Cloudflare not clearing | Increase `max_wait` in stealth config, try non-headless |
| SSL certificate error | Update Chrome, add `--ignore-certificate-errors` |
| Element not found | Site redesigned — update selectors in solver.py |
| Timeout | Increase `page_load_timeout_seconds` in config |
| Rate limited | Increase `rate_limit_delay_seconds` |
| Memory crash | Reduce `max_pages`, add `page.quit()` between detail pages |
| Date parse error | Add the new date format to `core/normalizer.py` |

## When to Escalate
- Site requires CAPTCHA solving → needs human review
- Site now requires login → architecture change needed
- IP permanently banned → needs proxy rotation setup
- Schema changed fundamentally → needs `.agent/SCHEMA_CHANGES.md` process
