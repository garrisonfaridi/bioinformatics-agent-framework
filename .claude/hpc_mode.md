## 5. HPC Pipeline Mode

Some analyses require HPC execution (large WGS cohorts, genome-wide imputation,
GWAS N > 500, scRNA-seq > 100k cells, etc.).

**When HPC is required:**
1. NEVER attempt to run the pipeline locally
2. Generate all pipeline files but do NOT execute them
3. Create `hpc/` in the project with:
   - `submit.sh` — master SLURM submission script
   - `job_configs/` — per-step SLURM headers (use `templates/hpc/slurm_header_template.sh`)
   - `transfer_instructions.md` — what to rsync to the cluster (use `templates/hpc/transfer_instructions.md`)
   - `expected_outputs.md` — expected files with size thresholds (use `templates/hpc/expected_outputs_template.md`)
   - `local_postprocess.sh` — steps to run locally after retrieval (use `templates/hpc/local_postprocess_template.sh`)
4. Deliverable = validated pipeline code + complete submission package
   The human submits, monitors, and retrieves results.

**Auto-trigger HPC mode for:**
- Nextflow or Snakemake pipeline with >50 samples
- GWAS with N > 500
- WGS variant calling (any N)
- Imputation with any reference panel
- scRNA-seq with >100k cells
- Any step requiring >32 GB RAM or >8 cores sustained

See `knowhow/pipeline_dev.md` → HPC/SLURM section for Nextflow executor config,
`-resume` patterns, file staging, and memory tier guidance.
