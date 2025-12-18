# SWFL Bail Suite - Project Summary

## 🎯 What We Built

A production-grade, multi-county arrest ingestion and lead management system for **Shamrock Bail Bonds**.

### Core Capabilities:
*   **Dual-Stack Scraping:** High-stealth ingestion from 8+ counties (Orange, Hillsborough, Manatee, Sarasota, Charlotte, Hendry, Palm Beach, DeSoto, Lee, Collier).
*   **Unified Schema:** Normalizes disparate county data into a strict 34-column "Universal Record."
*   **Lead Scoring:** Algorithmic qualification (HOT leads ≥ 70) based on bond amount and charge severity.
*   **Automated CRM:** Syncs directly to a Master Google Sheet with real-time Dashboard updates.
*   **Legal Integration:** Fully integrated SignNow workflow for Email, SMS, and Embedded signing of bond paperwork.

---

## 📦 System Components

### 1. Scraper Engines
*   **Primary (Python):** Located in `/python_scrapers`, uses `DrissionPage` for advanced anti-detection.
*   **Legacy (Node.js):** Located in `/scrapers`, uses Puppeteer Stealth for simpler targets.
*   **Native (Apps Script):** Custom internal scrapers for Lee and Collier.

### 2. Job Orchestration
*   **`jobs/runAll.js`:** Coordinates staggered execution of all county scrapers to prevent rate-limiting.
*   **`jobs/updateBondPaid.js`:** Monitors and updates the payment status of previous arrests.

### 3. Google Apps Script Dashboard
*   **Location:** `/apps_script`
*   **Features:** Real-time data visualization, manual lead qualification, and SignNow packet generation.

---

## 🛠️ The "34-Column" Schema
Every record in the system follows the same field structure:
`Booking_Number`, `Full_Name`, `DOB`, `Arrest_Date`, `Charges`, `Bond_Amount`, `Lead_Score`, `Lead_Status`, etc.

---

## 🚀 Key Integrations

### **Slack Notifications**
*   Success/Failure summaries for every scraper run.
*   Real-time "Hot Lead" alerts when a score ≥ 70 is detected.

### **SignNow**
*   Automated generation of Intake, Indemnity, and Promissory Note packets.
*   Multi-channel delivery: Email, SMS, or In-Person (Embedded).

---

## ✅ Success Metrics
*   **Deduplication:** 100% accuracy via composite keys (`County` + `Booking_Number`).
*   **Sync:** Real-time synchronization between scrapers and the [Master Database](https://docs.google.com/spreadsheets/d/121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E/edit).
*   **Efficiency:** Automated ingestion saves ~4 hours of manual data entry per day.

---
*Maintained by: Shamrock Engineering Team*
