---
name: gws-sheets
description: "Google Sheets: Read and write spreadsheets via the Sheets API v4."
metadata:
  version: 0.22.5
  openclaw:
    category: "productivity"
    requires:
      bins:
        - gws
    cliHelp: "gws sheets --help"
---

# sheets (v4)

> **PREREQUISITE:** Read `../gws-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `gws generate-skills` to create it.

```bash
gws sheets <resource> <method> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| `+append` | Append a row to a spreadsheet |
| `+read` | Read values from a spreadsheet |

## API Resources

### spreadsheets

  - `batchUpdate` — Applies one or more updates to the spreadsheet. Each request is validated before being applied. If any request is not valid then the entire request will fail and nothing will be applied.
  - `create` — Creates a spreadsheet, returning the newly created spreadsheet.
  - `get` — Returns the spreadsheet at the given ID.
  - `getByDataFilter` — Returns the spreadsheet at the given ID with data filtering.
  - `developerMetadata` — Operations on the 'developerMetadata' resource
  - `sheets` — Operations on the 'sheets' resource
  - `values` — Operations on the 'values' resource

## Discovering Commands

Before calling any API method, inspect it:

```bash
# Browse resources and methods
gws sheets --help

# Inspect a method's required params, types, and defaults
gws schema sheets.<resource>.<method>
```

Use `gws schema` output to build your `--params` and `--json` flags.

## Scraper-Specific Patterns

### Writing Arrest Records
```python
# Our SheetsWriter uses the Sheets API v4 to insert at row 2 (newest first)
from core.writers.sheets_writer import SheetsWriter
writer = SheetsWriter(sheet_id)
result = writer.write_records(records, county="Lee")
# result = {'new_records': N, 'duplicates_skipped': N, 'qualified_records': N}
```

### Deduplication
```python
# Booking_Number + County is the dedup key
# SheetsWriter checks existing Booking_Number column before insert
```

### Tab Naming Convention
Each county gets its own tab: `Lee`, `Charlotte`, `Collier`, etc.
The `Qualified_Arrests` tab aggregates high-value leads across all counties.
