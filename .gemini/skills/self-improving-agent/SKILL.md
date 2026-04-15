---
name: self-improving-agent
description: >
  Use this skill when debugging scrapers, fixing bugs, or completing any task in this repo.
  After completing work, the agent should reflect on what it learned and update the relevant
  skill files to capture new patterns, gotchas, and solutions for future sessions.
---

# Self-Improving Agent

You are a self-improving coding agent. After completing any significant task in this repository, you MUST reflect on what you learned and update the relevant skill files to prevent repeating mistakes and to codify new patterns.

## When to Trigger

- After fixing a bug or debugging a scraper
- After adding a new county scraper
- After resolving a CI/CD or dependency issue
- After discovering a new pattern or anti-pattern in the codebase
- When the user provides feedback about a mistake you made

## Self-Improvement Loop

### Step 1: Complete the Task
Do the work first. Fix the bug, build the feature, debug the issue.

### Step 2: Reflect
After completing the task, ask yourself:
- What was the root cause?
- Was there a pattern I missed that I should recognize next time?
- Did the codebase have a convention I violated?
- Is there a gotcha that future sessions should know about?

### Step 3: Patch the Skills
Update the appropriate `SKILL.md` file(s) in `.gemini/skills/` to capture the new knowledge. Common updates include:
- Adding a new entry to a "Known Gotchas" or "Common Bugs" section
- Adding a new pattern to a "Conventions" section
- Updating a checklist with a new verification step
- Adding a new county-specific note to the scraper builder skill

### Step 4: Commit the Skill Update
Include skill file updates in your commit alongside the code fix. Use the commit message pattern:
```
fix: [description of fix]

Also updated .gemini/skills/[skill-name] with [what was learned]
```

## Rules
1. **Never delete existing skill content** — only add to it or refine it
2. **Be specific** — "Collier uses `scrape_collier()` not `scrape_county()`" is better than "check function names"
3. **Include examples** — code snippets in skills are more useful than abstract descriptions
4. **Date your additions** — prefix new gotchas with `[YYYY-MM-DD]` so we can track recency
