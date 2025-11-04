# Fixtures

This directory contains saved HTML samples from county websites for testing and development.

## Structure

Each county has its own subdirectory:
- `list.html` - List/search page
- `detail-1.html` - First detail page example
- `detail-2.html` - Second detail page example

## Usage

Fixtures help with:
1. **Testing** - Run scrapers offline against known HTML
2. **Development** - Iterate on selectors without hitting live sites
3. **Debugging** - Compare working vs broken HTML when sites change

## Updating Fixtures

When a county site changes:
```bash
# Manually save pages from browser:
# 1. Visit site in Chrome
# 2. Right-click → Save As → Web Page, Complete
# 3. Move HTML to appropriate fixtures/ subdirectory
```

## Do Not Commit Sensitive Data

Ensure fixture files don't contain:
- Real booking numbers that could identify individuals
- Personally identifiable information (PII)
- Images or mugshots

Sanitize if necessary before committing.
