# 🤝 CONTRIBUTING.md — Agent & Human Contribution Guide

> **Whether you're human or AI, this is how we ship code in this repo.**

---

## For AI Agents

### Orientation (Do This First)
```
1. Read docs/IDENTITY.md — understand your role
2. Read docs/RULES.md — understand constraints
3. Read docs/ARCHITECTURE.md — understand the pipeline
4. Read docs/COUNTY_REGISTRY.md — understand the landscape
5. Check docs/MEMORY.md — learn from past mistakes
```

### Complexity Tiers
| Tier | Description | Approval Required? | Examples |
|---|---|---|---|
| **T1** (Trivial) | Config tweak, doc fix, dependency bump | No | Update a user-agent string |
| **T2** (Standard) | Bug fix, selector update, new SmartCOP county | No (if tests pass) | Fix Charlotte selector drift |
| **T3** (Complex) | New county scraper, schema change, infra change | Yes — explain before doing | Build Broward scraper |
| **T4** (Critical) | Architecture change, credential rotation, data migration | Yes — full plan required | MongoDB primary migration |

### Agent Workflow
```
1. IDENTIFY complexity tier
2. READ relevant docs (minimum: IDENTITY + RULES + ARCHITECTURE)
3. CHECK MEMORY.md for prior art
4. PLAN your approach (T3/T4: present plan before coding)
5. IMPLEMENT with tests
6. TEST locally (2+ consecutive idempotent runs)
7. UPDATE docs (MEMORY.md, COUNTY_REGISTRY.md, etc.)
8. COMMIT with conventional message format
```

### What Agents Should NEVER Do
- ❌ Modify credentials or env files without explicit approval
- ❌ Delete data from Google Sheets
- ❌ Push directly to `main` (always use branches)
- ❌ Skip testing to save time
- ❌ Ignore `RULES.md` constraints for "quick fixes"
- ❌ Deploy without monitoring the first 3 runs

---

## For Humans

### Development Setup
```bash
# Clone the repo
git clone https://github.com/Shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers

# For Python scrapers
cd python_scrapers
pip install -r requirements.txt

# For Node.js scrapers
npm install

# Set up environment
cp .env.example .env
# Fill in GOOGLE_SA_KEY_JSON, SLACK_WEBHOOK_URL, GOOGLE_SHEETS_ID
```

### Running Locally
```bash
# Python — single county
python3 python_scrapers/run_charlotte.py

# Node.js — single county
node scrapers/desoto_incremental.js

# Docker — full stack
docker-compose up --build
```

### Branch Naming
```
feature/<county>-scraper        # New county scraper
fix/<county>-selector           # Selector fix
fix/<county>-parsing            # Data parsing fix
chore/update-dependencies       # Dependency updates
docs/<topic>                    # Documentation changes
infra/<change>                  # Infrastructure changes
```

### PR Checklist
Before submitting a PR, verify:
```
□ Tests pass locally
□ 2+ consecutive idempotent runs successful
□ No credentials in committed code
□ Commit messages follow conventional format
□ COUNTY_REGISTRY.md updated (if adding/modifying county)
□ MEMORY.md updated (if resolving an issue)
□ No new `file 2` or `file 3` duplicate artifacts
```

---

## Code Standards

### Python
- **Formatter:** `black` (default settings)
- **Linter:** `flake8` with max line length 120
- **Type hints:** Optional but encouraged for public functions
- **Docstrings:** Required for all classes and public functions
- **Imports:** Standard → Third-party → Local (use `isort`)

### Node.js
- **Style:** ES6+ with `const`/`let` (no `var`)
- **Async:** `async/await` preferred over callbacks
- **Error handling:** Try/catch with specific error types
- **Logging:** Console with structured format `[COUNTY] message`

### Commit Messages
```
<type>(<scope>): <description>

feat(charlotte): add date multi-format parser
fix(sarasota): update selectors for new layout
docs(memory): add Cloudflare bypass lesson
chore(deps): bump DrissionPage to 4.1.0
ci(miami-dade): add scrape workflow
refactor(writer): extract dedup logic to shared util
```

---

## Testing Requirements

### New County Scraper
1. Run locally against live site — verify records extracted
2. Run twice consecutively — verify no duplicates (idempotency)
3. Verify all required schema fields populated
4. Verify Slack notification fires correctly
5. Check `Ingestion_Log` for clean entry

### Selector Fix
1. Download updated HTML fixture
2. Update selectors in solver file
3. Run locally — verify records match expected count
4. Compare output with previous fixture data

### Schema Change
1. Update `config/schema.json`
2. Update `docs/SCHEMA.md`
3. Verify all active scrapers produce valid output
4. Check Sheets tab headers match new schema

---

## Review Checklist (For Reviewers)

| Category | Check |
|---|---|
| **Security** | No credentials in code? `.env` in `.gitignore`? |
| **Idempotency** | Dedup logic uses `County` + `Booking_Number`? |
| **Stealth** | Random delays? User-agent rotation? No brute force? |
| **Error Handling** | Specific catches? Slack alerts on failure? |
| **Data Quality** | Required fields populated? Dates normalized? |
| **Documentation** | COUNTY_REGISTRY updated? MEMORY updated? |
| **Tests** | 2+ idempotent runs verified? |

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
