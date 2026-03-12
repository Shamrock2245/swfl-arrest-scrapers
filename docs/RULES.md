# 🛡️ RULES.md — Governance, Guardrails & Protocols

> **These rules are non-negotiable. Breaking any Prime Directive is a critical incident.**

---

## Prime Directives

### 1. Idempotency Is Sacred
All writers must check for existing records using the composite key: **`County` + `Booking_Number`** (or equivalent unique agency ID).

| Scenario | Action |
|---|---|
| Record does not exist | **Insert** as new row |
| Record exists, data unchanged | **Skip** — do nothing |
| Record exists, data changed | **Update** in place |
| Record exists, should be removed | **Never delete** — mark as archived |

> ⚠️ **NEVER insert duplicate rows. NEVER delete existing data. NEVER truncate a sheet tab.**

### 2. Data Completeness > Schema Rigidity
The 34-column schema is a **baseline**, not a ceiling.

- Scrapers must extract **ALL** available data that each county provides
- If a county provides fields beyond the 34 columns, **append new columns** to that county's sheet
- Normalize common fields (Name, Booking Number, DOB, Charges, Mugshot) where possible
- **Priority order:** Capture everything → Normalize what you can → Score what's scorable

### 3. Stealth First
All scrapers must assume hostile environments.

| Stack | Required Stealth |
|---|---|
| Python (Primary) | `DrissionPage` with anti-detection defaults |
| Node.js (Legacy) | `puppeteer-extra-plugin-stealth` |
| Direct HTTP | `curl_cffi` or `cloudscraper` — never raw `requests` against protected sites |

**Mandatory evasion techniques:**
- Random delays between requests (2–8 seconds, jittered)
- User-agent rotation from a curated pool
- No more than 3 concurrent requests to the same domain
- Respect `robots.txt` rate limits where specified
- Never brute-force past a CAPTCHA — escalate or use a solver

### 4. Credential Safety
**NEVER expose, log, output, print, or commit any of these:**

| Secret | Storage Location |
|---|---|
| `GOOGLE_SA_KEY_JSON` | `.env` file / GH Actions secrets |
| `SLACK_WEBHOOK_URL` | `.env` file / GH Actions secrets |
| `SIGNNOW_TOKEN` | Wix Secrets Manager / GAS Script Properties |
| `GOOGLE_SHEETS_ID` | `.env` file (not a secret, but treat as internal) |
| Any API key | Environment variables only |

**Rules:**
- `.env` is in `.gitignore`. If it's not, **stop everything and fix it.**
- Never log full request/response bodies that may contain credentials
- Never hardcode credentials in source files — even temporarily
- Use `os.getenv()` (Python) or `process.env` (Node.js) exclusively

### 5. Fail Loud, Recover Quietly
- **On failure:** Log the error with full context, alert Slack, increment error counter
- **On recovery:** Retry automatically using backoff, log success, clear error state
- **On persistent failure:** Escalate to Slack with `@channel` after 3 consecutive failures

### 6. One County's Failure Must Never Cascade
Each county scraper runs in isolation. If Charlotte breaks, Hillsborough must still run. Design accordingly:
- No shared state between county scrapers
- No shared browser instances between counties
- Catch all exceptions at the county level — log and continue

---

## Guardrails & Limits

### Rate Limits
| Resource | Limit | Enforcement |
|---|---|---|
| Google Sheets API | 300 requests/min | Batch writes, exponential backoff |
| Per-county scrape interval | ≥15 minutes | GitHub Actions cron schedule |
| Concurrent browser instances | ≤3 | Sequential execution in Docker |
| Per-page request delay | 2–8 seconds (jittered) | `time.sleep(random.uniform(2, 8))` |
| Max scrape duration per county | 10 minutes | Timeout kill after 600s |

### Memory Budgets
| Environment | Max RAM per scraper | Max total |
|---|---|---|
| GitHub Actions | 4GB (shared runner) | 7GB total |
| Docker (local) | 1GB per container | Set via `docker-compose.yml` |
| macOS (dev) | No hard limit | Be reasonable |

### Timeout Maximums
| Operation | Timeout | Action on Timeout |
|---|---|---|
| Page load | 30 seconds | Log `E_TIMEOUT`, skip page |
| Element wait | 15 seconds | Log `E_SELECTOR`, try fallback |
| Full county scrape | 10 minutes | Kill process, alert Slack |
| Sheets write | 30 seconds | Retry once, then log `E_SHEET_TIMEOUT` |

---

## Protocols

### When Blocked by Anti-Bot (Cloudflare/CAPTCHA)
```
1. DO NOT brute force. Stop immediately.
2. Check MEMORY.md for known workarounds for this county.
3. Try switching from headless to headful mode.
4. If still blocked, escalate via Slack (#scraper-alerts).
5. File an entry in MEMORY.md with what you learned.
6. Consider reducing scrape frequency for this county.
```

