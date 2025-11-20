// test_normalize_collier.js
// Test normalization of Collier data

import { normalizeRecord } from "./normalizers/normalize.js";

// Sample raw data from Collier (from our debug output)
const rawRecord = {
  "name": "DANLEY,LENNON",
  "dob": "01/09/1987",
  "address": "NAPLES,  34119",
  "arrestNumber": "00242263",
  "race": "W",
  "pin": "0001995419",
  "sex": "M",
  "bookingDate": "11/19/2025",
  "bookingNumber": "202500008896",
  "agency": "NPD",
  "mugshot_url": "https://www2.colliersheriff.org/arrestsearch/PicThumb.aspx?p=0001995419"
};

console.log('🔍 Testing Collier normalization...\n');
console.log('📥 Raw input:');
console.log(JSON.stringify(rawRecord, null, 2));

console.log('\n📤 Normalized output:');
const normalized = normalizeRecord(rawRecord, "COLLIER", "https://www2.colliersheriff.org/arrestsearch/Report.aspx");
console.log(JSON.stringify(normalized, null, 2));

console.log('\n✅ Test complete');
