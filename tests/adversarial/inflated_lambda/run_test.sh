#!/usr/bin/env bash
# Adversarial test: inflated lambda GC
# Checks that peer review issues.json contains a critical statistical flag.

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
critical_stat = [i for i in issues
                 if i.get("category") == "statistical"
                 and i.get("severity") == "critical"]
if critical_stat:
    print(f"PASS: {len(critical_stat)} critical statistical issue(s) detected")
    for i in critical_stat:
        print(f"  {i['description'][:80]}")
    sys.exit(0)
else:
    print("FAIL: inflated lambda not flagged as critical statistical issue")
    sys.exit(1)
EOF
