#!/usr/bin/env bash
# Pre-bash hook: enforce plan approval gate before pipeline execution

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null)

# Commands that require plan approval before execution
PIPELINE_PATTERNS=(
  "snakemake"
  "nextflow run"
  "sbatch"
  "srun"
  "qsub"
)

for pattern in "${PIPELINE_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -q "$pattern"; then
    # Check for plan.approved sentinel file in current working directory only
    if ! [ -f "./plan.approved" ]; then
      echo "BLOCKED: Pipeline execution requires plan approval."
      echo "Review plan.md and run 'touch plan.approved' in your project directory to proceed."
      echo "Command attempted: $COMMAND"
      exit 2  # exit code 2 = block the tool call
    fi
  fi
done

exit 0  # allow
