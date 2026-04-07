---
name: spatial-cnv
description: "Copy number variation inference from spatial transcriptomics data using
  inferCNV or CopyKAT. Input: --input <.h5ad> [--reference <normal_cells_annotation>]
  --output <dir>. Output: cnv_map.h5ad, cnv_spatial_heatmap.png, tumor_normal_calls.csv."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-cnv — Spatial Copy Number Variation

Infer somatic copy number alterations from spatial transcriptomics to map tumor heterogeneity.

### When to use

- Cancer spatial transcriptomics: mapping tumor subclones
- Identifying CNV-driven spatial patterns
- Distinguishing tumor from normal cells in tissue sections

### Example

```bash
python3 spatial_cnv.py --input cancer_visium.h5ad --reference "normal_epithelial" --output results/cnv/
```
