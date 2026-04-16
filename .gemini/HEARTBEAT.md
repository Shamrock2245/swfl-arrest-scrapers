# 💓 HEARTBEAT — System Health Pulse

> **Quick-glance health check. Updated each session or on significant state changes.**

---

## Current Pulse

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Active Counties** | 24 | 67 | 🟡 36% |
| **Success Rate (7d)** | ~100% | ≥95% | 🟢 On Target |
| **Data Freshness** | ≤2h per county | ≤2h | 🟢 On Target |
| **Dedup Accuracy** | 100% | 100% | 🟢 Perfect |
| **GitHub Actions** | Operational | Operational | 🟢 Healthy |
| **Google Sheets API** | Operational | Operational | 🟢 Healthy |
| **MongoDB Atlas** | Operational | Operational | 🟢 Healthy |
| **Slack Webhooks** | Operational | Operational | 🟢 Healthy |

---

## County Health Matrix

### 🟢 Healthy (No Issues)
Alachua, Brevard, Charlotte, Collier, DeSoto, Duval, Escambia, Hendry, Highlands, Hillsborough, Indian River, Lake, Lee, Manatee, Martin, Orange, Osceola, Palm Beach, Pasco, Pinellas, Polk, Sarasota, Seminole, Volusia

### 🟡 Degraded (Intermittent Issues)
(none)

### 🔴 Down (Failing)
(none)

### ⏸️ Paused (Intentionally Stopped)
(none)

---

## SLO Dashboard

| SLO | Target | Current | Trend |
|-----|--------|---------|-------|
| Scrape success rate | ≥95% per county/week | ~100% | ↗️ Improving |
| Data freshness | ≤2 hours | ≤2 hours | → Stable |
| Hot lead latency | ≤5 min from booking to Slack | ~2 min | → Stable |
| Error recovery | <3 consecutive failures | 0 streak | → Stable |
| Dedup accuracy | 100% | 100% | → Stable |

---

## Last 5 Incidents

| Date | County | Issue | Resolution | Duration |
|------|--------|-------|------------|----------|
| (No recent incidents logged) | — | — | — | — |

---

## Resource Usage

| Resource | Usage | Limit | Status |
|----------|-------|-------|--------|
| GitHub Actions (minutes/month) | ~2,000 | 2,000 (free) | 🟡 Near limit |
| Google Sheets API (requests/day) | ~5,000 | 500,000 | 🟢 Low |
| Slack Webhooks (messages/day) | ~200 | 10,000 | 🟢 Low |
| MongoDB Atlas (storage) | ~50MB | 512MB (free tier) | 🟢 Low |

---

## Agent Action Items

When reviewing heartbeat at session start:
1. Check if any county has moved to 🟡 or 🔴 status
2. Review `Ingestion_Log` for recent `E_*` error codes
3. Check GitHub Actions for failed workflows in the last 24h
4. Update this file if any metrics have changed
