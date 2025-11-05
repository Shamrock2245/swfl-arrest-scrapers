
---

## `/docs/COUNTY_ADAPTER_TEMPLATE.md`
```markdown
# County Adapter Template

> Copy this file to start a new county.

## 1) Scraper
- File: `scrapers/<county>.js`
- Must:
  - Visit list URL, paginate or export.
  - Write raw files to `fixtures/<county>/latest/` (optional).
  - Return objects with at least: `booking_id`, `full_name_last_first`, `arrest_date`, `booking_date`, `source_url`, `county`.

## 2) Mapping
- Update `config/counties.json` with:
  - `listUrl`, `detailUrl` (optional), `selectors` or `export` flags.
  - `dateFormats`, currency rules, text cleanup patterns.

## 3) Normalize
- Ensure `normalize.js` converts county’s fields → unified schema.
- Compute `qualified_score`.

## 4) Test
- Save HTML fixture(s) in `fixtures/<county>/`.
- `npm run run:<county>` should produce ≥1 row.

## 5) Register in Orchestration
- Add to `jobs/runAll.js` order and schedule.

## 6) Done Checklist
- [ ] Pulls rows in local test
- [ ] Keys correct (no duplicates)
- [ ] Required fields filled
- [ ] Dashboard shows qualified (if any)
