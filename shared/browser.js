import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Apply stealth plugin to avoid detection
puppeteer.use(StealthPlugin());

const USER_AGENTS = [
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
];

/**
 * Create a new browser instance with anti-detection settings and stealth mode
 */
export async function newBrowser() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
      '--disable-web-security',
      '--disable-features=VizDisplayCompositor'
    ],
    defaultViewport: {
      width: 1366,
      height: 900
    }
  });

  return browser;
}

/**
 * Create a new page with randomized user agent and common headers
 */
export async function newPage(browser) {
  const page = await browser.newPage();
  
  // Random user agent
  const userAgent = USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
  await page.setUserAgent(userAgent);

  // Set extra headers
  await page.setExtraHTTPHeaders({
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
  });

  // Additional stealth measures (redundant with plugin but ensures coverage)
  await page.evaluateOnNewDocument(() => {
    // Remove webdriver flag
    Object.defineProperty(navigator, 'webdriver', {
      get: () => false
    });
    
    // Mock plugins
    Object.defineProperty(navigator, 'plugins', {
      get: () => [1, 2, 3, 4, 5]
    });
    
    // Mock languages
    Object.defineProperty(navigator, 'languages', {
      get: () => ['en-US', 'en']
    });
  });

  return page;
}

/**
 * Navigate to URL with retry logic and exponential backoff
 */
export async function navigateWithRetry(page, url, options = {}) {
  const {
    retryLimit = 4,
    backoffBase = 500,
    timeout = 30000,
    waitUntil = 'domcontentloaded'
  } = options;

  for (let attempt = 0; attempt < retryLimit; attempt++) {
    try {
      await page.goto(url, { 
        waitUntil, 
        timeout 
      });
      return true;
    } catch (error) {
      if (attempt < retryLimit - 1) {
        const delay = backoffBase * Math.pow(2, attempt);
        console.log(`⚠️  Navigation failed (attempt ${attempt + 1}/${retryLimit}), retrying in ${delay}ms...`);
        await sleep(delay);
      } else {
        throw new Error(`Navigation failed after ${retryLimit} attempts: ${error.message}`);
      }
    }
  }
  return false;
}

/**
 * Extract text from element with fallback
 */
export async function extractText(page, selector, defaultValue = '') {
  try {
    const element = await page.$(selector);
    if (!element) return defaultValue;
    return await page.evaluate(el => el.textContent?.trim() || '', element);
  } catch (error) {
    return defaultValue;
  }
}

/**
 * Extract attribute from element
 */
export async function extractAttribute(page, selector, attribute, defaultValue = '') {
  try {
    const element = await page.$(selector);
    if (!element) return defaultValue;
    return await page.evaluate((el, attr) => el.getAttribute(attr) || '', element, attribute);
  } catch (error) {
    return defaultValue;
  }
}

/**
 * Extract all matching elements' text
 */
export async function extractAllText(page, selector) {
  try {
    return await page.$$eval(selector, elements => 
      elements.map(el => el.textContent?.trim()).filter(Boolean)
    );
  } catch (error) {
    return [];
  }
}

/**
 * Sleep utility
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Random delay between requests (with jitter)
 */
export async function randomDelay(baseMs = 1000, jitterMs = 400) {
  const delay = baseMs + Math.random() * jitterMs;
  await sleep(delay);
}

/**
 * Check if page has CAPTCHA
 */
export async function hasCaptcha(page) {
  const captchaSelectors = [
    'iframe[src*="recaptcha"]',
    'iframe[src*="captcha"]',
    '.g-recaptcha',
    '#captcha',
    '[name="captcha"]',
    'div[class*="captcha"]'
  ];

  for (const selector of captchaSelectors) {
    const element = await page.$(selector);
    if (element) return true;
  }

  const bodyText = await page.evaluate(() => document.body.textContent?.toLowerCase() || '');
  return bodyText.includes('captcha') || bodyText.includes('verify you are human');
}

/**
 * Check if blocked by Cloudflare
 */
export async function isCloudflareBlocked(page) {
  try {
    const bodyText = await page.evaluate(() => document.body.textContent?.toLowerCase() || '');
    return bodyText.includes('just a moment') || 
           bodyText.includes('cloudflare') ||
           bodyText.includes('checking your browser');
  } catch (error) {
    return false;
  }
}
