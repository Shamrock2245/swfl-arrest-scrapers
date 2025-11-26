# SWFL Arrest Scrapers - 34-Column Data Schema

## Overview

All county scrapers normalize data to a standardized **34-column schema** for consistent storage and lead scoring.

**Version**: 2.0  
**Last Updated**: November 26, 2025

---

## Column Definitions

### 1-10: Booking Identification

| # | Column | Type | Required | Format | Description |
|---|--------|------|----------|--------|-------------|
| 1 | `Booking_Number` | String | ✅ Yes | Alphanumeric | Unique booking/inmate ID (primary key) |
| 2 | `Full_Name` | String | ✅ Yes | LAST, FIRST MIDDLE | Complete name as shown on booking |
| 3 | `First_Name` | String | No | Proper Case | First name only |
| 4 | `Last_Name` | String | No | Proper Case | Last name only |
| 5 | `DOB` | String | No | MM/DD/YYYY | Date of birth |
| 6 | `Sex` | String | No | M/F/U | Gender (M=Male, F=Female, U=Unknown) |
| 7 | `Race` | String | No | W/B/H/A/O | Race code (W=White, B=Black, H=Hispanic, A=Asian, O=Other) |
| 8 | `Arrest_Date` | String | No | MM/DD/YYYY | Date of arrest |
| 9 | `Arrest_Time` | String | No | HH:MM AM/PM | Time of arrest |
| 10 | `Booking_Date` | String | ✅ Yes | MM/DD/YYYY | Date booked into jail |

### 11-20: Location & Agency

| # | Column | Type | Required | Format | Description |
|---|--------|------|----------|--------|-------------|
| 11 | `Booking_Time` | String | No | HH:MM AM/PM | Time booked into jail |
| 12 | `Agency` | String | No | Text | Arresting agency (e.g., "HCSO", "Tampa PD") |
| 13 | `Address` | String | No | Text | Street address of arrestee |
| 14 | `City` | String | No | Text | City of residence |
| 15 | `State` | String | No | FL | State (usually FL) |
| 16 | `Zipcode` | String | No | 12345 or 12345-6789 | ZIP code |
| 17 | `Charges` | String | No | Text | All charges separated by "; " |
| 18 | `Charge_1` | String | No | Text | Primary charge description |
| 19 | `Charge_1_Statute` | String | No | Text | Florida statute number for charge 1 |
| 20 | `Charge_1_Bond` | String | No | $0.00 | Bond amount for charge 1 |

### 21-30: Charges & Bond

| # | Column | Type | Required | Format | Description |
|---|--------|------|----------|--------|-------------|
| 21 | `Charge_2` | String | No | Text | Secondary charge description |
| 22 | `Charge_2_Statute` | String | No | Text | Florida statute number for charge 2 |
| 23 | `Charge_2_Bond` | String | No | $0.00 | Bond amount for charge 2 |
| 24 | `Bond_Amount` | String | No | $0.00 | Total bond amount (sum of all charges) |
| 25 | `Bond_Type` | String | No | Text | Type of bond (CASH, SURETY, ROR, NO BOND, etc.) |
| 26 | `Status` | String | No | Text | Custody status (IN, OUT, IN CUSTODY, RELEASED, etc.) |
| 27 | `Court_Date` | String | No | MM/DD/YYYY | Next court appearance date |
| 28 | `Case_Number` | String | No | Text | Court case number |
| 29 | `Mugshot_URL` | String | No | URL | Full URL to mugshot image |
| 30 | `County` | String | ✅ Yes | UPPERCASE | County name (LEE, COLLIER, HENDRY, etc.) |

### 31-34: Metadata & Lead Scoring

| # | Column | Type | Required | Format | Description |
|---|--------|------|----------|--------|-------------|
| 31 | `Court_Location` | String | No | Text | Courthouse location |
| 32 | `Detail_URL` | String | No | URL | Full URL to booking detail page |
| 33 | `Lead_Score` | Number | No | 0-100 | Calculated lead qualification score |
| 34 | `Lead_Status` | String | No | Hot/Warm/Cold/Disqualified | Lead status based on score |

