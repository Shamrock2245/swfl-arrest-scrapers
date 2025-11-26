#!/usr/bin/env node
/**
 * setup_credentials.js
 * 
 * Simple script to set up Google Sheets credentials
 * Creates service-account-key.json from .env or prompts user
 */

import { writeFileSync, existsSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import * as readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

async function setupCredentials() {
  console.log('\n' + '═'.repeat(60));
  console.log('  GOOGLE SHEETS CREDENTIALS SETUP');
  console.log('═'.repeat(60) + '\n');
  
  const keyPath = join(__dirname, 'service-account-key.json');
  
  // Check if credentials already exist
  if (existsSync(keyPath)) {
    console.log('✅ Credentials file already exists: service-account-key.json\n');
    const overwrite = await question('Do you want to overwrite it? (y/N): ');
    if (overwrite.toLowerCase() !== 'y') {
      console.log('\n✅ Using existing credentials.\n');
      rl.close();
      return;
    }
  }
  
  console.log('📋 You need a Google Service Account to write to Google Sheets.\n');
  console.log('Steps to create one:');
  console.log('1. Go to: https://console.cloud.google.com/');
  console.log('2. Create a new project (or select existing)');
  console.log('3. Enable Google Sheets API');
  console.log('4. Create Service Account');
  console.log('5. Download JSON key\n');
  
  console.log('Options:');
  console.log('A) Paste the JSON key directly');
  console.log('B) Provide path to downloaded JSON file');
  console.log('C) Exit and do it manually\n');
  
  const choice = await question('Choose option (A/B/C): ');
  
  if (choice.toUpperCase() === 'A') {
    console.log('\n📝 Paste the entire JSON key (Ctrl+D when done):\n');
    
    let jsonContent = '';
    rl.on('line', (line) => {
      jsonContent += line + '\n';
    });
    
    rl.on('close', () => {
      try {
        // Validate JSON
        const parsed = JSON.parse(jsonContent);
        
        if (!parsed.type || !parsed.project_id || !parsed.private_key) {
          console.error('\n❌ Invalid service account JSON. Missing required fields.\n');
          process.exit(1);
        }
        
        // Write to file
        writeFileSync(keyPath, JSON.stringify(parsed, null, 2));
        console.log('\n✅ Credentials saved to: service-account-key.json');
        
        // Update .env
        updateEnvFile();
        
        console.log('\n✅ Setup complete! You can now run: node run_all_counties.js\n');
        
      } catch (error) {
        console.error('\n❌ Invalid JSON:', error.message, '\n');
        process.exit(1);
      }
    });
    
  } else if (choice.toUpperCase() === 'B') {
    const filePath = await question('\n📁 Enter path to JSON key file: ');
    
    try {
      const content = readFileSync(filePath.trim(), 'utf8');
      const parsed = JSON.parse(content);
      
      if (!parsed.type || !parsed.project_id || !parsed.private_key) {
        console.error('\n❌ Invalid service account JSON. Missing required fields.\n');
        rl.close();
        process.exit(1);
      }
      
      // Copy to project directory
      writeFileSync(keyPath, JSON.stringify(parsed, null, 2));
      console.log('\n✅ Credentials saved to: service-account-key.json');
      
      // Update .env
      updateEnvFile();
      
      console.log('\n✅ Setup complete! You can now run: node run_all_counties.js\n');
      rl.close();
      
    } catch (error) {
      console.error('\n❌ Error reading file:', error.message, '\n');
      rl.close();
      process.exit(1);
    }
    
  } else {
    console.log('\n📝 Manual setup:');
    console.log('1. Download service account JSON key');
    console.log('2. Save as: service-account-key.json');
    console.log('3. Place in project root directory');
    console.log('4. Create .env file with:');
    console.log('   GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E');
    console.log('   GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json\n');
    rl.close();
  }
}

function updateEnvFile() {
  const envPath = join(__dirname, '.env');
  let envContent = '';
  
  if (existsSync(envPath)) {
    envContent = readFileSync(envPath, 'utf8');
  }
  
  // Add or update GOOGLE_SERVICE_ACCOUNT_KEY_PATH
  if (envContent.includes('GOOGLE_SERVICE_ACCOUNT_KEY_PATH=')) {
    envContent = envContent.replace(
      /GOOGLE_SERVICE_ACCOUNT_KEY_PATH=.*/,
      'GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json'
    );
  } else {
    envContent += '\nGOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json\n';
  }
  
  // Add GOOGLE_SHEETS_ID if not present
  if (!envContent.includes('GOOGLE_SHEETS_ID=')) {
    envContent += 'GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E\n';
  }
  
  writeFileSync(envPath, envContent);
  console.log('✅ Updated .env file');
}

// Run setup
setupCredentials().catch(error => {
  console.error('\n❌ Setup failed:', error.message, '\n');
  process.exit(1);
});
