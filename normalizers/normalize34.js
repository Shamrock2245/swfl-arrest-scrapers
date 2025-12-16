// normalizers/normalize34.js
// Normalizer for 34-column Google Sheets schema with Lead_Score and Lead_Status

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const schema = JSON.parse(readFileSync(join(__dirname, '../config/schema.json'), 'utf8'));

/**
 * Normalize a raw arrest record to the 34-column Google Sheets schema
 * @param {Object} rawPairs - Raw key-value pairs from scraper
 * @param {string} countyCode - County code (e.g., 'MANATEE')
 * @param {string} sourceUrl - Source URL of the record
 * @returns {Object} - Normalized record matching 34-column schema
 */
export function normalizeRecord34(rawPairs, countyCode, sourceUrl = '') {
  const record = {
    Scrape_Timestamp: new Date().toISOString(),
    Booking_Number: '',
    Full_Name: '',
    First_Name: '',
    Last_Name: '',
    DOB: '',
    Sex: '',
    Race: '',
    Arrest_Date: '',
    Arrest_Time: '',
    Booking_Date: '',
    Booking_Time: '',
    Agency: '',
    Address: '',
    City: '',
    State: 'FL',
    Zipcode: '',
    Charges: '',
    Charge_1: '',
    Charge_1_Statute: '',
    Charge_1_Bond: '',
    Charge_2: '',
    Charge_2_Statute: '',
    Charge_2_Bond: '',
    Bond_Amount: '',
    Bond_Type: '',
    Status: '',
    Court_Date: '',
    Case_Number: '',
    Mugshot_URL: '',
    County: countyCode,
    Court_Location: '',
    Detail_URL: sourceUrl,
    Lead_Score: '', // Will be calculated by Apps Script
    Lead_Status: '' // Will be calculated by Apps Script
  };

  // Map raw pairs to canonical fields using aliases
  const mapped = mapFieldsWithAliases(rawPairs);

  // Apply mapped values
  // Use raw Scrape_Timestamp if provided, otherwise keep default (current time)
  if (mapped.Scrape_Timestamp) {
    record.Scrape_Timestamp = mapped.Scrape_Timestamp;
  }

  record.Booking_Number = cleanString(mapped.Booking_Number || '');

  // Name parsing
  const fullName = cleanString(mapped.Full_Name || '');
  if (fullName) {
    const nameParts = parseFullName(fullName);
    record.Full_Name = nameParts.fullName;
    record.First_Name = nameParts.first;
    record.Last_Name = nameParts.last;
  }

  record.DOB = normalizeDate(mapped.DOB || '');
  record.Sex = normalizeSex(mapped.Sex || '');
  record.Race = normalizeRace(mapped.Race || '');

  // Dates and times
  const arrestDatetime = parseDatetime(mapped.Arrest_Date || '');
  record.Arrest_Date = arrestDatetime.date;
  record.Arrest_Time = arrestDatetime.time;

  const bookingDatetime = parseDatetime(mapped.Booking_Date || '');
  record.Booking_Date = bookingDatetime.date;
  record.Booking_Time = bookingDatetime.time;

  record.Agency = cleanString(mapped.Agency || '');

  // Address parsing
  const address = cleanString(mapped.Address || '');
  if (address) {
    const addressParts = parseAddress(address);
    record.Address = addressParts.street;
    record.City = mapped.City || addressParts.city;
    record.State = mapped.State || addressParts.state || 'FL';
    record.Zipcode = mapped.Zipcode || addressParts.zip;
  } else {
    record.City = cleanString(mapped.City || '');
    record.State = cleanString(mapped.State || 'FL');
    record.Zipcode = cleanString(mapped.Zipcode || '');
  }

  // Charges parsing
  const chargesRaw = cleanString(mapped.Charges || '');
  record.Charges = chargesRaw;

  if (chargesRaw) {
    const charges = parseCharges(chargesRaw);
    if (charges.length > 0) {
      record.Charge_1 = charges[0].description;
      record.Charge_1_Statute = charges[0].statute;
      record.Charge_1_Bond = charges[0].bond;
    }
    if (charges.length > 1) {
      record.Charge_2 = charges[1].description;
      record.Charge_2_Statute = charges[1].statute;
      record.Charge_2_Bond = charges[1].bond;
    }
  }

  // Bond
  const bondAmount = mapped.Bond_Amount || '';
  record.Bond_Amount = normalizeMoney(bondAmount);
  record.Bond_Type = cleanString(mapped.Bond_Type || '');
  record.Status = cleanString(mapped.Status || '');

  record.Court_Date = normalizeDate(mapped.Court_Date || '');
  record.Case_Number = cleanString(mapped.Case_Number || '');

  // Mugshot
  const mugshotUrl = cleanString(mapped.Mugshot_URL || '');
  record.Mugshot_URL = mugshotUrl;

  record.Court_Location = cleanString(mapped.Court_Location || '');

  return record;
}

/**
 * Map raw field names to canonical names using aliases
 */
function mapFieldsWithAliases(rawPairs) {
  const mapped = {};

  for (const [rawKey, value] of Object.entries(rawPairs)) {
    const normalizedKey = rawKey.toLowerCase().trim();

    // Find matching canonical field
    for (const [canonicalField, aliases] of Object.entries(schema.fieldAliases)) {
      if (aliases.some(alias => normalizedKey === alias.toLowerCase())) {
        mapped[canonicalField] = value;
        break;
      }
    }
  }

  return mapped;
}

/**
 * Parse full name into components
 */
