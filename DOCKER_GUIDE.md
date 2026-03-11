# 🐳 Docker Guide — SWFL Arrest Scrapers

> **One command to run all scrapers, anywhere.**

---

## Prerequisites

- **Docker Desktop** installed ([download](https://docs.docker.com/get-docker/))
- Your `creds/service-account-key.json` file (Google Sheets access)
- A `.env` file in the project root with your secrets

---

## Step 1: Create Your `.env` File

Create a `.env` file in the project root (if one doesn't exist):

```bash
cp .env.example .env
```

Then fill in:

```env
# MongoDB Connection
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority

# Google Sheets (the path inside the container — don't change this)
GOOGLE_APPLICATION_CREDENTIALS=/app/creds/service-account-key.json

# Spreadsheet IDs (per county)
COLLIER_SHEET_ID=your_sheet_id_here
CHARLOTTE_SHEET_ID=your_sheet_id_here
SARSOTA_SHEET_ID=your_sheet_id_here
HENDRY_SHEET_ID=your_sheet_id_here

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Twilio (optional)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
```

---

## Step 2: Verify Credentials

Make sure your Google service account key is at:

```
swfl-arrest-scrapers/
└── creds/
    └── service-account-key.json   ← This file
```

This gets **mounted** into the container at runtime (never baked into the image).

---

## Step 3: Build the Images

```bash
cd /path/to/swfl-arrest-scrapers

# Build both images
docker compose build
```

**First build** takes 5-10 minutes (downloading Chromium, Playwright, npm packages).
Subsequent builds are fast due to layer caching.

---

## Step 4: Start the Python Scrapers (24/7 Scheduler)

```bash
# Start the scheduler in the background
docker compose up python-scrapers -d
```

This starts `run_scheduler.py` which fires scrapers on schedule:
- **Collier**: Twice daily (8 AM & 8 PM)
- **Charlotte**: Every 30 minutes
- **Sarasota/Hendry/Manatee**: Every hour (with random delay)

---

## Step 5: Run Node.js Scrapers On-Demand

The Node.js scrapers use a `manual` profile — they don't auto-start. Run them when needed:

```bash
# Run a specific county
docker compose run --rm node-scrapers node index.js collier

# Run all counties
docker compose run --rm node-scrapers node index.js

# Update bond status
docker compose run --rm node-scrapers node index.js --update-bonds
```

---

## Step 6: Monitor Logs

```bash
# Follow all logs in real-time
docker compose logs -f

# Follow only the Python scheduler
docker compose logs -f python-scrapers

# Show last 100 lines
docker compose logs --tail=100 python-scrapers
```

---

## Step 7: Stop / Restart

```bash
# Stop everything
docker compose down

# Restart the scheduler
docker compose restart python-scrapers

# Rebuild after code changes
docker compose build && docker compose up python-scrapers -d
```

---

## Deploying to a VPS / Cloud Server

### Option A: DigitalOcean / Hetzner / Any VPS ($6-12/month)

```bash
# 1. SSH into your server
ssh root@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com | sh

# 3. Clone the repo
git clone https://github.com/your-org/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers

# 4. Add credentials
mkdir -p creds
nano creds/service-account-key.json   # Paste your key
nano .env                              # Add your secrets

# 5. Build and launch
docker compose build
docker compose up python-scrapers -d

# 6. Verify it's running
docker compose logs -f
```

### Option B: AWS ECS / GCP Cloud Run

For managed container platforms:
1. Push your images to a container registry (ECR/GCR)
2. Create a task definition referencing the image
3. Mount secrets via AWS Secrets Manager or GCP Secret Manager

This is more complex but gives auto-scaling and zero-ops maintenance.

---

## Troubleshooting

### Browser crashes inside container
```bash
# Increase shared memory (already set to 2GB in compose)
# If still crashing, try:
docker compose run --rm -e SHM_SIZE=4gb python-scrapers python run_collier.py
```

### "Cannot find module" errors
```bash
# Rebuild from scratch (no cache)
docker compose build --no-cache
```

### Permission denied on creds
```bash
# Fix permissions on the host
chmod 644 creds/service-account-key.json
```

### Container keeps restarting
```bash
# Check what's failing
docker compose logs python-scrapers

# Run interactively to debug
docker compose run --rm python-scrapers bash
```

### View running containers
```bash
docker compose ps
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              docker-compose.yml                  │
│                                                  │
│  ┌──────────────────┐  ┌─────────────────────┐  │
│  │ python-scrapers  │  │   node-scrapers      │  │
│  │ (always-on)      │  │   (on-demand)        │  │
│  │                  │  │                      │  │
│  │ run_scheduler.py │  │ node index.js ...    │  │
│  │ ├─ Collier       │  │ ├─ Collier (JS)     │  │
│  │ ├─ Charlotte     │  │ ├─ Charlotte (JS)   │  │
│  │ ├─ Sarasota      │  │ ├─ Sarasota (JS)    │  │
│  │ ├─ Hendry        │  │ ├─ Hendry (JS)      │  │
│  │ ├─ Manatee       │  │ ├─ DeSoto (JS)      │  │
│  │ └─ + Central FL  │  │ └─ Manatee (JS)     │  │
│  └────────┬─────────┘  └──────────┬──────────┘  │
│           │                       │              │
│     ┌─────┴───────────────────────┴─────┐        │
│     │         Shared Volumes            │        │
│     │  • creds/ (read-only)             │        │
│     │  • .env (secrets)                 │        │
│     │  • progress/ (persistent)         │        │
│     └───────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
           │                    │
     ┌─────┴─────┐       ┌─────┴─────┐
     │  MongoDB  │       │  Google   │
     │  Atlas    │       │  Sheets   │
     └───────────┘       └───────────┘
```
