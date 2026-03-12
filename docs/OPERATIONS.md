# ⚙️ OPERATIONS.md — Runbook, SLOs & Incident Playbooks

> **This is the field manual. When something breaks at 2am, this document tells you what to do.**

---

## Service Level Objectives (SLOs)

| Metric | Target | Measurement | Alert Threshold |
|---|---|---|---|
| **Data Freshness** | ≤2 hours per active county | Time since last `Ingestion_Log` entry | >3 hours triggers Slack alert |
| **Scrape Success Rate** | ≥95% per county per week | Successful runs / total scheduled runs | <90% triggers review |
| **Deduplication Accuracy** | 100% | Zero duplicate `Booking_Number` per county | Any duplicate = critical |
| **Hot Lead Latency** | ≤5 minutes from booking to Slack | Booking timestamp vs Slack message timestamp | >15 minutes triggers review |
| **Error Recovery** | <3 consecutive failures | Count of back-to-back failed runs | 3+ = auto-pause county |

---

## Daily Routine

### Automated (No Human Required)
| Time | Action | System |
|---|---|---|
| Every 15–120m | County scrapers execute | GitHub Actions / Docker cron |
| On new records | Slack notifications fire | `slack/notify.js` |
| On hot lead | Slack `@channel` alert fires | Lead scoring engine |
| On error | Error logged + Slack alert | Per-scraper error handling |
| Weekly | Bond status refresh | `jobs/updateBondPaid.js` |

### Human Review (Once Daily)
1. **Check `Ingestion_Log`** tab for any `E_*` error codes in the last 24 hours
2. **Review Slack `#scraper-alerts`** for persistent failures
3. **Spot-check county tabs** — ensure data looks reasonable (no blank rows, no garbled text)
4. **Check GitHub Actions** — review any failed workflow runs

---

## Running Scrapers

### Local Execution (Development)
```bash
# Python (Primary) — Single county
python3 python_scrapers/run_charlotte.py
python3 python_scrapers/run_hillsborough.py
python3 python_scrapers/run_sarasota.py

# Node.js (Legacy) — Single county
npm run run:desoto

# All counties (Orchestrated)
npm run scrape:all
```

### Docker Execution (Production)
```bash
# Build containers
docker-compose build

# Run all scrapers
docker-compose up

# Run specific service
docker-compose run python-scrapers python3 run_charlotte.py
```

### GitHub Actions (CI/CD)
- **Automatic:** Cron-scheduled per county (see `.github/workflows/scrape_*.yml`)
- **Manual trigger:** Go to GitHub → Actions tab → Select workflow → "Run workflow"

---

## Monitoring & Alerting

### Health Check Endpoints
| Check | Method | Expected |
|---|---|---|
| GAS bridge health | GET `?action=health` | `{"status":"ok"}` |
| Sheets API access | Read `Ingestion_Log` | Returns data |
| Slack webhook | POST test message | `ok` response |

### Key Slack Channels
| Channel | Purpose | Alert Level |
|---|---|---|
| `#new-arrests-{county}` | New booking notifications | INFO |
| `#leads` | Hot lead alerts (Score ≥70) | HIGH |
| `#scraper-alerts` | Scraper errors and failures | ERROR |
| `#drive` | Run summaries | INFO |

### What to Watch For
| Symptom | Likely Cause | Severity |
|---|---|---|
| 0 records for 3+ consecutive runs | Selector drift or site down | 🔴 ERROR |
| Sudden spike in record count | Scraper grabbing old data | 🟡 WARN |
| `E_CLOUDFLARE` errors | IP block or increased protection | 🔴 ERROR |
| Sheets write failures | API quota exhausted | 🔴 ERROR |
| Duplicate records appearing | Dedup key logic broken | 🔴 CRITICAL |

---

## Incident Playbooks

