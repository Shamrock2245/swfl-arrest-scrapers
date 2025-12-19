/**
 * SetupUtilities.gs
 * 
 * Utility functions for setting up the Shamrock Bail Bonds integration
 * Run these functions once during initial setup
 * 
 * USES EXISTING PROPERTY NAMES (from your GAS project):
 * - SIGNNOW_ACCESS_TOKEN
 * - SIGNNOW_API_BASE_URL
 * - SIGNNOW_SENDER_EMAIL
 * - SIGNNOW_MASTER_TEMPLATE_ID
 * - SIGNNOW_TEMPLATE_COLLATERAL
 * - SIGNNOW_TEMPLATE_DEFENDANT_APP
 * - GOOGLE_DRIVE_FOLDER_ID
 * - GOOGLE_DRIVE_OUTPUT_FOLDER_ID
 * - REDIRECT_URL
 * - WIX_API_KEY (for Wix integration)
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
  
  // Optionally set it automatically in GAS
  PropertiesService.getScriptProperties().setProperty('WIX_API_KEY', key);
  console.log('WIX_API_KEY has been set automatically in Script Properties!');
  
  return key;
}

/**
 * Check all required Script Properties
 * Run this function to verify your configuration
 */
function checkScriptProperties() {
  const props = PropertiesService.getScriptProperties();
  const allProps = props.getProperties();
  
  console.log('='.repeat(60));
  console.log('SCRIPT PROPERTIES CHECK');
  console.log('='.repeat(60));
  console.log('');
  
  // Required properties
  const required = [
    { name: 'SIGNNOW_ACCESS_TOKEN', description: 'SignNow API authentication token' },
    { name: 'SIGNNOW_API_BASE_URL', description: 'SignNow API base URL', default: 'https://api.signnow.com' },
    { name: 'SIGNNOW_SENDER_EMAIL', description: 'Email shown as sender' },
    { name: 'GOOGLE_DRIVE_OUTPUT_FOLDER_ID', description: 'Folder for completed bonds' },
    { name: 'REDIRECT_URL', description: 'Wix site URL for redirects' }
  ];
  
  // Optional properties
  const optional = [
    { name: 'SIGNNOW_MASTER_TEMPLATE_ID', description: 'Master template ID' },
    { name: 'SIGNNOW_TEMPLATE_COLLATERAL', description: 'Collateral template ID' },
    { name: 'SIGNNOW_TEMPLATE_DEFENDANT_APP', description: 'Defendant app template ID' },
    { name: 'GOOGLE_DRIVE_FOLDER_ID', description: 'Input folder ID' },
    { name: 'WIX_API_KEY', description: 'API key for Wix integration' },
    { name: 'QUEUE_STORE_DL', description: 'Store DL in queue' },
    { name: 'QUEUE_STORE_SSN', description: 'Store SSN in queue' }
  ];
  
  console.log('REQUIRED PROPERTIES:');
  console.log('-'.repeat(40));
  
  let missingRequired = [];
  for (const prop of required) {
    const value = allProps[prop.name];
    const status = value ? '✅' : '❌';
    const displayValue = value ? (value.length > 30 ? value.substring(0, 30) + '...' : value) : '(not set)';
    console.log(`${status} ${prop.name}`);
    console.log(`   Value: ${displayValue}`);
    console.log(`   Description: ${prop.description}`);
    if (prop.default) {
      console.log(`   Default: ${prop.default}`);
    }
    console.log('');
    
    if (!value && !prop.default) {
      missingRequired.push(prop.name);
    }
  }
  
  console.log('');
  console.log('OPTIONAL PROPERTIES:');
  console.log('-'.repeat(40));
  
  for (const prop of optional) {
    const value = allProps[prop.name];
    const status = value ? '✅' : '⚪';
    const displayValue = value ? (value.length > 30 ? value.substring(0, 30) + '...' : value) : '(not set)';
    console.log(`${status} ${prop.name}`);
    console.log(`   Value: ${displayValue}`);
    console.log(`   Description: ${prop.description}`);
    console.log('');
  }
  
  console.log('');
  console.log('='.repeat(60));
  
  if (missingRequired.length > 0) {
    console.log('⚠️  MISSING REQUIRED PROPERTIES:');
    missingRequired.forEach(name => console.log(`   - ${name}`));
    console.log('');
    console.log('Please add these properties in Project Settings → Script Properties');
  } else {
    console.log('✅ All required properties are configured!');
  }
  
  console.log('='.repeat(60));
  
  return {
    configured: missingRequired.length === 0,
    missing: missingRequired,
    all: allProps
  };
}

