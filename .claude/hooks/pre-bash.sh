#!/usr/bin/env bash
# Pre-bash hook: enforce plan approval gate and narration checkpoint

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null)

# ── 1. Plan approval gate ────────────────────────────────────────────────────
# Block pipeline execution without a plan.approved sentinel file

PIPELINE_PATTERNS=(
  "snakemake"
  "nextflow run"
  "sbatch"
  "srun"
  "qsub"
)

for pattern in "${PIPELINE_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -q "$pattern"; then
    if ! [ -f "./plan.approved" ]; then
      echo "BLOCKED: Pipeline execution requires plan approval."
      echo "Review plan.md and run 'touch plan.approved' in your project directory to proceed."
      echo "Command attempted: $COMMAND"
      exit 2
    fi
  fi
done

# ── 2. Narration checkpoint gate ─────────────────────────────────────────────
# Block significant analysis commands if narrate.py was not called recently.
# narrate.py writes ~/.claude/narration_checkpoint on every invocation.
# MAX_AGE: 300 seconds (5 minutes). Enough for a rapid sequence of steps from
# one narration; short enough to require re-narration for new phases.

ANALYSIS_PATTERNS=(
  "python scripts/"
  "Rscript"
  "nextflow"
  "snakemake"
  "samtools"
  "gatk "
  "bwa "
  "STAR "
  "salmon "
  "featureCounts"
  "gemma"
  "plink"
  "bcftools"
  "multiqc"
  "fastp"
  "cellranger"
  "STARsolo"
  "bismark"
  "macs2"
)

NARRATION_SENTINEL="$HOME/.claude/narration_checkpoint"
MAX_AGE=300  # seconds

for pattern in "${ANALYSIS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -q "$pattern"; then
    # Sentinel missing entirely
    if [ ! -f "$NARRATION_SENTINEL" ]; then
      echo "BLOCKED: No narration checkpoint found."
      echo "Explain what you are doing before running this command:"
      echo "  python scripts/narrate.py --phase <phase> --event <event> --message '<one sentence>'"
      echo "Command attempted: $COMMAND"
      exit 2
    fi

    # Sentinel too old
    NOW=$(date +%s)
    LAST_NARRATED=$(stat -f %m "$NARRATION_SENTINEL" 2>/dev/null || echo 0)
    AGE=$(( NOW - LAST_NARRATED ))
    if [ "$AGE" -gt "$MAX_AGE" ]; then
      echo "BLOCKED: Last narration was ${AGE}s ago (max ${MAX_AGE}s)."
      echo "Narrate this step before proceeding:"
      echo "  python scripts/narrate.py --phase <phase> --event <event> --message '<one sentence>'"
      echo "Command attempted: $COMMAND"
      exit 2
    fi

    break  # one match is enough; don't re-check remaining patterns
  fi
done

exit 0  # allow
