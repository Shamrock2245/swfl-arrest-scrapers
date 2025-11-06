import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteerExtra.use(StealthPlugin());

async function test() {
  const browser = await puppeteerExtra.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.goto('https://www.hendrysheriff.org/inmateSearch', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForTimeout(5000);
  
  const result = await page.evaluate(() => {
    const allLinks = Array.from(document.querySelectorAll('a'));
    const nameLinks = allLinks.filter(a => {
      const text = a.textContent.trim();
      return text.match(/^[A-Z]+,\s+[A-Z\s]+$/);
    });
    
    return {
      totalLinks: allLinks.length,
      nameLinksCount: nameLinks.length,
      sampleNameLinks: nameLinks.slice(0, 5).map(a => ({
        text: a.textContent.trim(),
        href: a.href
      }))
    };
  });
  
  console.log(JSON.stringify(result, null, 2));
  
  await browser.close();
}

test().catch(console.error);
