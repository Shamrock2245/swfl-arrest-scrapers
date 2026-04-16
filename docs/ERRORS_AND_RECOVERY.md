# 🚨 ERRORS_AND_RECOVERY — Error Codes, Playbooks & Recovery

> **When something breaks at 2am, this document tells you what to do.**

---

## Error Code Catalog

### Scraper Errors (E_SCRAPE_*)
| Code | Meaning | Severity | Auto-Recoverable |
|---|---|---|---|
| `E_SCRAPE_EMPTY` | Scraper returned 0 records | 🟡 WARN | Maybe — could be site down or selector drift |
| `E_SCRAPE_TIMEOUT` | Page load exceeded timeout | 🟡 WARN | Yes — retry with longer timeout |
| `E_SCRAPE_SELECTOR` | Expected HTML element not found | 🔴 ERROR | No — site likely redesigned |
| `E_SCRAPE_PARSE` | Data extraction failed (bad format) | 🟡 WARN | Maybe — log raw data for analysis |
| `E_SCRAPE_CRASH` | Unhandled exception in solver | 🔴 ERROR | No — code bug requiring fix |

### Anti-Bot Errors (E_BLOCK_*)
| Code | Meaning | Severity | Auto-Recoverable |
|---|---|---|---|
| `E_BLOCK_CLOUDFLARE` | Cloudflare JS challenge not bypassed | 🔴 ERROR | Maybe — try headful mode |
| `E_BLOCK_403` | HTTP 403 Forbidden | 🔴 ERROR | Maybe — IP may be temporarily blocked |
| `E_BLOCK_CAPTCHA` | CAPTCHA challenge presented | 🔴 ERROR | No — manual investigation required |
| `E_BLOCK_RATELIMIT` | Too many requests (429) | 🟡 WARN | Yes — backoff and retry |
| `E_BLOCK_IPBAN` | Persistent block from county IP | 🔴 CRITICAL | No — need proxy or schedule change |

### Storage Errors (E_STORE_*)
| Code | Meaning | Severity | Auto-Recoverable |
|---|---|---|---|
| `E_STORE_SHEETS_PERM` | Google Sheets API permission denied | 🔴 ERROR | No — check service account |
| `E_STORE_SHEETS_QUOTA` | Sheets API quota exceeded (429) | 🟡 WARN | Yes — wait 60s and retry |
| `E_STORE_SHEETS_WRITE` | Row write failed | 🔴 ERROR | Yes — retry once |
| `E_STORE_MONGO_CONN` | MongoDB connection failed | 🟡 WARN | Non-fatal — pipeline continues |
| `E_STORE_MONGO_WRITE` | MongoDB write failed | 🟡 WARN | Non-fatal — pipeline continues |
| `E_STORE_DEDUP_FAIL` | Dedup check failed | 🟡 WARN | Default to SKIP (safe choice) |

### Alert Errors (E_ALERT_*)
| Code | Meaning | Severity | Auto-Recoverable |
|---|---|---|---|
| `E_ALERT_SLACK` | Slack webhook POST failed | 🟡 WARN | Non-fatal — log and continue |
| `E_ALERT_SLACK_RATE` | Slack rate limit hit | 🟡 WARN | Yes — queue and retry in 1s |

---

## Recovery Playbooks

### 🔴 Playbook 1: Cloudflare / Bot Detection Block
**Symptoms**: `E_BLOCK_CLOUDFLARE`, `E_BLOCK_403`, empty results, CAPTCHA challenges
```
1. STOP — Do not retry aggressively (makes it worse)
2. CHECK .gemini/MEMORY.md for known workarounds for this county
3. TRY switching from headless → headful mode
4. TRY updating DrissionPage to latest version
5. TRY adding longer delays between requests (10-15s)
6. IF still blocked → reduce scrape frequency (e.g., every 2h instead of 30m)
7. IF still blocked → consider proxy (last resort)
8. DOCUMENT the incident in LOGBOOK.md and MEMORY.md
```

