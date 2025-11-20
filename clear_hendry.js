import { GoogleSpreadsheet } from 'google-spreadsheet';
import { JWT } from 'google-auth-library';

const SHEET_ID = '121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E';
const auth = new JWT({
  keyFile: './creds/service-account.json',
  scopes: ['https://www.googleapis.com/auth/spreadsheets'],
});

const doc = new GoogleSpreadsheet(SHEET_ID, auth);
await doc.loadInfo();
const sheet = doc.sheetsByTitle['Hendry'];
const rows = await sheet.getRows();
console.log('Deleting', rows.length, 'rows...');
for (const row of rows) {
  await row.delete();
}
console.log('✅ Hendry sheet cleared');
