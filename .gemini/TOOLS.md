# 🛠 TOOLS — Technology & Tool Ecosystem

## Scraping Engines

### DrissionPage (Primary — Python)
| Attribute | Value |
|-----------|-------|
| **Purpose** | Stealth browser automation for JS-heavy / Cloudflare-protected sites |
| **Counties** | 16+ (Charlotte, Hendry, Hillsborough, Manatee, Orange, etc.) |
| **Anti-Detection** | Built-in stealth mode, real Chromium fingerprint |
| **Install** | `pip install drissionpage` |
| **Key Pattern** | `ChromiumPage()` with `ChromiumOptions()` for headless/headful |

```python
from DrissionPage import ChromiumPage, ChromiumOptions
co = ChromiumOptions()
co.headless(True)
co.set_argument('--no-sandbox')
co.set_argument('--disable-blink-features=AutomationControlled')
page = ChromiumPage(co)
page.get('https://county-site.com')
```

### requests + BeautifulSoup4 (Lightweight — Python)
| Attribute | Value |
|-----------|-------|
| **Purpose** | Simple HTML scraping without browser overhead |
| **Counties** | 8+ (Alachua, Brevard, Collier, Escambia, Hillsborough, etc.) |
| **Anti-Detection** | Custom headers, session cookies |
| **Install** | `pip install requests beautifulsoup4` |
| **Best For** | Static HTML, API endpoints, no-JS sites |

```python
import requests
from bs4 import BeautifulSoup
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 ...'})
resp = session.get(url, timeout=30)
soup = BeautifulSoup(resp.text, 'html.parser')
```

### Puppeteer (Legacy — Node.js)
| Attribute | Value |
|-----------|-------|
| **Purpose** | Legacy scraper for DeSoto and Collier |
| **Counties** | 2 (DeSoto, Collier legacy) |
| **Anti-Detection** | `puppeteer-extra-plugin-stealth` |
| **Install** | `npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth` |
| **Status** | Legacy — new counties use Python |

---

## Data Storage

### Google Sheets (Primary Database)
| Attribute | Value |
|-----------|-------|
| **Library** | `gspread` + `google-auth` |
| **Sheet ID** | `121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E` |
| **Auth** | Service account JSON (`GOOGLE_SERVICE_ACCOUNT_JSON` env var) |
| **Write Pattern** | Insert at row 2 (header at row 1, newest on top) |
| **Dedup** | Check `Booking_Number + County` before insert |

```python
import gspread
gc = gspread.service_account_from_dict(creds_dict)
sheet = gc.open_by_key(SHEETS_ID)
worksheet = sheet.worksheet('Charlotte')
worksheet.insert_row(row_data, index=2)
```

### MongoDB Atlas (Analytics & Backup)
| Attribute | Value |
|-----------|-------|
| **Library** | `pymongo[srv]` |
| **Connection** | `MONGODB_URI` env var (SRV connection string) |
| **Collection** | `arrests` |
| **Write Pattern** | Bulk upsert with `Booking_Number + County` as key |
| **Failure Mode** | Non-fatal — pipeline continues if MongoDB is unreachable |

```python
from pymongo import MongoClient
client = MongoClient(MONGO_URI)
db = client['shamrock_arrests']
db.arrests.update_one(
    {'Booking_Number': record['Booking_Number'], 'County': record['County']},
    {'$set': record},
    upsert=True
)
```

---

## Communication

### Slack Webhooks
| Attribute | Value |
|-----------|-------|
| **Library** | Direct `requests.post()` to webhook URL |
| **Auth** | `SLACK_WEBHOOK_URL` env var |
| **Channels** | `#new-arrests-{county}`, `#leads`, `#scraper-alerts` |
| **Format** | Slack Block Kit JSON |
| **Rate Limit** | 1 message per second |

### Twilio (SMS/WhatsApp — via GAS)
| Attribute | Value |
|-----------|-------|
| **Usage** | Not directly used by scrapers — GAS handles outbound messages |
| **Relevance** | Scraper data triggers outreach via The Closer |

---

## CI/CD

### GitHub Actions
| Attribute | Value |
|-----------|-------|
| **Workflows** | 24+ per-county workflows in `.github/workflows/` |
| **Template** | `scrape.yml` (reusable workflow) |
| **Runners** | Ubuntu-latest (shared) + self-hosted (Hetzner) |
| **Secrets** | `GOOGLE_SERVICE_ACCOUNT_JSON`, `SLACK_WEBHOOK_URL`, `MONGODB_URI` |
| **Schedule** | Staggered cron (20min to 3h depending on county priority) |

### Docker
| Attribute | Value |
|-----------|-------|
| **Compose** | `docker-compose.yml` (Python + Node.js dual-stack) |
| **Image** | Custom Dockerfile with Chromium + Python + Node |
| **Usage** | Local development, self-hosted production |

---

## Configuration

### YAML Config System
| File | Scope | Example Content |
|------|-------|----------------|
| `config/global.yaml` | System-wide | Timeouts, retry counts, browser settings |
| `config/counties/_defaults.yaml` | All counties | `days_back: 7`, `max_pages: 10` |
| `config/counties/{name}.yaml` | Per-county | URLs, selectors, schedule, tab name |

### Schema Files
| File | Purpose |
|------|---------|
| `config/schema.json` | 34-column canonical schema + scoring rules |
| `config/field_aliases.json` | Raw field name → schema column mapping |

---

## Python Dependencies (Key Packages)

| Package | Purpose | Required By |
|---------|---------|-------------|
| `drissionpage` | Browser automation | Most Python solvers |
| `requests` | HTTP client | Lightweight solvers |
| `beautifulsoup4` | HTML parsing | Lightweight solvers |
| `gspread` | Google Sheets API | All writers |
| `google-auth` | GCP authentication | All writers |
| `pymongo[srv]` | MongoDB client | MongoDB writer |
| `pyyaml` | Config loading | Config system |
| `playwright` | Alternative browser automation | Hendry, Osceola |

See `pyproject.toml` for the complete dependency list.
