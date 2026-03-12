# ❌ Error Catalog

Known errors and their fixes. Add new entries as you encounter them.

## Scraper Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ScraperBlocked: Cloudflare did not clear` | Cloudflare JS challenge didn't resolve | Increase `max_wait`, try non-headless, add delay |
| `SiteDown: Connection refused` | Jail site is offline | Wait and retry. Check site manually |
| `ParseError: Element not found` | Site HTML changed or redesigned | Update selectors in solver.py |
| `TimeoutError: Page load timed out` | Slow site or network | Increase `page_load_timeout_seconds` in config |
| `SchemaValidationError: Missing Booking_Number` | Solver didn't extract booking number | Fix parsing logic in solver.py |

## Writer Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `WriterError: 403 on Sheets API` | Bad service account credentials | Check `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` |
| `WriterError: Sheet not found` | Wrong `sheet_name` in county config | Update county YAML config |
| `DuplicateRecordError` | Record already exists in sheet | Expected behavior — not a bug |

## CI/CD Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'DrissionPage'` | Dependency not installed | Check `pyproject.toml` includes it |
| `Chrome process crashed` | Docker needs `--no-sandbox` | Verify `core/browser.py` sets this flag |
| `GitHub Actions timeout` | Scraper ran too long | Reduce `max_pages` or `days_back` |

## Configuration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ConfigError: County config not found` | Missing YAML file | Create `config/counties/{county}.yaml` |
| `KeyError: 'search_url'` | County config missing required field | Add field to county YAML |
