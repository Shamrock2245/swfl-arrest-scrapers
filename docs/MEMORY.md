# 🧠 MEMORY.md — Institutional Knowledge & Lessons Learned

> **This is the brain's long-term memory. Every hard-won lesson lives here so the next agent doesn't have to learn it the hard way.**

When you spend hours solving an obscure edge case, **document it here**. Future agents (including future you) will thank you.

---

## How to Use This Document

1. **Before debugging:** Search this file for the county name or error symptom
2. **After resolving:** Add a new entry with the structured format below
3. **When uncertain:** Check the Victory Log for techniques that have worked before

---

## Lessons by County

### 🟢 Charlotte (Python/DrissionPage)
| Date | Lesson | Category |
|---|---|---|
| Jan 2026 | CCSO redesigned their arrest database page. All CSS selectors changed. Resolution: Downloaded new HTML fixture, rebuilt selectors. | Selector Drift |
| Feb 2026 | Date format changed from `MM/DD/YYYY` to `YYYY-MM-DD` without notice. Fix: Added multi-format date parser. | Data Format |
| Mar 2026 | ColdFusion site occasionally returns empty table when under load. Fix: Retry once after 10s delay. | Transient Error |

### 🟢 Sarasota (Python/DrissionPage)
| Date | Lesson | Category |
|---|---|---|
| Feb 2026 | **Cloudflare strict mode.** `requests`, `cloudscraper`, and `curl_cffi` all fail. Only DrissionPage in headful mode works. Do not waste time on lightweight approaches for this county. | Anti-Bot |
| Feb 2026 | The search results load inside an iframe. Must switch to iframe context before extracting data. | Page Structure |
| Mar 2026 | Detail pages have a Turnstile challenge. Must wait 3-5 seconds for it to auto-solve in headful mode. | Anti-Bot |

### 🟢 Hillsborough (Python/DrissionPage)
| Date | Lesson | Category |
|---|---|---|
| Dec 2025 | ASP.NET ViewState is ~50KB. Never try to replay this with raw requests — use DrissionPage to handle it automatically. | Platform Quirk |
| Jan 2026 | High-volume county (~200+ records/day). Batch writes are essential to stay under Sheets API quota. | Performance |

### 🟢 DeSoto (Node.js/Puppeteer)
| Date | Lesson | Category |
|---|---|---|
| Nov 2025 | SmartCOP system. The `Jail.aspx` page is standardized across 13+ Florida counties. Cloning this script is the fastest way to add new SmartCOP counties. | Pattern |
| Dec 2025 | Session times out after ~5 minutes of inactivity. Must refresh the page periodically for long scrapes. | Session Mgmt |

### 🟢 Hendry (Python/DrissionPage)
| Date | Lesson | Category |
|---|---|---|
| Mar 2026 | Despite the web frontend, Hendry has a JSON API endpoint behind the scenes. Direct API access is faster and stealthier than scraping the HTML. | Discovery |

### 🟢 Orange (Python/DrissionPage)
| Date | Lesson | Category |
|---|---|---|
| Jan 2026 | Orange publishes a PDF roster in addition to their web portal. The PDF is more reliable and complete. Consider using `pdfplumber` as primary, web as fallback. | Strategy |

---

## Lessons by Technology

### DrissionPage
| Lesson | Context |
|---|---|
| Always use `headless(False)` for Cloudflare-protected sites | Headless mode is detectable by modern anti-bot |
| Set `--disable-blink-features=AutomationControlled` | Removes the `navigator.webdriver` flag |
| DrissionPage's `.wait.ele_loaded()` is more reliable than manual `time.sleep()` | But always add a small random sleep too |
| Memory usage: ~300MB per Chromium instance | Don't run more than 3 in parallel on GH Actions (7GB limit) |
| DrissionPage does NOT work well inside Docker without `--no-sandbox` | Always set this flag in containerized environments |

### Google Sheets API
| Lesson | Context |
|---|---|
| Batch writes are 10x faster than individual appends | Use `values.batchUpdate` for multi-row operations |
| Quota: 300 requests/minute per project | Never schedule 6+ counties to write simultaneously |
| ViewState columns can push row size over limits | Store large blobs elsewhere, not in Sheets |
| Conditional formatting is lost when batch-updating ranges | Only update value ranges, not formatting |

### GitHub Actions
| Lesson | Context |
|---|---|
| Shared runner IPs are used by many projects | Counties may block popular IPs; consider self-hosted runners for critical counties |
| Ubuntu runners have Chrome pre-installed | But the version may lag; pin Chromium version in your config |
| Actions have a 6-hour timeout by default | Set explicit `timeout-minutes` in your workflow |
| Secrets are not available in fork PRs | Test credential handling in private repo workflows |

