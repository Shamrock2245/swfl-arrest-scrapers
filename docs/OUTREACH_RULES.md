# 📞 OUTREACH_RULES — Contact Workflow & Messaging Rules

> **We reach out to help. We do it legally, ethically, and respectfully.**

---

## Core Principles

1. **Public records are public** — We may contact individuals whose arrest data is publicly posted
2. **One chance, not harassment** — Respectful contact, never aggressive
3. **Opt-out is sacred** — If someone says stop, we stop forever
4. **Timing matters** — Contact during appropriate hours only
5. **Comply with all laws** — TCPA, 10DLC, CAN-SPAM, Florida statutes

---

## Contact Channels (Priority Order)

| Channel | Status | Owner | Tool |
|---|---|---|---|
| 1. **In-Person** | ✅ Active | Human staff | Walk-in at 1528 Broadway |
| 2. **Phone (Inbound)** | ✅ Active | Shannon (Voice AI) | ElevenLabs |
| 3. **Telegram** | ✅ Active | Manus Brain | Telegram Bot API |
| 4. **SMS** | ⏸️ Paused (10DLC) | The Closer | Twilio |
| 5. **WhatsApp** | ⏸️ Blocked (10DLC) | The Closer | Twilio |
| 6. **Email** | 📋 Planned | The Closer | TBD |
| 7. **Web Chat** | ✅ Active | The Concierge | Wix Portal |

---

## Contact Timing Windows

| Day | Allowed Hours (ET) | Notes |
|-----|---------------------|-------|
| Monday–Friday | 9:00 AM – 8:00 PM | Standard business + evening |
| Saturday | 10:00 AM – 6:00 PM | Reduced window |
| Sunday | 12:00 PM – 5:00 PM | Minimal window |
| Federal holidays | **NO CONTACT** | Suppress all automated outreach |

**After-hours inbound**: Shannon (voice AI) handles calls 24/7. Outbound messaging is time-windowed only.

---

## The Closer — Drip Campaign Rules

The Closer handles abandoned intake follow-ups via SMS/WhatsApp:

### Sequence Timing
| Touch | Delay | Message Type | Channel |
|-------|-------|-------------|---------|
| 1 | +30 minutes | "We can help" intro | SMS |
| 2 | +4 hours | Bond amount + next steps | SMS |
| 3 | +24 hours | "Still in custody?" check | SMS |
| 4 | +72 hours | Final opportunity | SMS |
| **STOP** | After touch 4 | No further contact | — |

### Rules
1. **MAX 4 touches** per individual per arrest event
2. **STOP immediately** on any "STOP", "No", "Don't contact me" reply
3. **Never re-contact** after 4 touches, even if still in custody
4. **Separate arrest = separate sequence** — A new arrest resets the counter
5. **No contact if released** — Check custody status before each touch
6. **Same arrest, same channel** — Don't cross-channel blast (SMS + WhatsApp + email for same event)

---

## Message Content Rules

### Required Elements
- Identify as Shamrock Bail Bonds
- Include our phone number: (239) 384-1945
- Include opt-out instructions: "Reply STOP to unsubscribe"
- Be factual — state the bond amount, not opinions

### Prohibited Content
❌ No pressure language ("You MUST call us", "Time is running out")
❌ No legal advice or opinions on charges
❌ No discussion of victims or case details
❌ No mention of co-defendants
❌ No information about ongoing investigations
❌ No claims about judge behavior or court outcomes
❌ No disparaging other bail bond agencies

### Tone Guidelines
- **Professional**: We are a licensed business providing a legal service
- **Empathetic**: This is someone's worst day. Be human.
- **Brief**: Under 160 characters per SMS when possible
- **Clear**: Bond amount, next steps, how to reach us. That's it.

---

## Who NOT to Contact (Suppression List)

Before ANY outreach, check against the suppression list:

| Suppressed Category | Detection Method |
|---|---|
| Minors (under 18) | DOB check |
| Opted-out individuals | SuppressionList collection in GAS |
| Capital offense charges | Charge keyword filter (Murder, Capital) |
| Federal detainees | "Federal" / "ICE" in charges |
| Released individuals | Status check at time of outreach |
| Previously contacted (4 touches) | Touch counter in GAS |
| Do-not-call registry | TBD — future integration |

---

## Inbound Lead Handling

When someone contacts US (inbound):

1. **Answer immediately** — Shannon handles 24/7 voice, Concierge handles chat
2. **Verify identity** — Confirm name matches a recent booking
3. **Provide bond info** — Bond amount, premium (typically 10%), next steps
4. **Start intake** — If they want to proceed, begin intake flow
5. **Send paperwork** — SignNow packet via SMS/Telegram within 5 minutes
6. **Track in CRM** — Log in IntakeQueue (Wix CMS + Google Sheets)

---

## Compliance Checkpoints

Before deploying any new outreach workflow:
- [ ] Reviewed by human (Brendan)
- [ ] TCPA-compliant (no auto-dial without consent)
- [ ] 10DLC approved (for SMS campaigns)
- [ ] Opt-out mechanism tested and working
- [ ] Suppression list check integrated
- [ ] Contact timing windows enforced
- [ ] Message content reviewed for prohibited elements
