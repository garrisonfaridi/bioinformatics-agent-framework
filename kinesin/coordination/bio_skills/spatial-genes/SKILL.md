---
name: spatial-genes
description: "Detection of spatially variable genes (SVGs) in spatial transcriptomics data
  using SpatialDE, SPARK, or Moran's I. Input: --input <processed.h5ad> --output <dir>.
  Output: spatially_variable_genes.csv, svg_plot.png. User alias: spatial-svg-detection."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-genes — Spatially Variable Gene Detection

Identify genes with significant spatial expression patterns (spatially variable genes, SVGs).

### Capabilities

| Method | Notes |
|--------|-------|
| SpatialDE | Gaussian process, well-validated |
| SPARK | Faster, handles large datasets |
| Moran's I | Simple autocorrelation, no DL deps |

### When to use

- Discovering genes with spatial structure before DE analysis
- Identifying tissue-specific marker genes
- Input for spatial trajectory or communication analysis

### Example

```bash
python3 spatial_genes.py --input preprocessed.h5ad --output results/svg/
python3 spatial_genes.py --input preprocessed.h5ad --method morans_i --output results/svg/
```