/**
 * Test the SignNow API connection using existing properties
 */
function testSignNowConnection() {
  try {
    const props = PropertiesService.getScriptProperties();
    const accessToken = props.getProperty('SIGNNOW_ACCESS_TOKEN');
    const baseUrl = props.getProperty('SIGNNOW_API_BASE_URL') || 'https://api.signnow.com';
    
    if (!accessToken) {
      console.log('❌ SIGNNOW_ACCESS_TOKEN not set in Script Properties');
      return false;
    }
    
    console.log('Testing SignNow connection...');
    console.log(`Base URL: ${baseUrl}`);
    
    const response = UrlFetchApp.fetch(`${baseUrl}/user`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      muteHttpExceptions: true
    });
    
    if (response.getResponseCode() === 200) {
      const user = JSON.parse(response.getContentText());
      console.log('');
      console.log('✅ SignNow connection successful!');
      console.log(`   Connected as: ${user.email}`);
      console.log(`   User ID: ${user.id}`);
      console.log(`   First Name: ${user.first_name}`);
      console.log(`   Last Name: ${user.last_name}`);
      return true;
    } else {
      console.log('');
      console.log('❌ SignNow connection failed');
      console.log(`   Response code: ${response.getResponseCode()}`);
      console.log(`   Response: ${response.getContentText()}`);
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
    const props = PropertiesService.getScriptProperties();
    const wixApiKey = props.getProperty('WIX_API_KEY');
    const redirectUrl = props.getProperty('REDIRECT_URL') || 'https://www.shamrockbailbonds.biz';
    
    if (!wixApiKey) {
      console.log('⚠️  WIX_API_KEY not set in Script Properties');
      console.log('   Run generateWixApiKey() to create one');
      return false;
    }
    
    console.log('Testing Wix connection...');
    console.log(`Site URL: ${redirectUrl}`);
    
    const response = UrlFetchApp.fetch(redirectUrl + '/_functions/health', {
      method: 'GET',
      headers: {
        'X-API-Key': wixApiKey
      },
      muteHttpExceptions: true
    });
    
    if (response.getResponseCode() === 200) {
      console.log('');
      console.log('✅ Wix connection successful!');
      console.log(`   Response: ${response.getContentText()}`);
      return true;
    } else {
      console.log('');
      console.log('⚠️  Wix connection returned: ' + response.getResponseCode());
      console.log('   This may be normal if the health endpoint is not deployed yet');
      console.log('   The Wix HTTP functions need to be published first');
      return false;
    }
    
  } catch (error) {
    console.log('⚠️  Wix connection test: ' + error.message);
    console.log('   This may be normal if the Wix HTTP functions are not deployed yet');
    return false;
  }
}

/**
 * Test Google Drive access using existing folder ID
 */
function testGoogleDriveAccess() {
  try {
    const props = PropertiesService.getScriptProperties();
    const outputFolderId = props.getProperty('GOOGLE_DRIVE_OUTPUT_FOLDER_ID');
    
    console.log('Testing Google Drive access...');
    
    if (outputFolderId) {
      const folder = DriveApp.getFolderById(outputFolderId);
      console.log('');
      console.log('✅ Google Drive access successful!');
      console.log(`   Output Folder: ${folder.getName()}`);
      console.log(`   Folder ID: ${outputFolderId}`);
      console.log(`   Folder URL: ${folder.getUrl()}`);
      return true;
    } else {
      console.log('');
      console.log('⚠️  GOOGLE_DRIVE_OUTPUT_FOLDER_ID not set');
      console.log('   Completed bonds will be saved to a "Completed Bonds" folder in root');
      
      // Try to find or create the folder
      const folders = DriveApp.getFoldersByName('Completed Bonds');
      if (folders.hasNext()) {
        const folder = folders.next();
        console.log(`   Found existing folder: ${folder.getUrl()}`);
      } else {
        console.log('   No "Completed Bonds" folder found - will be created on first use');
      }
      return true;
    }
    
  } catch (error) {
    console.log('❌ Google Drive access error: ' + error.message);
    return false;
  }
}

