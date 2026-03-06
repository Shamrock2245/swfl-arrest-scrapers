# Southwest Florida Arrest Scrapers - County Status Report

Generated: November 21, 2025

## Summary

This document compares the county analysis from the planning spreadsheet with the current GitHub implementation status.

## Priority Counties (Southwest Florida)

### ✅ Collier County
- **Status**: Production Ready
- **Implementation**: Node.js + Puppeteer
- **URL**: https://www2.colliersheriff.org/arrests/
- **Records Scraped**: 6 records
- **Features**: 10-day backfill capability
- **Notes**: Fully functional, writing to Google Sheets

### ✅ Hendry County  
- **Status**: Production Ready
- **Implementation**: Node.js + Puppeteer
- **URL**: https://hendrysheriff.org/inmates
- **Records Scraped**: 5 records with full charges and bond amounts
- **Notes**: Fixed duplicate records and bond extraction issues

### ✅ Lee County
- **Status**: Production Ready (Apps Script)
- **Implementation**: Google Apps Script (JSON API)
- **URL**: https://www2.sheriffleefl.org/app/arrest/search.php
- **Notes**: Simple JSON API, existing implementation working

### 🔧 Charlotte County
- **Status**: Code exists, needs testing
- **Implementation**: Node.js + Puppeteer (scrapers/charlotte.js)
- **URL**: https://www.ccso.org/arrests
- **Plan Analysis**: JSON API available
- **Next Step**: Test scraper and verify data extraction

### 🔧 Sarasota County
- **Status**: Code exists, needs testing  
- **Implementation**: Node.js + Puppeteer (scrapers/sarasota.js)
- **URL**: https://so.sarasotasheriff.org/
- **Plan Analysis**: JSON API available
- **Next Step**: Test scraper and verify data extraction

### 🔧 DeSoto County
- **Status**: Code exists, needs testing
- **Implementation**: Node.js + Puppeteer (scrapers/desoto.js)
- **URL**: https://www.desotosheriff.org/
- **Plan Analysis**: Simple HTML table scraping
- **Next Step**: Test scraper and verify data extraction

### 🔍 Manatee County
- **Status**: Code exists, but needs API endpoint
- **Current Implementation**: Desktop website scraper (scrapers/manatee.js)
- **Desktop URL**: https://www.manateesheriff.com/arrest_inquiries/
- **Plan Analysis**: Mobile API endpoint available (better approach)
- **Next Step**: User finding mobile API endpoint via Charles Proxy
- **Recommendation**: Switch from desktop scraping to mobile API once endpoint is found

## Extended Counties (Updated March 6, 2026)

### Runner-Fixed Counties (Ready for Live Testing)

#### ✅ Hillsborough County (Tampa)
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + DrissionPage (`hillsborough_solver.py` + `run_hillsborough.py`)
- **URL**: https://core.hillsboroughcounty.org/en/residents/public-safety/sheriff-s-office/arrests-and-inmates/arrest-inquiry
- **Approach**: DrissionPage browser automation with authorized member login
- **Priority**: High (major metro area)
- **Fix Applied**: Added argparse, fixed duplicate print, fixed JSON error handling

#### ✅ Orange County (Orlando)
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + DrissionPage + pdfplumber (`orange_solver.py` + `run_orange.py`)
- **URL**: https://netapps.ocfl.net/BestJail/PDF/bookings.pdf
- **Approach**: PDF parsing (daily booking report) + web enrichment via DrissionPage
- **Priority**: High (major metro area)
- **Fix Applied**: Added argparse, fixed undefined `stdout_str` variable, fixed JSON fallback

#### ✅ Pinellas County (St. Petersburg/Clearwater)
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + Selenium (`pinellas_solver.py` + `run_pinellas.py`)
- **URL**: https://www.pinellassheriff.gov/InmateBooking
- **Approach**: Selenium with date-based search and detail page enrichment
- **Priority**: High (major metro area)
- **Fix Applied**: Added argparse, fixed duplicate print, fixed JSON error handling

