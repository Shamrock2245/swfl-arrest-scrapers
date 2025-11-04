// scrapers/collier.js
// Collier County (ASPX) scraper wired to your existing helpers & writers.

import {
  newBrowser,
  newPage,
  navigateWithRetry,
  randomDelay,
  hasCaptcha,
} from "../shared/browser.js";
import { normalizeRecord } from "../normalizers/normalize.js";
import {
  upsertRecords,
  mirrorQualifiedToDashboard,
  logIngestion,
} from "../writers/sheets.js";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, "../config/counties.json"), "utf8")
).collier;

// Derive Report.aspx (Today's Arrest Reports) from baseUrl
const REPORT_URL = `${config.baseUrl.replace(/\/$/, "")}/arrestsearch/Report.aspx`;

/**
 * Main entry
 */
export async function runCollier() {
  const startTime = Date.now();
  console.log("═══════════════════════════════════════");
  console.log("🚦 Starting Collier County Scraper");
  console.log("═══════════════════════════════════════");

  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // 1) Land on terms page
    console.log(`📡 Loading: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);
    await randomDelay(1200, 400);

    // 2) CAPTCHA check early
    if (await hasCaptcha(page))
      throw new Error("CAPTCHA detected - cannot proceed");

    // 3) Accept terms / click entry points if present
    await acceptTermsOrDirectToToday(page);

    // 4) Ensure we are on Report.aspx (today's reports)
    if (!page.url().toLowerCase().includes("/arrestsearch/report.aspx")) {
      console.log(
        "↪️ Navigating directly to Today’s Arrest Reports (Report.aspx) …"
      );
      await navigateWithRetry(page, REPORT_URL);
    }
    await randomDelay(1000, 300);

    // 5) Gather all detail links (handles pagination safely)
    const detailLinks = await collectAllDetailLinks(page);
    console.log(`🔗 Found ${detailLinks.length} detail links`);

    if (detailLinks.length === 0) {
      // soft retry once (site can be slow)
      console.log("   ↻ Retry once to collect links …");
      await navigateWithRetry(page, REPORT_URL);
      await randomDelay(1000, 300);
      const retry = await collectAllDetailLinks(page);
      detailLinks.push(...retry);
      console.log(`   ↪️ After retry: ${detailLinks.length} detail links`);
    }

    // 6) Visit each detail page and extract data
    const records = [];
    const detailPage = page; // reuse same tab (gentler to site)
    for (let i = 0; i < detailLinks.length; i++) {
      const url = detailLinks[i];
      try {
        await randomDelay(400, 250);
        await navigateWithRetry(detailPage, url);
        const merged = await extractDetail(detailPage);
        // Normalize to your canonical shape
        const record = normalizeRecord(merged, "COLLIER", url);

        if (record?.booking_id) {
          records.push(record);
          console.log(
            `   ✅ [${i + 1}/${detailLinks.length}] ${record.full_name_last_first || merged.name || "(no name)"}`
          );
        } else {
          console.log(
            `   ⚠️  [${i + 1}/${detailLinks.length}] Missing booking_id; skipping`
          );
        }
      } catch (e) {
        console.error(
          `   ⚠️  [${i + 1}/${detailLinks.length}] detail failed:`,
          e?.message || e
        );
      }
    }

    // 7) Upsert to Google Sheets, mirror to dashboard, and log
    console.log(`\n📊 Parsed ${records.length} valid records`);
    if (records.length > 0) {
      const result = await upsertRecords(config.sheetName, records);
      console.log(
        `✅ Inserted: ${result.inserted}, Updated: ${result.updated}`
      );
      await mirrorQualifiedToDashboard(records);
    }

    await logIngestion("COLLIER", true, records.length, startTime);
    console.log("✅ Finished Collier successfully.");
    console.log("═══════════════════════════════════════\n");
    return { success: true, count: records.length };
  } catch (error) {
    console.error("❌ Fatal error:", error?.message || error);
    if (error?.stack) console.error(error.stack);
    await logIngestion(
      "COLLIER",
      false,
      0,
      startTime,
      String(error?.message || error)
    );
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

/**
 * Accept terms or click through to "Today's Arrest Reports".
 * Handles typical ASP.NET controls: input[type=submit], buttons, and anchor text.
 */
async function acceptTermsOrDirectToToday(page) {
  // First, try obvious "Click Here to See Todays Arrest Reports"
  const clickedDirect = await clickByText(page, /todays arrest reports/i);
  if (clickedDirect) {
    await waitPostback(page);
    return;
  }

  // Try "I Accept" / "I Agree"
  const clickedAccept =
    (await clickInputValueContains(page, /accept|agree/i)) ||
    (await clickButtonText(page, /accept|agree/i));
  if (clickedAccept) {
    await waitPostback(page);
    // After acceptance, some templates still require a second click → try direct link again
    const clicked = await clickByText(page, /todays arrest reports/i);
    if (clicked) await waitPostback(page);
  }
}

/**
 * Collect all ReportDetail.aspx links across pages.
 */
async function collectAllDetailLinks(page) {
  const links = new Set();

  async function harvest() {
    const found = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll('a[href*="ReportDetail.aspx"]').forEach((a) => {
        let href = a.getAttribute("href") || "";
        if (!href) return;
        // Convert relative → absolute
        try {
          const url = new URL(href, location.href).toString();
          out.push(url);
        } catch {}
      });
      return out;
    });
    for (const u of found) links.add(u);
  }

  await page.waitForTimeout(800);
  await harvest();

  // ASP.NET often uses numeric page links / Next
  for (let i = 0; i < 20; i++) {
    const moved = await clickPagination(page);
    if (!moved) break;
    await waitPostback(page);
    await page.waitForTimeout(600);
    await harvest();
  }

  return Array.from(links);
}

/**
 * Extract details from ReportDetail.aspx page (KV scan with fallbacks).
 */
async function extractDetail(page) {
  // Wait for any table-ish content to appear
  await page
    .waitForSelector("table, .detail, .content, #main", { timeout: 15000 })
    .catch(() => {});

  const data = await page.evaluate(() => {
    const text = (el) => (el?.textContent || "").replace(/\s+/g, " ").trim();
    const kv = {};

    // Strategy A: pairwise <td>Label</td><td>Value</td>
    const tds = [...document.querySelectorAll("table td")];
    for (let i = 0; i + 1 < tds.length; i += 2) {
      const k = text(tds[i]).replace(/:$/, "");
      const v = text(tds[i + 1]);
      if (k && v && v !== k) kv[k.toLowerCase()] = v;
    }

    // Strategy B: definition lists <dt><dd>
    const dts = [...document.querySelectorAll("dt")];
    for (const dt of dts) {
      const dd = dt.nextElementSibling;
      const k = text(dt).replace(/:$/, "");
      const v = text(dd);
      if (k && v && v !== k) kv[k.toLowerCase()] = v;
    }

    // Headings (name sometimes only appears here)
    const h1 = text(document.querySelector("h1"));
    const h2 = text(document.querySelector("h2"));
    if (h1) kv["headline"] = h1;
    if (h2) kv["subhead"] = h2;

    const pick = (...keys) => {
      for (const k of keys) {
        const v = kv[k];
        if (typeof v === "string" && v) return v;
      }
      return "";
    };

    const name =
      pick("name", "inmate", "defendant", "headline") ||
      pick("last, first", "last first");

    const bookingNumber =
      pick("booking #", "booking number", "booking no", "booking") ||
      pick("booking#", "booking#", "booking id");

    const bookingDate = pick("booking date", "booked", "arrest date", "date");
    const dob = pick("dob", "date of birth", "d.o.b", "birth date");
    const race = pick("race");
    const sex = pick("sex", "gender");
    const address = pick("address", "home address");
    const agency = pick("agency", "arresting agency");

    const chargesBlock =
      pick("charges", "charge(s)", "charge") ||
      [kv["charge 1"], kv["charge 2"], kv["charge 3"]]
        .filter(Boolean)
        .join(" | ");

    const bond =
      pick("bond", "bond amount", "total bond", "bond total", "bail") ||
      pick("total bond amount");

    // Mugshot (if present)
    let mugshot_url = "";
    const img = document.querySelector(
      'img[src*="photo"], img[src*="mug"], img[src*="Image"]'
    );
    if (img?.src) mugshot_url = img.src;

    return {
      name,
      bookingNumber,
      bookingDate,
      dob,
      race,
      sex,
      address,
      agency,
      charges: chargesBlock,
      bond,
      mugshot_url,
      detail_url: location.href,
      raw: kv,
      page_title: document.title || "",
    };
  });

  return data;
}

/* ----------------------- helper DOM actions ----------------------- */

async function waitPostback(page) {
  // ASP.NET postbacks can be quick; try for DOMContentLoaded first, fallback to short sleep.
  try {
    await page.waitForNavigation({
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });
  } catch {
    await page.waitForTimeout(500);
  }
}

async function clickInputValueContains(page, regex) {
  return await page.evaluate((pattern) => {
    const rx = new RegExp(pattern, "i");
    const btn = [
      ...document.querySelectorAll(
        'input[type="submit"], input[type="button"]'
      ),
    ].find((el) => rx.test(el.value || ""));
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  }, regex.source);
}

async function clickButtonText(page, regex) {
  return await page.evaluate((pattern) => {
    const rx = new RegExp(pattern, "i");
    const btn = [...document.querySelectorAll("button")].find((el) =>
      rx.test(el.textContent || "")
    );
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  }, regex.source);
}

async function clickByText(page, regex) {
  return await page.evaluate((pattern) => {
    const rx = new RegExp(pattern, "i");
    const els = [...document.querySelectorAll("a, button")];
    const el = els.find((e) => rx.test((e.textContent || "").trim()));
    if (el) {
      el.click();
      return true;
    }
    return false;
  }, regex.source);
}

async function clickPagination(page) {
  // prefer "Next", else the next page number
  const didClick = await page.evaluate(() => {
    const as = [...document.querySelectorAll("a")];
    // normalize text
    const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
    const nextA =
      as.find((a) => /^next$/i.test(clean(a.textContent))) ||
      as.find((a) => clean(a.textContent) === ">");
    if (nextA) {
      nextA.click();
      return true;
    }
    // try any numeric page link not marked active
    const nums = as.filter((a) => /^\d+$/.test(clean(a.textContent)));
    if (nums.length > 0) {
      // choose the first one that isn't bold/active
      const cand = nums[0];
      cand.click();
      return true;
    }
    return false;
  });
  return didClick;
}

/* ----------------------- direct-run support ----------------------- */

if (import.meta.url === `file://${process.argv[1]}`) {
  runCollier().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

export default runCollier;
