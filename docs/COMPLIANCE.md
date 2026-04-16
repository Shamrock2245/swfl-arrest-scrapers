# ⚖️ COMPLIANCE — Legal, Privacy & Data Handling

> **We scrape public records. We follow the law. Period.**

---

## Legal Foundation

### Florida Public Records Law (Chapter 119, Florida Statutes)
- All arrest records in Florida are **public records** under F.S. §119.01
- Booking information, charges, and mugshots are **publicly accessible** by law
- We scrape ONLY data that is already published on public-facing jail/sheriff websites
- We do NOT access restricted systems, internal databases, or sealed records

### What We May Collect
✅ Booking number, name, charges, bond amount, custody status
✅ Mugshot URLs (publicly posted by the sheriff's office)
✅ Court dates and case numbers (public court records)
✅ Arresting agency information
✅ Booking and arrest dates/times

### What We May NOT Collect
❌ Social Security Numbers
❌ Financial account information
❌ Victim information or names
❌ Juvenile records (defendants under 18)
❌ Sealed or expunged records
❌ Medical or mental health information
❌ Attorney-client privileged information

---

## Data Classes & Suppression

### Suppressed Classes (NEVER Contact)
These individuals must be identified and suppressed from all outreach:

| Class | Rule | How to Detect |
|---|---|---|
| **Minors** | Never contact or store data for anyone under 18 | DOB check — if `age < 18`, suppress |
| **Sealed/Expunged** | Immediately delete if discovered | County flags or court records showing sealed status |
| **Federal detainees** | Do not contact — federal bond system is different | Charges containing "Federal", "U.S.", "ICE Hold" |
| **Capital offenses** | Do not contact — non-bondable | Murder 1st/2nd degree, Capital Sexual Battery |
| **Deceased** | Remove from all systems | Release status = "Deceased" or equivalent |

### Data Minimization
- Collect **only** what is needed for bond services
- Do not store data beyond the 34-column schema unless county-specific and relevant
- Physical descriptions (height, weight, hair/eye color) are retained ONLY for identification
- Address information is used ONLY for service area verification

---

## Consumer Contact Compliance

### TCPA (Telephone Consumer Protection Act)
- **No auto-dial** to cell phones without prior express consent
- **No prerecorded messages** to cell phones
- Applies to SMS, WhatsApp, and voice calls
- The Closer's drip campaigns MUST use human-initiated or properly consented messaging

### 10DLC (10-Digit Long Code) Compliance
- All Twilio SMS messaging must be 10DLC registered
- Campaign use case: "Legal services notification"
- **Current status**: Pending reapplication (see ROADMAP.md)
- Until approved: SMS outreach via Node-RED is paused

### CAN-SPAM
- Every automated email must include:
  - Clear identification of sender (Shamrock Bail Bonds)
  - Physical address (1528 Broadway, Ft. Myers, FL 33901)
  - Unsubscribe mechanism
  - Honest subject lines

---

## Opt-Out Rules

### Opt-Out Mechanisms
Any individual who requests to not be contacted MUST be immediately and permanently suppressed:

1. **SMS opt-out**: Reply `STOP` → automatic suppression in Twilio
2. **Email opt-out**: Unsubscribe link → automatic suppression
3. **Verbal opt-out**: If Shannon (voice AI) or a human receives a "don't contact me" → manual suppression
4. **Written opt-out**: Any written request → permanent suppression

### Suppression Storage
- Suppressed contacts stored in GAS `SuppressionList` collection
- Checked BEFORE any outreach attempt
- **Retention**: Permanent (never re-contact an opted-out individual)
- Cross-referenced across ALL channels (SMS, email, Telegram, voice)

---

## Data Retention

| Data Type | Retention | Deletion Method |
|---|---|---|
| Active arrest records | Indefinite | Never deleted from Sheets |
| Qualified leads | Indefinite | Never deleted |
| Ingestion logs | 90 days | Archive to `Log_Archive` tab |
| HTML fixtures | 30 days | CI maintenance prunes |
| Opt-out records | Permanent | Never deleted |
| Scraper logs | 30 days | Automatic rotation |

### Right to Deletion
If an individual requests deletion of their data:
1. We are NOT required to delete public record data under Florida law
2. However, we MUST stop all outreach and add to suppression list
3. If data was obtained from a non-public source, we MUST delete it

---

## Rate Limiting & Ethical Scraping

### We Follow These Rules
1. **Respect `robots.txt`** — Check before scraping any new county
2. **Rate limit all requests** — Minimum 2-second delay between requests to same domain
3. **No login wall bypass** — If a site requires authentication, we do NOT scrape it
4. **No CAPTCHA cracking** — If a site uses CAPTCHA as primary defense, we flag and pause
5. **Identify as scrapers when asked** — If a county contacts us, we cooperate
6. **Public data only** — We never access admin panels, restricted areas, or API endpoints requiring keys we don't own

### If a County Asks Us to Stop
1. **Immediately pause** the affected county scraper
2. **Document** the request in `LOGBOOK.md`
3. **Notify** Brendan via Slack `#scraper-alerts`
4. **Do NOT resume** without explicit human authorization
5. Consider alternative data sources (e.g., Florida FDLE feed)

---

## Audit Trail

Every data access and modification is logged:
- **Scraper runs**: `Ingestion_Log` tab in Google Sheets
- **API calls**: GitHub Actions workflow logs (retained 90 days)
- **Data exports**: Drive activity log
- **Schema changes**: Git commit history
- **Suppression additions**: GAS SuppressionList audit log
