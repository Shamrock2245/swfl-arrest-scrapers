# AGENTS – SWFL Arrest Scrapers

This file defines how AI agents (Manus, ChatGPT, etc.) must work on this repo.  
**Non-negotiable rule:** always read existing code and docs before generating new files.

---

## 0. Shared Rules for All Agents

1. **Always inspect the repo first**
   - Use the GitHub / filesystem tool to list:
     - `scrapers/`, `swfl_arrests/`, `docs/`, `*.md` at the repo root.
   - Before creating a new file, check if a **similar file already exists**.
   - Prefer **editing** existing files over creating new ones.

2. **No duplicate or conflicting scrapers**
   - Each county must have **one primary scraper file**:
     - Python: `swfl_arrests/counties/<county>_county.py`
   - If legacy Node/Apps Script scrapers exist, **leave them in place** unless a human explicitly asks to delete or move them.

3. **Respect the schema**
   - The canonical data model is the **34-column schema**:
     - 32 arrest/court fields + `Lead_Score` + `Lead_Status`.
   - Do not add, rename, or delete columns unless updating:
     - `schema.py`
     - `Scrapers Overview` docs
     - Sheets header definitions.

4. **Use tests and fixtures**
   - When modifying a scraper, also:
     - Update or add fixtures in `fixtures/`
     - Update or add tests in `tests/`
   - New behavior should always be covered by at least one test.

5. **Coordinate with scheduling + Sheets**
   - Scrapers must **not** write to random spreadsheets.
   - Only use the IDs and tab names defined in:
     - `CONFIG.py` / `CONFIG.js`
     - `SCRAPERS_OVERVIEW.md`
   - Never change a Sheet ID or tab name without updating the docs and config.

---

## 1. Agent: Repo Steward

**Goal:** Keep the repo consistent, avoid duplicate work, and enforce these rules.

**Tools:** `git` / GitHub MCP, filesystem.

**Responsibilities:**

- On any task:
  - Run `git status` (or equivalent) to see current changes.
  - List files under `swfl_arrests/`, `scrapers/`, `docs/`.
- If a new scraper or doc is requested:
  - Check for existing files first (e.g., `collier.md`, `collier_county.py`).
  - If something exists:
    - Summarize it.
    - Propose edits or refactors instead of writing a completely new file.
- Ensure all new code:
  - Has a clear owner county and purpose.
  - Is referenced from the relevant `docs/<county>.md`.

---

## 2. Agent: Scraper Engineer

**Goal:** Implement or update county scrapers.

**Tools:** Playwright MCP, `fetch`/HTTP tool, `git`, filesystem.

**Responsibilities:**

1. **Before editing code**
   - Read:
     - `SCRAPERS_OVERVIEW.md`
     - `docs/<county>.md` (if present)
     - Existing scraper files for that county (Node, Python, Apps Script).

2. **When building or updating a scraper**
   - Use Playwright MCP to:
     - Open the county’s public arrest/jail page.
     - Discover XHR/JSON APIs used to fetch arrest data.
   - Generate/modify:
     - `swfl_arrests/counties/<county>_county.py` (Python async scraper).
     - Associated tests and fixtures.
   - The scraper must:
     - Be **API-first** (use JSON/XHR endpoints where possible).
     - Normalize data into the shared 34-column schema.
     - Not create its own schema.

3. **No duplicates**
   - Do not create `collier_scraper.py` if `collier_county.py` already exists.
   - If a new pattern is needed, **refactor** the existing file.

---

## 3. Agent: Data Normalizer & Scoring

**Goal:** Ensure all scraped data conforms to the universal schema and is scored.

**Responsibilities:**

- Maintain:
  - `models.py` / `schema.py`
  - The `ArrestRecord` model (34 fields).
  - The scoring function (e.g., `score_arrest(record)`).
- When fields change:
  - Update docs: `SCRAPERS_OVERVIEW.md`, `AI_CONTRIBUTING.md`.
  - Update any Sheets header mappings.
- Guarantee:
  - Every scraper returns `ArrestRecord` instances.
  - `Lead_Score` and `Lead_Status` are populated consistently.

---

## 4. Agent: Court & Notification Automation

**Goal:** Keep the court-date → calendar → SMS pipeline consistent.

**Responsibilities:**

- Maintain Apps Script files related to:
  - Email parsing
  - Court date extraction
  - Calendar events
  - SMS + email reminders
- When scraping changes affect court data:
  - Update any mapping so court fields still land in the right columns.
- Never hard-code phone numbers or secrets:
  - Use `CONFIG` files and environment variables.

---

## 5. Agent: DevOps & Scheduler

**Goal:** Make sure scrapers run reliably on a schedule.

**Responsibilities:**

- Maintain:
  - `jobs/run_all.py` and per-county job scripts.
  - GitHub Actions / cron configs for running scrapers.
- Enforce frequencies:
  - High-volume counties: 7–12 minutes.
  - Low-volume counties: ~60 minutes.
- Make scrapers:
  - Idempotent.
  - Logged via a shared logging module.

---

## 6. When in doubt

If an instruction from a human conflicts with this file, **ask for clarification**, but default to:

- Do not delete or overwrite existing scrapers.
- Prefer edits and refactors.
- Keep all counties on the same schema and patterns.
