# 📚 Documentation Index

## For Engineers

| Document | Contents |
|----------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow diagrams, interface contracts, concurrency model |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Docker setup, GitHub Actions, environment variables, credentials guide |
| [SCHEMA.md](SCHEMA.md) | 39-column universal schema, field types, scoring rubric |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Code style, PR process, testing requirements |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [QUICKSTART.md](QUICKSTART.md) | First-run setup in under 5 minutes |

## For Operations

| Document | Contents |
|----------|----------|
| [OPERATIONS.md](OPERATIONS.md) | County registry, scraper health monitoring, alerting |
| [COUNTY_REGISTRY.md](COUNTY_REGISTRY.md) | Per-county status, URLs, schedule, quirks |
| [STEALTH_PLAYBOOK.md](STEALTH_PLAYBOOK.md) | Anti-bot techniques, Cloudflare bypass, detection avoidance |
| [ROADMAP.md](ROADMAP.md) | Feature roadmap, 67-county expansion plan |

## For AI Agents

All agent instruction files live in `../.agent/` — see [../.agent/IDENTITY.md](../.agent/IDENTITY.md) for the entry point.

Key files:
- **RULES.md** — What you can and cannot modify
- **ADDING_A_COUNTY.md** — Step-by-step new scraper guide
- **DEBUGGING_SCRAPERS.md** — Troubleshooting playbook
- **SECRETS_AND_CONFIG.md** — How to handle env vars and credentials
- **SCHEMA_AND_COLUMNS.md** — Column contract and validation rules

## Consolidated Reference

These docs were consolidated during the March 2026 repo restructuring:

| Old File(s) | → Consolidated Into |
|-------------|---------------------|
| `DEPLOYMENT.md` + `DEPLOYMENT_GUIDE.md` + `PRODUCTION_READY_GUIDE.md` + `CREDENTIALS_GUIDE.md` | `docs/DEPLOYMENT.md` |
| `COUNTY_SCRAPER_STATUS.md` + `COUNTY_STATUS.md` | `docs/COUNTY_REGISTRY.md` |
| `SCHEMA.md` (root) | `docs/SCHEMA.md` |
| `ARCHITECTURE.md` (root) | `docs/ARCHITECTURE.md` |
| `LOCAL_SCRAPER_GUIDE.md` + `QUICK_START.md` | `docs/QUICKSTART.md` |
| `SCRAPING_RULES.md` | `.agent/RULES.md` |
| `SECURITY.md` | `.agent/SECRETS_AND_CONFIG.md` |
| `STEALTH_IMPLEMENTATION.md` | `docs/STEALTH_PLAYBOOK.md` |
| `TROUBLESHOOTING.md` | `.agent/DEBUGGING_SCRAPERS.md` |
| `DEVELOPMENT.md` | `docs/CONTRIBUTING.md` |
