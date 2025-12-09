// test_charlotte_debug.js
// Debug script to test Charlotte scraper and see raw field extraction

import { newBrowser, newPage, navigateWithRetry, randomDelay, isCloudflareBlocked, waitForCloudflare, humanScroll } from './shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
    readFileSync(join(__dirname, './config/counties.json'), 'utf8')
).charlotte;

const LIST_URL = 'https://inmates.charlottecountyfl.revize.com/bookings';
const BASE_URL = 'https://inmates.charlottecountyfl.revize.com';

async function testCharlotteDebug() {
    console.log('🔍 Testing Charlotte scraper with debug logging...\n');

    let browser = null;

    try {
        browser = await newBrowser();
        const page = await newPage(browser);

        console.log(`📡 Navigating to: ${LIST_URL}`);
        await navigateWithRetry(page, LIST_URL, { timeout: 45000 });
        await randomDelay(3000, 1000);

        await humanScroll(page, 200);
        await randomDelay(1000, 500);

        if (await isCloudflareBlocked(page)) {
            console.log('⚠️  Cloudflare detected, waiting...');
            await waitForCloudflare(page, 30000);
        }

        // Extract first detail URL
        const detailUrls = await page.$$eval('a[href*="/bookings/"]', (links, baseUrl) => {
            const uniqueUrls = new Set();

            links.forEach(link => {
                let href = link.getAttribute('href');
                if (!href) return;

                if (/\/bookings\/?$/i.test(href)) return;

                if (!href.startsWith('http')) {
                    href = baseUrl.replace(/\/$/, '') + (href.startsWith('/') ? href : `/${href}`);
                }
                uniqueUrls.add(href);
            });

            return Array.from(uniqueUrls);
        }, BASE_URL);

        console.log(`📋 Found ${detailUrls.length} booking detail URLs\n`);

        if (detailUrls.length === 0) {
            console.log('ℹ️  No bookings found');
            await browser.close();
            return;
        }

        // Test first record only
        const url = detailUrls[0];
        console.log(`🔍 Testing first record: ${url}\n`);

        await randomDelay(3000, 2000);
        await navigateWithRetry(page, url, { timeout: 30000 });

        if (await isCloudflareBlocked(page)) {
            console.log('⚠️  Cloudflare detected, waiting...');
            await waitForCloudflare(page, 20000);
        }

        await humanScroll(page, 150);
        await randomDelay(500, 300);

        // Extract raw data with debug logging
        const tableData = await page.$$eval('table tr', rows => {
            const result = {};
            rows.forEach(row => {
                const tds = row.querySelectorAll('td');
                if (tds.length >= 2) {
                    const label = tds[0].textContent.trim();
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
                    const label = dt.textContent.trim();
                    const dd = dt.nextElementSibling;
                    if (dd && dd.tagName === 'DD') {
                        const value = dd.textContent.trim();
                        if (label && value) result[label] = value;
                    }
                });
            });
            return result;
        });

        const rawPairs = { ...tableData, ...dlData };

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

testCharlotteDebug().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
