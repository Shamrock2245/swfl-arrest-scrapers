#!/bin/bash
# ============================================================
# CLEANUP SCRIPT — Run after verifying all scrapers work
# ============================================================
# This script removes old/stale directories that have been
# superseded by the new counties/ and core/ structure.
#
# Usage: bash scripts/cleanup_old_dirs.sh
# ============================================================

set +e  # Continue past errors (some dirs may be sandbox-locked)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "🧹 SWFL Arrest Scrapers — Cleanup Script"
echo "=========================================="
echo ""

# --- 1. Stale Git directories ---
echo "1️⃣  Removing stale .git directories..."
rm -rf ".git 2" ".git 3" 2>/dev/null || echo "   ⚠️  .git 2/3 locked — remove manually: rm -rf '.git 2' '.git 3'"
echo "   ✅ Attempted .git 2, .git 3"

# --- 2. Wrong-repo directories ---
echo ""
echo "2️⃣  Removing directories that belong in other repos..."
rm -rf apps_script
rm -rf wix_integration
echo "   ✅ apps_script/ (belongs in shamrock-bail-portal-site)"
echo "   ✅ wix_integration/ (belongs in shamrock-bail-portal-site)"

# --- 3. Temp browser profile directories ---
echo ""
echo "3️⃣  Removing temp browser profiles..."
rm -rf tmp_userdata_mac_*
echo "   ✅ tmp_userdata_mac_*"

# --- 4. Debug artifacts ---
echo ""
echo "4️⃣  Removing debug files..."
rm -f debug_charlotte.html debug_charlotte.png
rm -f browser_server.py test_collier.py
echo "   ✅ debug files"

# --- 5. Old code now in core/ ---
echo ""
echo "5️⃣  Removing old code dirs (consolidated into core/)..."
rm -rf normalizers    # → core/normalizer.py
rm -rf shared         # → core/browser.py
rm -rf writers        # → core/writers/
echo "   ✅ normalizers/, shared/, writers/"

# --- 6. Old python_scrapers (solvers now in counties/) ---
echo ""
echo "6️⃣  Removing old python_scrapers..."
# Keep models/ and scoring/ (still imported by runners)
# Remove everything else
rm -rf python_scrapers/venv python_scrapers/venv2 python_scrapers/venv_hendry
rm -rf python_scrapers/.patchright-browsers python_scrapers/.playwright-browsers
rm -f python_scrapers/debug_* python_scrapers/test_* python_scrapers/extracted_strings.txt
rm -f python_scrapers/main_formatted.js python_scrapers/hendry_fetch.py
rm -f python_scrapers/run_*.py python_scrapers/requirements.txt
rm -f python_scrapers/LEAD_SCORING_SPEC.md python_scrapers/README_PYTHON_SCRAPERS.md
echo "   ✅ Cleaned python_scrapers/ (kept models/ and scoring/)"

# --- 7. Old root-level Node scripts (now in counties/) ---
echo ""
echo "7️⃣  Cleaning up root-level files..."
rm -f run_all_counties.js setup.sh PUSH_INSTRUCTIONS.txt
echo "   ✅ Root scripts"

# --- 8. Duplicate root markdown (consolidated into docs/) ---
echo ""
echo "8️⃣  Removing duplicate root-level markdown..."
rm -f APPS_SCRIPT_API.md           # GAS stuff, wrong repo
rm -f ARCHITECTURE.md             # → docs/ARCHITECTURE.md
rm -f COUNTY_SCRAPER_STATUS.md    # → docs/COUNTY_STATUS.md (merged)
rm -f COUNTY_STATUS.md            # → docs/COUNTY_STATUS.md
rm -f CREDENTIALS_GUIDE.md        # → docs/DEPLOYMENT.md (merged)
rm -f DEPLOYMENT.md               # → docs/DEPLOYMENT.md
rm -f DEPLOYMENT_GUIDE.md         # → docs/DEPLOYMENT.md (merged)
rm -f DEVELOPMENT.md              # → docs/CONTRIBUTING.md (merged)
rm -f LOCAL_SCRAPER_GUIDE.md      # → docs/QUICKSTART.md (merged)
rm -f PRODUCTION_READY_GUIDE.md   # → docs/DEPLOYMENT.md (merged)
rm -f QUICK_START.md              # → docs/QUICKSTART.md
rm -f SCHEMA.md                   # → docs/SCHEMA.md
rm -f SCRAPING_RULES.md           # → .agent/RULES.md (merged)
rm -f SECURITY.md                 # → .agent/SECRETS_AND_CONFIG.md
rm -f STEALTH_IMPLEMENTATION.md   # → .agent/MEMORY.md
rm -f TROUBLESHOOTING.md          # → .agent/DEBUGGING_SCRAPERS.md
rm -f DESOTO_INCREMENTAL_STRATEGY.md  # → counties/desoto/quirks.md
echo "   ✅ Root markdown consolidated"

# --- 9. Duplicate docs/ files that overlap with .agent/ ---
echo ""
echo "9️⃣  Deduplicating docs/ vs .agent/..."
rm -f docs/IDENTITY.md             # → .agent/IDENTITY.md (canonical)
rm -f docs/RULES.md                # → .agent/RULES.md (canonical)
rm -f docs/ERROR_CATALOG.md        # → .agent/ERROR_CATALOG.md (canonical)
rm -f docs/MEMORY.md               # → .agent/MEMORY.md (canonical)
rm -f docs/SELF_HEALING.md         # → .agent/DEBUGGING_SCRAPERS.md (merged)
rm -f docs/SIGNNOW_INTEGRATION.md  # Wrong repo
rm -f docs/PROJECT_SUMMARY.md      # → README.md
echo "   ✅ docs/ deduplicated"

# --- 10. Old fixtures dir at root level ---
echo ""
echo "🔟  Removing old root fixtures..."
rm -rf fixtures
echo "   ✅ fixtures/ (now in counties/{name}/fixtures/)"

echo ""
echo "🎉 Cleanup complete!"
echo ""
echo "Remaining structure should be:"
echo "  counties/     — all scrapers"
echo "  core/         — shared modules"
echo "  config/       — YAML configs + schema"
echo "  scripts/      — CLI entry points"
echo "  .agent/       — AI agent instructions"
echo "  docs/         — human documentation"
echo "  tests/        — test suite"
echo "  .github/      — CI/CD workflows"
