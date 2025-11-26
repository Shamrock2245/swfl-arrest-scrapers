#!/usr/bin/env node

/**
 * Environment diagnostic script for GitHub Actions
 * Tests if all required dependencies and secrets are available
 */

console.log('═══════════════════════════════════════');
console.log('🔍 Environment Diagnostic Test');
console.log('═══════════════════════════════════════\n');

// 1. Check Node.js version
console.log(`✓ Node.js version: ${process.version}`);

// 2. Check required environment variables
console.log('\n📋 Environment Variables:');
const requiredEnvVars = ['GOOGLE_SHEETS_ID', 'GOOGLE_SA_KEY_JSON'];
let allEnvVarsSet = true;

for (const envVar of requiredEnvVars) {
  const value = process.env[envVar];
  if (value) {
    console.log(`  ✓ ${envVar}: Set (${value.length} characters)`);
  } else {
    console.log(`  ✗ ${envVar}: NOT SET`);
    allEnvVarsSet = false;
  }
}

// 3. Check if GOOGLE_SA_KEY_JSON is valid JSON
if (process.env.GOOGLE_SA_KEY_JSON) {
  try {
    const parsed = JSON.parse(process.env.GOOGLE_SA_KEY_JSON);
    console.log(`  ✓ GOOGLE_SA_KEY_JSON is valid JSON`);
    console.log(`  ✓ Service account email: ${parsed.client_email || 'N/A'}`);
  } catch (error) {
    console.log(`  ✗ GOOGLE_SA_KEY_JSON is NOT valid JSON: ${error.message}`);
    allEnvVarsSet = false;
  }
}

// 4. Check required packages
console.log('\n📦 Required Packages:');
const requiredPackages = [
  'googleapis',
  'google-auth-library',
  'puppeteer',
  'puppeteer-extra',
  'puppeteer-extra-plugin-stealth'
];

let allPackagesInstalled = true;
for (const pkg of requiredPackages) {
  try {
    await import(pkg);
    console.log(`  ✓ ${pkg}: Installed`);
  } catch (error) {
    console.log(`  ✗ ${pkg}: NOT INSTALLED`);
    allPackagesInstalled = false;
  }
}

// 5. Check if Chrome/Chromium is available for Puppeteer
console.log('\n🌐 Browser Check:');
try {
  const puppeteer = await import('puppeteer');
  console.log(`  ✓ Puppeteer imported successfully`);
  
  // Try to get the browser path
  try {
    const browser = await puppeteer.default.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    console.log(`  ✓ Chrome/Chromium launched successfully`);
    await browser.close();
  } catch (error) {
    console.log(`  ✗ Failed to launch browser: ${error.message}`);
  }
} catch (error) {
  console.log(`  ✗ Puppeteer import failed: ${error.message}`);
}

// 6. Summary
console.log('\n═══════════════════════════════════════');
console.log('📊 Summary:');
console.log(`  Environment Variables: ${allEnvVarsSet ? '✓ OK' : '✗ MISSING'}`);
console.log(`  Required Packages: ${allPackagesInstalled ? '✓ OK' : '✗ MISSING'}`);
console.log('═══════════════════════════════════════\n');

if (!allEnvVarsSet || !allPackagesInstalled) {
  console.log('❌ Environment check FAILED');
  process.exit(1);
} else {
  console.log('✅ Environment check PASSED');
  process.exit(0);
}
