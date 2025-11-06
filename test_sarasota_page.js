import { newBrowser, newPage } from './shared/browser.js';

async function testSarasotaPage() {
  const browser = await newBrowser();
  const page = await newPage(browser);
  
  console.log('Loading Sarasota page...');
  await page.goto('https://www.sarasotasheriff.org/arrest-reports/index.php', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForTimeout(3000);
  
  // Save screenshot
  await page.screenshot({ path: '/home/ubuntu/sarasota_page.png', fullPage: true });
  console.log('Screenshot saved to /home/ubuntu/sarasota_page.png');
  
  // Check for iframes
  const iframes = await page.evaluate(() => {
    const frames = document.querySelectorAll('iframe');
    return Array.from(frames).map(f => ({
      src: f.src,
      id: f.id,
      className: f.className
    }));
  });
  
  console.log('\nIframes found:', iframes);
  
  // Check body text
  const bodyText = await page.evaluate(() => document.body.textContent);
  console.log('\nBody text preview (first 500 chars):', bodyText.substring(0, 500));
  
  // Check for CAPTCHA indicators
  const hasCaptcha = await page.evaluate(() => {
    const bodyText = document.body.textContent?.toLowerCase() || '';
    return {
      hasRecaptchaIframe: !!document.querySelector('iframe[src*="recaptcha"]'),
      hasCaptchaDiv: !!document.querySelector('div[class*="captcha"]'),
      bodyIncludesCaptcha: bodyText.includes('captcha'),
      bodyIncludesCloudflare: bodyText.includes('cloudflare'),
      bodyIncludesJustAMoment: bodyText.includes('just a moment')
    };
  });
  
  console.log('\nCAPTCHA indicators:', hasCaptcha);
  
  // Try to find arrest data
  const arrestLinks = await page.evaluate(() => {
    const links = document.querySelectorAll('a[href*="detail"], a[href*="id="]');
    return Array.from(links).map(a => a.href).slice(0, 10);
  });
  
  console.log('\nArrest detail links found:', arrestLinks.length);
  if (arrestLinks.length > 0) {
    console.log('Sample links:', arrestLinks.slice(0, 3));
  }
  
  await browser.close();
}

testSarasotaPage().catch(console.error);
