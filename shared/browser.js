import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Apply stealth plugin to avoid detection
puppeteer.use(StealthPlugin());

// Expanded user agent pool with recent versions
const USER_AGENTS = [
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
];

// Randomized viewport sizes (common resolutions)
const VIEWPORTS = [
  { width: 1920, height: 1080 },
  { width: 1366, height: 768 },
  { width: 1536, height: 864 },
  { width: 1440, height: 900 },
  { width: 1280, height: 720 }
];

/**
 * Create a new browser instance with enhanced anti-detection settings
 */
export async function newBrowser() {
  const browser = await puppeteer.launch({
    headless: true,
    ignoreHTTPSErrors: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
      '--disable-web-security',
      '--disable-features=VizDisplayCompositor',
      '--window-size=1920,1080',
      '--start-maximized',
      '--disable-infobars',
      '--disable-notifications',
      '--disable-popup-blocking',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--no-zygote',
      '--single-process'
    ],
    ignoreHTTPSErrors: true,
    defaultViewport: null
  });

  return browser;
}

/**
 * Create a new page with randomized fingerprint and enhanced stealth
 */
export async function newPage(browser) {
  const page = await browser.newPage();

  // Random user agent
  const userAgent = USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
  await page.setUserAgent(userAgent);

  // Random viewport
  const viewport = VIEWPORTS[Math.floor(Math.random() * VIEWPORTS.length)];
  await page.setViewport(viewport);

  // Set realistic headers
  await page.setExtraHTTPHeaders({
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
  });

  // Enhanced stealth measures
  await page.evaluateOnNewDocument(() => {
    // Remove webdriver flag
    Object.defineProperty(navigator, 'webdriver', {
      get: () => false
    });

    // Mock plugins
    Object.defineProperty(navigator, 'plugins', {
      get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
      ]
    });

    // Mock languages
    Object.defineProperty(navigator, 'languages', {
      get: () => ['en-US', 'en']
    });

    // Mock permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
      parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
    );

    // Mock chrome runtime
    window.chrome = {
      runtime: {}
    };

    // Override the `navigator.platform` property
    Object.defineProperty(navigator, 'platform', {
      get: () => 'Win32'
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
    backoffBase = 1000,
    timeout = 60000,
    waitUntil = 'domcontentloaded'
  } = options;

  for (let attempt = 0; attempt < retryLimit; attempt++) {
    try {
      await page.goto(url, {
        waitUntil,
        timeout
      });

      // Wait for page to be fully loaded
      await randomDelay(2000, 1000);

      // Check if blocked by Cloudflare
      const isBlocked = await isCloudflareBlocked(page);
      if (isBlocked) {
        console.log('⚠️  Cloudflare detected, waiting for challenge to resolve...');
        await sleep(10000); // Wait 10 seconds for Cloudflare challenge

        // Check again
        const stillBlocked = await isCloudflareBlocked(page);
        if (stillBlocked) {
          throw new Error('Blocked by Cloudflare after waiting');
        }
      }

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
 * Simulate human-like mouse movements
 */
export async function humanMouseMove(page, x, y) {
  const steps = 10 + Math.floor(Math.random() * 10); // 10-20 steps
  const currentPosition = await page.evaluate(() => ({
    x: window.innerWidth / 2,
    y: window.innerHeight / 2
  }));

  for (let i = 0; i <= steps; i++) {
    const progress = i / steps;
    const currentX = currentPosition.x + (x - currentPosition.x) * progress;
    const currentY = currentPosition.y + (y - currentPosition.y) * progress;

    await page.mouse.move(currentX, currentY);
    await sleep(10 + Math.random() * 20); // 10-30ms between steps
  }
}

/**
 * Simulate human-like scrolling
 */
export async function humanScroll(page, distance = 300) {
  const scrollSteps = 5 + Math.floor(Math.random() * 5); // 5-10 steps
  const stepDistance = distance / scrollSteps;

  for (let i = 0; i < scrollSteps; i++) {
    await page.evaluate((step) => {
      window.scrollBy(0, step);
    }, stepDistance);
    await sleep(100 + Math.random() * 100); // 100-200ms between steps
  }
}

/**
 * Simulate human-like typing with random delays
 */
export async function humanType(page, selector, text) {
  await page.click(selector);
  await randomDelay(300, 200);

  for (const char of text) {
    await page.keyboard.type(char);
    await sleep(50 + Math.random() * 150); // 50-200ms between keystrokes
  }
}

/**
 * Simulate human-like click with mouse movement
 */
export async function humanClick(page, selector) {
  const element = await page.$(selector);
  if (!element) {
    throw new Error(`Element not found: ${selector}`);
  }

  const box = await element.boundingBox();
  if (box) {
    const x = box.x + box.width / 2 + (Math.random() - 0.5) * 10;
    const y = box.y + box.height / 2 + (Math.random() - 0.5) * 10;

    await humanMouseMove(page, x, y);
    await randomDelay(200, 100);
    await page.mouse.click(x, y);
  } else {
    await element.click();
  }
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
 * Random delay between requests (with increased base times for more human-like behavior)
 */
export async function randomDelay(baseMs = 2000, jitterMs = 1000) {
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
    'div[class*="captcha"]',
    'div[class*="cf-challenge"]'
  ];

  for (const selector of captchaSelectors) {
    const element = await page.$(selector);
    if (element) return true;
  }

  const bodyText = await page.evaluate(() => document.body.textContent?.toLowerCase() || '');
  return bodyText.includes('captcha') ||
    bodyText.includes('verify you are human') ||
    bodyText.includes('checking your browser');
}

/**
 * Check if blocked by Cloudflare
 */
export async function isCloudflareBlocked(page) {
  try {
    const bodyText = await page.evaluate(() => document.body.textContent?.toLowerCase() || '');
    const title = await page.title();

    return bodyText.includes('just a moment') ||
      bodyText.includes('cloudflare') ||
      bodyText.includes('checking your browser') ||
      bodyText.includes('enable javascript and cookies') ||
      title.toLowerCase().includes('just a moment');
  } catch (error) {
    return false;
  }
}

/**
 * Wait for Cloudflare challenge to complete
 */
export async function waitForCloudflare(page, maxWaitTime = 30000) {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitTime) {
    const isBlocked = await isCloudflareBlocked(page);
    if (!isBlocked) {
      console.log('✅ Cloudflare challenge passed');
      return true;
    }

    console.log('⏳ Waiting for Cloudflare challenge to resolve...');
    await sleep(2000);
  }

  throw new Error('Cloudflare challenge timeout');
}
