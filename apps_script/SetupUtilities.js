/**
 * SetupUtilities.gs
 * 
 * Utility functions for setting up the Shamrock Bail Bonds integration
 * Run these functions once during initial setup
 */

/**
 * Generate a secure API key for Wix integration
 * Run this function and save the output to both:
 * 1. GAS Script Properties as 'WIX_API_KEY'
 * 2. Wix Secrets Manager as 'GAS_API_KEY'
 */
function generateWixApiKey() {
  const key = Utilities.getUuid() + '-' + Utilities.getUuid();
  
  console.log('='.repeat(60));
  console.log('GENERATED WIX API KEY');
  console.log('='.repeat(60));
  console.log('');
  console.log('Your API Key:');
  console.log(key);
  console.log('');
  console.log('IMPORTANT: Save this key in TWO places:');
  console.log('');
  console.log('1. GAS Script Properties:');
  console.log('   - Go to Project Settings → Script Properties');
  console.log('   - Add property: WIX_API_KEY');
  console.log('   - Value: ' + key);
  console.log('');
  console.log('2. Wix Secrets Manager:');
  console.log('   - Go to Wix Dashboard → Developer Tools → Secrets Manager');
  console.log('   - Add secret: GAS_API_KEY');
  console.log('   - Value: ' + key);
  console.log('');
  console.log('='.repeat(60));
  
  return key;
}

/**
 * Set up all required Script Properties
 * Run this function to configure the integration
 */
function setupScriptProperties() {
  const props = PropertiesService.getScriptProperties();
  
  // Check what's already set
  const existing = props.getProperties();
  
  console.log('Current Script Properties:');
  console.log(JSON.stringify(existing, null, 2));
  
  // Set defaults for missing properties
  const defaults = {
    'SIGNNOW_ACCESS_TOKEN': '0c35edbbf6823555a8434624aaec4830fd4477bb5befee3da2fa29e2b258913d',
    'SIGNNOW_SENDER_EMAIL': 'admin@shamrockbailbonds.biz',
    'WIX_SITE_URL': 'https://www.shamrockbailbonds.biz',
    'REDIRECT_URL': 'https://www.shamrockbailbonds.biz'
  };
  
  for (const [key, value] of Object.entries(defaults)) {
    if (!existing[key]) {
      props.setProperty(key, value);
      console.log(`Set default for ${key}`);
    }
  }
  
  // Check for required properties that need manual setup
  const required = ['WIX_API_KEY', 'COMPLETED_BONDS_FOLDER_ID'];
  const missing = required.filter(key => !existing[key]);
  
  if (missing.length > 0) {
    console.log('');
    console.log('MISSING REQUIRED PROPERTIES:');
    missing.forEach(key => {
      console.log(`  - ${key}`);
    });
    console.log('');
    console.log('Run generateWixApiKey() to create WIX_API_KEY');
    console.log('Run getCompletedBondsFolderId() to get COMPLETED_BONDS_FOLDER_ID');
  }
  
  console.log('');
  console.log('Setup complete. Check the logs above for any missing properties.');
}

/**
 * Get or create the Completed Bonds folder and return its ID
 */
function getCompletedBondsFolderId() {
  const folderName = 'Completed Bonds';
  const folders = DriveApp.getFoldersByName(folderName);
  
  let folder;
  if (folders.hasNext()) {
    folder = folders.next();
    console.log('Found existing folder: ' + folderName);
  } else {
    folder = DriveApp.createFolder(folderName);
    console.log('Created new folder: ' + folderName);
  }
  
  const folderId = folder.getId();
  
  console.log('');
  console.log('='.repeat(60));
  console.log('COMPLETED BONDS FOLDER');
  console.log('='.repeat(60));
  console.log('');
  console.log('Folder ID: ' + folderId);
  console.log('Folder URL: ' + folder.getUrl());
  console.log('');
  console.log('Add this to Script Properties:');
  console.log('  Property: COMPLETED_BONDS_FOLDER_ID');
  console.log('  Value: ' + folderId);
  console.log('');
  
  // Optionally set it automatically
  PropertiesService.getScriptProperties().setProperty('COMPLETED_BONDS_FOLDER_ID', folderId);
  console.log('Property set automatically!');
  
  return folderId;
}

/**
 * Deploy the web app and get the URL
 * Note: This function provides instructions; actual deployment must be done manually
 */
