---
name: spatial-annotate
description: "Cell type annotation of spatial transcriptomics data using marker gene databases
  or reference single-cell datasets. Input: --input <domains.h5ad> [--reference <sc.h5ad>]
  --output <dir>. Output: annotated.h5ad, annotation_plot.png, cell_type_fractions.csv."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-annotate — Spatial Cell Type Annotation

Annotate spatial spots/bins with cell type labels using marker genes or reference scRNA-seq transfer.

### Capabilities

| Method | Input | Notes |
|--------|-------|-------|
| Marker-based | domains.h5ad + marker list | Manual or CellMarker database |
| Reference transfer | domains.h5ad + sc reference | Label transfer via scVI/Seurat anchor |
| Decoupler | domains.h5ad | Transcription factor activity scores |

### When to use

- After spatial-domains: label each domain with cell type identity
- When reference scRNA-seq atlas is available for the tissue

### When NOT to use

- Without prior domain identification (run spatial-domains first)
- Deconvolving mixed spots (use spatial-deconv instead)

### Example

```bash
python3 spatial_annotate.py --input domains.h5ad --output results/annotated/
python3 spatial_annotate.py --input domains.h5ad --reference sc_reference.h5ad --output results/annotated/
```
