---
name: repo-conventions
description: >
  Non-negotiable rules, safe refactoring patterns, shared code modification guidelines,
  secrets management, config hierarchy, and schema change process for the swfl-arrest-scrapers
  repo. Read this before modifying any core infrastructure.
---

# Repository Conventions

## The 10 Non-Negotiable Rules

### 1. Never Break Production
- Never modify a county's `solver.py` without running it locally first
- Never delete a file without checking it isn't imported elsewhere
- Never change `core/` without testing multiple counties
- Never push code that imports a module you haven't verified exists

### 2. One County, One Folder
- All county code lives in `counties/{county_name}/`
- Never put county-specific logic in `core/`
- Never put shared logic in a county folder
- Never make one county's solver depend on another county's code

### 3. Preserve the Schema
- `core/writers/sheets_writer.py` defines the 34-column `HEADER_ROW`
- Never add, remove, or rename columns without updating the writer AND all county parsers
- Dedup key is always `Booking_Number + County` — never change this

### 4. Config Hierarchy is Sacred
- **Priority**: Env vars > county YAML > county defaults > global.yaml
- Never hardcode values that belong in config
- Never put secrets in YAML files — use env vars for credentials
- Never commit `.env` files

### 5. Safe File Operations
- **Allowed to modify**: County-specific files (`counties/{name}/`)
- **Requires extra care**: `core/` modules, `config/` files
- **Never modify**: `.env` files, `creds/` directory
- **Never delete**: Any file in `core/` — deprecate first, delete later

### 6. Output Standards
- Raw scraper output → stdout as JSON array
- Logs → `sys.stderr.write()` for progress
- `print()` in `__main__` block only

### 7. Documentation Requirements
- Every new county must have its workflow YAML created
- Every change to `core/` must be documented in a commit message
- Schema changes require full migration plan

### 8. Testing Before Merge
- All county changes must pass local `--dry-run`
- All `core/` changes must pass unit tests
- Run solver standalone: `python counties/{county}/solver.py --days-back 3`

### 9. No Destructive Patterns
- Never `except: pass` — always log the error
- Never use `time.sleep()` longer than 30 seconds in a loop
- Never store credentials in code files
- Never make HTTP requests without timeout parameters
- Never write infinite loops without escape conditions

### 10. Idempotent Writes
- Every write operation must check for duplicates first
- Re-running a scraper should never create duplicate rows
- Dedup key: `Booking_Number + County`

---

## Modifying Shared Code (`core/`)

### When to Modify `core/`
✅ **DO modify** when:
- Adding a new utility that 3+ counties would use
- Fixing a bug that affects multiple counties
- Improving performance of a shared function

❌ **DON'T modify** when:
- Only one county needs different behavior — put it in the solver
- You're "cleaning up" code that works fine — leave it alone
- You want to rename a function — that breaks all imports

### The 3-County Rule
Before adding anything to `core/`, ask: **Would at least 3 counties use this?**
- Yes → put it in `core/`
- No → keep it in the county's solver

### Safe Change Patterns

**Adding a new function** ✅ Safe
```python
# core/stealth.py
def handle_recaptcha(page):  # NEW — no existing callers
    ...
```

**Adding an optional parameter** ✅ Safe
```python
# default preserves old behavior
def wait_for_cloudflare(page, max_wait=20, retry_on_fail=False):
```

**Changing behavior of existing function** ❌ DANGEROUS
```python
# BEFORE — returns True/False
def wait_for_cloudflare(page):
    return True
# AFTER — now returns dict
def wait_for_cloudflare(page):
    return {"cleared": True, "wait_time": 5}
# Every caller expects True/False!
```

### Required Steps After Modifying `core/`
1. Run at least 2 active county solvers locally
2. Update module docstrings if signatures changed
3. Document the change in your commit message

### Function Deprecation Pattern
```python
import warnings
def old_function():
    warnings.warn("old_function is deprecated, use new_function", DeprecationWarning)
    return new_function()
```

---

## Safe Refactoring Rules

### Core Principle
> **If it works, and nobody asked you to change it, leave it alone.**

### When Refactoring Is SAFE
✅ Renaming a local variable inside a single function
✅ Adding a docstring to an undocumented function
✅ Extracting a helper function WITHIN the same file
✅ Adding type hints to existing parameters
✅ Removing dead code (verified unused with `grep`)
✅ Fixing a typo in comments

### When Refactoring Is DANGEROUS
❌ Renaming a function or method that's imported elsewhere
❌ Changing return types of existing functions
❌ Moving a file to a different directory
❌ Changing function parameter names (breaks keyword callers)
❌ "Simplifying" error handling (may hide real errors)
❌ Replacing a working library with a "better" one
❌ Merging two functions that "do the same thing" without verifying

### County-Specific Code
- **Never** refactor a county solver that's running in production unless asked
- **Never** merge two county solvers "because they look similar"
- **Always** preserve county-specific workarounds (they're there for a reason)
- If you find duplicated logic across 3+ counties, extract to `core/` — but keep the original code working until all counties are migrated

---

## Secrets and Configuration

### Config Hierarchy (Priority Order)
1. **Environment variables** (highest) — for secrets and CI overrides
2. **`config/counties/{county}.yaml`** — per-county overrides
3. **`config/counties/_defaults.yaml`** — shared county defaults
4. **`config/global.yaml`** — system-wide defaults (lowest)

### What Goes Where

**In `config/global.yaml`** (checked into git):
- Timeout values, retry counts, backoff settings
- Output directory paths, writer enable/disable flags
- Browser settings (headless, window size)

**In `config/counties/{name}.yaml`** (checked into git):
- Site URLs, pagination type, selectors
- Schedule cron expressions
- County-specific overrides (days_back, max_pages)

**In Environment Variables** (NEVER in git):
- `GOOGLE_SHEETS_ID` — Spreadsheet ID
- `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` — Path to JSON credentials
- `SLACK_WEBHOOK_URL` — Slack webhook
- `MONGO_URI` — MongoDB connection string

### Rules
1. **NEVER** commit `.env` files
2. **NEVER** commit `creds/` directory contents
3. **NEVER** hardcode API keys, passwords, or tokens in code
4. **NEVER** log secrets — mask them in logging output
5. **ALWAYS** use `os.getenv()` to access secrets

---

## Schema Change Process

The 34-column `HEADER_ROW` in `core/writers/sheets_writer.py` is the source of truth.

### When Schema Changes Are Needed
- A jail site provides a new field important for all counties
- An existing field needs to be split or merged
- A field name is confusing and needs renaming

### Process
1. **Propose**: Document what fields change and why
2. **Update Code**: `sheets_writer.py` HEADER_ROW, dedup logic, any normalization
3. **Update Tests**: Add test cases for new fields, update fixtures
4. **Migration**: If adding a column, add to the rightmost position in Sheets

### Rules
- Schema changes affect ALL counties — treat with extreme care
- Always add new fields as optional (with defaults) first
- Never remove a column from Sheets — deprecate by clearing values
- Changing column ORDER requires updating all writers and Sheet headers
- Test with `--dry-run` on at least 3 active counties before merging
