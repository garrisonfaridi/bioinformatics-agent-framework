---
name: spatial-velocity
description: "RNA velocity analysis for spatial transcriptomics data using scVelo with
  spatial embedding. Input: --input <.h5ad with spliced/unspliced> --output <dir>.
  Output: velocity.h5ad, velocity_embedding_plot.png, velocity_confidence.csv."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-velocity — Spatial RNA Velocity

Compute RNA velocity for spatial transcriptomics data to infer differentiation trajectories
in tissue context.

### Requirements

- Spliced/unspliced count matrices (from STARsolo or velocyto)
- scVelo installed

### When to use

- Inferring differentiation directionality in spatial context
- Identifying source/sink regions in tissue sections
- Validating trajectory inference with spatial context

### Example

```bash
python3 spatial_velocity.py --input spliced_unspliced.h5ad --output results/velocity/
```