### When Selectors Change (0 Records Returned)
```
1. Save the current page HTML to fixtures/ for offline debugging.
2. Compare with the previous fixture (if available) to identify changes.
3. Update selectors in the solver file.
4. Test locally: python3 python_scrapers/run_<county>.py
5. Verify records appear in the correct sheet tab.
6. Update MEMORY.md with the selector change details.
7. Commit with message: "fix(<county>): update selectors for site redesign"
```

### When a County Goes Offline
```
1. Confirm the site is actually down (not just our IP being blocked).
2. Set county status to "PAUSED" in COUNTY_REGISTRY.md.
3. Alert Slack with expected downtime if known.
4. Do NOT remove the scraper code — sites come back.
5. Set up a daily health check to detect when the site returns.
```

### When Adding a New County
```
1. Read COUNTY_REGISTRY.md to understand the county's tech stack.
2. Read COUNTY_ADAPTER_TEMPLATE.md for the boilerplate.
3. Create solver + runner files.
4. Test locally with at least 2 consecutive runs (verify idempotency).
5. Create GitHub Actions workflow from template.
6. Add county to COUNTY_REGISTRY.md with status "BETA".
7. Monitor for 72 hours before promoting to "STABLE".
```

---

## Escalation Matrix

| Severity | Condition | Auto-Action | Human Notification |
|---|---|---|---|
| **INFO** | Successful scrape, 0 new records | Log only | None |
| **WARN** | 1 failed county, others healthy | Retry in next cycle | Slack summary |
| **ERROR** | 3+ consecutive failures for a county | Pause county, alert | Slack `@channel` |
| **CRITICAL** | Sheets API down, all scrapers failing | Halt all scrapers | Slack `@channel` + SMS |
| **SECURITY** | Credential exposure detected | Immediate shutdown | Slack `@channel` + rotate keys |

---

## Compliance & Legal

### Public Record Only
- We **only** ingest data explicitly marked as "Public Record" by the source county
- Arrest records in Florida are public under **Florida Statute 119** (Public Records Law)
- We do not access restricted/sealed records, juvenile records, or non-public databases

### PII Handling
- All ingested PII (names, DOBs, addresses, mugshots) is public record data
- We do not enrich records with non-public data sources
- Data retention follows the policies in `RULES.md` → Data Governance section

### Data Retention
| Data Type | Retention | Managed By |
|---|---|---|
| County sheet tabs | Indefinite | Never delete rows |
| `Qualified_Arrests` tab | Indefinite | Mirrored from county tabs |
| `Ingestion_Log` tab | 90 days | Auto-archived to `Log_Archive` |
| Fixtures (`fixtures/`) | 30 days | Pruned by CI maintenance |
| MongoDB records | Indefinite | Atlas retention policy |

### Deduplication Authority
The composite key **`County` + `Booking_Number`** is the authoritative unique identifier across all systems:
- Google Sheets
- MongoDB Atlas
- Slack notifications
- Lead scoring

### Audit Trail
Every write operation must include:
- `Scrape_Timestamp` — ISO 8601 datetime of ingestion
- `County` — Source county identifier
- `Booking_Number` — Source system's unique ID

---

## Security & Access

### Service Account
- **Email:** `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com`
- **Permissions:** Editor on specifically authorized spreadsheets only
- **Key Rotation:** Rotate every 90 days (tracked in OPERATIONS.md)

### Repository Security
- `.env` files are **always** in `.gitignore`
- GitHub Actions secrets are the only CI/CD credential store
- No credentials in Docker images — mount via environment variables
- Branch protection on `main` — no direct pushes

### IP Hygiene
- GitHub Actions runners use shared IPs — expect occasional blocks
- Local development uses home IP — do not abuse
- Future: Proxy rotation for high-volume counties

---

## Code Standards for This Repo

### Commit Messages
```
<type>(<scope>): <description>

Types: feat, fix, refactor, docs, test, ci, chore
Scopes: <county>, schema, writer, scorer, docker, ops
```

### Error Handling Pattern
```python
# Python — ALWAYS use this pattern
try:
    records = scrape_county()
except CloudflareBlockError:
    log_error("E_CLOUDFLARE", county=COUNTY)
    notify_slack(f"🔴 {COUNTY}: Cloudflare block")
    sys.exit(1)
except SelectorNotFoundError as e:
    log_error("E_SELECTOR", county=COUNTY, detail=str(e))
    notify_slack(f"🟡 {COUNTY}: Selector changed — {e}")
    sys.exit(1)
except Exception as e:
    log_error("E_UNKNOWN", county=COUNTY, detail=str(e))
    notify_slack(f"🔴 {COUNTY}: Unexpected error — {e}")
    sys.exit(1)
```

### Logging Requirements
Every scraper run must log:
1. Start time
2. County name
3. Records found
4. Records inserted (new)
5. Records updated (existing)
6. Records skipped (duplicates)
7. Errors encountered
8. End time and duration

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
