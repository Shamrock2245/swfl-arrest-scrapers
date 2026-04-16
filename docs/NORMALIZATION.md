# 🔄 NORMALIZATION — Field Mapping & Data Cleanup

> **Every Florida county calls the same data by different names. This is how we unify them.**

---

## The Problem

```
Charlotte:  "Booking Number"     →  Booking_Number
Collier:    "booking_id"         →  Booking_Number
Hillsborough: "BOOKING NO"      →  Booking_Number
DeSoto:     "Book #"             →  Booking_Number
```

67 counties × 34+ fields = hundreds of field name variations. The normalizer maps them all to one canonical schema.

---

## Normalization Pipeline

```
Raw county data (arbitrary field names)
    │
    ▼
Step 1: Field Alias Mapping
    config/field_aliases.json → map raw names to schema names
    │
    ▼
Step 2: Value Standardization
    Dates → MM/DD/YYYY
    Names → UPPERCASE, LAST, FIRST MIDDLE
    Sex → M/F/U
    Race → W/B/H/A/I/U
    Bond → numeric only, no $ or commas
    Charges → pipe-separated
    │
    ▼
Step 3: Defaults & Validation
    County → hardcoded by scraper
    State → default "FL"
    Scrape_Timestamp → auto-generated
    Missing required fields → skip record or use fallback
    │
    ▼
Normalized 34-column record
```

---

## Field Alias Map

The authoritative mapping lives in `config/field_aliases.json`. Key examples:

| Schema Column | Accepted Aliases |
|---|---|
| `Booking_Number` | `booking_number`, `Booking Number`, `booking_id`, `Booking_ID`, `booking_num`, `Case Number`, `booking_no`, `Booking#`, `BookingNo` |
| `Full_Name` | `name`, `full_name`, `inmate_name`, `defendant`, `Inmate Name`, `Name`, `DEFENDANT`, `FullName` |
| `DOB` | `dob`, `date_of_birth`, `Date of Birth`, `birth_date`, `Birthday`, `BirthDate`, `DateOfBirth` |
| `Booking_Date` | `booking_date`, `arrest_date`, `Arrest Date`, `Date Arrested`, `ArrestDate`, `Date Booked`, `Committed` |
| `Bond_Amount` | `bond_amount`, `Bond Amount`, `bond`, `Bond`, `Total Bond`, `total_bond`, `bail`, `Bail`, `BailAmount` |
| `Charges` | `charges`, `charge`, `charge_description`, `offense`, `Offense`, `offenses`, `ChargeDescription` |
| `Mugshot_URL` | `mugshot_url`, `Mugshot`, `Photo URL`, `photo_url`, `image_url`, `photo` |

**Full alias map**: See `config/field_aliases.json` (625+ mappings)

---

## Value Standardization Rules

### Names
```python
# Input: "John Michael Smith" or "smith, john m" or "SMITH,JOHN MICHAEL"
# Output: "SMITH, JOHN MICHAEL"

def normalize_name(raw):
    name = raw.upper().strip()
    if ',' not in name:
        parts = name.split()
        name = f"{parts[-1]}, {' '.join(parts[:-1])}"
    return name
```

### Dates
```python
# Input: "2026-04-16", "04/16/2026", "April 16, 2026", "16-Apr-2026"
# Output: "04/16/2026"

ACCEPTED_FORMATS = [
    "%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d-%b-%Y",
    "%B %d, %Y", "%b %d, %Y", "%m/%d/%y"
]
```

### Sex
| Input | Output |
|-------|--------|
| `Male`, `male`, `M`, `m` | `M` |
| `Female`, `female`, `F`, `f` | `F` |
| anything else, empty | `U` |

### Race
| Input | Output |
|-------|--------|
| `White`, `Caucasian`, `W` | `W` |
| `Black`, `African American`, `B` | `B` |
| `Hispanic`, `Latino`, `H` | `H` |
| `Asian`, `Pacific Islander`, `A` | `A` |
| `Native American`, `Indian`, `I` | `I` |
| anything else, empty | `U` |

### Bond Amount
```python
# Input: "$5,000.00", "5000", "NO BOND", "$0", "ROR", ""
# Output: 5000, 5000, 0, 0, 0, 0

def normalize_bond(raw):
    if not raw or str(raw).upper() in ('NO BOND', 'ROR', 'N/A', 'NONE'):
        return 0
    cleaned = re.sub(r'[^0-9.]', '', str(raw))
    return int(float(cleaned)) if cleaned else 0
```

### Charges
```python
# Input: ["DUI - 1ST OFFENSE", "RECKLESS DRIVING"]
# or: "DUI - 1ST OFFENSE; RECKLESS DRIVING"
# Output: "DUI - 1ST OFFENSE|RECKLESS DRIVING"

def normalize_charges(raw):
    if isinstance(raw, list):
        return '|'.join(raw)
    for sep in [';', '\n', '\\n', ' / ']:
        raw = raw.replace(sep, '|')
    return raw.strip()
```

---

## Adding New Aliases

When a new county uses a field name not in `field_aliases.json`:

1. **Identify** the unmapped field in the solver output
2. **Add** the alias to `config/field_aliases.json` under the correct schema column
3. **Test** by running the solver and verifying the field maps correctly
4. **Commit**: `fix: add "{new_alias}" alias for {Schema_Column}`

**Rules**:
- Aliases are case-sensitive in the JSON map
- One alias can only map to ONE schema column
- If ambiguous (e.g., "Date" could be arrest or booking), use solver-level mapping instead

---

## County-Specific Overrides

Some counties need solver-level normalization that doesn't fit the generic pipeline:

```python
# In counties/hillsborough/solver.py
def parse_record(raw):
    record = {}
    # Hillsborough splits name into separate first/last fields
    record['Full_Name'] = f"{raw['Last Name']}, {raw['First Name']} {raw.get('Middle Name', '')}".strip()
    # Hillsborough uses "Confined" instead of "In Custody"
    status = raw.get('Status', '')
    record['Status'] = 'In Custody' if status == 'Confined' else status
    return record
```

These overrides stay in the solver — they do NOT go into the global normalizer.
