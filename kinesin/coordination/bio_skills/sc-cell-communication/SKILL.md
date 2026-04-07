---
name: sc-cell-communication
description: "Cell-cell communication inference from scRNA-seq using CellChat or LIANA.
  Input: --input <annotated.h5ad> --output <dir>. Output: communication_results.csv,
  interaction_chord_plot.png, bubble_plot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-cell-communication — scRNA-seq Cell-Cell Communication

Infer ligand-receptor interactions between cell types from single-cell RNA-seq data.

### Methods

| Tool | Database | Notes |
|------|----------|-------|
| CellChat | CellChat LR DB | Signaling pathway groups |
| LIANA | CellPhoneDB, NicheNet, etc. | Multi-database consensus |
| CellPhoneDB | CellPhoneDB | Statistical permutation |

### When to use

- Tumor microenvironment signaling analysis
- Immune cell crosstalk in disease
- Identifying therapeutic targets in cell communication

### When NOT to use

- Spatial data with proximity constraints (use spatial-communication)

### Example

```bash
python3 sc_cell_communication.py --input annotated.h5ad --output results/cell_communication/
```
