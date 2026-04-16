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

All agent skills live in `../.gemini/skills/` — see [../.gemini/GEMINI.md](../.gemini/GEMINI.md) for the entry point.

Key skills:
- **repo-conventions/** — Rules, safe refactoring, secrets management, schema changes
- **county-scraper-builder/** — Step-by-step new scraper guide
- **scraper-debugger/** — Troubleshooting playbook
- **systematic-debugging/** — 4-phase root cause analysis
- **testing-guide/** — Parser tests, fixtures, TDD patterns
- **self-improving-agent/** — Post-task learning loop

## Consolidated Reference

These docs were consolidated during the March 2026 repo restructuring:

| Old File(s) | → Consolidated Into |
|-------------|---------------------|
| `DEPLOYMENT.md` + `DEPLOYMENT_GUIDE.md` + `PRODUCTION_READY_GUIDE.md` + `CREDENTIALS_GUIDE.md` | `docs/DEPLOYMENT.md` |
| `COUNTY_SCRAPER_STATUS.md` + `COUNTY_STATUS.md` | `docs/COUNTY_REGISTRY.md` |
| `SCHEMA.md` (root) | `docs/SCHEMA.md` |
| `ARCHITECTURE.md` (root) | `docs/ARCHITECTURE.md` |
| `LOCAL_SCRAPER_GUIDE.md` + `QUICK_START.md` | `docs/QUICKSTART.md` |
| `SCRAPING_RULES.md` | `.gemini/skills/repo-conventions/` |
| `SECURITY.md` | `.gemini/skills/repo-conventions/` |
| `STEALTH_IMPLEMENTATION.md` | `docs/STEALTH_PLAYBOOK.md` |
| `TROUBLESHOOTING.md` | `.gemini/skills/scraper-debugger/` |
| `DEVELOPMENT.md` | `docs/CONTRIBUTING.md` |
