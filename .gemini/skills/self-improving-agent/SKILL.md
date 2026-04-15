---
name: self-improving-agent
description: >
  Automatically triggered after completing ANY task in this repo — fixing a bug, adding a county,
  debugging a failure, or modifying infrastructure. Implements a multi-memory learning loop that
  extracts patterns from experiences and patches skill files to prevent repeating mistakes.
  Based on the charon-fan/agent-playbook self-improving-agent pattern.
---

# Self-Improving Agent

> "An AI agent that learns from every interaction, accumulating patterns and insights
> to continuously improve its own capabilities."

## Overview

This implements a complete self-improvement feedback loop with:
- **Semantic Memory**: Patterns/rules stored in skill SKILL.md files (Known Gotchas, Best Practices)
- **Episodic Memory**: Specific fix experiences stored as dated entries in skills
- **Self-Correction**: Detects and fixes inaccurate guidance via correction markers

## When This Triggers

This skill activates automatically after:
- Fixing a bug or debugging a scraper
- Adding a new county scraper
- Resolving a CI/CD or dependency issue
- Discovering a new website anti-bot pattern
- User provides corrective feedback

## The Learning Loop

### Phase 1: Complete the Task
Do the work first. Fix the bug, build the scraper, debug the workflow.

### Phase 2: Extract Experience
After task completion, capture structured experience:

```yaml
skill_used: county-scraper-builder  # or scraper-debugger
task: "Fix Collier County function name mismatch"
outcome: success
root_cause: "Solver exported scrape_county() but runner expects scrape_collier()"
lesson: "Function name MUST match the county directory name"
confidence: 0.99  # Very high — deterministic code bug
```

### Phase 3: Abstract to Pattern
Convert to reusable knowledge using these rules:

| Condition | Pattern Level | Action |
|-----------|--------------|--------|
| Error repeats 2+ times | 🔴 Critical | Add to **Known Gotchas** section |
| Solution was effective | 🟢 Best Practice | Add to **Best Practices** section |
| Website changed structure | 🟡 Site-Specific | Add note under county entry |
| Anti-bot pattern discovered | 🔵 Infrastructure | Add to stack selection guide |

### Phase 4: Patch the Skills
Update the appropriate `SKILL.md` file(s) in `.gemini/skills/`:

```markdown
<!-- Evolution: 2026-04-14 | source: collier-function-name-fix | skill: county-scraper-builder -->
- `[2026-04-14]` **Collier**: Used `scrape_county()` instead of `scrape_collier()` — runner couldn't find it
```

Correction markers (when fixing wrong guidance):
```markdown
<!-- Correction: 2026-04-14 | was: "Use requests for all sites" | reason: SPA sites return empty HTML -->
**Corrected**: Indian River detail pages are JS-rendered SPAs — use listing page extraction
or DrissionPage for browser-based scraping instead of requests+BS4.
```

### Phase 5: Commit with Skill Updates
Include skill file updates alongside code fixes:
```
fix: patch Collier function name mismatch

Also updated .gemini/skills/county-scraper-builder with new gotcha:
function name must match directory name exactly.
```

## Rules

### DO ✅
- Learn from EVERY skill interaction
- Extract patterns at the right abstraction level
- Update multiple related skills when a lesson applies broadly
- Date-prefix all new entries (`[YYYY-MM-DD]`)
- Include code snippets — they're more useful than prose
- Track which county a lesson came from

### DON'T ❌
- Over-generalize from a single experience
- Delete existing skill content — only add or refine
- Make changes without understanding the full context
- Create contradictory guidance (check existing content first)
- Skip self-improvement just because the fix was "obvious"

## Memory Locations

| Memory Type | Location | Purpose |
|-------------|----------|---------|
| Semantic (Patterns) | `.gemini/skills/*/SKILL.md` | Reusable rules, checklists, gotchas |
| Episodic (Experiences) | Dated entries in Known Gotchas sections | What happened, when, and why |
| Working (Current) | This conversation's context | Active session state |

## Pattern Categories for This Repo

1. **solver_conventions** — Function naming, return types, parameter signatures
2. **website_patterns** — Anti-bot strategies, site stack detection, HTML structure changes
3. **pipeline_patterns** — Runner behavior, Sheets writing, Slack notifications
4. **ci_cd_patterns** — GitHub Actions, Docker, dependency management
5. **expansion_patterns** — New county onboarding, config setup, workflow creation
6. **data_quality** — Dedup logic, field normalization, record validation
