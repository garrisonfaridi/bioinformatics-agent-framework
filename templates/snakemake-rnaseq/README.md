# [Project Title] — Bulk RNA-seq Pipeline (Snakemake)

## Description

[2–3 sentence description of the project, client, biological question, and organism.]

## Requirements

- Snakemake ≥8.0
- conda/mamba (for rule-level environments) or Singularity
- ≥32 GB RAM (for STAR genome index)

## Usage

```bash
# 1. Edit config
cp config/config.yaml.template config/config.yaml
cp config/samples.tsv.template config/samples.tsv

# 2. Dry run (validate DAG)
snakemake --dry-run --cores 1

# 3. Run (local with conda)
snakemake --cores 8 --use-conda

# 4. Run (HPC with SLURM + Singularity)
snakemake --profile profiles/slurm --use-singularity
```

## Inputs

| File | Description |
|------|-------------|
| `config/config.yaml` | Paths, parameters, contrast definitions |
| `config/samples.tsv` | sample, unit, fq1, fq2, condition |
| `data/ref/genome.fa` | Reference genome FASTA |
| `data/ref/annotation.gtf` | Gene annotation GTF |

## Outputs

| Directory | Contents |
|-----------|----------|
| `results/qc/` | FastQC, fastp, MultiQC HTML |
| `results/alignment/` | Sorted BAMs, STAR logs |
| `results/counts/` | featureCounts count matrix (TSV) |
| `results/deseq2/` | DE tables, PCA, volcano plots |

## Methods

See `METHODS.md` for publishable methods text.

## Contact

[Your name] — [email]
