# SWFL Arrest Scrapers - Security Guidelines

## Overview

This document outlines security best practices for the SWFL Arrest Scrapers system to protect sensitive credentials, prevent unauthorized access, and maintain data integrity.

---

## Credential Management

### Service Account Keys

**NEVER commit service account JSON files to Git**

**✅ Correct**:
```bash
# Add to .gitignore
echo "service-account-key.json" >> .gitignore
echo ".env" >> .gitignore

# Use environment variables
export GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
```

**❌ Incorrect**:
```bash
# DON'T commit credentials
git add service-account-key.json  # ❌ NEVER DO THIS
```

### Environment Variables

**Local Development**:
```bash
# Create .env file (NOT in Git)
cat > .env << EOF
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
EOF

# Load in code
import dotenv from 'dotenv';
dotenv.config();
```

**GitHub Actions**:
```yaml
# Use GitHub Secrets
env:
  GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
  GOOGLE_SA_KEY_JSON: ${{ secrets.GOOGLE_SA_KEY_JSON }}
```

**NEVER hardcode**:
```javascript
// ❌ NEVER DO THIS
const GOOGLE_SHEETS_ID = '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E';
const SERVICE_ACCOUNT_KEY = { type: 'service_account', ... };

// ✅ Use environment variables
const GOOGLE_SHEETS_ID = process.env.GOOGLE_SHEETS_ID;
```

---

## GitHub Security

### Repository Visibility

**Current**: Private  
**Recommendation**: Keep private

**Why**:
- Contains sensitive scraping logic
- Protects county website URLs
- Prevents unauthorized access to system architecture

### Branch Protection

**Enable for `main` branch**:
1. Go to: Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

### GitHub Secrets

**Configure these secrets**:

| Secret Name | Description | Access |
|-------------|-------------|--------|
| `GOOGLE_SHEETS_ID` | Target Google Sheet ID | GitHub Actions only |
| `GOOGLE_SA_KEY_JSON` | Service account JSON key | GitHub Actions only |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | Service account email | GitHub Actions only |

**How to add**:
1. Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/settings/secrets/actions
2. Click "New repository secret"
3. Add name and value
4. Click "Add secret"

**Rotation policy**:
- Rotate service account keys every 90 days
- Update GitHub Secrets immediately after rotation
- Test workflows after rotation

---

## Google Cloud Security

### Service Account Permissions

**Principle of Least Privilege**:
- Only grant necessary permissions
- Use role-based access control (RBAC)

**Recommended roles**:
- Google Sheets API: Editor (for read/write)
- Google Drive API: Viewer (if needed)

**NOT recommended**:
- Owner (too broad)
- Project Editor (too broad)

### API Key Restrictions

**Enable API restrictions**:
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on service account
3. Click "Edit"
4. Under "API restrictions":
   - Select "Restrict key"
   - Select only: Google Sheets API
5. Save

**Enable IP restrictions** (optional):
- Add GitHub Actions IP ranges
- Add your office/home IP
- Blocks all other IPs

### Audit Logging

**Enable Cloud Audit Logs**:
1. Go to: https://console.cloud.google.com/iam-admin/audit
2. Enable "Data Access" logs for Google Sheets API
3. Review logs regularly

**Monitor for**:
- Unauthorized API calls
- Failed authentication attempts
- Unusual access patterns

---

## Google Sheets Security

### Sharing Permissions

**ONLY share with**:
- Service account email (Editor)
- Authorized users (Viewer or Editor)

**NEVER**:
- Make public ("Anyone with the link")
- Share with untrusted emails

**How to verify**:
1. Open Google Sheet
2. Click "Share" button
3. Review list of people with access
4. Remove any unauthorized users

### Sheet Protection

**Protect sensitive tabs**:
1. Right-click on sheet tab
2. Select "Protect sheet"
3. Set permissions:
   - "Only you" (for Manual_Bookings)
   - "Custom" (for county tabs, allow service account)

**Protect header row**:
1. Select row 1 (header)
2. Data → Protect sheets and ranges
3. Set permissions: "Only you"

### Data Validation

