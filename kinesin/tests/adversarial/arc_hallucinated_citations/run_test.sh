#!/usr/bin/env bash
# Adversarial test: ARC hallucinated citation detection.
# Injects a fake DOI into stage-23/ and verifies run_paper_phase() raises RuntimeError.
# No API calls required.

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

skip() { echo "SKIP: $1"; SKIP_COUNT=$((SKIP_COUNT + 1)); }

# Check researchclaw is installed — skip gracefully if not
if ! python3 -c "import researchclaw" 2>/dev/null; then
    skip "researchclaw not installed (run: pip install researchclaw==0.3.1)"
    echo "Results: $SKIP_COUNT skipped (install researchclaw to run this test)"
    exit 0
fi

pass() { echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

PROJECT_DIR="$TMPDIR/hallucinated_test"
ARC_RUN="$PROJECT_DIR/arc_run"
RESULTS_DIR="$PROJECT_DIR/results"

# Setup: create minimal directories
mkdir -p "$ARC_RUN/stage-23" "$RESULTS_DIR/peer_review/round1"

# Inject: fake failed citations file (simulates Stage 23 catching a hallucinated DOI)
echo "10.9999/fake.doi.2026 - Hallucinated Study on Neuroblastoma, 2026" \
    > "$ARC_RUN/stage-23/failed_citations.txt"

# Create stub results/analysis files so experiment_injector doesn't error
echo "## Findings\n- Test finding" > "$RESULTS_DIR/peer_review/round1/review_report.md"

# Run the paper bridge and expect a non-zero exit (RuntimeError)
python3 -c "
import sys
sys.path.insert(0, '.')
from pathlib import Path
from kinesin.writing.arc_writer_bridge import run_paper_phase
from kinesin.coordination.debate_result import DebateResult

debate_result = DebateResult(validated_hypotheses=['H1'], consensus_score=0.7)
config = {'writing': {'target_conference': 'biorxiv', 'authors': 'Test'}}

try:
    run_paper_phase(
        results_dir='$RESULTS_DIR',
        arc_run_dir=Path('$ARC_RUN'),
        debate_result=debate_result,
        config=config,
    )
    print('ERROR: run_paper_phase() did not raise RuntimeError', file=sys.stderr)
    sys.exit(1)
except RuntimeError as e:
    error_msg = str(e)
    if '10.9999/fake.doi.2026' in error_msg or 'CITATION_VERIFY' in error_msg or 'failed' in error_msg.lower():
        print('Citation error correctly raised and contains citation info')
        sys.exit(0)
    else:
        print(f'ERROR: RuntimeError raised but message did not mention citation: {error_msg}', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'ERROR: Unexpected exception type {type(e).__name__}: {e}', file=sys.stderr)
    sys.exit(1)
" && pass "run_paper_phase() raised RuntimeError for hallucinated DOI" \
  || fail "run_paper_phase() did NOT raise RuntimeError"

# Assert: stage-22/paper_draft.md must NOT exist (RuntimeError prevented write)
if [ ! -f "$ARC_RUN/stage-22/paper_draft.md" ]; then
    pass "stage-22/paper_draft.md not written (correct — error raised before write)"
else
    fail "stage-22/paper_draft.md was written despite citation failure"
fi

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed, $SKIP_COUNT skipped"
[ "$FAIL_COUNT" -eq 0 ] && exit 0 || exit 1