### Slack Webhooks
| Lesson | Context |
|---|---|
| Webhook URLs expire if the Slack app is uninstalled | Keep backup of webhook URLs securely |
| Messages >3000 chars get truncated | Summarize, don't dump full records |
| Channel-specific webhooks are more maintainable than generic ones | Use per-county channels for arrest alerts |

---

## Platform Quirks

### Cloudflare Behaviors
- **Strict mode:** Presents an interstitial challenge page. Only headful + real Chromium passes.
- **Managed Challenge:** May auto-solve after 5s. Wait for redirect before extracting.
- **Turnstile:** Checkbox CAPTCHA. Usually auto-solves in headful mode if browser looks human.
- **Rate Limit Rule:** Some sites return 429 after ~10 requests in 60 seconds. Back off to 1 req/10s.

### SmartCOP Patterns
- All SmartCOP instances share the same HTML structure
- The `Jail.aspx` page path is consistent: `/smartwebclient/Jail.aspx` or `/SmartWEBClient/Jail.aspx`
- Some use HTTP (not HTTPS) — handle both
- Session cookies are required — always navigate to the page first (don't direct-link)

### ASP.NET ViewState
- ViewState is a base64-encoded blob in a hidden field
- It contains the page's state and must be included in form submissions
- Size can be 50KB+ for complex pages
- **Never** try to construct ViewState manually — use a real browser
- DrissionPage handles this transparently

---

## Anti-Patterns (What NOT To Do)

| Anti-Pattern | Why It Fails | What To Do Instead |
|---|---|---|
| Brute-forcing past Cloudflare | Gets IP permanently banned | Use DrissionPage headful |
| Disabling JavaScript in the browser | Sites detect and block | Keep JS enabled always |
| Hardcoding selectors without fixtures | Can't debug when they change | Save fixture HTML on every run |
| Running all counties simultaneously | Sheets API quota exhaustion | Stagger with 60s+ offsets |
| Storing credentials in code | Security breach risk | Environment variables only |
| Deleting rows from Sheets | Data loss risk | Mark as archived, never delete |
| Ignoring Ingestion_Log errors | Problems compound silently | Review daily |
| Using `time.sleep(10)` exactly | Machine-like timing = detection | Use `random.uniform(8, 15)` |

---

## Victory Log

Techniques that solved particularly difficult problems — keep these for reference.

### Victory #1: Sarasota Cloudflare Bypass
**Problem:** Every HTTP library failed against Sarasota's Cloudflare strict mode.
**Solution:** DrissionPage in headful mode with a 5-second wait after page load for the challenge to auto-solve. No CAPTCHA solver needed.
**Key Insight:** Cloudflare's managed challenge auto-solves in real browsers — you just need patience.

### Victory #2: SmartCOP Cloning Pattern
**Problem:** Adding 13 new counties seemed like massive effort.
**Solution:** Discovered all SmartCOP sites share identical HTML structure. One script, cloned 13 times with URL swap.
**Key Insight:** Before building a new scraper, check if it uses a platform you've already solved.

### Victory #3: Hendry API Discovery
**Problem:** Hendry's web frontend was flaky and slow.
**Solution:** Discovered a hidden JSON API endpoint using browser DevTools network tab.
**Key Insight:** Always check the network tab — some "dynamic" sites are just frontends to clean APIs.

### Victory #4: Batch Write Optimization
**Problem:** 6 counties writing simultaneously exceeded Sheets API quota.
**Solution:** Batched all writes per county into a single `batchUpdate` call, staggered county execution by 5 minutes.
**Key Insight:** One batch call writing 50 rows is cheaper than 50 individual append calls.

---

## Regression Watch List

Sites that have changed before and will likely change again. Check these proactively.

| County | Last Change | Frequency | What Changed |
|---|---|---|---|
| Charlotte | Jan 2026 | ~Yearly | Full CSS redesign |
| Sarasota | Feb 2026 | ~6 months | Anti-bot upgrades |
| Hillsborough | Stable | ~2 years | Last changed 2024 |
| Orange | Stable | Unknown | PDF format unchanged since 2023 |

---

## Adding a New Entry

Use this template when documenting a new lesson:

```markdown
### [County Name] or [Technology Name]
| Date | Lesson | Category |
|---|---|---|
| YYYY-MM | Brief description of what happened and how it was resolved. | Category |
```

**Categories:** `Anti-Bot`, `Selector Drift`, `Data Format`, `Platform Quirk`, `Performance`, `Session Mgmt`, `Strategy`, `Discovery`, `Security`, `Transient Error`, `Pattern`

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
