import { normalizeRecord } from './normalizers/normalize.js';

// Sample raw data from Collier scraper
const rawRecord = {
  name: 'SERRATO,ELIAS',
  dob: '04/06/1992',
  address: 'NAPLES, FL 34112',
  bookingNumber: '202500008474',
  bookingDate: '11/03/2025',
  agency: 'CSO',
  race: 'W',
  sex: 'M',
  height: '505',
  weight: '165',
  arrestNumber: '00241275',
  pin: '0000743329',
  hairColor: 'BLK',
  eyeColor: 'BRO',
  age: '33',
  charges: 'DRUG EQUIP-POSSESS-AND OR USE',
  mugshot_url: 'https://www2.colliersheriff.org/arrestsearch/PicThumb.aspx?p=0000743329'
};

console.log('Raw record:');
console.log(JSON.stringify(rawRecord, null, 2));

const normalized = normalizeRecord(rawRecord, 'COLLIER', 'https://www2.colliersheriff.org/arrestsearch/Report.aspx');

console.log('\nNormalized record:');
console.log(JSON.stringify(normalized, null, 2));
