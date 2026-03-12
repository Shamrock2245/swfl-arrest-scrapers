# 🔧 Modifying Shared Code (`core/`)

## When to Modify `core/`
✅ **DO modify** when:
- Adding a new utility that 3+ counties would use
- Fixing a bug that affects multiple counties
- Improving performance of a shared function

❌ **DON'T modify** when:
- Only one county needs different behavior — put it in the solver
- You're "cleaning up" code that works fine — leave it alone
- You want to rename a function — that breaks all imports

## Before You Touch `core/`
1. Run all existing tests: `pytest tests/`
2. Count how many counties import the function you're changing
3. If changing a function signature, check ALL callers first

## Safe Change Patterns

### Adding a new function
```python
# core/stealth.py
def handle_recaptcha(page):  # NEW — no existing callers
    """Handle reCAPTCHA challenges."""
    ...
```
✅ Safe — nothing depends on it yet.

### Adding an optional parameter
```python
# BEFORE
def wait_for_cloudflare(page, max_wait=20):

# AFTER — safe, default preserves old behavior
def wait_for_cloudflare(page, max_wait=20, retry_on_fail=False):
```
✅ Safe — existing callers are unaffected.

### Changing behavior of existing function
```python
# BEFORE — returns True/False
def wait_for_cloudflare(page):
    return True

# AFTER — now returns detailed result
def wait_for_cloudflare(page):
    return {"cleared": True, "wait_time": 5}
```
❌ DANGEROUS — every caller expects True/False.

## Required Steps After Modifying `core/`
1. Run `pytest tests/unit/` — all unit tests must pass
2. Run `pytest tests/parsers/` — all parser tests must pass
3. Dry-run at least 2 active counties: `python scripts/run_county.py charlotte --dry-run`
4. Update module docstrings if signatures changed
5. Document the change in your commit message

## Function Deprecation Pattern
```python
import warnings

def old_function():
    warnings.warn("old_function is deprecated, use new_function", DeprecationWarning)
    return new_function()
```