function parseFullName(fullName) {
  if (!fullName) return { first: '', last: '', fullName: '' };

  const cleaned = fullName.trim();

  // Format: "LAST, FIRST MIDDLE"
  if (cleaned.includes(',')) {
    const parts = cleaned.split(',').map(p => p.trim());
    const last = parts[0];
    const firstMiddle = parts[1] || '';
    const first = firstMiddle.split(/\s+/)[0] || '';
    return {
      first: toTitleCase(first),
      last: toTitleCase(last),
      fullName: `${toTitleCase(last)}, ${toTitleCase(firstMiddle)}`
    };
  }

  // Format: "FIRST MIDDLE LAST"
  const parts = cleaned.split(/\s+/);
  if (parts.length >= 2) {
    const first = parts[0];
    const last = parts[parts.length - 1];
    return {
      first: toTitleCase(first),
      last: toTitleCase(last),
      fullName: `${toTitleCase(last)}, ${toTitleCase(first)}`
    };
  }

  // Single name
  return {
    first: '',
    last: toTitleCase(cleaned),
    fullName: toTitleCase(cleaned)
  };
}

/**
 * Parse address into components
 */
function parseAddress(address) {
  const result = { street: '', city: '', state: '', zip: '' };

  if (!address) return result;

  // Try to extract ZIP code
  const zipMatch = address.match(/\b(\d{5}(?:-\d{4})?)\b/);
  if (zipMatch) {
    result.zip = zipMatch[1];
  }

  // Try to extract state
  const stateMatch = address.match(/\b([A-Z]{2})\b/);
  if (stateMatch) {
    result.state = stateMatch[1];
  }

  // Extract city (word before state)
  const cityMatch = address.match(/,\s*([A-Za-z\s]+),?\s+[A-Z]{2}/);
  if (cityMatch) {
    result.city = cityMatch[1].trim();
  }

  // Street is everything before city
  const streetMatch = address.match(/^(.+?),/);
  if (streetMatch) {
    result.street = streetMatch[1].trim();
  } else {
    result.street = address;
  }

  return result;
}

/**
 * Parse charges string into structured array
 */
function parseCharges(chargesStr) {
  if (!chargesStr) return [];

  const charges = [];

  // Split by common delimiters
  const parts = chargesStr.split(/[;|\n]/);

  for (const part of parts) {
    const cleaned = part.trim();
    if (!cleaned) continue;

    // Try to extract statute number
    const statuteMatch = cleaned.match(/\b(\d{3,4}(?:\.\d+)?(?:\([a-z0-9]+\))?)\b/i);
    const statute = statuteMatch ? statuteMatch[1] : '';

    // Try to extract bond amount
    const bondMatch = cleaned.match(/\$[\d,]+(?:\.\d{2})?/);
    const bond = bondMatch ? bondMatch[0] : '';

    // Description is the full text
    const description = cleaned;

    charges.push({ description, statute, bond });
  }

  return charges.slice(0, 2); // Only return first 2 charges
}

/**
 * Parse datetime string
 */
function parseDatetime(str) {
  if (!str) return { date: '', time: '' };

  const cleaned = str.trim();

  // Try to extract time (HH:MM format)
  const timeMatch = cleaned.match(/\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\b/i);
  const time = timeMatch ? timeMatch[1] : '';

  // Try to extract date
  const dateMatch = cleaned.match(/\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b/);
  const date = dateMatch ? normalizeDate(dateMatch[1]) : '';

  return { date, time };
}

/**
 * Normalize date to MM/DD/YYYY format
 */
function normalizeDate(dateStr) {
  if (!dateStr) return '';

  const cleaned = dateStr.trim();

  // Try parsing various formats
  const formats = [
    /(\d{1,2})[-/](\d{1,2})[-/](\d{4})/, // MM/DD/YYYY or MM-DD-YYYY
    /(\d{4})[-/](\d{1,2})[-/](\d{1,2})/, // YYYY-MM-DD
    /(\d{1,2})[-/](\d{1,2})[-/](\d{2})/  // MM/DD/YY
  ];

  for (const format of formats) {
    const match = cleaned.match(format);
    if (match) {
      let month, day, year;
      if (format === formats[1]) {
        // YYYY-MM-DD
        year = match[1];
        month = match[2];
        day = match[3];
      } else {
        month = match[1];
        day = match[2];
        year = match[3];
      }

      // Convert 2-digit year to 4-digit
      if (year.length === 2) {
        year = parseInt(year) < 50 ? `20${year}` : `19${year}`;
      }

      return `${month.padStart(2, '0')}/${day.padStart(2, '0')}/${year}`;
    }
  }

  return cleaned;
}

/**
 * Normalize money amount
 */
function normalizeMoney(amount) {
  if (!amount) return '';

  const cleaned = amount.toString().replace(/[^0-9.]/g, '');
  const num = parseFloat(cleaned);

  if (isNaN(num)) return amount;

  return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Normalize sex/gender
 */
function normalizeSex(sex) {
  if (!sex) return '';
  const cleaned = sex.trim().toUpperCase();
  if (cleaned.startsWith('M')) return 'M';
  if (cleaned.startsWith('F')) return 'F';
  return cleaned;
}

/**
 * Normalize race
 */
function normalizeRace(race) {
  if (!race) return '';
  const cleaned = race.trim().toUpperCase();

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

  return raceMap[cleaned] || race;
}

/**
 * Clean string
 */
function cleanString(str) {
  if (!str) return '';
  return str.toString().trim().replace(/\s+/g, ' ');
}

/**
 * Convert to title case
 */
function toTitleCase(str) {
  if (!str) return '';
  return str.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}

export default normalizeRecord34;
