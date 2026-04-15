---
name: github-actions-docs
description: Use when writing, customizing, or troubleshooting GitHub Actions workflows for scraper scheduling, Docker builds, or CI/CD pipeline issues.
source: xixu-me/skills (skills.sh #87, 56.7K installs)
---

# GitHub Actions for Scraper Workflows

## Overview

Every county scraper runs on a GitHub Actions cron schedule. This skill covers
writing, maintaining, and debugging these workflows.

## When to Use

- Creating a new scraper workflow for a new county
- Debugging a failing workflow run
- Adjusting cron schedules to avoid rate limiting
- Fixing Docker container issues in CI
- Managing secrets (Google Sheets credentials, Slack webhooks)

## Our Workflow Architecture

### Reusable Template
We have a reusable workflow template at `.github/workflows/scrape.yml` that handles:
- Checking out the repo
- Setting up Python + Chrome/Chromium
- Injecting credentials from secrets
- Running the solver
- Writing results to Google Sheets
- Sending Slack notifications

### Per-County Workflows
Each county has a dedicated workflow file:
```yaml
name: Scrape {County} County
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours — STAGGER THESE
  workflow_dispatch:        # Manual trigger button

jobs:
  scrape:
    uses: ./.github/workflows/scrape.yml
    with:
      county: {county_name}
      days_back: 7
      stack: python  # or nodejs
    secrets: inherit
```

## New County Workflow Checklist

1. Copy existing workflow: `cp scrape_brevard.yml scrape_{county}.yml`
2. Update `name`, `county` parameter, and `cron` schedule
3. **STAGGER the cron** — never reuse another county's schedule
4. Set `needs_xvfb: true` if using DrissionPage/Playwright
5. Test with `workflow_dispatch` before relying on cron

## Cron Staggering Strategy

```
# Offset each county by 5 minutes within a 6-hour cycle
County A:  '0  */6 * * *'
County B:  '5  */6 * * *'
County C:  '10 */6 * * *'
County D:  '15 */6 * * *'
...
County L:  '55 */6 * * *'
County M:  '0  1,7,13,19 * * *'  # Shift to different hour set
```

## Secrets Required

| Secret | Purpose |
|--------|---------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | JSON key for Sheets API access |
| `GOOGLE_SHEETS_ID` | Target spreadsheet ID |
| `SLACK_WEBHOOK_URL` | Arrest notification webhook |
| `SLACK_WEBHOOK_ERRORS` | Error alert webhook |

## Common Workflow Issues

### 1. "No module named 'DrissionPage'"
**Fix**: Add to workflow setup step:
```yaml
- run: pip install DrissionPage
```

### 2. Chrome/Chromium not found
**Fix**: Use `setup-chrome` action or install via apt:
```yaml
- uses: browser-actions/setup-chrome@latest
  with:
    chrome-version: stable
```

### 3. Xvfb required for headed tests
**Fix**: Add virtual framebuffer:
```yaml
- run: |
    sudo apt-get install -y xvfb
    Xvfb :99 -screen 0 1920x1080x24 &
    export DISPLAY=:99
```

### 4. Cron not triggering
- GitHub disables cron on repos with no commits for 60 days
- Solution: Any push to `main` re-activates crons
- Minimum interval: 5 minutes (shorter is clamped)

### 5. Concurrent workflow runs
```yaml
concurrency:
  group: scrape-${{ inputs.county }}
  cancel-in-progress: true
```

## Docs Reference

Ground answers in official GitHub documentation at `https://docs.github.com/en/actions`:
- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)
- [Using secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
