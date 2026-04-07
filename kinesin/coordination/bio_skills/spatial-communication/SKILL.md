---
name: spatial-communication
description: "Spatially-aware cell-cell communication inference using CellChat or LIANA
  with spatial proximity constraints. Input: --input <annotated.h5ad> --output <dir>.
  Output: communication_network.json, interaction_chord_plot.png.
  User alias: spatial-cell-communication."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-communication — Spatial Cell-Cell Communication

Infer cell-cell communication ligand-receptor interactions with spatial proximity weighting.

### Capabilities

| Method | Notes |
|--------|-------|
| CellChat (spatial) | Weighted by physical distance |
| LIANA | Multi-database LR pairs, spatially aware |
| NicheNet | Ligand activity prioritization |

### When to use

- Tumor microenvironment signaling analysis
- Tissue niche communication patterns
- Spatially constrained signaling hypotheses

### When NOT to use

- scRNA-seq without coordinates (use sc-cell-communication)
- Bulk RNA-seq (no cell resolution)

### Example

```bash
python3 spatial_communication.py --input annotated.h5ad --output results/cell_communication/
```
