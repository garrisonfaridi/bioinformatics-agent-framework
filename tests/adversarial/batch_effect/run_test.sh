#!/usr/bin/env bash
# Adversarial test: batch effect injection
# Checks that peer review detects the inflation.

set -euo pipefail

ISSUES_FILE="results/peer_review/round1/issues.json"

if [ ! -f "$ISSUES_FILE" ]; then
  echo "SKIP: $ISSUES_FILE not found; run the pipeline first"
  exit 0
fi

python3 - <<'EOF'
import json, sys
with open("results/peer_review/round1/issues.json") as fh:
    data = json.load(fh)
issues = data.get("issues", [])
stat_issues = [i for i in issues if i.get("category") == "statistical"
               and i.get("severity") in ("critical", "major")]
if stat_issues:
    print(f"PASS: {len(stat_issues)} statistical issue(s) flagged")
    for i in stat_issues:
        print(f"  [{i['severity']}] {i['description'][:80]}")
    sys.exit(0)
else:
    print("FAIL: no critical/major statistical issues found in peer review")
    print("Expected batch effect / lambda GC inflation to be detected")
    sys.exit(1)
EOF