#### ✅ Osceola County
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + DrissionPage (`osceola_solver.py` + `run_osceola.py`)
- **Approach**: DrissionPage automation with configurable days_back
- **Priority**: Medium
- **Fix Applied**: Fixed duplicate print, fixed JSON error handling

#### ✅ Polk County
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + DrissionPage (`polk_solver.py` + `run_polk.py`)
- **URL**: https://www.polksheriff.org/detention/jail-inquiry
- **Approach**: DrissionPage automation with HTML table scraping
- **Priority**: Medium
- **Fix Applied**: Fixed duplicate print, fixed JSON error handling

#### ✅ Seminole County
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + DrissionPage (`seminole_solver.py` + `run_seminole.py`)
- **URL**: https://seminole.northpointesuite.com/CustodyPortal
- **Approach**: Equivant/Northpointe Suite API via DrissionPage
- **Priority**: Medium
- **Fix Applied**: Fixed argparse mismatch (`max_records` → `days_back`), fixed JSON error handling

#### ✅ Manatee County
- **Status**: Runner Fixed — Ready for Live Testing
- **Implementation**: Python + DrissionPage (`manatee_solver.py` + `run_manatee.py`)
- **URL**: https://www.manateesheriff.com/arrest_inquiries/
- **Approach**: Desktop website scraping with configurable days_back and max_pages
- **Priority**: Medium-High
- **Fix Applied**: Added `datetime` import, fixed undefined `stdout_clean` variable

### Not Yet Implemented

#### Miami-Dade County
- **URL**: https://www8.miamidade.gov/Apps/MDC/InmateSearch/
- **Approach**: JSON API available
- **Priority**: High (largest county in Florida)

## Technical Architecture

### Current Stack
- **Node.js Scrapers**: Puppeteer for complex web scraping
- **Google Apps Script**: For simple JSON API scrapers
- **Data Storage**: Google Sheets (Shamrock_Arrests_Master)
- **Normalization**: Unified 35-column schema
- **Authentication**: Service account (shamrock-mcp-bot@shamrock-mcp-automation.iam.gserviceaccount.com)
- **Source Control**: GitHub (shamrock2245/swfl-arrest-scrapers)

### Unified Schema (35 columns)
All scrapers normalize data to a consistent schema including:
- booking_id, full_name, charges, bond_amounts, mugshots
- arrest_date, booking_date, release_date
- demographics (age, sex, race, height, weight)
- location data (address, city, state, zip)
- case information (case_number, court_date, attorney)

### Data Flow
1. **Scrapers** extract raw data from county websites
2. **Normalizers** map raw data to unified schema
3. **Writers** upsert to Google Sheets using composite key (booking_id|arrest_date)
4. **Qualified_Arrests** tab filters for bail-eligible arrests

## Next Steps

### Immediate Actions
1. **Manatee County**: Find mobile API endpoint via Charles Proxy
2. **Charlotte County**: Test existing scraper
3. **Sarasota County**: Test existing scraper  
4. **DeSoto County**: Test existing scraper

### Future Expansion
1. **Major Metro Counties**: Implement Miami-Dade, Hillsborough, Pinellas, Orange, Broward
2. **Automation**: Set up GitHub Actions or cron jobs for daily scraping
3. **Menu Integration**: Deploy Bail Suite menu integration (MenuIntegration.gs)
4. **Monitoring**: Add alerting for scraper failures
5. **Historical Data**: Implement backfill capability for all counties

## Resources

- **GitHub Repository**: https://github.com/shamrock2245/swfl-arrest-scrapers
- **Google Sheets**: Shamrock_Arrests_Master (ID: 121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E)
- **Account**: admin@shamrockbailbonds.biz
- **Planning Spreadsheet**: FL_WestCoast_And_Majors_Sheriff_Arrest_Scrape_Plan.xlsx
