# 📊 SCORING — Lead Qualification Algorithm

> **Not every arrest is a lead. Scoring separates the signal from the noise.**

---

## How It Works

Every normalized arrest record is scored 0-100 based on:
1. **Bond amount** — Is there a bondable amount in the sweet spot?
2. **Charge severity** — Are these charges we can bond?
3. **Recency** — Was this arrest recent enough to act on?
4. **Data completeness** — Do we have enough info to make contact?
5. **Custody status** — Is the person still in jail?

---

## Scoring Rubric (Max 100 Points)

### Positive Modifiers (Adding Points)

| Factor | Points | Condition |
|---|---|---|
| **Bond Sweet Spot** | +30 | `$500 ≤ Bond_Amount ≤ $50,000` |
| **High Bond** | +20 | `$50,001 ≤ Bond_Amount ≤ $100,000` |
| **Premium Bond** | +10 | `Bond_Amount > $100,000` |
| **In Custody** | +20 | `Status = "In Custody"` |
| **Bondable Charge** | +20 | Keywords: Battery, DUI, Theft, Drug, Burglary, Assault, Domestic |
| **Cash/Surety Bond** | +25 | `Bond_Type IN ("Cash", "Surety")` |
| **Data Complete** | +15 | All required fields present + DOB + charges |
| **Recent Booking** | +10 | Booked within last 24 hours |
| **Serious Charge** | +20 | Felony-level charge with bondable amount |

### Negative Modifiers (Subtracting Points)

| Factor | Points | Condition |
|---|---|---|
| **Released** | -30 | `Status = "Released"` or `"Bonded Out"` |
| **No Bond** | -50 | `Bond_Amount = 0` or `Bond_Type = "No Bond"` |
| **Capital Charge** | -100 | Murder, Capital Sexual Battery, Federal charges |
| **Hold/Detainer** | -30 | ICE hold, out-of-county warrant, federal detainer |
| **Minor Offense** | -10 | Trespassing, loitering, open container |
| **Old Booking** | -10 | Booked more than 7 days ago |

---

## Classification Thresholds

| Score Range | Status | Color | Slack Alert | Action |
|---|---|---|---|---|
| **≥ 70** | 🔴 `Hot` | Red | `@channel` in `#leads` | **Immediate outreach** |
| **40–69** | 🟡 `Warm` | Yellow | Summary only | Priority follow-up |
| **1–39** | 🔵 `Cold` | Blue | None | Archive for analytics |
| **≤ 0** | ⚫ `Disqualified` | Black | None | Capital/federal flag — do not contact |

---

## Scoring Configuration

The scoring rules are defined in `config/schema.json` under `qualificationRules`:

```json
{
  "qualificationRules": {
    "minScore": 50,
    "scoring": {
      "bondAmount": [
        { "min": 5000, "points": 40 },
        { "min": 2000, "points": 30 },
        { "min": 1000, "points": 20 },
        { "min": 500,  "points": 10 }
      ],
      "seriousCharges": {
        "keywords": ["dui", "battery", "assault", "felony", "drug", "theft", "domestic", "violence"],
        "points": 20
      },
      "recency": [
        { "daysAgo": 1, "points": 30 },
        { "daysAgo": 3, "points": 20 },
        { "daysAgo": 7, "points": 10 }
      ]
    }
  }
}
```

---

## What Makes a "Qualified" Lead

A record is mirrored to the `Qualified_Arrests` tab when **all** of these are true:
1. `Lead_Score ≥ 50` (configurable via `minScore`)
2. `Lead_Status` is `Hot` or `Warm`
3. `Bond_Amount > 0` (there's actually a bond to post)
4. `Status` is NOT `Released` or `Bonded Out`
5. Record is not a duplicate of an existing qualified lead

---

## Disqualification Rules (Automatic Score = 0)

These conditions immediately disqualify a record:
- **Capital offenses**: Murder (1st/2nd degree), Capital Sexual Battery
- **Federal charges**: Any charge with "Federal" or "U.S." prefix
- **Non-bondable holds**: Immigration (ICE), out-of-state warrants with "No Bond"
- **Juvenile records**: Any indication the defendant is under 18

---

## Reason Codes

Every scored record includes machine-readable reason codes explaining how the score was derived:

| Code | Meaning | Points Impact |
|---|---|---|
| `BOND_SWEET_SPOT` | Bond in $500–$50K range | +30 |
| `BOND_HIGH` | Bond $50K–$100K | +20 |
| `BOND_PREMIUM` | Bond >$100K | +10 |
| `IN_CUSTODY` | Currently detained | +20 |
| `BONDABLE_CHARGE` | Charge matches bondable keywords | +20 |
| `CASH_SURETY` | Cash or surety bond type | +25 |
| `DATA_COMPLETE` | All key fields present | +15 |
| `RECENT_BOOKING` | Booked within 24h | +10 |
| `SERIOUS_CHARGE` | Felony with bondable amount | +20 |
| `RELEASED` | Already released | -30 |
| `NO_BOND` | Zero bond or "No Bond" type | -50 |
| `CAPITAL_CHARGE` | Murder / Capital offense | -100 |
| `HOLD_DETAINER` | ICE / federal / out-of-state hold | -30 |
| `MINOR_OFFENSE` | Low-severity charge | -10 |
| `OLD_BOOKING` | Booked >7 days ago | -10 |
| `DQ_MINOR` | Defendant under 18 | Disqualified |
| `DQ_FEDERAL` | Federal jurisdiction | Disqualified |

**Output format**: `reason_codes` field is a pipe-separated list: `BOND_SWEET_SPOT|IN_CUSTODY|BONDABLE_CHARGE`

---

## Manual Review Conditions

These conditions flag a record for `REVIEW_HOLD` — human must clear before outreach:

| Condition | Why |
|-----------|-----|
| `Bond_Amount` is negative or unrealistically high (>$10M) | Likely parser error |
| `Booking_Date` is in the future | Data integrity issue |
| `DOB` implies age >100 or <0 | Bad data or parsing failure |
| `Lead_Score` between 45–55 (borderline qualified) | Human should validate quality |
| Charge text is `UNKNOWN` or empty but bond exists | May be bondable but unverifiable |
| 3+ records for the same person in 24h | Possible dedup failure or rebooking |
| County first seen (new county launch) | 72-hour burn-in monitoring |

---

## Scoring vs. Business Value

| Lead_Score | What It Means for the Business |
|---|---|
| **85-100** | Premium lead — high bond, in custody, recent booking. Call immediately. |
| **70-84** | Hot lead — bondable amount, likely still in jail. Same-day outreach. |
| **50-69** | Warm lead — may have lower bond or partial data. Follow up within 24h. |
| **20-49** | Cold lead — low bond, released, or old booking. Archive for patterns. |
| **0-19** | Not viable — no bond, capital charge, or insufficient data. |

---

## Source of Truth
- **Scoring config**: `config/schema.json` → `qualificationRules`
- **Scorer implementation**: `python_scrapers/scoring/lead_scorer.py`
- **GAS scorer**: `LeadScoringSystem.js` (in `shamrock-bail-portal-site`)
