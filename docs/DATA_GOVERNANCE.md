# Data Governance

## PII Scope
Name, DOB, address, and charges data are public records. Collected only for operational use.

## Retention
| Data Type | Retain For | Location |
|------------|-------------|-----------|
| Raw scrape | 30 days | Drive /BailOps/Raw/ |
| Normalized JSON | 60 days | Drive /BailOps/Normalized/ |
| SignNow packets | 7 years | Drive /BailOps/Packets/ |
| Logs | 90 days | Sheets ingestion_log |

## Security
- Google Workspace domain sharing only.
- GitHub Secrets or Manus Secrets for keys.
- Rotate every quarter.
- 2FA enabled for Google + SignNow accounts.
