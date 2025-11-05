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
