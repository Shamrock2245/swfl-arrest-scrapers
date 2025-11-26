# SWFL Arrest Scrapers - Development Guidelines

## Code Standards

### JavaScript/Node.js

**Module System**: ES Modules (type: "module")
```javascript
// ✅ Correct
import { getSheetsClient } from '../writers/sheets34.js';

// ❌ Incorrect
const { getSheetsClient } = require('../writers/sheets34.js');
```

**Naming Conventions**:
- **Files**: `snake_case` (e.g., `hendry_stealth.js`)
- **Functions**: `camelCase` (e.g., `runHendryStealth()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `GOOGLE_SHEETS_ID`)
- **Classes**: `PascalCase` (e.g., `ArrestRecord`)

**Error Handling**:
```javascript
// ✅ Always use try-catch for async operations
try {
  const data = await scrapePage(url);
  await writeToSheets(data);
} catch (error) {
  console.error(`❌ Fatal error: ${error.message}`);
  process.exit(1);
}
```

**Logging**:
```javascript
// Use emoji for visual clarity
console.log('🚀 Starting scraper...');
console.log('✅ Success: 50 records inserted');
console.error('❌ Error: Connection failed');
console.warn('⚠️  Warning: Rate limit approaching');
```

---

## Project Structure

```
swfl-arrest-scrapers/
├── .github/
│   └── workflows/          # GitHub Actions workflows
│       ├── scrape-hillsborough.yml
│       ├── scrape-manatee.yml
│       └── ...
├── apps_script/            # Google Apps Script files
│   ├── ComprehensiveMenuSystem.gs
│   ├── LeadScoringSystem.gs
│   ├── Form_Enhanced.html
│   └── ...
├── config/                 # Configuration files
│   ├── schema.json
│   └── counties.json
├── normalizers/            # Data normalization
│   └── normalize34.js
├── scrapers/               # County scrapers
│   ├── hendry_stealth.js
│   ├── charlotte_stealth.js
│   └── ...
├── shared/                 # Shared utilities
│   └── browser.js
├── writers/                # Data writers
│   └── sheets34.js
├── .env                    # Environment variables (NOT in Git)
├── .gitignore
├── package.json
├── README.md
└── ARCHITECTURE.md
```

---

## Development Workflow

### 1. Setup Local Environment

```bash
# Clone repository
git clone https://github.com/Shamrock2245/swfl-arrest-scrapers.git
cd swfl-arrest-scrapers

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
EOF

# Add service account key
# (Download from Google Cloud Console and save as service-account-key.json)
```

### 2. Create Feature Branch

```bash
# Create branch from main
git checkout -b feature/add-pinellas-county

# Make changes
# ...

# Commit with descriptive message
git add .
git commit -m "Add Pinellas County scraper with stealth mode

- Implement click-through to detail pages
- Add 34-column normalization
- Include date-based searching
- Update documentation"

# Push to GitHub
git push origin feature/add-pinellas-county
```

### 3. Test Locally

```bash
# Test single county
node scrapers/hendry_stealth.js

# Test all counties
node run_all_counties.js

# Verify data in Google Sheets
# https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit
```

### 4. Create Pull Request

- Go to GitHub repository
- Click "Pull requests" → "New pull request"
- Select your feature branch
- Add description of changes
- Request review (if team member available)
- Merge when approved

---

## Adding a New County Scraper

### Step 1: Research County Website

1. **Find arrest/booking page**
2. **Identify data structure**:
   - Is it a table, list, or cards?
   - Are detail pages required?
   - Is there CAPTCHA or Cloudflare?
3. **Test manual extraction**:
   - Open browser DevTools
   - Inspect HTML structure
   - Note CSS selectors

### Step 2: Create Scraper File

**Template**: `/scrapers/[county]_stealth.js`

```javascript
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { normalizeToSchema } from '../normalizers/normalize34.js';
import { writeToSheets, logIngestion } from '../writers/sheets34.js';

puppeteer.use(StealthPlugin());

const CONFIG = {
  url: 'https://county-website.com/bookings',
  county: 'COUNTY_NAME',
  sheetTab: 'County_Name',
  timeout: 30000,
  delayMin: 800,
  delayMax: 1400
};

async function runCountyStealth() {
  console.log(`🚀 Starting ${CONFIG.county} County scraper...`);
  
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Navigate and scrape
    await page.goto(CONFIG.url, { waitUntil: 'networkidle2' });
    
    // Extract data
    const rawData = await page.evaluate(() => {
      // Your extraction logic here
    });
    
    // Normalize
    const normalized = rawData.map(record => normalizeToSchema(record, CONFIG.county));
    
    // Write to sheets
    const result = await writeToSheets(normalized, CONFIG.sheetTab);
    
    console.log(`✅ ${CONFIG.county}: inserted ${result.inserted}, updated ${result.updated}`);
    
    await logIngestion(CONFIG.county, 'SUCCESS', normalized.length);
    
  } catch (error) {
    console.error(`❌ Fatal ${CONFIG.county} error: ${error.message}`);
    await logIngestion(CONFIG.county, 'FAILURE', 0, error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

runCountyStealth();
```

### Step 3: Add Normalization Logic

Update `/normalizers/normalize34.js` if county has unique fields:

```javascript
export function normalizeToSchema(rawData, county) {
  // County-specific parsing
  if (county === 'NEW_COUNTY') {
    return {
      Booking_Number: rawData.inmate_id || '',
      Full_Name: rawData.name || '',
      // ... map all 34 fields
    };
  }
  
  // Default normalization
  return {
    // ... standard mapping
  };
}
```

### Step 4: Create GitHub Actions Workflow

**File**: `/.github/workflows/scrape-[county].yml`

```yaml
name: Scrape [County] County

on:
  schedule:
    - cron: '*/30 * * * *'  # Adjust frequency based on arrest volume
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install
      - run: npx puppeteer browsers install chrome
      - run: node scrapers/[county]_stealth.js
        env:
          GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
          GOOGLE_SA_KEY_JSON: ${{ secrets.GOOGLE_SA_KEY_JSON }}
```

### Step 5: Update Documentation

- Add county to `README.md`
- Update `ARCHITECTURE.md` with county details
- Create `[COUNTY]_34COLUMN_README.md` with specific notes

### Step 6: Test End-to-End

1. **Local test**: `node scrapers/[county]_stealth.js`
2. **Verify data**: Check Google Sheets
3. **GitHub Actions test**: Trigger manual workflow
4. **Monitor**: Check logs for errors

---

## Testing Guidelines

### Unit Testing (Future)

```javascript
// Example: test normalization
import { normalizeToSchema } from '../normalizers/normalize34.js';

test('normalizes Hendry data correctly', () => {
  const raw = {
    inmate_id: '46367113',
    name: 'ADAMS, TYJAE ISAIAH',
    // ...
  };
  
  const normalized = normalizeToSchema(raw, 'HENDRY');
  
  expect(normalized.Booking_Number).toBe('46367113');
  expect(normalized.Full_Name).toBe('ADAMS, TYJAE ISAIAH');
  expect(normalized.County).toBe('HENDRY');
});
```

### Integration Testing

```bash
# Test scraper without writing to production sheet
GOOGLE_SHEETS_ID=test_sheet_id node scrapers/hendry_stealth.js

# Verify test sheet has data
# (Create a separate test sheet for development)
```

### Manual Testing Checklist

- [ ] Scraper runs without errors
- [ ] Data appears in correct Google Sheets tab
- [ ] All 34 fields are populated (or empty if not available)
- [ ] No duplicate records
- [ ] Ingestion_Log shows SUCCESS
- [ ] Lead scoring works (if applicable)
- [ ] GitHub Actions workflow succeeds

---

## Debugging

### Local Debugging

```bash
# Run with verbose logging
DEBUG=* node scrapers/hendry_stealth.js

# Run in headful mode (see browser)
# (Already default in scrapers)

# Check Puppeteer screenshots
# Add to scraper:
await page.screenshot({ path: 'debug.png' });
```

### GitHub Actions Debugging

```yaml
# Add debug step to workflow
- name: Debug environment
  run: |
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    ls -la
    cat package.json
```

### Common Issues

**Issue**: "Cannot find module"
```bash
# Solution: Ensure .js extension in imports
import { func } from './file.js';  // ✅
import { func } from './file';     // ❌
```

**Issue**: "GOOGLE_SA_KEY_JSON not set"
```bash
# Solution: Check GitHub secrets
# Settings → Secrets → Actions → GOOGLE_SA_KEY_JSON
```

**Issue**: "Socket hang up"
```bash
# Solution: County website may be blocking
# - Check if stealth plugin is enabled
# - Increase delays between requests
# - Try different User-Agent
```

---

## Code Review Checklist

### Before Submitting PR

- [ ] Code follows naming conventions
- [ ] All imports have `.js` extension
- [ ] Error handling with try-catch
- [ ] Logging with emoji for clarity
- [ ] No hardcoded credentials
- [ ] `.env` file not committed
- [ ] Documentation updated
- [ ] Tested locally
- [ ] GitHub Actions workflow added
- [ ] Commit message is descriptive

### Reviewer Checklist

- [ ] Code is readable and maintainable
- [ ] No security vulnerabilities
- [ ] Follows project structure
- [ ] Tests pass (when implemented)
- [ ] Documentation is clear
- [ ] No breaking changes (or documented)

---

## Environment Variables

### Required

- `GOOGLE_SHEETS_ID` - Target Google Sheet ID
- `GOOGLE_SA_KEY_JSON` (GitHub) or `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` (Local)

### Optional

- `DEBUG` - Enable debug logging
- `HEADLESS` - Run browser in headless mode (default: false)
- `TIMEOUT` - Override default timeout (default: 30000ms)

### Example .env

```bash
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./service-account-key.json
DEBUG=puppeteer:*
HEADLESS=false
TIMEOUT=60000
```

---

## Dependencies

### Production

```json
{
  "puppeteer-extra": "^3.3.6",
  "puppeteer-extra-plugin-stealth": "^2.11.2",
  "dotenv": "^16.0.3",
  "googleapis": "^118.0.0"
}
```

### Development (Future)

```json
{
  "jest": "^29.5.0",
  "eslint": "^8.40.0",
  "prettier": "^2.8.8"
}
```

---

## Git Workflow

### Branch Naming

- `feature/add-pinellas-county` - New features
- `fix/hendry-scraper-timeout` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/normalize-function` - Code refactoring

### Commit Messages

**Format**: `<type>: <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat: Add Pinellas County scraper with stealth mode
fix: Handle timeout errors in Hendry scraper
docs: Update ARCHITECTURE.md with new county
refactor: Extract common scraper logic to shared module
```

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture
- **DEPLOYMENT.md** - Deployment procedures
- **SCRAPING_RULES.md** - Scraping best practices
- **SCHEMA.md** - 34-column data schema
- **TROUBLESHOOTING.md** - Common issues
- **SECURITY.md** - Security guidelines

---

**Last Updated**: November 26, 2025  
**Maintained By**: Shamrock Bail Bonds  
**Contact**: admin@shamrockbailbonds.biz
