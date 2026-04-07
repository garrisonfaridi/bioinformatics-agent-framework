---
name: spatial-deconv
description: "Deconvolution of spatial transcriptomics spots into cell type proportions
  using RCTD, Cell2location, or NNLS. Input: --spatial <.h5ad> --reference <sc.h5ad>
  --output <dir>. Output: deconv_proportions.csv, composition_plot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-deconv — Spatial Deconvolution

Estimate cell type proportions within each spatial spot/bin from bulk-like spot transcriptomes.

### Capabilities

| Method | Input | Notes |
|--------|-------|-------|
| RCTD | spatial + scRNA reference | Robust cross-technology |
| Cell2location | spatial + scRNA reference | Bayesian, full uncertainty |
| NNLS | spatial + signature matrix | Lightweight, no DL required |

### When to use

- Visium spots contain multiple cell types (typical ~1-10 cells/spot)
- Characterizing tumor microenvironment composition
- Validating domain annotations with deconvolution

### When NOT to use

- Single-cell resolution spatial data (Slide-seq v2, Stereo-seq) — use spatial-annotate
- When no scRNA-seq reference is available

### Example

```bash
python3 spatial_deconv.py --spatial visium.h5ad --reference scrnaseq_ref.h5ad --output results/deconv/
```
