# 🚫 Agent Rules — Non-Negotiable

These rules are **absolute**. No exceptions, no overrides.

---

## 1. Never Break Production
- Never modify a county's `solver.py` without running its tests
- Never delete a file without checking it isn't imported elsewhere
- Never change `core/` without running **all** tests
- Never push code that imports a module you haven't verified exists

## 2. One County, One Folder
- All county code lives in `counties/{county_name}/`
- Never put county-specific logic in `core/`
- Never put shared logic in a county folder
- Never make one county's solver depend on another county's code

## 3. Preserve the Schema
- `config/schema.json` defines the canonical 34-column format
- Never add, remove, or rename columns without updating schema.json AND all county parsers
- Always validate against the schema after normalization
- Dedup key is always `Booking_Number + County` — never change this

## 4. Config Hierarchy is Sacred
- **Priority**: Env vars > county YAML > county defaults > global.yaml
- Never hardcode values that belong in config
- Never put secrets in YAML files — use env vars for credentials
- Never commit `.env` files

## 5. Safe File Operations
- **Allowed to modify**: County-specific files (`counties/{name}/`)
- **Requires extra care**: `core/` modules, `config/` files
- **Never modify**: `config/schema.json` (without full migration plan), `.env` files, `creds/`
- **Never delete**: Any file in `core/` — deprecate first, delete in a later PR

## 6. Output Standards
- Raw scraper output → `output/raw/{county}/YYYY-MM-DD_raw.json`
- Normalized output → `output/normalized/{county}/YYYY-MM-DD_normalized.json`
- Failed records → `output/failed/{county}/YYYY-MM-DD_failed.json`
- Logs → `logs/{county}/YYYY-MM-DD.jsonl`

## 7. Documentation Requirements
- Every county must have `README.md` and `quirks.md`
- Every change to `core/` must be documented in a commit message
- Schema changes require updating `.agent/SCHEMA_CHANGES.md`

## 8. Testing Before Merge
- All county changes must pass their parser test
- All `core/` changes must pass unit tests
- All changes must pass `scripts/run_county.py {county} --dry-run`

## 9. No Destructive Patterns
- Never `except: pass` — always log the error
- Never use `time.sleep()` longer than 30 seconds in a loop
- Never store credentials in code files
- Never make HTTP requests without timeout parameters
- Never write infinite loops without escape conditions

## 10. Idempotent Writes
- Every write operation must check for duplicates first
- Re-running a scraper should never create duplicate rows
- Dedup key: `Booking_Number + County`
