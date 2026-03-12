# {COUNTY_NAME} County Scraper

| Field | Value |
|-------|-------|
| **Status** | 🔴 Not Implemented |
| **Stack** | Python (DrissionPage) |
| **Site URL** | {SITE_URL} |
| **Pagination** | {PAGINATION_TYPE} |
| **Cloudflare** | Yes / No |
| **Has API** | Yes / No |
| **CMS Platform** | Unknown |
| **Cron Schedule** | `{CRON}` |
| **Last Verified** | YYYY-MM-DD |
| **Owner** | TBD |

## Quick Run
```bash
python scripts/run_county.py {county_name} --days-back 3
```

## Onboarding Checklist
- [ ] Confirm jail site URL works
- [ ] Determine pagination type
- [ ] Determine anti-bot protections
- [ ] Implement `solver.py`
- [ ] Save fixtures (listing + detail HTML)
- [ ] Create `expected_output.json` fixture
- [ ] Write parser test
- [ ] Document quirks in `quirks.md`
- [ ] Create county config in `config/counties/{county_name}.yaml`
- [ ] Create GitHub Actions workflow
- [ ] Run end-to-end test
- [ ] Update `docs/COUNTY_STATUS.md`

## Notes
- {Any initial notes about this county}
