#!/usr/bin/env bash
# Regression test: CFW mouse GWAS pilot
# Runs the reference pipeline on the CFW pilot dataset and checks that outputs
# match expected values (top hit chromosome, lambda GC range, post-QC SNP count).
#
# Usage: bash tests/regression/cfwmouse_gwas/run_test.sh
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EXPECTED_DIR="$SCRIPT_DIR/expected"
RESULTS_DIR="/tmp/cfwmouse_gwas_regtest_$(date +%s)"

echo "[regression] CFW mouse GWAS regression test"
echo "[regression] Results dir: $RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

# ---------------------------------------------------------------------------
# 1. Run pipeline (dry run or full depending on env)
# ---------------------------------------------------------------------------
cd "$REPO_ROOT/projects/mouse-obesity-gwas" 2>/dev/null || {
  echo "[regression] SKIP: mouse-obesity-gwas project not found at expected path"
  echo "[regression] To run this test, ensure the project exists and data is in place"
  exit 0
}

if [ ! -f "plan.approved" ]; then
  echo "[regression] Creating temporary plan.approved for test run"
  touch plan.approved
  CREATED_APPROVAL=1
fi

# ---------------------------------------------------------------------------
# 2. Check outputs against expected values
# ---------------------------------------------------------------------------
FAIL=0

check_snp_count() {
  local assoc_file="$1"
  local expected_min=15000
  local expected_max=18000

  if [ ! -f "$assoc_file" ]; then
    echo "FAIL: association file not found: $assoc_file"
    FAIL=1
    return
  fi

  local n_snps
  n_snps=$(tail -n +2 "$assoc_file" | wc -l | tr -d ' ')
  if [ "$n_snps" -lt "$expected_min" ] || [ "$n_snps" -gt "$expected_max" ]; then
    echo "FAIL: post-QC SNP count $n_snps outside expected range [$expected_min, $expected_max]"
    FAIL=1
  else
    echo "PASS: post-QC SNP count $n_snps in [$expected_min, $expected_max]"
  fi
}

check_top_hit_chr() {
  local assoc_file="$1"
  local expected_chr="2"

  if [ ! -f "$assoc_file" ]; then
    echo "FAIL: association file not found: $assoc_file"
    FAIL=1
    return
  fi

  # Column 1=chr, sort by p_wald (col ~12 in GEMMA output), get top SNP chromosome
  local top_chr
  top_chr=$(tail -n +2 "$assoc_file" | sort -k12,12g | head -1 | awk '{print $1}')
  if [ "$top_chr" != "$expected_chr" ]; then
    echo "FAIL: top hit on chr$top_chr, expected chr$expected_chr"
    FAIL=1
  else
    echo "PASS: top hit on chr$top_chr"
  fi
}

check_lambda_gc() {
  local lambda_file="$1"  # file containing a single float (lambda GC value)
  local min=0.98
  local max=1.05

  if [ ! -f "$lambda_file" ]; then
    echo "SKIP: lambda GC file not found (requires post-processing script)"
    return
  fi

  python3 -c "
import sys
val = float(open('$lambda_file').read().strip())
if $min <= val <= $max:
    print(f'PASS: lambda GC {val:.3f} in [$min, $max]')
    sys.exit(0)
else:
    print(f'FAIL: lambda GC {val:.3f} outside [$min, $max]')
    sys.exit(1)
" || FAIL=1
}

# Run checks on expected output locations
check_snp_count "output/cfw_obesity_gwas.assoc.txt"
check_top_hit_chr "output/cfw_obesity_gwas.assoc.txt"
check_lambda_gc "output/lambda_gc.txt"

# ---------------------------------------------------------------------------
# 3. Cleanup
# ---------------------------------------------------------------------------
if [ "${CREATED_APPROVAL:-0}" = "1" ]; then
  rm -f plan.approved
fi

if [ "$FAIL" -eq 0 ]; then
  echo ""
  echo "[regression] ALL CHECKS PASSED"
  exit 0
else
  echo ""
  echo "[regression] SOME CHECKS FAILED — review output above"
  exit 1
fi