---

## Field Details

### Booking_Number (Column 1)

**Purpose**: Unique identifier for each booking  
**Format**: Varies by county
- Hendry: `46367113` (8 digits)
- Charlotte: `202506681` (9 digits, starts with year)
- Manatee: `2025010028` (10 digits, starts with year)
- Sarasota: `2025-CF-001234` (case number format)
- Hillsborough: `2025012345` (10 digits, starts with year)

**Validation**:
```javascript
if (!record.Booking_Number || record.Booking_Number.trim() === '') {
  throw new Error('Booking_Number is required');
}
```

**Deduplication**: Used as primary key to prevent duplicate records

---

### Full_Name (Column 2)

**Purpose**: Complete name as shown on booking  
**Format**: `LAST, FIRST MIDDLE` (preferred) or `FIRST MIDDLE LAST`

**Examples**:
- `SMITH, JOHN MICHAEL`
- `GARCIA-LOPEZ, MARIA ELENA`
- `O'BRIEN, PATRICK SEAN`

**Parsing**:
```javascript
// Parse "LAST, FIRST MIDDLE"
const [lastName, firstMiddle] = fullName.split(',').map(s => s.trim());
const [firstName, ...middleParts] = firstMiddle.split(' ');

// Parse "FIRST MIDDLE LAST"
const parts = fullName.split(' ');
const firstName = parts[0];
const lastName = parts[parts.length - 1];
```

---

### DOB (Column 5)

**Purpose**: Date of birth (for age calculation)  
**Format**: `MM/DD/YYYY`

**Examples**:
- `01/15/1990`
- `12/31/1985`

**Age Calculation**:
```javascript
const calculateAge = (dob) => {
  const birthDate = new Date(dob);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
};
```

---

### Charges (Column 17)

**Purpose**: All charges combined  
**Format**: Semicolon-separated list

**Examples**:
- `DUI; DRIVING WITH SUSPENDED LICENSE`
- `BATTERY; RESISTING ARREST WITHOUT VIOLENCE`
- `POSSESSION OF CONTROLLED SUBSTANCE; POSSESSION OF DRUG PARAPHERNALIA`

**Parsing**:
```javascript
const charges = chargeArray.map(c => c.description).join('; ');
```

---

### Bond_Amount (Column 24)

**Purpose**: Total bond amount (sum of all charges)  
**Format**: `$0.00` (with dollar sign, 2 decimal places)

**Examples**:
- `$10,000.00`
- `$250,000.00`
- `$0.00` (NO BOND)

**Calculation**:
```javascript
const totalBond = chargeArray.reduce((sum, charge) => {
  const amount = parseFloat(charge.bond.replace(/[$,]/g, ''));
  return sum + (isNaN(amount) ? 0 : amount);
}, 0);

const bondAmount = `$${totalBond.toFixed(2)}`;
```

**Lead Scoring Impact**:
- $500-$50,000: +30 points (sweet spot)
- $50,000-$100,000: +20 points
- >$100,000: +10 points
- <$500: -10 points
- $0: -50 points (NO BOND)

---

### Bond_Type (Column 25)

**Purpose**: Type of bond set  
**Format**: Text (uppercase preferred)

**Common Values**:
- `CASH` - Cash bond only
- `SURETY` - Bail bondsman allowed
- `ROR` - Released on own recognizance
- `NO BOND` - No bond set (hold)
- `CASH OR SURETY` - Either allowed

**Lead Scoring Impact**:
- CASH/SURETY: +25 points (good leads)
- NO BOND/HOLD: -50 points (disqualified)
- ROR: -30 points (already released)

---

### Status (Column 26)

**Purpose**: Current custody status  
**Format**: Text (uppercase preferred)

