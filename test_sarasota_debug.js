// test_sarasota_debug.js
// Debug script to test Sarasota scraper and see raw field extraction

import { newBrowser, newPage, navigateWithRetry, randomDelay, isCloudflareBlocked, waitForCloudflare } from './shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
    readFileSync(join(__dirname, './config/counties.json'), 'utf8')
).sarasota;

const MAIN_URL = 'https://www.sarasotasheriff.org/arrest-reports/index.php';
const IFRAME_URL = 'https://cms.revize.com/revize/apps/sarasota/index.php';

async function testSarasotaDebug() {
    console.log('🔍 Testing Sarasota scraper with debug logging...\n');

    let browser = null;

    try {
        browser = await newBrowser();
        const page = await newPage(browser);

        console.log(`📡 Loading main page: ${MAIN_URL}`);
        await navigateWithRetry(page, MAIN_URL, { timeout: 45000 });
        await randomDelay(1000, 400);

        const iframeUrl = await page.evaluate(() => {
            const iframe = document.querySelector('iframe[src*="cms.revize.com/revize/apps/sarasota"]');
            return iframe ? iframe.src : null;
        });

        if (!iframeUrl) {
            throw new Error('Could not find arrest search iframe');
        }

        console.log(`➡️  Navigating to: ${iframeUrl}`);
        await navigateWithRetry(page, iframeUrl, { timeout: 45000 });
        await randomDelay(2000, 500);

        if (await isCloudflareBlocked(page)) {
            console.log('⚠️  Cloudflare detected, waiting...');
            await waitForCloudflare(page, 30000);
        }

        // Get today's date
        const today = new Date();
        const arrestDate = `${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getDate().toString().padStart(2, '0')}/${today.getFullYear()}`;

        console.log(`📅 Searching for arrests on: ${arrestDate}\n`);

        // Try to find and fill the date input
        const dateInput = await page.$('input[name="arrest_date"], input[type="text"][placeholder*="date"], input#arrest_date');
        if (dateInput) {
            await dateInput.click({ clickCount: 3 });
            await dateInput.type(arrestDate);
            await randomDelay(500, 200);

            const searchButton = await page.$('button:has-text("Search"), input[type="submit"][value*="Search"]');
            if (searchButton) {
                console.log('🔎 Submitting search...');
                await searchButton.click();
                await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => { });
                await randomDelay(2000, 500);
            }
        }

        // Extract first detail URL
        const detailUrls = await page.$$eval('a[href*="viewInmate.php"], a[href*="detail.php"]', (links) => {
            const urls = [];
            links.forEach(link => {
                let href = link.getAttribute('href');
                if (href && !href.includes('javascript')) {
                    if (!href.startsWith('http')) {
                        const currentUrl = window.location.href;
                        const urlObj = new URL(currentUrl);
                        const base = `${urlObj.protocol}//${urlObj.host}${urlObj.pathname.substring(0, urlObj.pathname.lastIndexOf('/') + 1)}`;
                        href = base + href;
                    }
                    urls.push(href);
                }
            });
            return [...new Set(urls)];
        });

        console.log(`📋 Found ${detailUrls.length} arrest records\n`);

        if (detailUrls.length === 0) {
            console.log('ℹ️  No arrests found for this date');
            await browser.close();
            return;
        }

        // Test first record only
        const url = detailUrls[0];
        console.log(`🔍 Testing first record: ${url}\n`);

        await randomDelay(2000, 500);
        await navigateWithRetry(page, url, { timeout: 30000 });
        await randomDelay(1000, 300);

        // Extract raw data with debug logging
        const rawPairs = await page.$$eval('table tr', rows => {
            const result = {};
            rows.forEach(row => {
                const tds = row.querySelectorAll('td');
                if (tds.length >= 2) {
                    const label = tds[0].textContent.trim().replace(/:$/, '');
                    const value = tds[1].textContent.trim();
                    if (label && value) result[label] = value;
                }
            });
            return result;
        });

        // Also check for dl/dt/dd structure
        const dlData = await page.$$eval('dl', dls => {
            const result = {};
            dls.forEach(dl => {
                const dts = dl.querySelectorAll('dt');
                dts.forEach(dt => {
                    const label = dt.textContent.trim().replace(/:$/, '');
                    const dd = dt.nextElementSibling;
                    if (dd && dd.tagName === 'DD') {
                        const value = dd.textContent.trim();
                        if (label && value) result[label] = value;
                    }
                });
            });
            return result;
        });

        Object.assign(rawPairs, dlData);

        console.log('═══════════════════════════════════════');
        console.log('📊 RAW EXTRACTED FIELDS:');
        console.log('═══════════════════════════════════════');

        // Sort keys for easier reading
        const sortedKeys = Object.keys(rawPairs).sort();
        sortedKeys.forEach(key => {
            console.log(`  "${key}": "${rawPairs[key]}"`);
        });

        console.log('═══════════════════════════════════════\n');

        // Check for date-related fields
        console.log('🔍 DATE-RELATED FIELDS:');
        const dateFields = sortedKeys.filter(key =>
            key.toLowerCase().includes('date') ||
            key.toLowerCase().includes('arrest') ||
            key.toLowerCase().includes('book')
        );

        if (dateFields.length > 0) {
            dateFields.forEach(key => {
                console.log(`  ✓ "${key}": "${rawPairs[key]}"`);
            });
        } else {
            console.log('  ⚠️  No date-related fields found!');
        }

        console.log('\n');

        await browser.close();

    } catch (error) {
        console.error('❌ Error:', error.message);
        if (browser) await browser.close();
        throw error;
    }
}

testSarasotaDebug().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
