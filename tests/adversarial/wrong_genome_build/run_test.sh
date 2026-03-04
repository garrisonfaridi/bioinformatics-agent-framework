#!/usr/bin/env bash
# Adversarial test: wrong genome build
# Checks that peer review flags a reproducibility/computational issue.

ISSUES_FILE="results/peer_review/round1/issues.json"
if [ ! -f "$ISSUES_FILE" ]; then
  echo "SKIP: $ISSUES_FILE not found"
  exit 0
fi

python3 - <<'EOF'
import json, sys
with open("results/peer_review/round1/issues.json") as fh:
    data = json.load(fh)
issues = data.get("issues", [])
build_issues = [i for i in issues
                if i.get("category") in ("computational", "reproducibility")]
if build_issues:
    print(f"PASS: {len(build_issues)} computational/reproducibility issue(s) flagged")
    sys.exit(0)
else:
    print("FAIL: no computational/reproducibility issues detected")
    sys.exit(1)
EOF
