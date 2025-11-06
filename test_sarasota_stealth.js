import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Use stealth plugin to bypass Cloudflare
puppeteer.use(StealthPlugin());

async function testSarasotaStealth() {
  console.log('Testing Sarasota with stealth plugin...\n');
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled'
    ]
  });
  
  const page = await browser.newPage();
  
  // Set viewport
  await page.setViewport({ width: 1366, height: 900 });
  
  console.log('1. Loading main page...');
  await page.goto('https://www.sarasotasheriff.org/arrest-reports/index.php', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForTimeout(2000);
  
  // Check for iframe
  console.log('2. Looking for iframe...');
  const iframeElement = await page.$('iframe');
  
  if (!iframeElement) {
    console.log('❌ No iframe found');
    await browser.close();
    return;
  }
  
  const iframeSrc = await page.evaluate(iframe => iframe.src, iframeElement);
  console.log(`   Found iframe: ${iframeSrc}`);
  
  // Try to access iframe directly with stealth
  console.log('\n3. Loading iframe URL directly with stealth...');
  await page.goto(iframeSrc, {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  // Wait a bit for Cloudflare to process
  console.log('   Waiting for Cloudflare check...');
  await page.waitForTimeout(5000);
  
  // Check if we passed Cloudflare
  const pageContent = await page.evaluate(() => ({
    title: document.title,
    bodyText: document.body.textContent.substring(0, 500),
    hasCloudflare: document.body.textContent.toLowerCase().includes('cloudflare'),
    hasJustAMoment: document.body.textContent.toLowerCase().includes('just a moment'),
    hasVerifying: document.body.textContent.toLowerCase().includes('verifying')
  }));
  
  console.log('\n4. Page content check:');
  console.log(`   Title: ${pageContent.title}`);
  console.log(`   Has Cloudflare: ${pageContent.hasCloudflare}`);
  console.log(`   Has "Just a moment": ${pageContent.hasJustAMoment}`);
  console.log(`   Has "Verifying": ${pageContent.hasVerifying}`);
  
  if (pageContent.hasCloudflare || pageContent.hasJustAMoment) {
    console.log('\n❌ Still blocked by Cloudflare');
    await page.screenshot({ path: '/home/ubuntu/sarasota_stealth_blocked.png' });
    console.log('   Screenshot saved to /home/ubuntu/sarasota_stealth_blocked.png');
  } else {
    console.log('\n✅ Cloudflare bypassed!');
    await page.screenshot({ path: '/home/ubuntu/sarasota_stealth_success.png' });
    console.log('   Screenshot saved to /home/ubuntu/sarasota_stealth_success.png');
    
    // Look for arrest data
    const arrestLinks = await page.evaluate(() => {
      const links = document.querySelectorAll('a[href*="detail"], a[href*="id="], a[href*="booking"]');
      return Array.from(links).map(a => a.href).slice(0, 10);
    });
    
    console.log(`\n5. Found ${arrestLinks.length} potential arrest links`);
    if (arrestLinks.length > 0) {
      console.log('   Sample links:', arrestLinks.slice(0, 3));
    }
  }
  
  await browser.close();
}

testSarasotaStealth().catch(console.error);