**Common Values**:
- `IN` or `IN CUSTODY` - Currently in jail
- `OUT` or `RELEASED` - Released from jail
- `BONDED OUT` - Released on bond
- `TRANSFERRED` - Moved to another facility

**Lead Scoring Impact**:
- IN CUSTODY: +20 points (hot lead)
- RELEASED: -30 points (cold lead)

---

### County (Column 30)

**Purpose**: County where arrest occurred  
**Format**: UPPERCASE text

**Valid Values**:
- `LEE`
- `COLLIER`
- `HENDRY`
- `CHARLOTTE`
- `MANATEE`
- `SARASOTA`
- `HILLSBOROUGH`

**Validation**:
```javascript
const VALID_COUNTIES = ['LEE', 'COLLIER', 'HENDRY', 'CHARLOTTE', 'MANATEE', 'SARASOTA', 'HILLSBOROUGH'];

if (!VALID_COUNTIES.includes(record.County)) {
  throw new Error(`Invalid county: ${record.County}`);
}
```

---

### Lead_Score (Column 33)

**Purpose**: Calculated lead qualification score  
**Format**: Number (0-100, or negative for disqualified)

**Calculation Factors**:
1. **Bond Amount** (max +30)
2. **Bond Type** (max +25)
3. **Custody Status** (max +20)
4. **Data Completeness** (max +15)
5. **Disqualifying Charges** (-100)

**Example**:
```javascript
let score = 0;

// Bond amount
if (bondAmount >= 500 && bondAmount <= 50000) score += 30;
else if (bondAmount > 50000 && bondAmount <= 100000) score += 20;
else if (bondAmount > 100000) score += 10;
else if (bondAmount < 500 && bondAmount > 0) score -= 10;
else if (bondAmount === 0) score -= 50;

// Bond type
if (['CASH', 'SURETY'].includes(bondType)) score += 25;
else if (['NO BOND', 'HOLD'].includes(bondType)) score -= 50;
else if (bondType === 'ROR') score -= 30;

// Status
if (status === 'IN CUSTODY') score += 20;
else if (status === 'RELEASED') score -= 30;

// Data completeness
const hasAllFields = [bookingNumber, fullName, dob, charges, bondAmount, courtDate].every(f => f);
if (hasAllFields) score += 15;
else score -= 10;

// Disqualifying charges
const disqualifyingKeywords = ['MURDER', 'CAPITAL', 'FEDERAL'];
const hasDisqualifying = disqualifyingKeywords.some(kw => charges.toUpperCase().includes(kw));
if (hasDisqualifying) score = -100;

return score;
```

---

### Lead_Status (Column 34)

**Purpose**: Categorical lead status based on score  
**Format**: Text

**Mapping**:
- Score < 0: `Disqualified`
- Score ≥ 70: `Hot`
- Score ≥ 40: `Warm`
- Otherwise: `Cold`

**Example**:
```javascript
function getLeadStatus(score) {
  if (score < 0) return 'Disqualified';
  if (score >= 70) return 'Hot';
  if (score >= 40) return 'Warm';
  return 'Cold';
}
```

---

## Example Records

### Hot Lead (Score: 90)

