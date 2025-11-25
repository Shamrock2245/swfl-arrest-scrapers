# SCRAPERS_OVERVIEW.md

## Southwest Florida Arrest Scraper System — Overview

This document provides a high‑level technical overview of the multi‑county arrest‑scraping system. It defines the architecture, workflow, module responsibilities, and county‑specific considerations required for stable, scalable, API‑first extraction.

---

## 1. System Architecture

### Core Principles

* **API‑First**: Always pull data from the county’s underlying XHR/AJAX endpoint when possible.
* **Asynchronous Scheduled Execution**: Scrapers are designed to run on tight intervals without blocking.
* **32‑Column Universal Schema**: All counties map their output to the normalized schema.
* **Idempotent Upserts**: Each run deduplicates by Booking_Number.
* **Modular Files**: One Python scraper module per county.

### Major Components

1. **County Scraper Modules** (`*_county.py`)
2. **Scheduler / Throttling Layer**
3. **Mapping Layer → 32‑Column Schema**
4. **Upload Layer → Google Sheets**
5. **Future: Bond Qualification Engine**

---

## 2. Scraper Execution Cycle

### High‑Volume Counties (Manatee, Sarasota)

* Run every **7–12 minutes**.
* Lightweight requests → fast API pull → transform → upload.

### Low‑Volume Counties (Charlotte, DeSoto)

* Run every **60 minutes**.
* Same flow, but tolerant of Cloudflare and HTML‑only sites.

### Lifecycle

1. Call county API (or Cloudflare‑authenticated endpoint).
2. Parse and normalize fields.
3. Map to the universal schema.
4. Merge into Google Sheet (update or insert).
5. Log counts, failures, and timestamps.

---

## 3. Universal 32‑Column Schema

All outputs must conform exactly to this structure:

### Core Minimum (25 fields)

* Scrape_Timestamp
* County
* Booking_Number
* Person_ID
* Full_Name
* First_Name
* Middle_Name
* Last_Name
* DOB
* Booking_Date
* Booking_Time
* Status
* Facility
* Race
* Sex
* Height
* Weight
* Address
* City
* State
* ZIP
* Mugshot_URL
* Charges[]
* Bond_Amount
* Detail_URL

### Additional Required (7 fields)

* Bond_Paid
* Bond_Type
* Court_Type
* Case_Number
* Court_Date
* Court_Time
* Court_Location

---

## 4. County Profiles

### Sarasota County

* **Goal**: Identify the AJAX endpoint via Charles Proxy.
* **Implementation**: Direct `requests` call; no Playwright.
* **Output**: JSON → normalized → sheet.

### Charlotte County

* **Challenge**: Cloudflare anti‑bot.
* **Solution**: After solving Cloudflare manually, capture cookies + endpoint via Charles Proxy.
* **Implementation**: `requests` with cookie header. If Cloudflare rotates, refresh cookies.

### Manatee County

* **Approach**: Use the Manatee Sheriff Arrest Inquiry internal endpoint.
* **Implementation**: Fetch JSON via Charles‑extracted URL.

### DeSoto County

* **Approach**: Attempt Charles Proxy to find internal source.
* **Fallback**: HTML parsing with BeautifulSoup.
* **Requirement**: Must still populate the full schema.

---

## 5. File Structure

```
scrapers/
  manatee_county.py
  sarasota_county.py
  charlotte_county.py
  desoto_county.py

shared/
  mapping.py
  transform.py
  google_sheets.py
  scheduler.py
```

---

## 6. Scheduler & Throttling

The scheduler assigns iteration windows:

* **Every 7–12 minutes** → Manatee, Sarasota.
* **Every 60 minutes** → Charlotte, DeSoto.

Throttling rules:

* Backoff on non‑200 responses.
* For Cloudflare sites, use retry-with-cookie-rotation support.
* On HTML scrapes, apply randomized sleep (0.75–1.5s) between detail lookups.

---

## 7. Future Expansion: Bond Qualification

Scrapers must preserve:

* Full charge list
* Bond type and amount
* Status
* Court dates

This enables downstream automated scoring.

A separate module will:

* Compute qualifying_score
* Rank and surface high‑value candidates
* Push notifications to Slack

---

## 8. Logging & Observability

Each run logs:

* Run timestamp
* Number of new/updated records
* Duration
* Errors with traceback

All logs funnel into a structured handler for monitoring.

---

## 9. Deployment Notes

* Scrapers are designed for continuous operation via scheduled runners.
* Cookie‑based bypass (Charlotte) requires renewing cookies periodically.
* All modules are safe to re‑run indefinitely.

---

## 10. Summary

This overview defines the operating framework for the SWFL arrest‑scraper system. All subsequent `.md` documents will dive into per‑county specifications, authentication handling, endpoint discovery, and schema mapping.
