import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const schema = JSON.parse(readFileSync(join(__dirname, '../config/schema.json'), 'utf8'));

/**
 * Normalize a raw arrest record to our unified schema
 */
export function normalizeRecord(rawPairs, countyCode, sourceUrl = '') {
  const record = {
    booking_id: '',
    full_name_last_first: '',
    first_name: '',
    last_name: '',
    dob: '',
    sex: '',
    race: '',
    arrest_date: '',
    arrest_time: '',
    booking_date: '',
    booking_time: '',
    agency: '',
    address: '',
    city: '',
    state: 'FL',
    zipcode: '',
    charges_raw: '',
    charge_1: '',
    charge_1_statute: '',
    charge_1_bond: '',
    charge_2: '',
    charge_2_statute: '',
    charge_2_bond: '',
    total_bond: '',
    bond_paid: '',
    court_date: '',
    case_number: '',
    mugshot_url: '',
    mugshot_image: '',
    source_url: sourceUrl,
    county: countyCode,
    ingested_at_iso: new Date().toISOString(),
    qualified_score: 0,
    is_qualified: false,
    extra_fields_json: ''
  };

  // Map raw pairs to canonical fields using aliases
  const mapped = mapFieldsWithAliases(rawPairs);

  // Apply mapped values
  record.booking_id = cleanString(mapped.Booking_Number || '');

  // Name parsing
  const fullName = cleanString(mapped.Full_Name || '');
  const firstName = cleanString(mapped.First_Name || '');
  const lastName = cleanString(mapped.Last_Name || '');
  
  if (fullName) {
    const nameParts = parseFullName(fullName);
    record.full_name_last_first = nameParts.lastFirst;
    record.first_name = firstName || nameParts.first;
    record.last_name = lastName || nameParts.last;
  } else if (firstName && lastName) {
    // Build from separate fields
    record.first_name = toTitleCase(firstName);
    record.last_name = toTitleCase(lastName);
    record.full_name_last_first = `${record.last_name}, ${record.first_name}`;
  } else if (firstName) {
    record.first_name = toTitleCase(firstName);
  } else if (lastName) {
    record.last_name = toTitleCase(lastName);
  }

  record.dob = normalizeDate(mapped.DOB || '');
  record.sex = normalizeSex(mapped.Sex || '');
  record.race = normalizeRace(mapped.Race || '');

  // Dates and times
  const arrestDatetime = parseDatetime(mapped.Arrest_Date || '');
  record.arrest_date = arrestDatetime.date;
  record.arrest_time = arrestDatetime.time;

  const bookingDatetime = parseDatetime(mapped.Booking_Date || '');
  record.booking_date = bookingDatetime.date;
  record.booking_time = bookingDatetime.time;
  
  // Infer booking date from arrest date if missing
  if (!record.booking_date && record.arrest_date) {
    record.booking_date = record.arrest_date;
  }
  // Infer arrest date from booking date if missing
  if (!record.arrest_date && record.booking_date) {
    record.arrest_date = record.booking_date;
  }

  record.agency = cleanString(mapped.Agency || '');

  // Address parsing
  const address = cleanString(mapped.Address || '');
  if (address) {
    const addressParts = parseAddress(address);
    record.address = addressParts.street;
    record.city = mapped.City || addressParts.city;
    record.state = mapped.State || addressParts.state || 'FL';
    record.zipcode = mapped.Zipcode || addressParts.zip;
  } else {
    record.city = cleanString(mapped.City || '');
    record.state = cleanString(mapped.State || 'FL');
    record.zipcode = cleanString(mapped.Zipcode || '');
  }

  // Charges parsing
  const chargesRaw = cleanString(mapped.Charges || '');
  record.charges_raw = chargesRaw;

  if (chargesRaw) {
    const charges = parseCharges(chargesRaw);
    if (charges.length > 0) {
      record.charge_1 = charges[0].description;
      record.charge_1_statute = charges[0].statute;
      record.charge_1_bond = charges[0].bond;
    }
    if (charges.length > 1) {
      record.charge_2 = charges[1].description;
      record.charge_2_statute = charges[1].statute;
      record.charge_2_bond = charges[1].bond;
    }
  }

  // Bond
  const bondAmount = mapped.Bond_Amount || '';
  record.total_bond = normalizeMoney(bondAmount);
  record.bond_paid = normalizeBondPaid(mapped.bond_paid || '');

  record.court_date = normalizeDate(mapped.Court_Date || '');
  record.case_number = cleanString(mapped.Case_Number || '');

  // Mugshot
  const mugshotUrl = cleanString(mapped.Mugshot_URL || '');
  record.mugshot_url = mugshotUrl;
  if (mugshotUrl) {
    record.mugshot_image = `=IMAGE("${mugshotUrl}")`;
  }

  // Calculate qualification score
  const scoreResult = calculateQualificationScore(record);
  record.qualified_score = scoreResult.score;
  record.is_qualified = scoreResult.qualified;

  // Map to schema columns
  record.Lead_Score = scoreResult.score;
  record.Lead_Status = scoreResult.qualified ? 'Hot' : 'Cold';

  // Store unmapped fields
  const extraFields = {};
  for (const [key, value] of Object.entries(rawPairs)) {
    if (!isFieldMapped(key) && value) {
      extraFields[key] = value;
    }
  }
  if (Object.keys(extraFields).length > 0) {
    record.extra_fields_json = JSON.stringify(extraFields);
  }

  return record;
}