**Prevent invalid data**:
1. Select column (e.g., County)
2. Data → Data validation
3. Criteria: List of items
4. Items: LEE, COLLIER, HENDRY, CHARLOTTE, MANATEE, SARASOTA, HILLSBOROUGH
5. Reject invalid input

---

## Code Security

### Input Validation

**Always validate user input**:
```javascript
function validateRecord(record) {
  // Check required fields
  if (!record.Booking_Number || record.Booking_Number.trim() === '') {
    throw new Error('Booking_Number is required');
  }
  
  // Sanitize strings
  record.Full_Name = record.Full_Name.replace(/[<>]/g, '');
  
  // Validate county
  const VALID_COUNTIES = ['LEE', 'COLLIER', 'HENDRY', 'CHARLOTTE', 'MANATEE', 'SARASOTA', 'HILLSBOROUGH'];
  if (!VALID_COUNTIES.includes(record.County)) {
    throw new Error(`Invalid county: ${record.County}`);
  }
  
  return record;
}
```

### SQL Injection Prevention

**Not applicable** (using Google Sheets API, not SQL database)

**If migrating to SQL**:
```javascript
// ✅ Use parameterized queries
const query = 'SELECT * FROM bookings WHERE booking_number = ?';
db.query(query, [bookingNumber]);

// ❌ NEVER concatenate user input
const query = `SELECT * FROM bookings WHERE booking_number = '${bookingNumber}'`;
```

### XSS Prevention

**Not applicable** (no user-facing web interface)

**If adding web interface**:
```javascript
// ✅ Escape HTML
const escaped = fullName.replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ✅ Use templating engine with auto-escaping
// (e.g., EJS, Handlebars, React)
```

### Dependency Security

**Audit dependencies regularly**:
```bash
# Check for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix

# Force fix (may break)
npm audit fix --force
```

**Use Dependabot**:
1. Go to: https://github.com/Shamrock2245/swfl-arrest-scrapers/settings/security_analysis
2. Enable "Dependabot alerts"
3. Enable "Dependabot security updates"

---

## Network Security

### HTTPS Only

**Always use HTTPS**:
```javascript
// ✅ Secure
await page.goto('https://county.com/bookings');

// ❌ Insecure
await page.goto('http://county.com/bookings');
```

### Rate Limiting

**Prevent IP bans**:
```javascript
// Add delays between requests
await delay(800 + Math.random() * 600);

// Limit concurrent requests
const MAX_CONCURRENT = 1;
```

### User-Agent Spoofing

**Appear as legitimate browser**:
```javascript
await page.setUserAgent(
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
);
```

---

## Data Security

### Data Retention

**Policy**:
- Keep arrest records for 7 years (Florida statute)
- Archive old records annually
- Delete test data after 30 days

**Implementation**:
```javascript
// Archive records older than 7 years
const cutoffDate = new Date();
cutoffDate.setFullYear(cutoffDate.getFullYear() - 7);

const oldRecords = records.filter(r => new Date(r.Booking_Date) < cutoffDate);
// Move to archive sheet or delete
```

### Data Encryption

**At rest**:
- Google Sheets: Encrypted by default (AES-256)
- GitHub: Encrypted by default

**In transit**:
- HTTPS: TLS 1.2+ (enforced by Google/GitHub)

**Service account key**:
```bash
# Encrypt with GPG (optional)
gpg --encrypt --recipient your-email@example.com service-account-key.json
```

### Data Backup

**Automated backups**:
```javascript
// Apps Script: Daily backup
function backupSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const backup = ss.copy(`Backup - ${new Date().toISOString()}`);
  
  // Move to backup folder
  const folder = DriveApp.getFolderById('BACKUP_FOLDER_ID');
  DriveApp.getFileById(backup.getId()).moveTo(folder);
}

// Set up daily trigger
```

**Manual backups**:
1. File → Download → Microsoft Excel (.xlsx)
2. Save to secure location
3. Encrypt with password (optional)

---

## Access Control

### User Roles

| Role | Access | Permissions |
|------|--------|-------------|
| Admin | Full access | Read, write, delete, configure |
| Operator | Limited access | Read, write (no delete) |
| Viewer | Read-only | View data only |
| Service Account | Automated access | Read, write (no delete) |

