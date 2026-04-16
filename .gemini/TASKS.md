# 📋 TASKS — Active Task Queue

> **What needs to be done, in priority order. Updated each session.**

---

## 🔴 High Priority

- `[ ]` **Tier 1 County Expansion**: Miami-Dade, Broward, St. Lucie
  - Highest population counties not yet scraped
  - Complex targets (CAPTCHA, SPAs) — expect 3-8 hours each
  - See `SOURCES.md` → Wave 3 for details

- `[ ]` **SmartCOP Wave** (13 counties, ~30 min each)
  - Bradford, Dixie, Escambia (done), Gadsden, Gilchrist, Glades, Hamilton, Levy, Putnam, Santa Rosa, Sumter, Suwannee, Taylor
  - Clone DeSoto pattern → change URL → test → deploy
  - See `SOURCES.md` → Wave 1 for details

---

## 🟡 Medium Priority

- `[ ]` **Update ROADMAP.md** with current 24-county status (was showing 14)
- `[ ]` **MongoDB primary migration** — move from Sheets-primary to MongoDB-primary
- `[ ]` **10DLC reapplication** — unblock SMS/WhatsApp outreach
- `[ ]` **Sentry Cron integration** — per-scraper health monitoring
- `[ ]` **Self-hosted runner fleet** — reduce dependency on GitHub shared runners

---

## 🟢 Low Priority

- `[ ]` **ML-based lead scoring** — upgrade from rule-based to ML model
- `[ ]` **Court date prediction** — predict court dates from charge patterns
- `[ ]` **Historical analytics dashboard** — visualize arrest trends over time
- `[ ]` **PDF scraper infrastructure** — Calhoun, Hardee (Wave 4)

---

## ✅ Recently Completed

- `[x]` Documentation overhaul — 24-file agent brain (2026-04-16)
- `[x]` Consolidated .agent/ → .gemini/skills/ (2026-04-15)
- `[x]` Added 10 new counties: Alachua, Brevard, Duval, Escambia, Highlands (fix), Indian River (fix), Collier (fix), Osceola (fix), Pasco, Volusia (2026-04-14)
- `[x]` JSON writer + runner.py standardization (2026-04-14)
- `[x]` 24-county network stabilization to 100% success rate (2026-04-14)