/**
 * Map raw field names to canonical names using aliases
 */
function mapFieldsWithAliases(rawPairs) {
  const mapped = {};

  for (const [rawKey, value] of Object.entries(rawPairs)) {
    const normalizedKey = rawKey.toLowerCase().trim();
    let matched = false;

    // Exact match first
    for (const [canonicalField, aliases] of Object.entries(schema.fieldAliases)) {
      if (aliases.some(alias => normalizedKey === alias.toLowerCase())) {
        mapped[canonicalField] = value;
        matched = true;
        break;
      }
    }

    // Fuzzy match if no exact match (handles typos, extra spaces, etc.)
    if (!matched) {
      for (const [canonicalField, aliases] of Object.entries(schema.fieldAliases)) {
        for (const alias of aliases) {
          const aliasLower = alias.toLowerCase();
          // Check if normalized key contains the alias or vice versa
          if (normalizedKey.includes(aliasLower) || aliasLower.includes(normalizedKey)) {
            // Ensure it's a meaningful match (not too short)
            if (normalizedKey.length >= 3 && aliasLower.length >= 3) {
              mapped[canonicalField] = value;
              matched = true;
              break;
            }
          }
        }
        if (matched) break;
      }
    }
  }

  return mapped;
}

/**
 * Check if a field was mapped
 */
function isFieldMapped(rawKey) {
  const normalizedKey = rawKey.toLowerCase().trim();
  for (const aliases of Object.values(schema.fieldAliases)) {
    if (aliases.some(alias => normalizedKey === alias.toLowerCase())) {
      return true;
    }
  }
  return false;
}

/**
 * Parse full name into components
 */
function parseFullName(fullName) {
  if (!fullName) return { first: '', last: '', lastFirst: '' };

  const cleaned = fullName.trim();

  // Format: "LAST, FIRST MIDDLE"
  if (cleaned.includes(',')) {
    const parts = cleaned.split(',').map(p => p.trim());
    const last = toTitleCase(parts[0]);
    const firstMiddle = parts[1] ? toTitleCase(parts[1]) : '';
    const first = firstMiddle.split(' ')[0] || '';
    return {
      first,
      last,
      lastFirst: `${last}, ${firstMiddle}`
    };
  }

  // Format: "FIRST MIDDLE LAST"
  const words = cleaned.split(/\s+/).filter(Boolean);
  if (words.length === 0) return { first: '', last: '', lastFirst: '' };

  const last = toTitleCase(words[words.length - 1]);
  const first = words.length > 1 ? toTitleCase(words[0]) : '';
  const middle = words.length > 2 ? words.slice(1, -1).map(toTitleCase).join(' ') : '';

  const lastFirst = middle
    ? `${last}, ${first} ${middle}`
    : `${last}, ${first}`;

  return { first, last, lastFirst };
}

/**
 * Parse address string into components
 */
