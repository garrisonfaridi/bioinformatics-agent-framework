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
