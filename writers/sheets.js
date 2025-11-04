// writers/sheets.js
import fs from "node:fs";
import { google } from "googleapis";

const SPREADSHEET_ID = process.env.SHEETS_SPREADSHEET_ID;

// 1) Build Google auth using the KEY FILE path from .env
function getAuth() {
  const keyPath = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;
  if (!keyPath || !fs.existsSync(keyPath)) {
    throw new Error(
      "GOOGLE_SERVICE_ACCOUNT_KEY_PATH is missing or file not found"
    );
  }
  return new google.auth.GoogleAuth({
    keyFile: keyPath,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
}

// 2) Get a Sheets client
export function getSheetsClient() { /* ... */ }
  const auth = getAuth();
  return google.sheets({ version: "v4", auth });
}

// 3) Make sure a tab named "ingestion_log" exists; create it if missing
export async function ensureIngestionSheet(sheets) {
  const title = "ingestion_log";
  const meta = await sheets.spreadsheets.get({
    spreadsheetId: SPREADSHEET_ID,
    fields: "sheets.properties.title",
  });
  const exists = meta.data.sheets?.some((s) => s.properties?.title === title);
  if (!exists) {
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      requestBody: {
        requests: [{ addSheet: { properties: { title } } }],
      },
    });
    console.log(`✅ Created sheet: ${title}`);
  }
}

// 4) Append ONE row to ingestion_log without using sheetId
//    Example row: [ISO time, 'Collier', 'started', 5, '']
//    This avoids the "No grid with id: 0" bug entirely.
export async function logIngestionRow(sheets, row) {
  const range = "ingestion_log!A1";
  await sheets.spreadsheets.values.append({
    spreadsheetId: SPREADSHEET_ID,
    range,
    valueInputOption: "USER_ENTERED",
    insertDataOption: "INSERT_ROWS",
    requestBody: { values: [row] },
  });
}
