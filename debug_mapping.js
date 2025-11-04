import { readFileSync } from 'fs';

const schema = JSON.parse(readFileSync('./config/schema.json', 'utf8'));

const rawFields = {
  name: 'SERRATO,ELIAS',
  dob: '04/06/1992',
  address: 'NAPLES, FL 34112',
  bookingNumber: '202500008474',
  bookingDate: '11/03/2025',
  agency: 'CSO',
  race: 'W',
  sex: 'M'
};

console.log('Field mapping test:\n');

for (const [rawKey, value] of Object.entries(rawFields)) {
  const normalizedKey = rawKey.toLowerCase().trim();
  let matched = false;
  
  for (const [canonicalField, aliases] of Object.entries(schema.fieldAliases)) {
    if (aliases.some(alias => normalizedKey === alias.toLowerCase())) {
      console.log(`✅ "${rawKey}" → "${canonicalField}" (matched alias: "${aliases.find(a => normalizedKey === a.toLowerCase())}")`);
      matched = true;
      break;
    }
  }
  
  if (!matched) {
    console.log(`❌ "${rawKey}" → NOT MATCHED`);
  }
}