### 🟡 Playbook 2: Selector Drift (0 Records)
**Symptoms**: `E_SCRAPE_EMPTY`, `E_SCRAPE_SELECTOR`, scraper runs but finds nothing
```
1. VERIFY the county site is actually live (visit in browser)
2. SAVE current page HTML → counties/{county}/fixtures/YYYY-MM-DD.html
3. COMPARE with previous fixture (if available)
4. IDENTIFY changed selectors (class names, IDs, DOM structure)
5. UPDATE the solver.py with new selectors
6. TEST locally: python counties/{county}/solver.py --days-back 3
7. VERIFY data appears correct and complete
8. COMMIT: fix({county}): update selectors for site redesign
9. UPDATE MEMORY.md with details of what changed
```

### 🔴 Playbook 3: Google Sheets API Quota Exceeded
**Symptoms**: `E_STORE_SHEETS_QUOTA`, 429 errors, write failures
```
1. CHECK Google Cloud Console → APIs & Services → Sheets API → Quotas
2. IDENTIFY which county is consuming the most quota
3. REDUCE concurrent sheet operations (stagger schedules)
4. INCREASE batch write sizes (fewer API calls per run)
5. IF persistent → request quota increase from Google Cloud Console
6. CONSIDER switching high-volume counties to batch-only writes
```

### 🔴 Playbook 4: Complete Scraper Failure (All Counties)
**Symptoms**: All scrapers failing simultaneously
```
1. CHECK GitHub Actions status page (github.com/status)
2. CHECK Google Workspace status (workspace.google.com/status)
3. CHECK internet connectivity on runners
4. IF infrastructure issue → wait for resolution, scrapers will auto-retry
5. IF credential issue → verify GOOGLE_SERVICE_ACCOUNT_JSON secret is valid
6. IF dependency issue → check DrissionPage/gspread for breaking updates
7. ESCALATE to Slack #scraper-alerts with @channel
```

### 🟡 Playbook 5: Duplicate Records Detected
**Symptoms**: Same booking appearing multiple times in a county tab
```
1. STOP the affected county scraper immediately
2. IDENTIFY root cause:
   - Booking_Number format changed?
   - County field mismatch?
   - Dedup check silently failing?
3. DO NOT manually delete rows — fix the writer logic first
4. FIX the dedup logic in sheets_writer.py
5. RUN dedup cleanup: python core/utils/dedup_sheet.py --county {county}
6. VERIFY no data was lost (compare record counts)
7. RESUME the scraper with monitoring
```

### 🟡 Playbook 6: County Site Completely Redesigned
**Symptoms**: Scraper returns junk or crashes on a previously working county
```
1. SAVE the new site HTML as a fixture
2. ANALYZE the new structure (is it still scrapable?)
3. DECIDE: patch the existing solver or rewrite?
   - Minor selector changes → patch
   - New framework (React, Angular) → rewrite
   - Login wall added → flag as BLOCKED
4. REBUILD using the county-scraper-builder skill
5. TEST with 3+ consecutive successful runs
6. DEPLOY and monitor for 72 hours
```

---

## Automatic Recovery Rules

| Error | Auto-Action | Max Retries |
|---|---|---|
| Timeout | Wait 30s, retry | 3 |
| Rate limit (429) | Wait 60s, retry | 5 |
| Network error | Wait 15s, retry | 3 |
| Slack failure | Log warning, continue | 0 (non-fatal) |
| MongoDB failure | Log warning, continue | 0 (non-fatal) |
| Sheets write failure | Wait 5s, retry | 2 |
| All retries exhausted | Log `E_*` code, alert Slack, exit with code 1 | — |

---

## When to Pause a County

Auto-pause triggers (scraper should stop scheduling):
1. **3 consecutive failures** of any type
2. **IP ban confirmed** (persistent 403 from the county)
3. **County explicitly requests we stop**
4. **Duplicate records detected** (data integrity risk)

Resume only after:
- Root cause identified and fixed
- Local test passes 2+ consecutive runs
- Human approval for county-requested pauses
