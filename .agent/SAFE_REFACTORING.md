# 🛡️ Safe Refactoring Rules

## Core Principle
> **If it works, and nobody asked you to change it, leave it alone.**

## When Refactoring Is SAFE
✅ Renaming a local variable inside a single function
✅ Adding a docstring to an undocumented function
✅ Extracting a helper function WITHIN the same file
✅ Adding type hints to existing parameters
✅ Removing dead code (verified unused with `grep`)
✅ Fixing a typo in comments

## When Refactoring Is DANGEROUS
❌ Renaming a function or method that's imported elsewhere
❌ Changing return types of existing functions
❌ Moving a file to a different directory
❌ Changing function parameter names (breaks keyword callers)
❌ "Simplifying" error handling (may hide real errors)
❌ Replacing a working library with a "better" one
❌ Merging two functions that "do the same thing" without verifying

## Before Any Refactor
1. `grep -r "function_name" .` — find all callers
2. `pytest tests/` — establish baseline
3. Make the change
4. `pytest tests/` — verify nothing broke
5. `python scripts/run_county.py charlotte --dry-run` — integration check

## County-Specific Code
- **Never** refactor a county solver that's running in production unless asked
- **Never** merge two county solvers "because they look similar"
- **Always** preserve county-specific workarounds (they're there for a reason)
- If you find duplicated logic across 3+ counties, extract to `core/` — but keep the original code working until all counties are migrated

## The "3-County Rule"
Before adding anything to `core/`, ask: **Would at least 3 counties use this?**
- Yes → put it in `core/`
- No → keep it in the county's solver
