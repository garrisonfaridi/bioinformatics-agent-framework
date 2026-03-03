# Nextflow RNA-seq Template — Claude Context

## Purpose
Bulk RNA-seq pipeline: QC → alignment → quantification → differential expression.

## Key Tools (pin versions in nextflow.config)
- **fastp** ≥0.23 — adapter trimming and QC
- **STAR** ≥2.7.11 — splice-aware alignment (human/mouse)
- **salmon** ≥1.10 — quasi-mapping quantification
- **DESeq2** ≥1.42 (R/Bioconductor) — differential expression
- **MultiQC** ≥1.21 — aggregated QC report
- **nf-core/rnaseq** modules — use where available

## Expected Inputs
- `data/raw/` — paired-end FASTQ files (`*_R1.fastq.gz`, `*_R2.fastq.gz`)
- `data/ref/` — genome FASTA + GTF annotation
- `config/samplesheet.csv` — sample,fastq_1,fastq_2,strandedness
- `config/comparisons.csv` — condition pairs for DESeq2 contrasts

## Expected Outputs
- `results/qc/` — FastQC + fastp reports + MultiQC HTML
- `results/alignment/` — sorted BAMs + STAR logs
- `results/counts/` — salmon quant.sf files
- `results/deseq2/` — DE result tables, MA plots, volcano plots, heatmaps

## Know-How Reference
Load before starting: `@~/bioinformatics-knowhow/rnaseq.md`

## Notes
- Check strandedness with RSeQC `infer_experiment.py` on first sample before full run
- Use `--stub-run` to validate pipeline logic before real data
- Import salmon output via `tximeta` for correct offset handling
