# 📚 Documentation Index

## Data Pipeline

| Document | Contents |
|----------|----------|
| [DATA_SCHEMA.md](DATA_SCHEMA.md) | 34-column universal arrest record schema, validation, lifecycle |
| [SOURCES.md](SOURCES.md) | Master 67-county reference — URLs, stacks, status, expansion waves |
| [NORMALIZATION.md](NORMALIZATION.md) | Field alias mapping, value standardization rules |
| [SCORING.md](SCORING.md) | Lead qualification algorithm (0-100 scoring rubric) |
| [QUEUE.md](QUEUE.md) | 6-stage pipeline: scrape → normalize → score → dedup → store → notify |

## Scraping & Compliance

| Document | Contents |
|----------|----------|
| [SCRAPING_RULES.md](SCRAPING_RULES.md) | Legal/ethical scraping rules, anti-detection, rate limits |
| [OUTREACH_RULES.md](OUTREACH_RULES.md) | Contact workflow rules, messaging timing, drip campaign limits |
| [COMPLIANCE.md](COMPLIANCE.md) | Florida public records law, TCPA, 10DLC, data retention, opt-outs |
| [SECRETS.md](SECRETS.md) | Credential handling, rotation, masking, incident response |

## Operations & Recovery

| Document | Contents |
|----------|----------|
| [ERRORS_AND_RECOVERY.md](ERRORS_AND_RECOVERY.md) | Error code catalog, 6 recovery playbooks, auto-recovery rules |
| [CHANGELOG.md](CHANGELOG.md) | Scraper network history, source breakages |
| [ROADMAP.md](ROADMAP.md) | Strategic 67-county expansion plan |

## Engineering

| Document | Contents |
|----------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow diagrams, repo layout |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Docker setup, GitHub Actions, environment variables |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Code style, PR process, testing requirements |
| [QUICKSTART.md](QUICKSTART.md) | First-run setup in under 5 minutes |
| [GLOSSARY.md](GLOSSARY.md) | Term definitions |

## For AI Agents

The complete agent brain lives in `../.gemini/` — see [GEMINI.md](../.gemini/GEMINI.md) for the master index.

12 agent context files + 15 specialized skills covering identity, boundaries, memory, task tracking, and self-improvement.
