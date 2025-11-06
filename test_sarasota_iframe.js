import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

async function testSarasotaIframe() {
  console.log('Testing Sarasota iframe handling...\n');
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage'
    ]
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 900 });
  
  console.log('1. Loading main page...');
  await page.goto('https://www.sarasotasheriff.org/arrest-reports/index.php', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  // Wait longer for iframe to load
  console.log('2. Waiting for iframe to load...');
  await page.waitForTimeout(5000);
  
  // Get iframe info
  const iframeInfo = await page.evaluate(() => {
    const iframe = document.querySelector('iframe');
    if (!iframe) return null;
    return {
      src: iframe.src,
      id: iframe.id,
      className: iframe.className,
      width: iframe.width,
      height: iframe.height
    };
  });
  
  console.log('   Iframe info:', iframeInfo);
  
  if (!iframeInfo || !iframeInfo.src) {
    console.log('❌ Iframe has no src attribute');
    
    // Try to find the iframe URL in page source
    const pageSource = await page.content();
    const iframeSrcMatch = pageSource.match(/cms\.revize\.com[^"']*/);
    if (iframeSrcMatch) {
      console.log(`   Found potential iframe URL in source: ${iframeSrcMatch[0]}`);
    }
    
    await browser.close();
    return;
  }
  
  // Try accessing iframe content
  console.log('\n3. Accessing iframe content...');
  const frames = page.frames();
  console.log(`   Total frames: ${frames.length}`);
  
  for (let i = 0; i < frames.length; i++) {
    const frame = frames[i];
    const frameUrl = frame.url();
    console.log(`   Frame ${i}: ${frameUrl}`);
    
    if (frameUrl.includes('revize') || frameUrl.includes('sarasota')) {
      console.log(`\n4. Found Sarasota iframe at index ${i}`);
      
      try {
        // Wait for content to load in iframe
        await frame.waitForTimeout(3000);
        
        const iframeContent = await frame.evaluate(() => ({
          title: document.title,
          bodyText: document.body ? document.body.textContent.substring(0, 500) : 'No body',
          hasCloudflare: document.body && document.body.textContent.toLowerCase().includes('cloudflare'),
          linksCount: document.querySelectorAll('a').length
        }));
        
        console.log('   Iframe content:', iframeContent);
        
        if (!iframeContent.hasCloudflare) {
          // Look for arrest links in iframe
          const arrestLinks = await frame.evaluate(() => {
            const links = document.querySelectorAll('a');
            return Array.from(links).map(a => ({
              href: a.href,
              text: a.textContent.trim()
            })).filter(l => l.href).slice(0, 10);
          });
          
          console.log(`\n5. Found ${arrestLinks.length} links in iframe`);
          arrestLinks.forEach((link, idx) => {
            console.log(`   ${idx + 1}. ${link.text} -> ${link.href}`);
          });
        }
      } catch (error) {
        console.log(`   Error accessing iframe: ${error.message}`);
      }
    }
  }
  
  await page.screenshot({ path: '/home/ubuntu/sarasota_iframe_test.png', fullPage: true });
  console.log('\nScreenshot saved to /home/ubuntu/sarasota_iframe_test.png');
  
  await browser.close();
}

testSarasotaIframe().catch(console.error);
