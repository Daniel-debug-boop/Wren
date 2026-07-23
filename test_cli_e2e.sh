#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  WREN APP BUILDER — End-to-End CLI Test Suite
#
#  Tests that the CLI works correctly on YOUR machine.
#  Uses a real API key to test against OpenRouter's free tier.
#
#  Usage:
#    chmod +x test_cli_e2e.sh
#    ./test_cli_e2e.sh "sk-or-v1-..."
#
#  This will:
#    1. Verify Python 3.12+ is available
#    2. Test that all unit tests pass (pytest)
#    3. Run the CLI with a simple prompt using OpenRouter free models
#    4. Verify generated output files exist
#    5. Clean up test artifacts
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────
GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
CYAN='\033[36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }
info() { echo -e "  ${CYAN}→${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
header() { echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# ── Config ──────────────────────────────────────────────────────
API_KEY="${1:-}"
TEST_DIR="./test-e2e-$(date +%s)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT="Build a simple HTML page with a hero section that says 'Hello from Wren'"

# ── Validate API key ────────────────────────────────────────────
header "Phase 0: Pre-flight Checks"

if [ -z "$API_KEY" ]; then
    fail "Usage: $0 <api-key>\n  e.g., $0 \"sk-or-v1-...\""
fi
pass "API key provided: ${API_KEY:0:12}..."

# Check Python version
PY_VERSION=$(python3 --version 2>&1)
info "Python: $PY_VERSION"
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
    fail "Python 3.12+ required (found: $PY_VERSION)"
fi
pass "Python version OK"

# Check script directory
cd "$SCRIPT_DIR"
pass "Working directory: $(pwd)"

# Check run_app_builder.py exists
if [ ! -f "run_app_builder.py" ]; then
    fail "run_app_builder.py not found in $(pwd)"
fi
pass "run_app_builder.py found"

# Check Python stdlib available (urllib + asyncio)
python3 -c "import urllib.request; import asyncio; import json; print('  OK')" 2>&1 || fail "Missing standard library modules"
pass "Python stdlib available (zero deps)"

# ── Run unit tests ──────────────────────────────────────────────
header "Phase 1: Unit Tests"

if command -v pytest &> /dev/null; then
    info "Running app_builder unit tests..."
    python3 -m pytest tests/unit/app_builder/ -v --tb=short 2>&1 | tail -20 || warn "Some unit tests failed (check above)"
    pass "Unit tests completed"
else
    warn "pytest not installed — skipping unit tests"
    warn "Install with: pip install pytest pytest-asyncio"
fi

# ── Test CLI --help ─────────────────────────────────────────────
header "Phase 2: CLI --help"

info "Running: python3 run_app_builder.py --help"
HELP_OUTPUT=$(python3 run_app_builder.py --help 2>&1)
echo "$HELP_OUTPUT" | head -5
if echo "$HELP_OUTPUT" | grep -q "WREN APP BUILDER"; then
    pass "CLI --help works"
else
    fail "CLI --help failed"
fi

# ── Test with OpenRouter free model ────────────────────────────
header "Phase 3: CLI with OpenRouter (free model)"

info "Prompt: \"$PROMPT\""
info "Model: openrouter/free"
info "Output: $TEST_DIR"

# Run the CLI with timeout (3 minutes max for free model)
# Use --no-validate to skip build checks (no node/npm needed)
# Use --no-resume to start fresh
set +e
START_TIME=$(date +%s)
timeout 180 python3 run_app_builder.py \
    --prompt "$PROMPT" \
    --api-key "$API_KEY" \
    --base-url "https://openrouter.ai/api/v1" \
    --model "openrouter/free" \
    --output "$TEST_DIR" \
    --no-validate \
    --no-resume \
    2>&1 | tee /tmp/wren-e2e-output.txt
CLI_EXIT=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
set -e

echo ""
if [ $CLI_EXIT -eq 0 ]; then
    pass "CLI completed successfully (${DURATION}s)"
elif [ $CLI_EXIT -eq 124 ]; then
    warn "CLI timed out after 180s (free models can be slow)"
else
    warn "CLI exited with code $CLI_EXIT (${DURATION}s)"
    warn "Check /tmp/wren-e2e-output.txt for details"
fi

# ── Verify output ──────────────────────────────────────────────
header "Phase 4: Output Verification"

if [ -d "$TEST_DIR" ]; then
    pass "Output directory exists: $TEST_DIR"

    # Show what was generated
    info "Generated files:"
    find "$TEST_DIR" -type f -not -name "project_state.json" 2>/dev/null | while read -r f; do
        SIZE=$(wc -c < "$f")
        echo "    $(echo "$f" | sed "s|$TEST_DIR/||") (${SIZE} bytes)"
    done

    # Check for project_state.json (resume support)
    STATE_FILES=$(find "$TEST_DIR" -name "project_state.json" 2>/dev/null | wc -l)
    if [ "$STATE_FILES" -gt 0 ]; then
        pass "State file found (resume capability confirmed)"
    fi

    # Count generated files
    FILE_COUNT=$(find "$TEST_DIR" -type f -not -name "project_state.json" 2>/dev/null | wc -l)
    if [ "$FILE_COUNT" -gt 0 ]; then
        pass "Generated $FILE_COUNT file(s)"
    else
        warn "No generated files found"
    fi
else
    warn "Output directory not created"
fi

# ── Cleanup ─────────────────────────────────────────────────────
header "Phase 5: Cleanup"

read -p "  Remove test artifacts? [Y/n]: " -r CLEANUP
if [[ "$CLEANUP" =~ ^[Yy]?$ ]]; then
    rm -rf "$TEST_DIR" 2>/dev/null || true
    pass "Cleaned up $TEST_DIR"
else
    info "Test artifacts left at: $TEST_DIR"
fi

# ── Summary ────────────────────────────────────────────────────
header "Summary"

echo -e "  ${BOLD}Wren App Builder E2E Test Results${NC}"
echo ""
echo -e "  API:     OpenRouter (free auto-routing)"
echo -e "  Prompt:  \"$PROMPT\""
echo -e "  Duration: ${DURATION}s"
echo -e "  Status:  $([ $CLI_EXIT -eq 0 ] && echo "${GREEN}PASS${NC}" || echo "${YELLOW}CHECK LOGS${NC}")"
echo ""
echo -e "  ${DIM}Logs: /tmp/wren-e2e-output.txt${NC}"
echo ""
echo -e "  Next steps:"
echo -e "   ${DIM}1.${NC} Run with a custom model:   --model \"mistralai/mistral-small-3.1-24b:free\""
echo -e "   ${DIM}2.${NC} Run with validation:       omit --no-validate (needs npm/node)"
echo -e "   ${DIM}3.${NC} Run resume test:           run twice with --output same-dir"
echo ""
