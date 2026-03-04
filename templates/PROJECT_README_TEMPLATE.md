# [Project Name]

## Analysis Summary

[1–2 sentence description of the biological question, dataset, species, and main finding.]

## How to Reproduce

```bash
# 1. Clone / navigate to project directory
cd projects/[project-name]

# 2. Check tool versions match knowhow docs
python ../../scripts/check_knowhow_versions.py --knowhow-dir ../../knowhow/

# 3. Review plan and approve
# (read plan.md, then:)
touch plan.approved

# 4. Run the pipeline
snakemake --cores 8 --use-singularity   # or: nextflow run main.nf -profile singularity,slurm

# 5. Local post-processing (after HPC results retrieved, if applicable)
bash hpc/local_postprocess.sh
```

## Key Decisions and Rationale

See `results/provenance_report.md` for the full decision chain.

## Peer Review History

See `results/peer_review/` for all rounds.

- `round1/review_report.md` — initial review
- `round1/issues.json` — structured issue list
- `review_diff_R1_R2.md` — what changed between rounds (if applicable)

## Reasoning Traces

See `reasoning_traces/` for sequential thinking logs and decision audit trail.

```bash
# Summarize a run's reasoning trace
python ../../scripts/trace_logger.py summarize \
  --run-id <run_id> \
  --project-dir .
```

## HPC Submission (if applicable)

See `hpc/` for SLURM submission scripts and transfer instructions.

```bash
# Transfer to cluster
bash hpc/transfer_instructions.md   # read and adapt

# After results return, verify
bash hpc/verify_outputs.sh
```

## Outputs

| Path | Description |
|------|-------------|
| `results/qc/multiqc_report.html` | Aggregated QC report |
| `results/[analysis]/` | Primary analysis outputs |
| `results/provenance_report.md` | Decision chain documentation |
| `results/peer_review/` | Peer review reports |

## Contact

[Your name] — [email]
