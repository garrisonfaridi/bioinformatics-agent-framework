---
name: spatial-trajectory
description: "Spatial trajectory inference to reconstruct developmental or differentiation
  paths in tissue context. Input: --input <.h5ad> --output <dir> [--root <cell_type>].
  Output: trajectory.h5ad, pseudotime_spatial_plot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-trajectory — Spatial Trajectory Inference

Reconstruct cell state trajectories in spatial context using Monocle3 or Palantir with spatial coordinates.

### When to use

- Mapping developmental progression across tissue space
- Identifying spatial routes of differentiation
- Validating trajectory with tissue morphology

### Example

```bash
python3 spatial_trajectory.py --input annotated.h5ad --root "progenitor" --output results/trajectory/
```
