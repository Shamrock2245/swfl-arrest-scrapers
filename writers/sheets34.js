// writers/sheets34.js
// Google Sheets writer for 34-column schema

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
 * Supports both GOOGLE_SA_KEY_JSON (direct JSON) and GOOGLE_SERVICE_ACCOUNT_KEY_PATH (file path)
 */
async function getSheetsClient() {
  if (sheetsClient) return sheetsClient;

  let keyFile;
  
  // Try GOOGLE_SA_KEY_JSON first (for GitHub Actions)
  if (process.env.GOOGLE_SA_KEY_JSON) {
    try {
      keyFile = JSON.parse(process.env.GOOGLE_SA_KEY_JSON);
    } catch (error) {
      throw new Error('Invalid GOOGLE_SA_KEY_JSON: ' + error.message);
    }
  }
  // Fall back to GOOGLE_SERVICE_ACCOUNT_KEY_PATH (for local development)
  else if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH) {
    try {
      keyFile = JSON.parse(readFileSync(process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH, 'utf8'));
    } catch (error) {
      throw new Error('Cannot read service account key file: ' + error.message);
    }
  }
  else {
    throw new Error('Neither GOOGLE_SA_KEY_JSON nor GOOGLE_SERVICE_ACCOUNT_KEY_PATH is set in environment');
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
 * Ensure sheet exists and has proper headers (34 columns)
 */
async function ensureSheet(sheetName) {
  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;

  try {
    // Get spreadsheet metadata
    const metadata = await sheets.spreadsheets.get({
      spreadsheetId
    });

    const sheet = metadata.data.sheets?.find(s => s.properties?.title === sheetName);
    
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
    }

    // Check/set headers (34 columns: A1:AH1)
    const headerRow = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: `${sheetName}!A1:AH1`
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
      const sheetId = sheet?.properties?.sheetId || 0;
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        requestBody: {
          requests: [{
            repeatCell: {
              range: {
                sheetId: sheetId,
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
                sheetId: sheetId,
                gridProperties: {
                  frozenRowCount: 1
                }
              },
              fields: 'gridProperties.frozenRowCount'
            }
          }]
        }
      });
      
      console.log(`✅ Set 34-column headers for: ${sheetName}`);
    }

  } catch (error) {
    console.error(`❌ Error ensuring sheet ${sheetName}:`, error.message);
    throw error;
  }
}

/**
 * Convert record object to row array matching HEADER order (34 columns)
 */
function recordToRow(record) {
  return HEADER.map(col => {
    const value = record[col];
    if (value === null || value === undefined) return '';
    return value;
  });
}

/**
 * Upsert records into sheet (insert new, update existing by Booking_Number)
 */
export async function upsertRecords34(sheetName, records) {
  if (!records || records.length === 0) {
    console.log(`ℹ️  No records to upsert for ${sheetName}`);
    return { inserted: 0, updated: 0 };
  }

  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;

  // Ensure sheet exists
  await ensureSheet(sheetName);

  // Read existing data (skip header) - 34 columns: A2:AH
  const existingData = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: `${sheetName}!A2:AH`
  });

  const rows = existingData.data.values || [];
  
  // Build index: Booking_Number -> row index
  const existingIndex = new Map();
  const bookingNumberCol = HEADER.indexOf('Booking_Number');
  
  rows.forEach((row, idx) => {
    const bookingNumber = row[bookingNumberCol] || '';
    if (bookingNumber) {
      existingIndex.set(bookingNumber, idx + 2); // +2 for header and 0-indexing
    }
  });

  let inserted = 0;
  let updated = 0;
  const updates = [];
  const appends = [];

  for (const record of records) {
    const bookingNumber = record.Booking_Number;
    const row = recordToRow(record);
    
    if (existingIndex.has(bookingNumber)) {
      // Update existing
      const rowIndex = existingIndex.get(bookingNumber);
      updates.push({
        range: `${sheetName}!A${rowIndex}:AH${rowIndex}`,
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
      range: `${sheetName}!A:AH`,
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
 * Log scraper run to ingestion_log sheet
 */
export async function logIngestion(county, success, count, startTime, errorMessage = '') {
  const sheets = await getSheetsClient();
  const spreadsheetId = process.env.GOOGLE_SHEETS_ID;
  const sheetName = 'Logs';

  try {
    const duration = Math.round((Date.now() - startTime) / 1000);
    const timestamp = new Date().toISOString();

    const logRow = [
      timestamp,
      county,
      success ? 'SUCCESS' : 'FAILED',
      count,
      `${duration}s`,
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

export { ensureSheet, recordToRow, getSheetsClient };
export default upsertRecords34;
