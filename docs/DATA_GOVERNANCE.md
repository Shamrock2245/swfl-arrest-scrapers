# Data Governance & Retention

## 📂 Master Database
All production data is stored in the **Shamrock Master Sheet**:
`121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E`

---

## 🕒 Data Retention Policies

### 1. Scrape Fixtures (`fixtures/`)
*   **Retention:** 30 days.
*   **Purpose:** Debugging and selector verification.
*   **Policy:** Automatically pruned by the CI maintenance job.

### 2. Google Sheets Data
*   **Retention:** Indefinite.
*   **Policy:** Rows are appended or upserted. No data is ever deleted from the primary county tabs by automated scripts.

### 3. Log Data (`Ingestion_Log`)
*   **Retention:** 90 days.
*   **Policy:** Older logs are archived to the `Log_Archive` tab to maintain sheet performance.

---

## 🔒 Security & Access

1.  **Service Account:** Access is restricted to `bail-suite-sa@shamrock-bail-suite.iam.gserviceaccount.com`.
2.  **Permissions:** The service account is granted **Editor** permissions only on specific authorized spreadsheets.
3.  **PII:** We only ingest and store data that is explicitly marked as "Public Record" by the source county.

---

## ⚖️ Compliance
*   **Deduplication:** The `Booking_Number` + `County` composite key is the authoritative unique identifier.
*   **Audit Trail:** Every write operation includes a `Scrape_Timestamp` (Line 1 of the schema).

---
*Maintained by: Shamrock Engineering Team*
