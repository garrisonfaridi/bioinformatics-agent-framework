---
last_verified: 2026-03-04
tool_versions:
  nextflow: "23.10.0"
  snakemake: "9.16.3"
  singularity: "3.11.0"
  docker: "25.0.0"
---

# Pipeline Development Know-How

## Framework Decision Matrix

| Criterion | Nextflow DSL2 | Snakemake | WDL |
|-----------|--------------|-----------|-----|
| HPC portability | Excellent | Good | Good |
| Cloud (AWS/GCP) | Native (Batch, GLS) | Requires setup | Terra/Cromwell |
| Community modules | nf-core (large) | Snakemake wrappers | BioWDL |
| Learning curve | Moderate | Low (Python-based) | Moderate |
| Container support | Native | Native | Native |
| **Choose when** | New pipelines, HPC+cloud | Python users, quick pipelines | Broad/Terra submission |

**Default: Nextflow DSL2** unless client specifies otherwise or quick one-off.

## nf-core Modules

- Browse: https://nf-co.re/modules
- Install: `nf-core modules install samtools/sort`
- Update: `nf-core modules update`
- Local override: copy to `modules/local/` and modify

nf-core pipeline template: `nf-core create` — sets up full CI, linting, stub tests

## Container Strategy

- **Docker** for local dev; **Singularity** for HPC (auto-pulled from Docker Hub by Nextflow)
- Use `quay.io/biocontainers/` images where available (pre-built, versioned)
- Custom containers: `Dockerfile` in `containers/toolname/`; push to GitHub Container Registry
- Pin by digest for production: `docker pull tool:version@sha256:abc123`

## GitHub Actions CI

Minimal workflow for Nextflow pipelines:
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: nf-core/setup-nextflow@v2
      - run: nextflow run . -profile docker,test --outdir results
```

Add `nf-core lint` check as separate job.

## Stub / Test Runs

- Always write `stub:` blocks in Nextflow process definitions
- `nextflow run main.nf -stub-run` — fast syntax/logic check without real data
- Maintain `tests/` dir with tiny FASTQ/BAM test data (<5 MB total)
- `--profile test` should run end-to-end in <5 min with test data

## Config Structure (Nextflow)

```
nextflow.config          # main config (params, profiles)
conf/
  base.config            # resource defaults
  hpc_slurm.config       # SLURM executor settings
  docker.config          # Docker profile
  singularity.config     # Singularity profile
```

---

## HPC/SLURM Pipeline Execution

### Nextflow with SLURM executor vs. manual SLURM submission

| Approach | When to use | Pros | Cons |
|----------|-------------|------|------|
| `nextflow run -profile singularity,slurm` | Nextflow pipeline with ≥5 steps | Automatic job chaining, `-resume`, monitoring | Requires Nextflow on HPC login node |
| Manual SLURM `sbatch` array | Simple parallel jobs (one script, many inputs) | No Nextflow dependency | No automatic dependency handling |
| Snakemake `--profile slurm` | Snakemake pipeline on HPC | Python-native, DAG-aware | Requires cluster profile YAML |

For Nextflow, use `conf/hpc_slurm.config`:
```groovy
process {
    executor = 'slurm'
    queue    = 'standard'          // fill in your partition
    clusterOptions = '--account=ACCOUNT'
    withLabel: 'high_mem' {
        memory = '128.GB'
        cpus   = 16
        time   = '24.h'
    }
}
```

### Checkpoint and resume on HPC

- **Nextflow:** `-resume` flag re-uses cached process outputs from `work/` directory;
  always pass `-resume` on re-submission after failure
- **Snakemake:** incomplete outputs are automatically re-run; use `--rerun-incomplete`
  after partial failures to force re-execution of broken checkpoints

### File staging patterns

- **Scratch vs. project storage:** run pipeline from scratch (`$SCRATCH` or `$TMPDIR`);
  only rsync final results back to project storage; scratch is faster for I/O-heavy steps
- **Reference data:** stage genome indices to a shared reference directory, not per-project;
  symlink from project `data/ref/` to shared location
- **Container images:** pull Singularity `.sif` files once to a shared cache
  (`export SINGULARITY_CACHEDIR=/shared/singularity_cache`); set in `~/.bashrc` on cluster

### Memory tiers (placeholder — fill in for your cluster)

| Tier | Partition | Max mem | Use for |
|------|-----------|---------|---------|
| Standard | standard | 256 GB | most pipeline steps |
| High-mem | highmem | 1 TB | BWA-MEM2 index, STAR index (large genomes) |
| GPU | gpu | 40 GB VRAM | deep learning steps (scVI, etc.) |

### Monitoring Nextflow HPC runs

```bash
# Tail main log
tail -f .nextflow.log

# List running jobs
squeue -u $USER

# If using Nextflow Tower (optional)
# Register run: nextflow run main.nf -with-tower
```
