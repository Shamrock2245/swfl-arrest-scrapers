import { google } from 'googleapis';
import { readFileSync } from 'fs';

const keyFile = JSON.parse(readFileSync('./creds/service-account-key.json', 'utf8'));
const auth = new google.auth.GoogleAuth({
  credentials: keyFile,
  scopes: ['https://www.googleapis.com/auth/spreadsheets']
});

const sheets = google.sheets({ version: 'v4', auth });
const spreadsheetId = '1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc';

async function checkCharges() {
  const result = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: 'collier-county-arrests!A1:U15'
  });
  
  const rows = result.data.values;
  const headers = rows[0];
  
  console.log('Headers:', headers.slice(0, 22).join(' | '));
  console.log('\nFirst 3 data rows:\n');
  
  for (let i = 1; i <= 3 && i < rows.length; i++) {
    const row = rows[i];
    console.log(`Row ${i+1}:`);
    console.log(`  Name: ${row[1]}`);
    console.log(`  DOB: ${row[4]}`);
    console.log(`  Booking Date: ${row[9]}`);
    console.log(`  charges_raw (Q): ${row[16] || '(empty)'}`);
    console.log(`  charge_1 (R): ${row[17] || '(empty)'}`);
    console.log('');
  }
}

checkCharges().catch(console.error);
