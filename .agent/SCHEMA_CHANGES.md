# 📐 Schema Changes

## The 34-Column Standard
`config/schema.json` defines the canonical arrest record format. **Every column, every county, every writer depends on this.**

## When Schema Changes Are Needed
- A jail site provides a new field that's important for all counties
- An existing field needs to be split or merged
- A field name is confusing and needs renaming

## Schema Change Process

### 1. Propose
Document the change in a PR description:
- What field(s) are being added/removed/renamed?
- Why is this needed?
- Which counties are affected?

### 2. Update Schema
Edit `config/schema.json`:
- Add new column to the `columns` array
- Add default value in `defaults` if applicable
- Add field aliases in `config/field_aliases.json`

### 3. Update Code
- `core/schema.py` — update validation if new required fields
- `core/normalizer.py` — add normalization for new field types
- `core/writers/sheets_writer.py` — update row ordering if column order changed

### 4. Update Tests
- Add test cases for new fields
- Update `expected_output.json` fixtures in affected counties

### 5. Migration
- If renaming a column, update the Google Sheet header row
- If adding a column, add it to the rightmost position in Sheets
- **NEVER** delete columns from Sheets — mark as deprecated

## Rules
- Schema changes affect ALL 67 counties — treat with extreme care
- Always add new fields as optional (with defaults) first
- Never remove a column — deprecate it by clearing values
- Changing column ORDER requires updating all writers and Sheet headers
- Test with `--dry-run` on at least 3 active counties before merging
