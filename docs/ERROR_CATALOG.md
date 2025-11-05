
---

## `/docs/ERROR_CATALOG.md`

```markdown
# Error Catalog

| Code | Description | Resolution |
|------|--------------|-------------|
| `E_EMPTY` | Scraper returned 0 rows | Check selectors or table path |
| `E_CLOUDFLARE` | Cloudflare challenge | Enable Worker proxy or cookies |
| `E_403` | Blocked request | Change UA, reduce freq |
| `E_SHEET_PERM` | No Sheet access | Share with service account |
| `E_PARSE_DATE` | Invalid date | Adjust regex or dateFormat |
| `E_SIGNNOW` | Packet generation failed | Retry with logged payload |