```json
{
  "Booking_Number": "2025010028",
  "Full_Name": "SMITH, JOHN MICHAEL",
  "First_Name": "JOHN",
  "Last_Name": "SMITH",
  "DOB": "01/15/1990",
  "Sex": "M",
  "Race": "W",
  "Arrest_Date": "11/25/2025",
  "Arrest_Time": "10:30 PM",
  "Booking_Date": "11/25/2025",
  "Booking_Time": "11:45 PM",
  "Agency": "HCSO",
  "Address": "123 Main St",
  "City": "Tampa",
  "State": "FL",
  "Zipcode": "33602",
  "Charges": "DUI; DRIVING WITH SUSPENDED LICENSE",
  "Charge_1": "DUI",
  "Charge_1_Statute": "316.193",
  "Charge_1_Bond": "$5,000.00",
  "Charge_2": "DRIVING WITH SUSPENDED LICENSE",
  "Charge_2_Statute": "322.34",
  "Charge_2_Bond": "$5,000.00",
  "Bond_Amount": "$10,000.00",
  "Bond_Type": "SURETY",
  "Status": "IN CUSTODY",
  "Court_Date": "12/15/2025",
  "Case_Number": "2025-CF-001234",
  "Mugshot_URL": "https://county.com/mugshots/2025010028.jpg",
  "County": "HILLSBOROUGH",
  "Court_Location": "Tampa Courthouse",
  "Detail_URL": "https://county.com/bookings/2025010028",
  "Lead_Score": 90,
  "Lead_Status": "Hot"
}
```

### Disqualified Lead (Score: -100)

```json
{
  "Booking_Number": "2025010029",
  "Full_Name": "DOE, JANE MARIE",
  "First_Name": "JANE",
  "Last_Name": "DOE",
  "DOB": "05/20/1985",
  "Sex": "F",
  "Race": "W",
  "Arrest_Date": "11/25/2025",
  "Arrest_Time": "02:15 AM",
  "Booking_Date": "11/25/2025",
  "Booking_Time": "03:30 AM",
  "Agency": "Tampa PD",
  "Address": "456 Oak Ave",
  "City": "Tampa",
  "State": "FL",
  "Zipcode": "33603",
  "Charges": "MURDER IN THE FIRST DEGREE",
  "Charge_1": "MURDER IN THE FIRST DEGREE",
  "Charge_1_Statute": "782.04",
  "Charge_1_Bond": "$0.00",
  "Charge_2": "",
  "Charge_2_Statute": "",
  "Charge_2_Bond": "",
  "Bond_Amount": "$0.00",
  "Bond_Type": "NO BOND",
  "Status": "IN CUSTODY",
  "Court_Date": "12/20/2025",
  "Case_Number": "2025-CF-001235",
  "Mugshot_URL": "https://county.com/mugshots/2025010029.jpg",
  "County": "HILLSBOROUGH",
  "Court_Location": "Tampa Courthouse",
  "Detail_URL": "https://county.com/bookings/2025010029",
  "Lead_Score": -100,
  "Lead_Status": "Disqualified"
}
```

---

## Validation Rules

### Required Fields

```javascript
const REQUIRED_FIELDS = ['Booking_Number', 'Full_Name', 'Booking_Date', 'County'];

function validateRecord(record) {
  for (const field of REQUIRED_FIELDS) {
    if (!record[field] || record[field].trim() === '') {
      throw new Error(`Required field missing: ${field}`);
    }
  }
}
```

### Data Types

```javascript
function validateTypes(record) {
  // Lead_Score must be number
  if (record.Lead_Score !== '' && isNaN(record.Lead_Score)) {
    throw new Error('Lead_Score must be a number');
  }
  
  // URLs must be valid
  if (record.Mugshot_URL && !record.Mugshot_URL.startsWith('http')) {
    throw new Error('Mugshot_URL must be a valid URL');
  }
  
  // County must be uppercase
  if (record.County !== record.County.toUpperCase()) {
    throw new Error('County must be uppercase');
  }
}
```

---

## Migration from Old Schema

### Old Schema (32 columns)

The old schema had 32 columns without Lead_Score and Lead_Status.

### Migration Steps

1. **Add two new columns** (AG and AH) to all county sheets
2. **Run schema update** in Apps Script: `updateSchemaTo34Columns()`
3. **Run lead scoring** on existing data: `scoreAllSheets()`
4. **Update scrapers** to populate new fields

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture
- **DEVELOPMENT.md** - Development guidelines
- **SCRAPING_RULES.md** - Scraping best practices
- **TROUBLESHOOTING.md** - Common issues

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
