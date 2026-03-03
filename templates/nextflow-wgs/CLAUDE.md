# Nextflow WGS/WES Template — Claude Context

## Purpose
Whole-genome/exome variant calling pipeline: alignment → BQSR → variant calling → annotation.

## Key Tools (pin versions in nextflow.config)
- **BWA-MEM2** ≥2.2.1 — short-read alignment
- **GATK4** ≥4.5 — MarkDuplicates, BQSR, HaplotypeCaller, GenomicsDBImport
- **Picard** ≥3.1 — duplicate marking, metrics
- **samtools** ≥1.19 — BAM processing
- **VEP** ≥111 — variant annotation (cache + CADD + SpliceAI plugins)
- **MultiQC** ≥1.21 — aggregated QC report

## Expected Inputs
- `data/raw/` — paired-end FASTQ files
- `data/ref/` — GRCh38 FASTA + known sites VCFs (dbSNP, Mills, 1000G)
- `data/ref/vep_cache/` — pre-downloaded VEP cache
- `config/samplesheet.csv` — sample,fastq_1,fastq_2,sex (optional)

## Expected Outputs
- `results/alignment/` — sorted, deduped, BQSR BAMs
- `results/gvcf/` — per-sample GVCFs
- `results/vcf/` — joint-genotyped, filtered VCFs
- `results/annotation/` — VEP-annotated VCFs + summary stats
- `results/qc/` — Picard metrics + MultiQC HTML

## Know-How Reference
Load before starting: `@~/bioinformatics-knowhow/variant_calling.md`

## Notes
- VQSR requires ≥30 samples; use hard filters for smaller cohorts (thresholds in know-how doc)
- Pre-download VEP cache offline to avoid runtime failures on HPC
- WES: add `--intervals` BED file to all GATK tools
