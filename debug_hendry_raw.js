import 'dotenv/config';
import scrapeHendry from './scrapers/hendry.js';

async function debugHendryRaw() {
  console.log('🔍 Debugging Hendry raw data extraction...');
  
  try {
    const records = await scrapeHendry();
    
    if (records && records.length > 0) {
      console.log(`\n📊 Total records extracted: ${records.length}`);
      console.log('\n📊 First raw record (before normalization):');
      console.log(JSON.stringify(records[0], null, 2));
      
      console.log('\n📊 Checking for charge fields:');
      console.log('- charges:', records[0].charges);
      console.log('- total_bond:', records[0].total_bond);
      console.log('- charges_raw:', records[0].charges_raw);
      console.log('- charge_1:', records[0].charge_1);
      console.log('- bond fields:', Object.keys(records[0]).filter(k => k.includes('bond')));
    } else {
      console.log('❌ No records extracted');
    }
    
    console.log('\n✅ Debug complete');
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  }
  
  process.exit(0);
}

debugHendryRaw();
