#!/usr/bin/env bash
# Adversarial test: truncated GEMMA output
# Checks that the pipeline or peer review detects unexpectedly low SNP counts.

ASSOC_FILE="output/cfw_obesity_gwas.assoc.txt"
MIN_EXPECTED=15000

if [ ! -f "$ASSOC_FILE" ]; then
  echo "SKIP: $ASSOC_FILE not found"
  exit 0
fi

n_snps=$(tail -n +2 "$ASSOC_FILE" | wc -l | tr -d ' ')
if [ "$n_snps" -lt "$MIN_EXPECTED" ]; then
  echo "PASS: correctly detected low SNP count ($n_snps < $MIN_EXPECTED)"
  exit 0
else
  echo "FAIL: SNP count $n_snps >= $MIN_EXPECTED (corruption not detected)"
  exit 1
fi
