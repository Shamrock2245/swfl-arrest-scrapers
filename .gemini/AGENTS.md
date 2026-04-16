# 🤖 AGENTS — The Digital Workforce

## Overview
Shamrock operates **9 AI agents** as a coordinated digital team. This repo (`swfl-arrest-scrapers`) is primarily operated by **The Clerk** and the **Scraper Agent**, but all agents consume or react to scraper output.

---

## Agent Roster

### The Clerk — Booking Scraper & OCR
| Attribute | Value |
|-----------|-------|
| **Role** | Scrape, parse, normalize, and deliver arrest records |
| **Channel** | Automated (GitHub Actions, Docker, cron) |
| **Code** | `counties/*/solver.py`, `core/*`, `config/*` |
| **Inputs** | 67 Florida county jail websites |
| **Outputs** | Google Sheets (34-col), MongoDB Atlas, Slack alerts |
| **GAS Files** | `AI_BookingParser.js`, `ArrestScraper*.js` |
| **Relevance** | ⭐⭐⭐ THIS REPO — primary operator |

### The Concierge — 24/7 Client Support & Intake
| Attribute | Value |
|-----------|-------|
| **Role** | First contact with potential clients. Answers questions, starts intake. |
| **Channel** | Web Chat, SMS, Telegram |
| **Code** | `AIConcierge.js`, `ai-service.jsw` |
| **Consumes from scrapers** | Qualified leads (Score ≥70) trigger proactive outreach |
| **Relevance** | ⭐⭐ Downstream consumer of scraper data |

### Shannon — After-Hours Voice Intake
| Attribute | Value |
|-----------|-------|
| **Role** | 24/7 phone intake via ElevenLabs Conversational AI |
| **Channel** | Phone calls |
| **Code** | `ElevenLabs_AfterHoursAgent.js`, `ElevenLabs_WebhookHandler.js` |
| **Consumes from scrapers** | Arrest data for caller verification |
| **Relevance** | ⭐ Indirect consumer |

### The Analyst — Risk Assessment & Underwriting
| Attribute | Value |
|-----------|-------|
| **Role** | Evaluate flight risk, score leads, recommend bond terms |
| **Channel** | Automated (triggered by new intake) |
| **Code** | `AI_FlightRisk.js`, `LeadScoringSystem.js` |
| **Consumes from scrapers** | Arrest records, charge details, booking history |
| **Relevance** | ⭐⭐ Direct consumer of scraper data |

### The Investigator — Deep Background Checks
| Attribute | Value |
|-----------|-------|
| **Role** | Deep dives on high-value or high-risk cases |
| **Channel** | Automated (triggered by Analyst flags) |
| **Code** | `AI_Investigator.js` |
| **Consumes from scrapers** | Full arrest records, prior bookings |
| **Relevance** | ⭐ Occasional consumer |

### The Closer — Lead Recovery & Drip Campaigns
| Attribute | Value |
|-----------|-------|
| **Role** | Follow up on abandoned intakes via SMS/WhatsApp sequences |
| **Channel** | SMS, WhatsApp (via Twilio) |
| **Code** | `TheCloser.js` |
| **Consumes from scrapers** | Warm/hot leads that haven't converted |
| **Relevance** | ⭐⭐ Downstream consumer |

### Manus Brain — Telegram AI Handler
| Attribute | Value |
|-----------|-------|
| **Role** | Handle Telegram bot conversations, inline queries, callbacks |
| **Channel** | Telegram (`@ShamrockBail_bot`) |
| **Code** | `Manus_Brain.js` |
| **Consumes from scrapers** | Arrest data for defendant lookup |
| **Relevance** | ⭐ Indirect consumer |

### The Watchdog — System Health Monitor
| Attribute | Value |
|-----------|-------|
| **Role** | Monitor all endpoints, detect outages, alert on failures |
| **Channel** | Node-RED (5-min health checks) |
| **Code** | Node-RED flows |
| **Monitors** | Scraper health (via Ingestion_Log), GAS endpoints, Sheets API |
| **Relevance** | ⭐⭐ Monitors scraper health |

### Bounty Hunter — High-Value Lead Surfacing
| Attribute | Value |
|-----------|-------|
| **Role** | Surface unposted bonds >$2,500 for priority action |
| **Channel** | Node-RED Dashboard (Bounty Board) |
| **Code** | Node-RED flows |
| **Consumes from scrapers** | Qualified_Arrests tab, filtered by bond amount |
| **Relevance** | ⭐⭐ Direct consumer |

---

## Agent Data Flow

```
Scrapers (The Clerk)
    │
    ├──→ Google Sheets ──→ GAS Lead Scoring ──→ The Analyst
    │                                          ──→ The Investigator
    │
    ├──→ Slack #leads  ──→ The Concierge (outreach)
    │                   ──→ The Closer (drip campaigns)
    │
    ├──→ Slack #new-arrests-{county} ──→ Human staff
    │
    ├──→ MongoDB Atlas ──→ Bounty Hunter (Node-RED)
    │
    └──→ Ingestion_Log ──→ The Watchdog (health monitoring)
```

## Who Can Modify This Repo?

| Agent | Read | Write | Modify Core |
|-------|------|-------|-------------|
| Scraper Agent (me) | ✅ | ✅ | ✅ (with testing) |
| The Clerk (automated) | ✅ | ✅ (data only) | ❌ |
| All other agents | ✅ | ❌ | ❌ |
| Human engineers | ✅ | ✅ | ✅ |
