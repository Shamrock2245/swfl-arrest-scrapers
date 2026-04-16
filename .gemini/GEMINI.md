# SWFL Arrest Scrapers — Agent Context

## Mission
Build and maintain a **67-county Florida arrest scraping network** that feeds real-time booking data into the Shamrock Bail Bonds lead pipeline. Currently at **24 counties active** (36% coverage). Every new county directly increases revenue and geographic reach.

Lee County is handled by the GAS internal scraper (in `shamrock-bail-portal-site/backend-gas/`), not this repo. It has a config here for reference only.

---

## Quick Navigation

### Agent Brain (`.gemini/`)
| File | Purpose |
|------|---------|
| [IDENTITY.md](IDENTITY.md) | Who I am, my mission, my personality |
| [SYSTEM.md](SYSTEM.md) | Full system architecture & topology |
| [AGENTS.md](AGENTS.md) | Digital workforce roster (9 agents) |
| [BOUNDARIES.md](BOUNDARIES.md) | What I may and may not do |
| [TOOLS.md](TOOLS.md) | Technology & tool ecosystem |
| [STATE.md](STATE.md) | Current operational state (live snapshot) |
| [HEARTBEAT.md](HEARTBEAT.md) | System health pulse & SLOs |
| [MEMORY.md](MEMORY.md) | Learned patterns & county quirks |
| [TASKS.md](TASKS.md) | Active task queue |
| [USER.md](USER.md) | Operator profile & preferences |
| [REFLECTION.md](REFLECTION.md) | Self-assessment & improvement |
| [LOGBOOK.md](LOGBOOK.md) | Chronological activity log |

### Technical Reference (`docs/`)
| File | Purpose |
|------|---------|
| [DATA_SCHEMA.md](../docs/DATA_SCHEMA.md) | 34-column universal arrest record schema |
| [SOURCES.md](../docs/SOURCES.md) | Master 67-county reference (URLs, stacks, status) |
| [NORMALIZATION.md](../docs/NORMALIZATION.md) | Field mapping & data cleanup rules |
| [SCORING.md](../docs/SCORING.md) | Lead scoring algorithm (0-100) |
| [QUEUE.md](../docs/QUEUE.md) | 6-stage pipeline: scrape → notify |
| [SCRAPING_RULES.md](../docs/SCRAPING_RULES.md) | Legal/ethical scraping + anti-detection |
| [OUTREACH_RULES.md](../docs/OUTREACH_RULES.md) | Contact workflow & messaging rules |
| [COMPLIANCE.md](../docs/COMPLIANCE.md) | Legal, privacy, data handling |
| [ERRORS_AND_RECOVERY.md](../docs/ERRORS_AND_RECOVERY.md) | Error codes & recovery playbooks |
| [SECRETS.md](../docs/SECRETS.md) | Credential handling & security |
| [CHANGELOG.md](../docs/CHANGELOG.md) | Scraper network history |
| [ROADMAP.md](../docs/ROADMAP.md) | Strategic expansion plan |

### Skills (`.gemini/skills/`)
| Skill | Purpose |
|-------|---------|
| `self-improving-agent/` | Post-task learning loop with multi-memory architecture |
| `county-scraper-builder/` | New county setup guide, naming conventions, checklist |
| `scraper-debugger/` | 7 common failure modes, diagnostic procedures |
| `county-expansion/` | 67-county roadmap, site recon, lead analysis strategy |
| `repo-conventions/` | Non-negotiable rules, safe refactoring, config hierarchy |
| `testing-guide/` | Parser tests, fixture guidelines, TDD patterns |
| `systematic-debugging/` | 4-phase root cause analysis |
| `verification-before-completion/` | Evidence before claims |
| `harden/` | Anti-bot, network resilience, edge cases |
| `python-performance-optimization/` | Connection pooling, batch writes, profiling |
| `github-actions-docs/` | Workflow writing, cron scheduling, CI/CD |
| `playwright-scraping/` | DrissionPage/Playwright anti-bot patterns |
| `playwright-cli/` | Browser automation CLI commands |
| `google-sheets-integration/` | 34-col schema, dedup, Sheets API patterns |
| `gws-sheets/` | Google Sheets API v4 reference |

---

## Pipeline Architecture
```
County Jail Website → solver.py (scrape) → runner.py (pipeline)
    → Google Sheets (34-col arrest row)
    → MongoDB Atlas (via Cloud Functions proxy)
    → Slack (#new-arrests-{county})
```

## Critical Conventions
1. **Function name = directory name**: `counties/collier/solver.py` MUST export `scrape_collier()`
2. **Return a list**: Solver functions MUST `return records` (list of dicts), never `print()`
3. **Parameters**: Always accept `days_back=7, max_pages=10` kwargs
4. **Dedup key**: `Booking_Number` + `County` — both required in every record
5. **Error handling**: Return `[]` on failure, never `None` or raise unhandled exceptions

## Environment Variables
```
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=creds/service-account-key.json
SLACK_WEBHOOK_URL=<from secrets>
TZ=America/New_York
```
