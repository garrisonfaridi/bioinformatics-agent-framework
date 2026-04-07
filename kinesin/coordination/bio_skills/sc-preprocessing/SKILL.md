---
name: sc-preprocessing
description: "Quality control, filtering, normalization, and dimensionality reduction for
  single-cell RNA-seq data. Input: --input <raw.h5ad or 10x dir> --output <dir>.
  Output: processed.h5ad, qc_report.md, figures/. Handles 10x Genomics, Smart-seq2, Drop-seq."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-preprocessing — scRNA-seq Preprocessing

Standard preprocessing pipeline for scRNA-seq: QC → normalization → HVG → PCA → UMAP.

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| QC filtering | raw .h5ad or 10x dir | QC metrics, filtered cells |
| Normalization | filtered cells | log-normalized counts |
| Dimensionality reduction | normalized | PCA, UMAP, neighbors graph |

### Formats supported

- 10x Genomics (CellRanger output directory)
- .h5ad (AnnData)
- .loom

### Example

```bash
python3 sc_preprocessing.py --input raw_counts.h5ad --output results/preprocessed/
python3 sc_preprocessing.py --input cellranger_output/ --output results/preprocessed/
```