/**
 * Run all setup checks
 */
function runFullSetupCheck() {
  console.log('');
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║     SHAMROCK BAIL BONDS - FULL SETUP CHECK                 ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');
  
  // Check Script Properties
  console.log('📋 STEP 1: Checking Script Properties...');
  console.log('');
  const propsResult = checkScriptProperties();
  console.log('');
  
  // Test SignNow
  console.log('📋 STEP 2: Testing SignNow Connection...');
  console.log('');
  const signNowResult = testSignNowConnection();
  console.log('');
  
  // Test Google Drive
  console.log('📋 STEP 3: Testing Google Drive Access...');
  console.log('');
  const driveResult = testGoogleDriveAccess();
  console.log('');
  
  // Test Wix
  console.log('📋 STEP 4: Testing Wix Connection...');
  console.log('');
  const wixResult = testWixConnection();
  console.log('');
  
  // Summary
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║                    SETUP CHECK SUMMARY                      ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`   Script Properties: ${propsResult.configured ? '✅ Configured' : '❌ Missing properties'}`);
  console.log(`   SignNow API:       ${signNowResult ? '✅ Connected' : '❌ Failed'}`);
  console.log(`   Google Drive:      ${driveResult ? '✅ Accessible' : '❌ Failed'}`);
  console.log(`   Wix Integration:   ${wixResult ? '✅ Connected' : '⚠️  Not configured (optional)'}`);
  console.log('');
  
  if (propsResult.configured && signNowResult && driveResult) {
    console.log('✅ Core setup is complete! You can start using the integration.');
    if (!wixResult) {
      console.log('');
      console.log('ℹ️  To enable Wix integration:');
      console.log('   1. Run generateWixApiKey()');
      console.log('   2. Add the key to Wix Secrets Manager as GAS_API_KEY');
      console.log('   3. Deploy the Wix HTTP functions');
    }
  } else {
    console.log('❌ Setup incomplete. Please fix the issues above.');
  }
  
  console.log('');
  console.log('═'.repeat(60));
}

/**
 * Get deployment instructions for the web app
 */
function getWebAppDeploymentInstructions() {
  console.log('');
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║           WEB APP DEPLOYMENT INSTRUCTIONS                   ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log('To deploy the webhook handler as a web app:');
  console.log('');
  console.log('1. Click "Deploy" in the top right corner');
  console.log('2. Select "New deployment"');
  console.log('3. Click the gear icon ⚙️ and select "Web app"');
  console.log('4. Configure:');
  console.log('   - Description: "Shamrock Bail Bonds Webhook Handler"');
  console.log('   - Execute as: "Me"');
  console.log('   - Who has access: "Anyone"');
  console.log('5. Click "Deploy"');
  console.log('6. Copy the Web app URL');
  console.log('');
  console.log('After deployment:');
  console.log('');
  console.log('1. Register the URL as a webhook in SignNow:');
  console.log('   - Go to SignNow Dashboard → API → Webhooks');
  console.log('   - Click "Add Webhook"');
  console.log('   - Enter your Web app URL');
  console.log('   - Select event: "document.complete"');
  console.log('   - Save');
  console.log('');
  console.log('2. Add the URL to Wix Secrets Manager:');
  console.log('   - Secret name: GAS_WEBHOOK_URL');
  console.log('   - Value: (your web app URL)');
  console.log('');
  console.log('═'.repeat(60));
}
