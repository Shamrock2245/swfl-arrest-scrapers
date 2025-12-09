import { google } from 'googleapis';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const schema = JSON.parse(readFileSync(join(__dirname, '../config/schema.json'), 'utf8'));
const HEADER = schema.columns;

let sheetsClient = null;

/**
 * Initialize Google Sheets client with service account
 */
async function getSheetsClient() {
  if (sheetsClient) return sheetsClient;

  let keyFile;

  // 1. Try direct JSON content from environment (supports raw JSON or Base64)
  // Check both variable names for compatibility
  const envVar = process.env.GOOGLE_SERVICE_ACCOUNT_JSON || process.env.GOOGLE_SA_KEY_JSON;

  if (envVar) {
    try {
      const content = envVar.trim();
      // If it doesn't start with '{', assume Base64
      if (!content.startsWith('{')) {
        const decoded = Buffer.from(content, 'base64').toString('utf8');
        keyFile = JSON.parse(decoded);
      } else {
        keyFile = JSON.parse(content);
      }
    } catch (error) {
      console.warn('⚠️ Warning: Failed to parse Google Service Account env var:', error.message);
    }
  }

  // 2. Fallback to file path
  if (!keyFile) {
    const keyPath = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;
    if (!keyPath) {
      // If neither is set, throw a clear error
      throw new Error(
        'Missing Google Credentials. Set GOOGLE_SERVICE_ACCOUNT_JSON (env) or GOOGLE_SERVICE_ACCOUNT_KEY_PATH (file).'
      );
    }
    keyFile = JSON.parse(readFileSync(keyPath, 'utf8'));
  }

  const auth = new google.auth.GoogleAuth({
    credentials: keyFile,
    scopes: [
      'https://www.googleapis.com/auth/spreadsheets',
      'https://www.googleapis.com/auth/drive.readonly'
    ]
  });

  const authClient = await auth.getClient();
  sheetsClient = google.sheets({ version: 'v4', auth: authClient });

  return sheetsClient;
}

/**
 * Ensure sheet exists and has proper headers
 */
async function ensureSheet(sheetName) {
  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;

  try {
    // Get spreadsheet metadata
    const metadata = await sheets.spreadsheets.get({
      spreadsheetId
    });

    let sheet = metadata.data.sheets?.find(s => s.properties?.title === sheetName);

    if (!sheet) {
      // Create sheet
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        requestBody: {
          requests: [{
            addSheet: {
              properties: {
                title: sheetName
              }
            }
          }]
        }
      });
      console.log(`✅ Created sheet: ${sheetName}`);

      // Fetch metadata again to get the new sheet's ID
      const updatedMetadata = await sheets.spreadsheets.get({
        spreadsheetId
      });
      const newSheet = updatedMetadata.data.sheets?.find(s => s.properties?.title === sheetName);
      if (newSheet) {
        sheet = newSheet;
      }
    }


    // Check/set headers
    const headerRow = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: `${sheetName}!A1:AI1`
    });

    if (!headerRow.data.values || headerRow.data.values.length === 0) {
      // Write headers
      await sheets.spreadsheets.values.update({
        spreadsheetId,
        range: `${sheetName}!A1`,
        valueInputOption: 'USER_ENTERED',
        requestBody: {
          values: [HEADER]
        }
      });

      // Format header row (bold, colored)
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        requestBody: {
          requests: [{
            repeatCell: {
              range: {
                sheetId: sheet?.properties?.sheetId || 0,
                startRowIndex: 0,
                endRowIndex: 1
              },
              cell: {
                userEnteredFormat: {
                  backgroundColor: { red: 0.0, green: 0.66, blue: 0.42 },
                  textFormat: {
                    bold: true,
                    foregroundColor: { red: 1, green: 1, blue: 1 }
                  }
                }
              },
              fields: 'userEnteredFormat(backgroundColor,textFormat)'
            }
          }, {
            updateSheetProperties: {
              properties: {
                sheetId: sheet?.properties?.sheetId || 0,
                gridProperties: {
                  frozenRowCount: 1
                }
              },
              fields: 'gridProperties.frozenRowCount'
            }
          }]
        }
      });

      console.log(`✅ Set headers for: ${sheetName}`);
    }

  } catch (error) {
    console.error(`❌ Error ensuring sheet ${sheetName}:`, error.message);
    throw error;
  }
}

/**
 * Convert record object to row array matching HEADER order
 * Maps normalized field names to schema column names
 */
function recordToRow(record) {
  // Field name mapping: normalized -> schema
  const fieldMap = {
    'Booking_Number': record.booking_id || record.Booking_Number,
    'Full_Name': record.full_name_last_first || record.Full_Name,
    'First_Name': record.first_name || record.First_Name,
    'Last_Name': record.last_name || record.Last_Name,
    'DOB': record.dob || record.DOB,
    'Sex': record.sex || record.Sex,
    'Race': record.race || record.Race,
    'Arrest_Date': record.arrest_date || record.Arrest_Date,
    'Arrest_Time': record.arrest_time || record.Arrest_Time,
    'Booking_Date': record.booking_date || record.Booking_Date,
    'Booking_Time': record.booking_time || record.Booking_Time,
    'Agency': record.agency || record.Agency,
    'Address': record.address || record.Address,
    'City': record.city || record.City,
    'State': record.state || record.State,
    'Zipcode': record.zipcode || record.Zipcode,
    'Charges': record.charges_raw || record.Charges,
    'Charge_1': record.charge_1 || record.Charge_1,
    'Charge_1_Statute': record.charge_1_statute || record.Charge_1_Statute,
    'Charge_1_Bond': record.charge_1_bond || record.Charge_1_Bond,
    'Charge_2': record.charge_2 || record.Charge_2,
    'Charge_2_Statute': record.charge_2_statute || record.Charge_2_Statute,
    'Charge_2_Bond': record.charge_2_bond || record.Charge_2_Bond,
    'Bond_Amount': record.total_bond || record.Bond_Amount,
    'Bond_Type': record.bond_paid || record.Bond_Type,
    'Status': record.status || record.Status,
    'Court_Date': record.court_date || record.Court_Date,
    'Case_Number': record.case_number || record.Case_Number,
    'Mugshot_URL': record.mugshot_url || record.Mugshot_URL,
    'County': record.county || record.County,
    'Court_Location': record.court_location || record.Court_Location,
    'Detail_URL': record.source_url || record.Detail_URL,
    'Lead_Score': record.qualified_score || record.Lead_Score || '',
    'Lead_Status': record.is_qualified ? 'Qualified' : (record.Lead_Status || '')
  };

  return HEADER.map(col => {
    const value = fieldMap[col];
    if (value === null || value === undefined) return '';
    return value;
  });
}

