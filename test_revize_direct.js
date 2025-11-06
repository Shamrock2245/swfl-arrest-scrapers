import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

async function testRevizeDirect() {
  console.log('Testing direct access to Revize CMS with stealth...\n');
  
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
  await page.setViewport({ width: 1366, height: 900 });
  
  // Set extra headers to look more like a real browser
  await page.setExtraHTTPHeaders({
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
  });
  
  const url = 'https://cms.revize.com/revize/apps/sarasota/index.php';
  
  console.log(`1. Loading ${url}...`);
  await page.goto(url, {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  console.log('2. Waiting 10 seconds for Cloudflare to process...');
  await page.waitForTimeout(10000);
  
  // Check page content
  const pageInfo = await page.evaluate(() => ({
    title: document.title,
    url: window.location.href,
    bodyText: document.body.textContent.substring(0, 1000),
    hasCloudflare: document.body.textContent.toLowerCase().includes('cloudflare'),
    hasJustAMoment: document.body.textContent.toLowerCase().includes('just a moment'),
    hasVerifying: document.body.textContent.toLowerCase().includes('verifying'),
    hasTurnstile: !!document.querySelector('[name="cf-turnstile-response"]'),
    formCount: document.querySelectorAll('form').length,
    inputCount: document.querySelectorAll('input').length,
    linkCount: document.querySelectorAll('a').length
  }));
  
  console.log('\n3. Page analysis:');
  console.log(`   Title: ${pageInfo.title}`);
  console.log(`   URL: ${pageInfo.url}`);
  console.log(`   Has Cloudflare text: ${pageInfo.hasCloudflare}`);
  console.log(`   Has "Just a moment": ${pageInfo.hasJustAMoment}`);
  console.log(`   Has "Verifying": ${pageInfo.hasVerifying}`);
  console.log(`   Has Turnstile widget: ${pageInfo.hasTurnstile}`);
  console.log(`   Forms: ${pageInfo.formCount}, Inputs: ${pageInfo.inputCount}, Links: ${pageInfo.linkCount}`);
  
  await page.screenshot({ path: '/home/ubuntu/revize_stealth.png', fullPage: true });
  console.log('\n4. Screenshot saved to /home/ubuntu/revize_stealth.png');
  
  if (pageInfo.hasCloudflare || pageInfo.hasJustAMoment || pageInfo.hasTurnstile) {
    console.log('\n❌ Still blocked by Cloudflare');
    console.log('\nBody text preview:');
    console.log(pageInfo.bodyText);
  } else {
    console.log('\n✅ Cloudflare bypassed!');
    
    // Look for arrest search interface
    const searchElements = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input[type="text"], input[type="search"], input[name*="name"], input[name*="search"]');
      const buttons = document.querySelectorAll('button, input[type="submit"]');
      const links = document.querySelectorAll('a[href*="detail"], a[href*="arrest"], a[href*="booking"]');
      
      return {
        searchInputs: Array.from(inputs).map(i => ({ name: i.name, id: i.id, placeholder: i.placeholder })),
        buttons: Array.from(buttons).map(b => b.textContent.trim()).slice(0, 5),
        arrestLinks: Array.from(links).map(a => a.href).slice(0, 10)
      };
    });
    
    console.log('\n5. Search interface elements:');
    console.log('   Search inputs:', searchElements.searchInputs);
    console.log('   Buttons:', searchElements.buttons);
    console.log('   Arrest links:', searchElements.arrestLinks);
  }
  
  await browser.close();
}

testRevizeDirect().catch(console.error);