function parseAddress(addressStr) {
  if (!addressStr) return { street: '', city: '', state: '', zip: '' };

  const str = addressStr.trim();

  // Pattern: "123 Main St, City, ST 12345"
  const match1 = str.match(/^(.+?),\s*([^,]+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$/i);
  if (match1) {
    return {
      street: match1[1].trim(),
      city: match1[2].trim(),
      state: match1[3].toUpperCase(),
      zip: match1[4]
    };
  }

  // Pattern: "City, ST ZIP"
  const match2 = str.match(/^([^,]+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$/i);
  if (match2) {
    return {
      street: '',
      city: match2[1].trim(),
      state: match2[2].toUpperCase(),
      zip: match2[3]
    };
  }

  // Pattern: "City, ST"
  const match3 = str.match(/^([^,]+?),\s*([A-Z]{2})$/i);
  if (match3) {
    return {
      street: '',
      city: match3[1].trim(),
      state: match3[2].toUpperCase(),
      zip: ''
    };
  }

  // Default: treat as street
  return {
    street: str,
    city: '',
    state: '',
    zip: ''
  };
}

/**
 * Parse charges string into structured array
 */
function parseCharges(chargesStr) {
  if (!chargesStr) return [];

  const charges = [];

  // Split by common delimiters (|, ;, newlines, multiple spaces, or numbered lists)
  let lines = chargesStr.split(/[|;\n]+|\d+\.\s+/);
  
  // If no delimiters found, try splitting by double spaces or "and"
  if (lines.length === 1) {
    lines = chargesStr.split(/\s{2,}|\s+and\s+/i);
  }

  for (const line of lines.slice(0, 2)) { // Only take first 2 charges
    const cleaned = line.trim();
    if (!cleaned || cleaned.length < 4) continue;

    // Try to extract statute (various formats)
    // Format 1: "Battery (784.03)" or "Battery (F.S. 784.03)"
    // Format 2: "784.03 Battery" or "F.S. 784.03 Battery"
    let statute = '';
    let description = cleaned;
    
    const statuteMatch1 = cleaned.match(/\((?:F\.?S\.?\s*)?([0-9\.]+)\)/);
    if (statuteMatch1) {
      statute = statuteMatch1[1];
      description = description.replace(statuteMatch1[0], '');
    } else {
      const statuteMatch2 = cleaned.match(/^(?:F\.?S\.?\s*)?([0-9\.]+)\s+/);
      if (statuteMatch2) {
        statute = statuteMatch2[1];
        description = description.replace(statuteMatch2[0], '');
      }
    }

    // Try to extract bond amount (e.g., "$1,500", "Bond: $1500")
    const bondMatch = cleaned.match(/(?:bond[:\s]*)?\$[\d,]+(?:\.\d{2})?/i);
    const bond = bondMatch ? normalizeMoney(bondMatch[0]) : '';
    if (bondMatch) {
      description = description.replace(bondMatch[0], '');
    }

    // Clean description
    description = description
      .replace(/\s+/g, ' ')
      .replace(/^[\s,:-]+|[\s,:-]+$/g, '')
      .trim();

    if (description) {
      charges.push({
        description,
        statute,
        bond
      });
    }
  }

  return charges;
}

/**
 * Calculate qualification score
 */
function calculateQualificationScore(record) {
  let score = 0;
  const rules = schema.qualificationRules;

  // Bond amount scoring
  const bondAmount = parseFloat(record.total_bond || '0');
  for (const rule of rules.scoring.bondAmount) {
    if (bondAmount >= rule.min) {
      score += rule.points;
      break; // Only apply highest matching rule
    }
  }

  // Serious charges scoring
  const chargesLower = (record.charges_raw || '').toLowerCase();
  for (const keyword of rules.scoring.seriousCharges.keywords) {
    if (chargesLower.includes(keyword)) {
      score += rules.scoring.seriousCharges.points;
      break; // Only count once
    }
  }

  // Recency scoring
  if (record.arrest_date) {
    const arrestDate = new Date(record.arrest_date);
    const now = new Date();
    const daysAgo = Math.floor((now - arrestDate) / (1000 * 60 * 60 * 24));

    for (const rule of rules.scoring.recency) {
      if (daysAgo <= rule.daysAgo) {
        score += rule.points;
        break;
      }
    }
  }

  return {
    score,
    qualified: score >= rules.minScore
  };
}

// ========== UTILITY FUNCTIONS ==========

function cleanString(str) {
  if (!str) return '';
  return String(str).trim().replace(/\s+/g, ' ');
}

function toTitleCase(str) {
  if (!str) return '';
  return str.toLowerCase().replace(/\b\w/g, char => char.toUpperCase());
}

function normalizeDate(dateStr) {
  if (!dateStr) return '';
  try {
    let date;

    // Handle MM/DD/YYYY format (common in US arrest records)
    const mmddyyyyMatch = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (mmddyyyyMatch) {
      const [, month, day, year] = mmddyyyyMatch;
      date = new Date(year, parseInt(month) - 1, day);
    } else {
      // Try standard Date parsing
      date = new Date(dateStr);
    }

    if (isNaN(date.getTime())) return '';
    return date.toISOString().split('T')[0]; // YYYY-MM-DD
  } catch (error) {
    return '';
  }
}

function parseDatetime(datetimeStr) {
  if (!datetimeStr) return { date: '', time: '' };
  try {
    let dt;

    // Handle MM/DD/YYYY HH:MM:SS format (e.g., "10/24/2024 07:13:34 EDT")
    const mmddyyyyTimeMatch = datetimeStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})/);
    if (mmddyyyyTimeMatch) {
      const [, month, day, year, hour, minute, second] = mmddyyyyTimeMatch;
      dt = new Date(year, parseInt(month) - 1, day, hour, minute, second);
    }
    // Handle MM/DD/YYYY format (common in US arrest records)
    else {
      const mmddyyyyMatch = datetimeStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
      if (mmddyyyyMatch) {
        const [, month, day, year] = mmddyyyyMatch;
        dt = new Date(year, parseInt(month) - 1, day);
      } else {
        // Try standard Date parsing
        dt = new Date(datetimeStr);
      }
    }

    if (isNaN(dt.getTime())) return { date: '', time: '' };

    return {
      date: dt.toISOString().split('T')[0],
      time: dt.toTimeString().split(' ')[0] // HH:mm:ss
    };
  } catch (error) {
    return { date: '', time: '' };
  }
}

