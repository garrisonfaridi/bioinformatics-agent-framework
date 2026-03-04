#!/usr/bin/env bash
# local_postprocess.sh — steps to run locally after retrieving HPC results
# Edit for each project; do not run until verify_outputs.sh passes.

set -euo pipefail

RESULTS_DIR="results"
PROJECT_DIR="$(pwd)"

echo "[postprocess] Starting local post-processing in $PROJECT_DIR"

# 1. Verify outputs arrived intact
echo "[postprocess] Verifying outputs..."
bash hpc/verify_outputs.sh || { echo "ERROR: outputs incomplete; check HPC logs"; exit 1; }

# 2. Generate any plots that are faster to render locally
# e.g.: Rscript scripts/plot_results.R --results $RESULTS_DIR

# 3. Run peer review agent
# python scripts/peer_review.py --results-dir $RESULTS_DIR --run-id "$RUN_ID"

# 4. Generate provenance report
# python scripts/provenance.py report --run-id "$RUN_ID" --project-dir "$PROJECT_DIR" \
#   --output "$RESULTS_DIR/provenance_report.md"

echo "[postprocess] Done. Review results/ and peer_review/ before delivering."
