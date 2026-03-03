# Snakemake RNA-seq Template — Claude Context

## Purpose
Bulk RNA-seq pipeline in Snakemake: QC → alignment → count → differential expression.

## Key Tools (pin versions in conda envs or containers)
- **fastp** ≥0.23 — adapter trimming and QC
- **STAR** ≥2.7.11 — splice-aware alignment
- **featureCounts** (subread ≥2.0) — gene-level count matrix
- **DESeq2** ≥1.42 (R/Bioconductor) — differential expression
- **MultiQC** ≥1.21 — aggregated QC report

## Expected Inputs
- `data/raw/` — paired-end FASTQ files
- `data/ref/` — genome FASTA + GTF annotation + STAR index
- `config/config.yaml` — paths, sample list, contrast definitions
- `config/samples.tsv` — sample, unit, fq1, fq2, condition columns

## Expected Outputs
- `results/qc/` — FastQC + fastp reports + MultiQC HTML
- `results/alignment/` — sorted BAMs + STAR summary logs
- `results/counts/` — featureCounts count matrix
- `results/deseq2/` — DE tables, normalized counts, PCA, volcano plots

## Know-How Reference
Load before starting: `@~/bioinformatics-knowhow/rnaseq.md`

## Notes
- Define per-rule conda envs in `envs/` or use `--use-singularity`
- Use `snakemake --dry-run` to validate DAG before execution
- featureCounts strandedness: `-s 0` (unstranded), `-s 1` (forward), `-s 2` (reverse)
- Check strandedness with RSeQC before choosing `-s` flag