### Authentication

**GitHub**:
- Enable 2FA for all users
- Use SSH keys (not HTTPS passwords)
- Rotate personal access tokens every 90 days

**Google**:
- Enable 2FA for admin@shamrockbailbonds.biz
- Use strong password (16+ characters)
- Review "Recent security events" regularly

### Authorization

**Principle of Least Privilege**:
- Grant minimum necessary permissions
- Review permissions quarterly
- Revoke access immediately upon termination

---

## Incident Response

### Security Incident Types

1. **Credential compromise** (service account key leaked)
2. **Unauthorized access** (unknown user in Google Sheet)
3. **Data breach** (sensitive data exposed)
4. **System compromise** (malware, backdoor)

### Response Plan

**Step 1: Contain**
- Revoke compromised credentials immediately
- Remove unauthorized users
- Disable affected systems

**Step 2: Investigate**
- Review audit logs
- Identify scope of breach
- Document timeline

**Step 3: Remediate**
- Rotate all credentials
- Patch vulnerabilities
- Update security policies

**Step 4: Notify**
- Inform affected parties
- Report to authorities (if required)
- Document incident

**Step 5: Prevent**
- Implement additional controls
- Update security training
- Schedule security audit

### Emergency Contacts

- **System Admin**: admin@shamrockbailbonds.biz
- **Google Support**: https://support.google.com/
- **GitHub Support**: https://support.github.com/

---

## Compliance

### Legal Requirements

**Florida Public Records Law**:
- Arrest records are public information
- No special permissions needed to access
- Must comply with website terms of service

**CFAA (Computer Fraud and Abuse Act)**:
- Do not exceed authorized access
- Respect robots.txt (if present)
- Do not cause damage to systems

**GDPR (if applicable)**:
- Not applicable (public arrest records in USA)

### Ethical Considerations

**Do**:
- Respect rate limits
- Use data for legitimate business purposes
- Protect personal information

**Don't**:
- Overwhelm county websites
- Share data with unauthorized parties
- Use data for discriminatory purposes

---

## Security Checklist

### Initial Setup

- [ ] Repository is private
- [ ] .gitignore includes .env and service-account-key.json
- [ ] GitHub Secrets configured
- [ ] Service account key rotated (if old)
- [ ] Google Sheet shared only with service account
- [ ] 2FA enabled on GitHub and Google accounts

### Monthly Review

- [ ] Review GitHub Actions logs for errors
- [ ] Check Google Sheets access list
- [ ] Review Ingestion_Log for anomalies
- [ ] Run `npm audit` and fix vulnerabilities
- [ ] Verify backups are working

### Quarterly Review

- [ ] Rotate service account key
- [ ] Review user access permissions
- [ ] Audit code for security issues
- [ ] Update dependencies
- [ ] Test incident response plan

### Annual Review

- [ ] Full security audit
- [ ] Update security policies
- [ ] Review compliance requirements
- [ ] Archive old data
- [ ] Penetration testing (optional)

---

## Security Tools

### GitHub Security Features

**Dependabot**:
- Automated dependency updates
- Security vulnerability alerts

**Code Scanning**:
- Static analysis for security issues
- CodeQL queries

**Secret Scanning**:
- Detects committed credentials
- Alerts on exposed secrets

### Third-Party Tools

**npm audit**:
```bash
npm audit
npm audit fix
```

**Snyk**:
```bash
npm install -g snyk
snyk test
snyk monitor
```

**ESLint Security Plugin**:
```bash
npm install --save-dev eslint-plugin-security
```

---

## Reporting Security Issues

**DO NOT create public GitHub issues for security vulnerabilities**

**Instead**:
1. Email: admin@shamrockbailbonds.biz
2. Subject: "SECURITY: [Brief description]"
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

**Response time**:
- Acknowledgment: Within 24 hours
- Initial assessment: Within 72 hours
- Fix deployment: Within 7 days (critical), 30 days (non-critical)

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture
- **DEVELOPMENT.md** - Development guidelines
- **DEPLOYMENT.md** - Deployment procedures
- **TROUBLESHOOTING.md** - Common issues

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
