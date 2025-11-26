/**
 * run_all_counties.js
 * 
 * Master script to run all county scrapers sequentially
 * Populates initial 30 days of data for all counties
 * 
 * ES MODULE VERSION
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const execPromise = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// County configurations with estimated daily arrests
const COUNTIES = [
  { name: 'Hendry', script: 'scrapers/hendry_stealth.js', dailyAvg: 8, priority: 3 },
  { name: 'Charlotte', script: 'scrapers/charlotte_stealth.js', dailyAvg: 25, priority: 2 },
  { name: 'Manatee', script: 'scrapers/manatee_stealth.js', dailyAvg: 50, priority: 1 },
  { name: 'Sarasota', script: 'scrapers/sarasota_stealth.js', dailyAvg: 40, priority: 2 },
  { name: 'Hillsborough', script: 'scrapers/hillsborough_stealth.js', dailyAvg: 100, priority: 1 }
];

/**
 * Run a single county scraper
 */
async function runCountyScraper(county) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🚀 Starting ${county.name} County scraper...`);
  console.log(`   Daily Average: ${county.dailyAvg} arrests`);
  console.log(`   Priority: ${county.priority} (1=highest)`);
  console.log(`${'='.repeat(60)}\n`);
  
  const startTime = Date.now();
  
  try {
    const { stdout, stderr } = await execPromise(`node ${county.script}`, {
      cwd: __dirname,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log(stdout);
    if (stderr) console.error(stderr);
    
    console.log(`\n✅ ${county.name} County completed in ${duration}s\n`);
    
    return {
      county: county.name,
      success: true,
      duration: duration,
      output: stdout
    };
    
  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.error(`\n❌ ${county.name} County failed after ${duration}s`);
    console.error(`Error: ${error.message}\n`);
    
    return {
      county: county.name,
      success: false,
      duration: duration,
      error: error.message
    };
  }
}

/**
 * Run all county scrapers sequentially
 */
async function runAllCounties() {
  console.log('\n' + '═'.repeat(60));
  console.log('  SWFL ARREST SCRAPERS - INITIAL 30-DAY DATA COLLECTION');
  console.log('═'.repeat(60));
  console.log(`\nStarting at: ${new Date().toLocaleString()}`);
  console.log(`Counties to scrape: ${COUNTIES.length}`);
  console.log(`Estimated total time: 10-15 minutes\n`);
  
  const results = [];
  const overallStart = Date.now();
  
  // Run each county sequentially (to avoid overwhelming the system)
  for (const county of COUNTIES) {
    const result = await runCountyScraper(county);
    results.push(result);
    
    // Wait 30 seconds between counties to be respectful
    if (county !== COUNTIES[COUNTIES.length - 1]) {
      console.log('⏳ Waiting 30 seconds before next county...\n');
      await new Promise(resolve => setTimeout(resolve, 30000));
    }
  }
  
  // Print summary
  const overallDuration = ((Date.now() - overallStart) / 60000).toFixed(1);
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log('\n' + '═'.repeat(60));
  console.log('  SUMMARY');
  console.log('═'.repeat(60));
  console.log(`\nCompleted at: ${new Date().toLocaleString()}`);
  console.log(`Total duration: ${overallDuration} minutes`);
  console.log(`\n✅ Successful: ${successful}/${COUNTIES.length}`);
  console.log(`❌ Failed: ${failed}/${COUNTIES.length}\n`);
  
  // Detailed results
  console.log('Detailed Results:');
  console.log('-'.repeat(60));
  results.forEach(r => {
    const status = r.success ? '✅' : '❌';
    console.log(`${status} ${r.county.padEnd(15)} - ${r.duration}s`);
    if (!r.success) {
      console.log(`   Error: ${r.error}`);
    }
  });
  console.log('-'.repeat(60));
  
  // Next steps
  console.log('\n📋 Next Steps:');
  console.log('1. Check Google Sheets for populated data');
  console.log('2. Run lead scoring: Apps Script → 🎯 Lead Scoring → 📊 Score All Sheets');
  console.log('3. Review hot leads in each county tab');
  console.log('4. Set up automated scheduling (see SCHEDULING_GUIDE.md)');
  
  console.log('\n' + '═'.repeat(60) + '\n');
  
  return results;
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllCounties()
    .then(results => {
      const failed = results.filter(r => !r.success).length;
      process.exit(failed > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('\n❌ Fatal error:', error);
      process.exit(1);
    });
}

export { runAllCounties, runCountyScraper };