function normalizeMoney(moneyStr) {
  if (!moneyStr) return '';
  const str = String(moneyStr).toLowerCase().trim();
  
  // Handle special bond cases
  if (str.includes('no bond') || str.includes('no bail') || str.includes('held without')) {
    return 'NO BOND';
  }
  if (str.includes('hold') || str.includes('detainer')) {
    return 'HOLD';
  }
  if (str.includes('released') || str.includes('ror') || str.includes('recognizance')) {
    return '0.00';
  }
  
  // Extract numeric value
  const cleaned = str.replace(/[$,]/g, '').trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? '' : num.toFixed(2);
}

function normalizeBondPaid(bondPaidStr) {
  if (!bondPaidStr) return '';
  const str = String(bondPaidStr).toLowerCase().trim();

  if (str.includes('yes') || str.includes('paid') || str.includes('posted') || str.includes('released')) {
    return 'TRUE';
  }
  if (str.includes('no') || str.includes('unpaid') || str.includes('not paid')) {
    return 'FALSE';
  }
  return '';
}

function normalizeSex(sexStr) {
  if (!sexStr) return '';
  const str = String(sexStr).toUpperCase().trim();
  if (str.startsWith('M')) return 'M';
  if (str.startsWith('F')) return 'F';
  return str;
}

function normalizeRace(raceStr) {
  if (!raceStr) return '';
  const str = String(raceStr).toUpperCase().trim();

  const raceMap = {
    'W': 'White',
    'B': 'Black',
    'H': 'Hispanic',
    'A': 'Asian',
    'I': 'Native American',
    'WHITE': 'White',
    'BLACK': 'Black',
    'HISPANIC': 'Hispanic',
    'ASIAN': 'Asian',
    'NATIVE': 'Native American'
  };

  return raceMap[str] || str;
}

export {
  parseFullName,
  parseAddress,
  parseCharges,
  calculateQualificationScore,
  normalizeDate,
  normalizeMoney
};
