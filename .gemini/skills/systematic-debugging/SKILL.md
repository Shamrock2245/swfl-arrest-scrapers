---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
source: obra/superpowers (skills.sh #84, 59.6K installs)
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Scraper failures or empty results
- GitHub Actions workflow errors
- Rate limiting / IP blocks
- Website structure changes
- Docker build failures
- Data quality issues (missing fields, bad encoding)
- Google Sheets API errors

## The Four Phases

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - Read stack traces completely
   - Note line numbers, file paths, error codes
   - Check GitHub Actions logs (not just local output)

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - Run the solver locally: `python counties/{county}/solver.py --days-back 3`
   - Does it fail the same way locally vs CI?

3. **Check Recent Changes**
   - `git log --oneline -10` — what changed recently?
   - Did the target website change? (check in browser)
   - New dependencies, config changes?

4. **Gather Evidence in Multi-Component Systems**
   - Our pipeline: Website → Solver → Runner → Sheets/Slack
   - Add diagnostic output at each boundary
   - Which layer fails? (scraping? parsing? writing?)

5. **Trace Data Flow**
   - Where does the bad value originate?
   - Is it a scraping issue or a parsing issue?
   - Keep tracing up until you find the source

### Phase 2: Pattern Analysis

1. **Find Working Examples**
   - Which counties work? Compare their solver code
   - Same website platform? (Revize, JailTracker, custom)

2. **Compare Against References**
   - Does the working solver use the same approach?
   - Different anti-bot strategy needed?

3. **Identify Differences**
   - HTML structure changed?
   - New CAPTCHA or Cloudflare protection?
   - Rate limiting kicked in?

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis**
   - "I think X is the root cause because Y"
   - Be specific, not vague

2. **Test Minimally**
   - Smallest possible change
   - One variable at a time

3. **Verify Before Continuing**
   - Did it work? → Phase 4
   - Didn't work? → Form NEW hypothesis
   - DON'T stack fixes

### Phase 4: Implementation

1. **Create Test Case**
   - Run solver locally with small date range
   - Verify it produces valid JSON output

2. **Implement Single Fix**
   - ONE change at a time
   - No "while I'm here" improvements

3. **Verify Fix**
   - Local run produces records?
   - Push and check GitHub Actions?
   - Records appear in Google Sheets?

4. **If 3+ Fixes Failed: Question Architecture**
   - Is requests+BS4 the wrong tool? Need DrissionPage?
   - Is the website fundamentally anti-scraping?
   - Should we try a different data source?

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix — just change the selector"
- "Just try a different User-Agent"
- "Add a sleep and it'll work"
- "The website is probably just down"

**ALL of these mean: STOP. Return to Phase 1.**

## Scraper-Specific Debugging Checklist

| Symptom | Common Root Cause | Investigation |
|---------|------------------|---------------|
| Empty results | Website changed HTML structure | View page source, compare to solver selectors |
| 403/503 errors | Anti-bot detection | Check with curl, try DrissionPage |
| Timeout errors | Page load too slow / Cloudflare | Add wait_for_cloudflare(), increase timeout |
| Partial data | Pagination broken | Check next-page logic, verify page count |
| Wrong data | Selector mismatch | Inspect elements, verify CSS selectors |
| Import errors | Missing dependency in Docker | Check Dockerfile, requirements.txt |
| Sheets write fail | Auth or schema mismatch | Verify service account, check column count |
