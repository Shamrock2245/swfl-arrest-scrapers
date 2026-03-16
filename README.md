# 🍀 SWFL Arrest Scrapers

> **Multi-county Florida jail roster scraping pipeline — Shamrock Bail Bonds**

Automated arrest data ingestion across 67 Florida counties. Scrapers collect, normalize, score, and deliver booking records to Google Sheets, MongoDB Atlas, and Slack — powering real-time lead generation for the agency.

**Active Counties:** 19 / 67 | **Status:** 🟢 Production | **Last Updated:** March 16, 2026

---

## ⚡ Quick Start

```bash
# Install Python dependencies
pip install -e .

# Run a single county
python scripts/run_county.py charlotte --days-back 7

# Run all enabled counties
python scripts/run_all.py

# Node.js counties (Collier, DeSoto, Lee)
npm install
node counties/collier/solver.js
```

### Required Environment Variables

```bash
GOOGLE_SHEETS_ID=your_sheet_id
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'   # or Base64
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/shamrock_arrests
```

See `.env.example` for the full list.

---

## 🏛️ County Status

| County | Stack | Status | Schedule | Notes |
|--------|-------|--------|----------|-------|
| **Brevard** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Simple HTML bookings |
| **Charlotte** | Python/DrissionPage | ✅ Active | `*/30 * * * *` | Revize CMS |
| **Collier** | Node.js/Puppeteer | ✅ Active | `*/30 * * * *` | Custom site |
| **DeSoto** | Node.js/Puppeteer | ✅ Active | `0 */2 * * *` | SmartCOP, incremental mode |
| **Hendry** | Python/Playwright | ✅ Active | `0 */2 * * *` | Wix API interception |
| **Highlands** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Interactive search |
| **Hillsborough** | Python/DrissionPage | ✅ Active | `*/20 * * * *` | Login required |
| **Indian River** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Interactive search form |
| **Lake** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Interactive search |
| **Lee** | GAS Internal | ✅ Active | `*/30 * * * *` | Home county |
| **Manatee** | Python/DrissionPage | ✅ Active | `*/30 * * * *` | Revize CMS |
| **Martin** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Recent Bookings page |
| **Orange** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | High volume |
| **Osceola** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Custom portal |
| **Palm Beach** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | High volume |
| **Pinellas** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | PCSO |
| **Polk** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Central FL |
| **Sarasota** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Cloudflare; DP required |
| **Seminole** | Python/DrissionPage | ✅ Active | `0 */3 * * *` | Sheriff's Office |

**19 active counties** — Goal: 67 Florida counties (Wave 1 SmartCOP blitz next: 13 easy clones).

---

## 📁 Repository Structure

```
counties/             → One folder per county (solver.py + runner.py)
core/                 → Shared Python modules
  ├── browser/        → DrissionPage browser management
  ├── normalizer/     → 39-column schema normalization
  └── writers/        → Output writers
      ├── sheets.py   → Google Sheets writer (newest at row 2)
      └── mongo_writer.py → MongoDB Atlas writer (bulk upsert, dedup)
config/               → Global + per-county YAML configs
scripts/              → CLI entry points (run_county.py, run_all.py)
.agent/               → AI agent instruction files (12 docs)
docs/                 → Human documentation
.github/workflows/    → GitHub Actions CI/CD (15 workflows)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design and data flow diagrams.

---

## 🔄 Data Pipeline

```
County Website → Scraper (DrissionPage/Puppeteer)
    → Normalize (39-column schema)
    → Deduplicate (County + Booking_Number)
    → Score (0-100 lead score)
    → Step 5a: Write to Google Sheets (newest at row 2)
    → Step 5b: Write to MongoDB Atlas (bulk upsert, non-fatal)
    → Cross-post qualified leads (score ≥ 70)
    → Slack alert → #new-arrests-{county}
```

**Key behaviors:**
- New records inserted at **row 2** — header stays at row 1, newest always on top.
- MongoDB writes are **non-fatal** — pipeline continues even if Atlas is unreachable.
- Dedup key: `County` + `Booking_Number` for both Sheets and MongoDB.

---

## 🤖 Adding a New County

```bash
# 1. Copy template
cp -r counties/_template counties/your_county

# 2. Create config
cp config/counties/_defaults.yaml config/counties/your_county.yaml

# 3. Edit solver.py with county-specific scraping logic

# 4. Test
python scripts/run_county.py your_county --dry-run

# 5. Document quirks
echo "Site uses SmartCOP, no Cloudflare" > counties/your_county/quirks.md
```

Full guide: [.agent/ADDING_A_COUNTY.md](.agent/ADDING_A_COUNTY.md)

---

## 🏗 Infrastructure

| Component | Technology | Details |
|-----------|-----------|---------|
| **Primary Engine** | Python/DrissionPage | Stealth browser automation, 16 counties |
| **Legacy Engine** | Node.js/Puppeteer | 3 counties (Collier, DeSoto, Lee) |
| **Storage** | Google Sheets + MongoDB Atlas | Sheets primary, MongoDB secondary (transitioning) |
| **CI/CD** | GitHub Actions | 15 workflows, staggered cron schedules |
| **Runners** | Hetzner Cloud VPS + GitHub Shared | `cpx21` servers, Ubuntu 24.04, self-hosted runners |
| **Containerization** | Docker Compose | Dual-stack (Python + Node.js) |
| **Alerts** | Slack | Per-county channels (`#new-arrests-{county}`) |
| **Dependencies** | `pymongo[srv]`, `drissionpage`, `gspread` | See `pyproject.toml` |

---

## 📚 Documentation

| Doc | For | Contents |
|-----|-----|----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Engineers | System design, data flows, interface contracts |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Ops | Docker, GitHub Actions, credentials |
| [SCHEMA.md](docs/SCHEMA.md) | Data | 39-column schema reference |
| [ROADMAP.md](docs/ROADMAP.md) | Strategy | Wave 1-5 county expansion plan |
| [.agent/RULES.md](.agent/RULES.md) | AI Agents | Do's, don'ts, modification rules |
| [.agent/DEBUGGING_SCRAPERS.md](.agent/DEBUGGING_SCRAPERS.md) | AI/Engineers | Troubleshooting playbook |

---

## 🔐 Security

- **Secrets** → `.env` (local), GitHub Secrets (CI), GAS Script Properties
- **Service Account** → `GOOGLE_SERVICE_ACCOUNT_JSON` env var (raw or Base64)
- **MongoDB** → `MONGODB_URI` env var with SRV connection string
- **Never** commit `.env`, `*_key.json`, or credentials to git
- See [.agent/SECRETS_AND_CONFIG.md](.agent/SECRETS_AND_CONFIG.md)

---

## 🔗 Related Repos

| Repo | Purpose |
|------|---------|
| [shamrock-bail-portal-site](https://github.com/Shamrock2245/shamrock-bail-portal-site) | Wix website + GAS backend |
| [shamrock-node-red](https://github.com/Shamrock2245/shamrock-node-red) | Node-RED automation engine |
| **swfl-arrest-scrapers** (this repo) | 19-county scraper fleet |
| [shamrock-telegram-app](https://github.com/Shamrock2245/shamrock-telegram-app) | Telegram Mini-Apps (Netlify) |

---

*Maintained by Shamrock Engineering & AI Agents · March 2026*
