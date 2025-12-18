# SignNow Integration Guide

The Shamrock Bail Suite integrates with SignNow via the `apps_script/SignNowAPI.gs` module to automate bond paperwork.

---

## 🛂 Authentication
Authentication is handled via a **Bearer Token** stored in Apps Script Project Properties as `SIGNNOW_API_TOKEN`.

---

## 📄 Supported Document Types
We maintain specific coordinate mapping for the following PDF forms:
*   **Intake Packet:** Comprehensive defendant information.
*   **Indemnity Agreement:** For indemnitors/co-signers.
*   **Promissory Note:** For payment plans.
*   **Surety Terms:** Legal disclosures.

---

## 🚚 Delivery Methods

### 1. Email (Standard)
Sends a signing invite link to the defendant or indemnitor's email address.
*   **Trigger:** Manual from Dashboard or Automated for Qualified leads.

### 2. SMS (Mobile-First)
Sends the signing link via SMS. This is the preferred method for high-speed field captures.
*   **Note:** Requires US/Canada formatted phone numbers.

### 3. Embedded (Kiosk Mode)
Generates a momentary signing link that can be opened immediately on an agent's tablet or computer.
*   **Use Case:** In-person signings at the jail or office.

---

## ⚙️ How it Works (Technical)
1.  **Pre-fill:** `pdf-lib` (JS) or Python merges Lead Data into the PDF forms.
2.  **Upload:** The pre-filled PDF is uploaded to SignNow as a new document.
3.  **Field Map:** SignNow signature and initial fields are dynamically placed based on coordinates in `SignNowAPI.gs`.
4.  **Invite:** The invite is sent via the chosen channel.
5.  **Sync:** Completed documents are automatically saved to the **"Completed Bonds"** folder in Google Drive.

---
*Maintained by: Shamrock Engineering Team*
