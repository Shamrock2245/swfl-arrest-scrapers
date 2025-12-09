import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { newBrowser, newPage } from './shared/browser.js';

puppeteerExtra.use(StealthPlugin());

const ROSTER_URL = 'https://www.hendrysheriff.org/inmateSearch';

async function debugHendry() {
    console.log('Debugging Hendry structure...');
    const browser = await newBrowser();
    try {
        const page = await newPage(browser);
        await page.goto(ROSTER_URL, { waitUntil: 'networkidle2', timeout: 60000 });
        await new Promise(r => setTimeout(r, 3000));

        // Dump all links
        const links = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a')).map(a => a.href);
        });

        console.log('Found links:', links.length);
        console.log('First 10 links:', links.slice(0, 10));
        console.log('Links containing "inmate":', links.filter(l => l.toLowerCase().includes('inmate')));

        // Dump body text preview
        const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
        console.log('Body text preview:', bodyText);

        await page.screenshot({ path: 'hendry_debug.png', fullPage: true });
        console.log('Screenshot saved to hendry_debug.png');

    } catch (error) {
        console.error('Debug failed:', error);
    } finally {
        await browser.close();
    }
}

debugHendry();
