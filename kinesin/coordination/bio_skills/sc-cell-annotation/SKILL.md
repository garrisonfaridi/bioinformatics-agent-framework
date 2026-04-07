---
name: sc-cell-annotation
description: "Cell type annotation for scRNA-seq clusters using marker genes or reference
  label transfer. Input: --input <clustered.h5ad> [--reference <ref.h5ad>] --output <dir>.
  Output: annotated.h5ad, cell_type_umap.png, marker_dotplot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-cell-annotation — scRNA-seq Cell Type Annotation

Annotate single-cell clusters with cell type labels using markers or reference transfer.

### Methods

| Method | Notes |
|--------|-------|
| Marker-based | CellMarker database or custom markers |
| scVI/scANVI | Reference label transfer |
| CellTypist | Automated, pre-trained models |

### When to use

- After clustering: assign biological identity to each cluster
- When CellTypist has a model for your tissue type

### Example

```bash
python3 sc_cell_annotation.py --input clustered.h5ad --output results/annotated/
python3 sc_cell_annotation.py --input clustered.h5ad --reference pbmc_reference.h5ad --output results/
```
