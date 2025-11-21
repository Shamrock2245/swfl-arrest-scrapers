# Charles Proxy Guide - Finding Manatee County Mobile API

## Overview

You're trying to find the mobile API endpoint for Manatee County Sheriff's Office arrest records. This guide will help you filter Charles Proxy to find the actual API calls instead of analytics beacons.

## Current Situation

- **Desktop Website**: https://www.manateesheriff.com/arrest_inquiries/
- **Goal**: Find mobile API endpoint (faster, more reliable than desktop scraping)
- **Problem**: Charles is showing Google Analytics beacons instead of arrest data API

## Step-by-Step Instructions

### 1. Set Up Filters in Charles

**Filter by Domain:**
```
Structure View → Right-click → Focus
Filter for: manateesheriff.com OR manatee
```

This will hide all the Google Analytics, ads, and tracking requests.

### 2. Look for These API Patterns

**Common API URL patterns:**
- `/api/arrests`
- `/api/inmates`
- `/api/search`
- `/data/arrests`
- `/services/arrests`
- `/mobile/api/`
- Any URL with `.json` or `.php` that returns JSON

**Common file patterns:**
- `search.php`
- `arrests.json`
- `inmates.json`
- `data.php`

### 3. Filter by Content Type

In Charles, look for requests with:
- **Content-Type**: `application/json`
- **Response Type**: JSON (you'll see structured data like `{"arrests": [...]}`)

**To filter:**
1. Go to **Sequence** view (not Structure)
2. Click on the **Type** column to sort
3. Look for `JSON` or `XHR` types

### 4. Ignore These (Not What We Want)

❌ **Google Analytics**: `google-analytics.com`, `gvt2.com`, `doubleclick.net`
❌ **Tag Managers**: `googletagmanager.com`
❌ **CDN Assets**: `.js`, `.css`, `.png`, `.jpg` files
❌ **Tracking Pixels**: `/beacon`, `/track`, `/pixel`
❌ **Social Media**: `facebook.com`, `twitter.com`

### 5. What to Look For

✅ **POST or GET requests** to manateesheriff.com
✅ **JSON responses** with arrest/inmate data
✅ **Query parameters** like `?date=`, `?search=`, `?page=`
✅ **Response size** > 1KB (actual data, not just status codes)

### 6. Test the Mobile Site

If you're on desktop, try:

1. **Open Chrome DevTools** (F12)
2. **Toggle Device Toolbar** (Ctrl+Shift+M or Cmd+Shift+M)
3. **Select a mobile device** (iPhone, Android)
4. **Navigate to**: https://www.manateesheriff.com/arrest_inquiries/
5. **Watch Charles** for new requests

Mobile sites often use different (simpler) APIs than desktop sites.

### 7. Check Network Tab in Browser

Sometimes it's easier to find APIs in the browser first:

1. **Open Chrome DevTools** → **Network tab**
2. **Filter by XHR/Fetch** (click the XHR button)
3. **Navigate to arrest search page**
4. **Perform a search**
5. **Look for JSON responses** in the Network tab
6. **Right-click** → **Copy as cURL** or **Copy URL**

### 8. Common Manatee County API Endpoints to Try

Based on similar sheriff's office sites, try these URLs directly:

```
https://www.manateesheriff.com/api/arrests
https://www.manateesheriff.com/api/inmates
https://www.manateesheriff.com/arrest_inquiries/api/search
https://www.manateesheriff.com/arrest_inquiries/data.php
https://www.manateesheriff.com/arrest_inquiries/search.php?format=json
```

Test these in your browser or Postman to see if they return JSON data.

## What to Send Me

Once you find the API endpoint, please provide:

1. **Full URL** of the API endpoint
2. **HTTP Method** (GET or POST)
3. **Request Headers** (if any special headers are required)
4. **Request Parameters** (query string or POST body)
5. **Sample Response** (copy/paste the JSON response)

Example:
```
URL: https://www.manateesheriff.com/api/arrests?days=1
Method: GET
Headers: None required
Response: {"arrests": [{"booking_id": "12345", "name": "John Doe", ...}]}
```

## Alternative Approach

If you can't find the mobile API, we can:

1. **Use the existing desktop scraper** (already coded in `scrapers/manatee.js`)
2. **Test it** to see if it works
3. **Optimize it** if needed

The desktop scraper uses Puppeteer with stealth mode, so it should work even if there's no public API.

## Next Steps

1. **Apply filters** in Charles Proxy
2. **Navigate** to the arrest search on mobile
3. **Find the API endpoint**
4. **Share the details** with me

Or, if you prefer, we can just test the existing desktop scraper and see if it works well enough.
