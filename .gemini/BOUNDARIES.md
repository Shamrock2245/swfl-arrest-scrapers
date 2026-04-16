# 🚧 BOUNDARIES — What I May and May Not Do

> **This is the guardrail document. When in doubt, check here first.**

---

## ✅ ALWAYS (Non-Negotiable Musts)

### Code Safety
1. **Test before deploying** — Run solver locally with `--dry-run` before any push
2. **Preserve dedup** — `Booking_Number + County` is the composite key. Never change this.
3. **Return `[]` on failure** — Solvers must never return `None`, raise unhandled exceptions, or crash
4. **Log errors to stderr** — `sys.stderr.write()` for progress, never swallow exceptions silently
5. **Use timeouts everywhere** — Every HTTP request, every browser wait, every API call must have a timeout

### Data Safety
6. **Idempotent writes** — Re-running a scraper must never create duplicate rows
7. **Schema compliance** — Every record must conform to the 34-column schema (see `DATA_SCHEMA.md`)
8. **County field is hardcoded** — The `County` field comes from the scraper, never from the source site
9. **Preserve existing data** — Never delete or overwrite rows in Google Sheets
10. **Non-fatal secondary writes** — MongoDB and Slack failures must not crash the pipeline

### Process Safety
11. **One county, one folder** — All county code in `counties/{name}/`, no cross-county imports
12. **Config hierarchy is sacred** — Env vars > county YAML > defaults > global.yaml
13. **Never commit secrets** — No `.env` files, no `creds/`, no API keys in source code
14. **Function name = directory name** — `counties/collier/solver.py` exports `scrape_collier()`
15. **Update docs when changing behavior** — Every structural change must update relevant docs

---

## ❌ NEVER (Hard Prohibitions)

### Code Prohibitions
1. **Never `except: pass`** — Always log the error, even if you continue
2. **Never `time.sleep()` > 30s in a loop** — Use exponential backoff with jitter instead
3. **Never infinite loops without escape** — Always have a max_iterations or timeout
4. **Never import between counties** — `counties/collier/` must never import from `counties/charlotte/`
5. **Never hardcode credentials** — Use `os.getenv()` or config files

### Data Prohibitions
6. **Never delete Google Sheets rows** — Deprecate by clearing values, never delete
7. **Never change column order in Sheets** — Append new columns to the right only
8. **Never scrape non-public data** — Only publicly accessible arrest records
9. **Never store personal data beyond the schema** — No SSNs, no financial data, no victim info
10. **Never bypass login walls** — If a site requires authentication, flag it and move on

### Ethical Prohibitions
11. **Never infer guilt** — We present arrest data, not convictions. No messaging should imply guilt.
12. **Never infer protected-class attributes** — Do not derive religion, sexuality, immigration status, or political affiliation from arrest data for targeting or scoring purposes.
13. **Never contact minors** — If `DOB` indicates under 18, suppress the record entirely. No storage, no outreach.
14. **Never use deceptive messaging** — Do not impersonate law enforcement, courts, government, or other bail agencies. Always identify as Shamrock Bail Bonds.
15. **Never perform private-person lookups** — Only use lawfully approved, publicly accessible sources. No social media stalking, no paid background check services without authorization.

### Operational Prohibitions
16. **Never retry aggressively when blocked** — Makes IP bans worse. Back off.
17. **Never run scrapers faster than configured** — Respect cron schedule and rate limits
18. **Never modify `core/` without testing 2+ counties** — Shared code changes affect everything
19. **Never push to main without local verification** — Test first, push second
20. **Never modify other Shamrock repos** — This agent operates within `swfl-arrest-scrapers` only

---

## ⚠️ REQUIRES APPROVAL (Ask Before Doing)

| Action | Why |
|--------|-----|
| Adding a new column to the schema | Affects ALL counties and downstream systems |
| Changing the dedup key logic | Could create duplicates or miss records |
| Modifying `core/writers/sheets_writer.py` | Affects all county data writes |
| Adding a new dependency to `pyproject.toml` | Must work in Docker + GitHub Actions |
| Changing cron schedule for a county | Affects rate limits and resource usage |
| Pausing a county scraper | May miss arrests during downtime |
| Deploying a new county to production | Requires 72-hour monitoring period first |

---

## 🔒 Safe Modification Zones

### Freely Modifiable (No Approval Needed)
- `counties/{name}/solver.py` — County-specific scraping logic
- `counties/{name}/runner.py` — Universal runner (usually identical)
- `config/counties/{name}.yaml` — County-specific config
- `.gemini/*.md` — Agent documentation
- `docs/*.md` — Human documentation
- Test files and fixtures

### Modify with Care (Test Required)
- `core/*.py` — Shared modules (test 2+ counties after change)
- `config/global.yaml` — System-wide defaults
- `config/counties/_defaults.yaml` — County defaults
- `.github/workflows/*.yml` — CI/CD workflows

### Do Not Touch
- `.env` — Local secrets (git-ignored)
- `creds/` — Service account keys (git-ignored)
- `config/schema.json` — Canonical schema definition
- `config/field_aliases.json` — Field mapping (change via NORMALIZATION.md process)

---

## Rate Limit Rules

| Target | Max Frequency | Backoff |
|--------|---------------|---------|
| Any county website | 1 request per 2 seconds minimum | Exponential with jitter |
| Google Sheets API | 60 requests per minute | 429 → wait 60s, retry |
| Slack webhooks | 1 message per second | Queue and batch |
| MongoDB Atlas | 100 writes per batch | Non-fatal failures |

## Escalation Protocol

When something is outside my boundaries:
1. **Stop** — Don't attempt the action
2. **Document** — Log what I was trying to do and why
3. **Alert** — Post to `LOGBOOK.md` and notify via Slack if urgent
4. **Wait** — Ask the human (Brendan) for guidance

---

## 👤 Human Review Triggers

These situations ALWAYS require human review before proceeding:

| Trigger | Why |
|---------|-----|
| Any outreach message template changes | Legal and brand risk |
| County explicitly requests we stop scraping | Legal compliance |
| Record involving a minor (under 18) | Absolute prohibition |
| Federal charge or ICE hold | Different jurisdiction, cannot bond |
| Duplicate spike (>20% of run) | Possible parser bug or site change |
| Empty results from a previously-working county | Site may have redesigned |
| New county deployment to production | Requires 72hr burn-in |
| Any schema change (column add/remove/rename) | Affects all downstream systems |
| Complaint from a contacted individual | Suppression + process review |
