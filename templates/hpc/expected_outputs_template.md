# Expected Outputs for [Project Name]

List all expected output files after a successful HPC run.
Use this to verify completeness before running local post-processing.

## Required files

| File path | Description | Min size |
|-----------|-------------|----------|
| `results/qc/multiqc_report.html` | Aggregated QC report | >50 KB |
| `results/alignment/*.bam` | Sorted BAMs (one per sample) | >1 MB |
| `results/counts/count_matrix.tsv` | Gene count matrix | >10 KB |
| `results/deseq2/*_results.tsv` | DE result tables | >1 KB |

## Verification script

The `verify_outputs.sh` script checks:
1. All required files exist
2. Files exceed minimum size thresholds
3. Key output files are valid (non-empty, parseable headers)

Run after rsync:
```bash
bash hpc/verify_outputs.sh
```

Exit code 0 = all outputs present and valid.
Exit code 1 = missing or undersized files (check HPC logs).