function getWebAppDeploymentInstructions() {
  console.log('='.repeat(60));
  console.log('WEB APP DEPLOYMENT INSTRUCTIONS');
  console.log('='.repeat(60));
  console.log('');
  console.log('To deploy the webhook handler as a web app:');
  console.log('');
  console.log('1. Click "Deploy" in the top right');
  console.log('2. Select "New deployment"');
  console.log('3. Click the gear icon and select "Web app"');
  console.log('4. Configure:');
  console.log('   - Description: "Shamrock Bail Bonds Webhook Handler"');
  console.log('   - Execute as: "Me"');
  console.log('   - Who has access: "Anyone"');
  console.log('5. Click "Deploy"');
  console.log('6. Copy the Web app URL');
  console.log('');
  console.log('After deployment, register the URL as a webhook in SignNow:');
  console.log('');
  console.log('1. Go to SignNow Dashboard → API → Webhooks');
  console.log('2. Click "Add Webhook"');
  console.log('3. Enter your Web app URL');
  console.log('4. Select event: "document.complete"');
  console.log('5. Save');
  console.log('');
  console.log('Also add the URL to Wix Secrets Manager:');
  console.log('  Secret: GAS_WEBHOOK_URL');
  console.log('  Value: (your web app URL)');
  console.log('');
}

/**
 * Test the SignNow API connection
 */
function testSignNowConnection() {
  try {
    const config = SN_getConfig();
    const accessToken = config.accessToken;
    
    const response = UrlFetchApp.fetch('https://api.signnow.com/user', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      muteHttpExceptions: true
    });
    
    if (response.getResponseCode() === 200) {
      const user = JSON.parse(response.getContentText());
      console.log('✅ SignNow connection successful!');
      console.log('Connected as: ' + user.email);
      console.log('User ID: ' + user.id);
      return true;
    } else {
      console.log('❌ SignNow connection failed');
      console.log('Response code: ' + response.getResponseCode());
      console.log('Response: ' + response.getContentText());
      return false;
    }
    
  } catch (error) {
    console.log('❌ SignNow connection error: ' + error.message);
    return false;
  }
}

/**
 * Test the Wix API connection
 */
function testWixConnection() {
  try {
    const wixApiKey = PropertiesService.getScriptProperties().getProperty('WIX_API_KEY');
    const wixSiteUrl = PropertiesService.getScriptProperties().getProperty('WIX_SITE_URL') || 'https://www.shamrockbailbonds.biz';
    
    if (!wixApiKey) {
      console.log('❌ WIX_API_KEY not set in Script Properties');
      console.log('Run generateWixApiKey() first');
      return false;
    }
    
    const response = UrlFetchApp.fetch(wixSiteUrl + '/_functions/health', {
      method: 'GET',
      headers: {
        'X-API-Key': wixApiKey
      },
      muteHttpExceptions: true
    });
    
    if (response.getResponseCode() === 200) {
      console.log('✅ Wix connection successful!');
      console.log('Response: ' + response.getContentText());
      return true;
    } else {
      console.log('⚠️ Wix connection returned: ' + response.getResponseCode());
      console.log('This may be normal if the health endpoint is not set up yet');
      return false;
    }
    
  } catch (error) {
    console.log('⚠️ Wix connection test: ' + error.message);
    console.log('This may be normal if the Wix HTTP functions are not deployed yet');
    return false;
  }
}

/**
 * Run all setup checks
 */
function runFullSetupCheck() {
  console.log('='.repeat(60));
  console.log('SHAMROCK BAIL BONDS - FULL SETUP CHECK');
  console.log('='.repeat(60));
  console.log('');
  
  // Check Script Properties
  console.log('📋 Checking Script Properties...');
  setupScriptProperties();
  console.log('');
  
  // Test SignNow
  console.log('📋 Testing SignNow Connection...');
  testSignNowConnection();
  console.log('');
  
  // Test Wix
  console.log('📋 Testing Wix Connection...');
  testWixConnection();
  console.log('');
  
  // Check Drive folder
  console.log('📋 Checking Google Drive Folder...');
  getCompletedBondsFolderId();
  console.log('');
  
  console.log('='.repeat(60));
  console.log('SETUP CHECK COMPLETE');
  console.log('='.repeat(60));
}

/**
 * Create a test document in SignNow to verify the workflow
 */
function createTestDocument() {
  console.log('Creating test document...');
  
  // Create a simple test PDF
  const testContent = 'This is a test document for Shamrock Bail Bonds integration testing.';
  const blob = Utilities.newBlob(testContent, 'text/plain', 'test-document.txt');
  
  // For a real test, you would upload this to SignNow
  // This is just a placeholder to show the structure
  
  console.log('Test document created (placeholder)');
  console.log('To fully test, use the Dashboard.html interface to generate a real packet');
}
