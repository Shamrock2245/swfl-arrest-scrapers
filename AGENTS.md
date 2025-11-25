# AGENTS.md — AI Operating Protocol for SWFL Arrest Scrapers

This document defines the rules all AI assistants (Manus, ChatGPT, GitHub Copilot, Claude, Cursor, etc.) MUST follow when interacting with this repository.  
Its purpose is to prevent duplicate work, ensure scraper consistency, maintain data integrity, and preserve human architecture decisions.

---

# 0. ABSOLUTE RULES (NON-NEGOTIABLE)

1. **Always inspect the repository BEFORE generating any code.**  
   - Use filesystem or GitHub MCP to list:
     - `/swfl_arrests/`
     - `/swfl_arrests/counties/`
     - `/fixtures/`
     - `/tests/`
     - Any existing `.md` files
   - Summarize findings before writing anything.

2. **Never create duplicate scrapers.**  
   - Every county has **one** authoritative scraper file:  
     `swfl_arrests/counties/<county>_county.py`  
   - If a file already exists, extend/refactor it instead of generating a new one.

3. **Never modify the schema without explicit human instruction.**  
   - The official schema is **34 fields**:  
     - 32 arrest/court fields  
     - + `Lead_Score`  
     - + `Lead_Status`  
   - All scrapers must output normalized records in this schema.

4. **All scrapers MUST be API-first and asynchronous.**  
   - Use JSON/XHR endpoints discovered via Playwright MCP.  
   - Do NOT build HTML scrapers unless explicitly instructed.  
   - Respect county rate limits and schedule cycles.

5. **All changes must be safe, minimal, and reviewed.**  
   - Always show diffs before finalizing.  
   - Never delete or heavily refactor code without summarizing what currently exists.

---

# 1. SCRAPER ENGINEER AGENT RULES

These rules apply when the AI is writing or modifying a scraper.

## 1.1. Before coding anything
- Check for:
  - Existing scraper file  
  - Existing docs for the county  
  - Existing fixtures/tests  
  - Existing shared utilities
- Report what exists and propose the minimal change.

## 1.2. When generating or updating a scraper
- The scraper must expose:

  ```python
  async def scrape_<county>_county_arrests(config) -> list[ArrestRecord]:
      ...

Use httpx or aiohttp.

Use endpoints discovered via Playwright MCP.

Normalize data into the 34-column ArrestRecord via the shared model.

1.3. Bond scoring must ALWAYS run

Every returned arrest record must include:

Lead_Score

Lead_Status

Scoring uses the shared scoring utility in models.py (or the equivalent module).

2. MCP & PLAYWRIGHT USAGE RULES

AI is authorized to use Playwright MCP but must follow these constraints:

Use Playwright MCP ONLY to discover:

API endpoints

Request headers

URL patterns

Required cookies (Cloudflare, Revize, etc.)

Do NOT write full scrapers using browser automation.

Browser automation is ONLY for reconnaissance.

The final scraper must use direct HTTP requests.

For Cloudflare counties (Charlotte, sometimes Sarasota):

Use persistent browser state via MCP to extract cookies.

Do not attempt to bypass Cloudflare with automated clicking unless explicitly asked.

Instead: discover API → build HTTP scraper → inject required cookies into headers.

3. FILE STRUCTURE RULES

AI must respect and maintain the following structure:

swfl_arrests/
  models.py
  schema.py
  utils/
  counties/
    collier_county.py
    charlotte_county.py
    manatee_county.py
    sarasota_county.py
    hendry_county.py
    desoto_county.py
fixtures/
tests/
docs/


No other structure should be introduced without human approval.

4. TESTING & FIXTURE RULES

Every scraper modification must include:

A fixture update (fixtures/<county>_sample.json)

A test update (tests/test_<county>_county.py)

Tests must verify:

Booking_Number

Name parsing

Bond fields

Court fields

Lead_Score

Lead_Status

5. COURT-DATE & AUTOMATION PIPELINE RULES

When interacting with court/email/calendar/SMS automation:

Never modify calendar or SMS logic unless explicitly instructed.

Ensure scraper output keeps:

Court_Date

Court_Time

Court_Location

Ensure nothing breaks the:

Court date → Calendar event → SMS → Reminder flow.

6. SAFETY CHECK BEFORE ANY FINAL ACTION

Before the AI writes or modifies any files, it must:

Summarize:

What exists

What will change

Why the change is safe

Display:

A full diff preview of changes

Ask:

“Confirm before I write these changes.”

7. HUMAN OVERRIDE CLAUSE

Humans can override any rule in this file by explicitly stating:

“Override AGENTS.md rule(s). Continue.”

AI must log which rule was overridden and proceed.