### 🔴 Playbook 1: Cloudflare/Bot Detection Block
**Symptoms:** `E_CLOUDFLARE`, `E_403`, empty results, CAPTCHA challenges
```
1. STOP — Do not retry aggressively (makes it worse)
2. CHECK docs/MEMORY.md for known workarounds for this county
3. TRY switching from headless → headful mode
4. TRY updating DrissionPage to latest version
5. TRY adding longer delays between requests (10-15s)
6. IF still blocked → reduce scrape frequency (e.g., every 2h instead of 30m)
7. IF still blocked → escalate via Slack #scraper-alerts
8. DOCUMENT the incident in MEMORY.md
```

### 🟡 Playbook 2: Selector Drift (0 Records)
**Symptoms:** `E_EMPTY`, `E_SELECTOR`, scraper runs but finds no data
```
1. VERIFY the county site is actually live (visit in browser)
2. SAVE current page HTML → fixtures/<county>_YYYY-MM-DD.html
3. COMPARE with previous fixture (if available)
4. IDENTIFY changed selectors (class names, IDs, structure)
5. UPDATE the solver file with new selectors
6. TEST locally: python3 python_scrapers/run_<county>.py
7. VERIFY data appears in the correct sheet tab
8. COMMIT: fix(<county>): update selectors for site redesign
9. UPDATE MEMORY.md with details
```

### 🔴 Playbook 3: Google Sheets API Quota Exceeded
**Symptoms:** `E_SHEET_PERM`, 429 errors, write failures
```
1. CHECK Google Cloud Console for API quota usage
2. REDUCE concurrent sheet operations
3. INCREASE batch write sizes (fewer API calls per run)
4. STAGGER scraper schedules to avoid simultaneous writes
5. IF persistent → request quota increase from Google
```

### 🔴 Playbook 4: Complete Scraper Failure (All Counties)
**Symptoms:** All scrapers failing simultaneously
```
1. CHECK internet connectivity on the runner
2. CHECK GitHub Actions status page (outage?)
3. CHECK Google Sheets API status
4. IF infrastructure issue → wait for resolution
5. IF credential issue → verify GOOGLE_SA_KEY_JSON and SLACK_WEBHOOK_URL
6. ESCALATE to Slack #scraper-alerts with @channel
```

### 🟡 Playbook 5: Duplicate Records Detected
**Symptoms:** Same booking appearing multiple times in a county tab
```
1. STOP the affected scraper immediately
2. IDENTIFY the root cause (broken dedup key? changed booking number format?)
3. DO NOT manually delete rows — fix the writer logic first
4. FIX the dedup logic in the relevant writer
5. RUN dedup cleanup script on the affected tab
6. VERIFY no data was lost
7. RESUME the scraper
```

---

## Maintenance Tasks

### Weekly
- [ ] Review `Ingestion_Log` for error patterns
- [ ] Check all active county success rates (target: >95%)
- [ ] Review Slack `#scraper-alerts` for unresolved issues

### Monthly
- [ ] Update DrissionPage and Puppeteer to latest stable versions
- [ ] Rotate user-agent strings (check for stale ones)
- [ ] Prune `fixtures/` directory (>30 days old)
- [ ] Archive `Ingestion_Log` entries >90 days to `Log_Archive`
- [ ] Review and update COUNTY_REGISTRY.md status for all counties

### Quarterly
- [ ] Rotate Google Service Account key
- [ ] Review and update Slack webhook URLs
- [ ] Audit all county sites for design changes (proactive selector check)
- [ ] Evaluate expansion candidates (next Wave)
- [ ] Update documentation for accuracy

---

## Deployment Checklist

### New County Deployment
```
□ Solver file created and tested locally
□ Runner file created and tested locally
□ 2+ consecutive runs show idempotent behavior
□ Sheet tab created with correct county name
□ GitHub Actions workflow created from template
□ Slack channel created (#new-arrests-{county})
□ COUNTY_REGISTRY.md updated with status BETA
□ 72-hour monitoring period before promoting to STABLE
```

### Code Change Deployment
```
□ Changes tested locally with at least one county
□ No new dependencies without updating requirements.txt / package.json
□ No credentials in committed code
□ PR reviewed and approved
□ Merged to main
□ Monitor first 3 scheduled runs post-deploy
```

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
