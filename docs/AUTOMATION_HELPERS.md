# Automation Helpers

## Slack Alerts
| Trigger | Message Type |
|----------|---------------|
| Success | ✅ Rows added/updated summary |
| Warning | ⚠️ Header drift / null-rate anomaly |
| Error | ❌ Scraper blocked / captcha detected |

Example payload:
```json
{
  "text": "✅ Lee County scrape complete\nAdded: 23\nUpdated: 5\nNulls: 2%"
}
```

## Google Sheet Reference
All scrapers write to the master sheet: https://docs.google.com/spreadsheets/d/10mphJQkWlDoscDoY8CGFPt96yzoB7rAbDTRrR02orUY/edit

## Future Integration
- SignNow document generation for qualified leads.
- SOCKS5 proxy configuration for external risk database lookups.
