# 🔐 Secrets and Configuration

## Config Hierarchy (Priority Order)
1. **Environment variables** (highest) — for secrets and CI overrides
2. **`config/counties/{county}.yaml`** — per-county overrides
3. **`config/counties/_defaults.yaml`** — shared county defaults
4. **`config/global.yaml`** — system-wide defaults (lowest)

## What Goes Where

### ✅ In `config/global.yaml` (checked into git)
- Timeout values, retry counts, backoff settings
- Output directory paths
- Writer enable/disable flags
- Browser settings (headless, window size)

### ✅ In `config/counties/{name}.yaml` (checked into git)
- Site URLs, pagination type, selectors
- Schedule cron expressions
- County-specific overrides (days_back, max_pages)
- CMS platform notes

### 🔒 In Environment Variables (NEVER in git)
- `GOOGLE_SHEETS_ID` — Spreadsheet ID
- `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` — Path to JSON credentials
- `SLACK_WEBHOOK_URL` — Slack webhook
- `MONGO_URI` — MongoDB connection string
- `PROXY_URL` — Proxy server (optional)

### 📁 In `.env` file (git-IGNORED, local only)
```bash
GOOGLE_SHEETS_ID=1abc...xyz
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=creds/service-account.json
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
MONGO_URI=mongodb+srv://...
```

### 🔒 In GitHub Secrets (CI/CD)
Same variables as `.env`, set in GitHub repo Settings → Secrets → Actions.

## Rules
1. **NEVER** commit `.env` files
2. **NEVER** commit `creds/` directory contents
3. **NEVER** hardcode API keys, passwords, or tokens in Python/JS files
4. **NEVER** log secrets — mask them in logging output
5. **ALWAYS** use `os.getenv()` or `config_loader.load_config()` to access secrets
6. **ALWAYS** check `.gitignore` includes `.env*`, `creds/`, `*.json` credential files

## Loading Config in Code
```python
from core.config_loader import load_config

config = load_config("charlotte")
# config["sheets_id"]        ← from env var GOOGLE_SHEETS_ID
# config["search_url"]       ← from config/counties/charlotte.yaml
# config["days_back"]        ← from county yaml or _defaults.yaml
# config["headless"]         ← from county yaml or global.yaml
```
