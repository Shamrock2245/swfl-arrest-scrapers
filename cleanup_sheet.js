import { google } from 'googleapis';
import { readFileSync } from 'fs';

const keyFile = JSON.parse(readFileSync('./creds/service-account-key.json', 'utf8'));
const auth = new google.auth.GoogleAuth({
  credentials: keyFile,
  scopes: ['https://www.googleapis.com/auth/spreadsheets']
});

const sheets = google.sheets({ version: 'v4', auth });
const spreadsheetId = '1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc';

async function cleanup() {
  // Get sheet ID for collier-county-arrests
  const sheetInfo = await sheets.spreadsheets.get({ spreadsheetId });
  const sheet = sheetInfo.data.sheets.find(s => s.properties.title === 'collier-county-arrests');
  const sheetId = sheet.properties.sheetId;
  
  console.log('Sheet ID:', sheetId);
  
  // Delete rows 2-5 (the bad data)
  const result = await sheets.spreadsheets.batchUpdate({
    spreadsheetId,
    requestBody: {
      requests: [{
        deleteDimension: {
          range: {
            sheetId: sheetId,
            dimension: 'ROWS',
            startIndex: 1,  // 0-indexed, so row 2
            endIndex: 5     // Exclusive, so this deletes rows 2-5
          }
        }
      }]
    }
  });
  
  console.log('Deleted rows 2-5 successfully');
}

cleanup().catch(console.error);