/**
 * Upsert records into sheet (insert new, update existing by booking_id + arrest_date)
 */
export async function upsertRecords(sheetName, records) {
  if (!records || records.length === 0) {
    console.log(`ℹ️  No records to upsert for ${sheetName}`);
    return { inserted: 0, updated: 0 };
  }

  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;

  // Ensure sheet exists
  await ensureSheet(sheetName);

  // Read existing data (skip header)
  const existingData = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: `${sheetName}!A2:AI`
  });

  const rows = existingData.data.values || [];

  // Build index: booking_id+arrest_date -> row index
  const existingIndex = new Map();
  const bookingIdCol = HEADER.indexOf('booking_id');
  const arrestDateCol = HEADER.indexOf('arrest_date');

  rows.forEach((row, idx) => {
    const bookingId = row[bookingIdCol] || '';
    const arrestDate = row[arrestDateCol] || '';
    if (bookingId) {
      const key = `${bookingId}|${arrestDate}`;
      existingIndex.set(key, idx + 2); // +2 for header and 0-indexing
    }
  });

  let inserted = 0;
  let updated = 0;
  const updates = [];
  const appends = [];

  for (const record of records) {
    const key = `${record.booking_id}|${record.arrest_date}`;
    const row = recordToRow(record);

    if (existingIndex.has(key)) {
      // Update existing
      const rowIndex = existingIndex.get(key);
      updates.push({
        range: `${sheetName}!A${rowIndex}:AI${rowIndex}`,
        values: [row]
      });
      updated++;
    } else {
      // Insert new
      appends.push(row);
      inserted++;
    }
  }

  // Execute batch updates
  if (updates.length > 0) {
    await sheets.spreadsheets.values.batchUpdate({
      spreadsheetId,
      requestBody: {
        valueInputOption: 'USER_ENTERED',
        data: updates
      }
    });
  }

  // Append new rows
  if (appends.length > 0) {
    await sheets.spreadsheets.values.append({
      spreadsheetId,
      range: `${sheetName}!A:AI`,
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: appends
      }
    });
  }

  console.log(`✅ ${sheetName}: inserted ${inserted}, updated ${updated}`);

  return { inserted, updated };
}

/**
 * Mirror qualified arrests to dashboard tab
 */
export async function mirrorQualifiedToDashboard(records) {
  if (!records || records.length === 0) return;

  const qualified = records.filter(r => r.is_qualified === true || r.is_qualified === 'TRUE');

  if (qualified.length === 0) {
    console.log('ℹ️  No qualified records to mirror');
    return;
  }

  await upsertRecords('dashboard', qualified);
  console.log(`✅ Mirrored ${qualified.length} qualified arrests to dashboard`);
}

/**
 * Read records from sheet (for bond_paid updates)
 */
export async function readRecentRecords(sheetName, daysBack = 14) {
  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;

  try {
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: `${sheetName}!A2:AI`
    });

    const rows = response.data.values || [];
    if (rows.length === 0) return [];

    const now = new Date();
    const cutoff = new Date(now.getTime() - (daysBack * 24 * 60 * 60 * 1000));

    const records = [];
    const arrestDateCol = HEADER.indexOf('arrest_date');
    const sourceUrlCol = HEADER.indexOf('source_url');

    for (const row of rows) {
      const arrestDate = row[arrestDateCol];
      if (!arrestDate) continue;

      const date = new Date(arrestDate);
      if (date >= cutoff) {
        const record = {};
        HEADER.forEach((col, idx) => {
          record[col] = row[idx] || '';
        });
        records.push(record);
      }
    }

    return records;
  } catch (error) {
    console.error(`❌ Error reading recent records from ${sheetName}:`, error.message);
    return [];
  }
}

/**
 * Log scraper run to ingestion_log sheet
 */
export async function logIngestion(county, success, count, startTime, errorMessage = '') {
  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;
  const sheetName = 'ingestion_log';

  try {
    await ensureSheet(sheetName);

    const duration = Date.now() - startTime;
    const timestamp = new Date().toISOString();

    const logRow = [
      timestamp,
      county,
      success ? 'SUCCESS' : 'FAILED',
      count,
      duration,
      errorMessage
    ];

    await sheets.spreadsheets.values.append({
      spreadsheetId,
      range: `${sheetName}!A:F`,
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: [logRow]
      }
    });

    console.log(`📝 Logged ingestion: ${county} - ${success ? 'SUCCESS' : 'FAILED'}`);
  } catch (error) {
    console.error('❌ Error logging ingestion:', error.message);
  }
}

export { ensureSheet, recordToRow };
