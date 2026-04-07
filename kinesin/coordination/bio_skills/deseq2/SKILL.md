---
name: deseq2
description: "Differential expression analysis using DESeq2 (R/Bioconductor) via subprocess.
  Input: --counts <counts.csv> --metadata <metadata.csv> --contrast <treatment vs control>
  --output <dir>. Output: deseq2_results.csv (log2FC, padj), MA_plot.png, volcano_plot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## deseq2 — Differential Expression Analysis

Run DESeq2 on a raw count matrix to identify differentially expressed genes between conditions.

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| Two-group DE | counts.csv + metadata.csv | deseq2_results.csv, MA_plot.png |
| Multi-factor | counts.csv + metadata.csv (multiple cols) | deseq2_results.csv per contrast |
| Shrinkage | lfcShrink via apeglm | shrunken_results.csv |

### Requirements

- R ≥ 4.3 with DESeq2, apeglm, ggplot2 installed
- Input: raw integer counts (not normalized TPM/FPKM)

### When to use

- Bulk RNA-seq differential expression
- ATAC-seq peak differential accessibility (with raw counts)
- Spatial transcriptomics DE between regions

### When NOT to use

- scRNA-seq (use sc-de skill with Wilcoxon/MAST)
- Microarray data (use limma skill)
- Already-normalized data

### Example

```bash
python3 run_deseq2.py \
  --counts counts_matrix.csv \
  --metadata sample_metadata.csv \
  --contrast "treatment:drug_vs_control" \
  --output results/deseq2/
```
