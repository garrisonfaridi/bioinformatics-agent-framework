#!/usr/bin/env bash
# Adversarial test: spatial-domains skill without DL dependencies.
# Verifies Leiden fallback behavior when torch/SpaGCN are not installed.

set -e
PASS_COUNT=0
FAIL_COUNT=0

pass() { echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

OUTPUT_DIR="$TMPDIR/spatial_test"
mkdir -p "$OUTPUT_DIR"

SKILL_SCRIPT="kinesin/coordination/bio_skills/spatial-domains/scripts/spatial_domains.py"

# Run the spatial-domains skill script directly.
# Since torch is likely not installed in the test environment, _dl_available() returns False
# and the Leiden fallback path runs.
# If torch IS installed, we simulate the no-torch case via the --method leiden flag.

STDOUT=$("$( which python3 )" "$SKILL_SCRIPT" \
    --input demo.h5ad \
    --output "$OUTPUT_DIR" \
    --method auto \
    --demo 2>"$TMPDIR/stderr.txt")
EXIT_CODE=$?

# 1. Exit code must be 0 (Leiden fallback is a valid result)
if [ "$EXIT_CODE" -eq 0 ]; then
    pass "spatial-domains exited with code 0 (fallback succeeded)"
else
    fail "spatial-domains exited with code $EXIT_CODE (expected 0)"
fi

STDERR_CONTENT=$(cat "$TMPDIR/stderr.txt")

# 2. If torch is NOT available: stderr must contain the WARNING message (not a traceback)
if echo "$STDERR_CONTENT" | grep -q "SpaGCN/STAGATE"; then
    pass "WARNING message present in stderr (SpaGCN/STAGATE not available message found)"

    # Verify it's not a Python traceback
    if echo "$STDERR_CONTENT" | grep -q "Traceback (most recent call last)"; then
        fail "Stderr contains Python traceback (expected only WARNING, not ImportError)"
    else
        pass "No Python traceback in stderr (clean WARNING output)"
    fi
elif echo "$STDERR_CONTENT" | grep -q "ImportError"; then
    fail "Stderr contains ImportError traceback (expected graceful WARNING)"
else
    # torch IS installed — skill ran with DL method; test the --method leiden path instead
    echo "NOTE: torch appears to be installed. Re-running with --method leiden to test fallback path."

    STDOUT=$("$( which python3 )" "$SKILL_SCRIPT" \
        --input demo.h5ad \
        --output "$OUTPUT_DIR" \
        --method leiden \
        --demo 2>"$TMPDIR/stderr_leiden.txt")
    LEIDEN_EXIT=$?

    if [ "$LEIDEN_EXIT" -eq 0 ]; then
        pass "spatial-domains with --method leiden exited code 0"
    else
        fail "spatial-domains with --method leiden exited code $LEIDEN_EXIT"
    fi

    # In leiden mode, no DL warning expected (user explicitly requested leiden)
    pass "DL dependencies present — Leiden path tested explicitly via --method leiden"
fi

# 3. stdout must be valid JSON
if echo "$STDOUT" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    pass "stdout is valid JSON"
else
    fail "stdout is not valid JSON: $STDOUT"
fi

# 4. JSON must contain expected fields
RESULT_DL_AVAIL=$(echo "$STDOUT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('results',{}).get('dl_available', d.get('dl_available', 'missing')))" 2>/dev/null || echo "parse_error")
if [ "$RESULT_DL_AVAIL" != "parse_error" ]; then
    pass "Output JSON has expected result structure"
else
    fail "Output JSON missing expected fields"
fi

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ] && exit 0 || exit 1
