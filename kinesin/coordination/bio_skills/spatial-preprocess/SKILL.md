---
name: spatial-preprocess
description: "QC filtering, normalization, HVG selection, and dimensionality reduction for
  spatial transcriptomics data. Input: --input <.h5ad> --output <dir>. Output: processed.h5ad,
  report.md, figures/. Optional: --tissue <preset> --leiden-resolution <float>."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-preprocess — Spatial Transcriptomics Preprocessing

QC and normalization pipeline for spatial transcriptomics data (Visium, Slide-seq, MERFISH, etc.).

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| QC filtering | .h5ad (raw counts) | QC metrics, filtered spots |
| Normalization | filtered .h5ad | log-normalized counts |
| HVG selection | normalized .h5ad | top HVGs for downstream |
| Dimensionality reduction | HVG matrix | PCA, UMAP embeddings |

### When to use

- First step for any spatial transcriptomics analysis
- Raw Visium/Space Ranger output needs preprocessing
- Integrating multiple spatial slides

### When NOT to use

- scRNA-seq data without spatial coordinates (use sc-preprocessing)
- Already-normalized data (skip to spatial-domains or spatial-genes)

### Example

```bash
python3 spatial_preprocess.py --input raw_visium.h5ad --output results/preprocessed/
python3 spatial_preprocess.py --input raw_visium.h5ad --tissue brain --output results/preprocessed/
```
