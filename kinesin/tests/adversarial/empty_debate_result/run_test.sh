#!/usr/bin/env bash
# Adversarial test: empty/non-actionable debate result.
# Verifies run.py surfaces dispute summary (not traceback) and exits code 2
# without writing plan_context.md.
# No API calls required — uses unittest.mock to patch debate function.

set -e
PASS_COUNT=0
FAIL_COUNT=0

pass() { echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

PROJECT_DIR="$TMPDIR/empty_debate_test"
CONFIG_PATH="$TMPDIR/test_config.yaml"

mkdir -p "$PROJECT_DIR"

cat > "$CONFIG_PATH" << 'EOF'
arc:
  config_file: kinesin/literature/arc_config.biology.yaml
  metaclaw_enabled: false
scienceclaw:
  agent_count: 3
  personalities: [skeptic, synthesizer, pragmatist]
writing:
  target_conference: biorxiv
  authors: Test
EOF

# Run with mocked literature and debate phases
python3 -c "
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, '.')

from kinesin.coordination.debate_result import DebateResult

# Non-actionable result: no validated hypotheses, low consensus
empty_result = DebateResult(
    validated_hypotheses=[],
    disputed_hypotheses=['H1: agents disagreed completely'],
    consensus_score=0.3,
    raw_agent_results=[{}, {}, {}],
)

# Minimal research_brief for layer 1 mock
stub_brief = {
    'topic': 'test topic',
    'hypotheses': ['H1'],
    'literature_gaps': [],
    'key_papers': [],
    'recommended_datasets': [],
    'suggested_analyses': [],
}

stub_kb = MagicMock()
stub_kb.get.return_value = ''
stub_kb.stage_completed.return_value = True
stub_kb.list_stages.return_value = ['stage-01','stage-08']

with patch('kinesin.literature.arc_bridge.run_literature_phase', return_value=(stub_kb, Path('$PROJECT_DIR/arc_run'))):
    with patch('kinesin.literature.arc_bridge.kb_to_research_brief', return_value=stub_brief):
        with patch('kinesin.coordination.scienceclaw_bridge.run_hypothesis_debate', side_effect=ValueError(empty_result.dispute_summary())):
            import kinesin.run as run_module
            try:
                run_module.main(
                    topic='test topic',
                    mode='literature-only',
                    config_path='$CONFIG_PATH',
                    project_dir='$PROJECT_DIR',
                )
                # Should not reach here — ValueError should cause sys.exit(2)
                print('ERROR: main() did not exit', file=sys.stderr)
                sys.exit(99)
            except SystemExit as e:
                if e.code == 2:
                    sys.exit(0)
                else:
                    print(f'ERROR: exit code was {e.code}, expected 2', file=sys.stderr)
                    sys.exit(1)
" 2>&1
EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 0 ]; then
    pass "run.py exited with code 2 for non-actionable debate result"
else
    fail "run.py did not exit with code 2 (got $EXIT_CODE)"
fi

# plan_context.md must NOT exist
if [ ! -f "$PROJECT_DIR/plan_context.md" ]; then
    pass "plan_context.md not written (correct — debate was not actionable)"
else
    fail "plan_context.md was written despite non-actionable debate"
fi

echo ""
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ] && exit 0 || exit 1
