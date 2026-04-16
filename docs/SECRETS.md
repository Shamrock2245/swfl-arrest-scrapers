# 🔐 SECRETS — Credential Handling & Security

> **Secrets are sacred. One leak can destroy everything.**

---

## Secret Inventory

| Secret | Where Stored | Used By |
|--------|-------------|---------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | GitHub Secrets / `.env` | All writers (Sheets, Drive) |
| `GOOGLE_SHEETS_ID` | GitHub Secrets / `.env` | sheets_writer.py |
| `SLACK_WEBHOOK_URL` | GitHub Secrets / `.env` | slack_notifier.py |
| `MONGODB_URI` | GitHub Secrets / `.env` | mongo_writer.py |
| `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` | `.env` (local only) | Local development |

---

## Storage Rules

### ✅ Allowed Secret Storage
| Location | Use Case | Access |
|----------|----------|--------|
| **GitHub Secrets** | CI/CD workflows | Encrypted, injected at runtime |
| **`.env` file** | Local development | Git-ignored, never committed |
| **GAS Script Properties** | Google Apps Script secrets | Encrypted, accessed via `PropertiesService` |

### ❌ Prohibited Secret Storage
| Location | Why |
|----------|-----|
| Source code (`.py`, `.js`) | Committed to git = exposed forever |
| Config files (`.yaml`, `.json`) | Checked into version control |
| Comments or docstrings | Still in git history |
| Slack messages | Visible to all channel members |
| Log output | May be captured in CI/CD logs |
| `.env.example` values | Template should have placeholders only |

---

## Accessing Secrets in Code

### Python (Local or CI)
```python
import os
import json

# Method 1: From environment variable (string)
sheets_id = os.getenv('GOOGLE_SHEETS_ID')

# Method 2: From environment variable (JSON)
sa_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
creds_dict = json.loads(sa_json)

# Method 3: From file path
key_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH', 'creds/service-account-key.json')
with open(key_path) as f:
    creds_dict = json.load(f)
```

### GitHub Actions Workflow
```yaml
env:
  GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
  GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  MONGODB_URI: ${{ secrets.MONGODB_URI }}
```

---

## Secret Rotation Schedule

| Secret | Rotation Period | Procedure |
|--------|----------------|-----------|
| Google Service Account Key | Quarterly (90 days) | Generate new key via `gcloud`, update GitHub Secrets |
| Slack Webhook URL | Only on compromise | Regenerate in Slack admin, update all references |
| MongoDB URI | Only on compromise | Rotate password in Atlas, update connection string |
| GitHub Token | Annual | Regenerate PAT, update local config |

### Key Rotation Procedure (Google SA)
```bash
# List existing keys
gcloud iam service-account-keys list --iam-account=SA_EMAIL

# Delete old key
gcloud iam service-account-keys delete KEY_ID --iam-account=SA_EMAIL

# Create new key
gcloud iam service-account-keys create new-key.json --iam-account=SA_EMAIL

# Update GitHub Secrets
# Go to repo → Settings → Secrets → Update GOOGLE_SERVICE_ACCOUNT_JSON

# Update local .env
cp new-key.json creds/service-account-key.json
```

---

## Logging & Masking

### Never Log These
```python
# BAD — exposes secret in logs
print(f"Using key: {api_key}")
logger.info(f"MongoDB URI: {mongo_uri}")

# GOOD — mask secrets
print(f"Using key: {api_key[:8]}...")
logger.info(f"MongoDB: connected to {mongo_uri.split('@')[1] if '@' in mongo_uri else '***'}")
```

### Mask in Error Messages
```python
try:
    client = MongoClient(MONGO_URI)
except Exception as e:
    # Don't include the URI in the error
    sys.stderr.write(f"MongoDB connection failed: {type(e).__name__}\n")
    # NOT: sys.stderr.write(f"Failed connecting to {MONGO_URI}: {e}\n")
```

---

## Incident Response (Secret Compromised)

If a secret is accidentally committed to git or leaked:

1. **IMMEDIATELY** rotate the compromised credential
2. **Revoke** the old credential (delete the key, change the password)
3. **Scrub** git history if the secret was committed:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret" HEAD
   ```
4. **Force push** the cleaned history
5. **Audit** logs for unauthorized access during the exposure window
6. **Document** the incident in `LOGBOOK.md`
7. **Notify** Brendan immediately

---

## `.gitignore` Requirements

These patterns MUST always be in `.gitignore`:
```
.env
.env.*
creds/
*.json.key
*_key.json
service-account*.json
```
