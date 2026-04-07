---
name: sc-pseudotime
description: "Pseudotime / trajectory inference for scRNA-seq using Monocle3, Palantir, or
  PAGA. Input: --input <annotated.h5ad> [--root <cell_type>] --output <dir>.
  Output: trajectory.h5ad, pseudotime_umap.png. User alias: sc-trajectory."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-pseudotime — scRNA-seq Trajectory / Pseudotime

Reconstruct developmental or differentiation trajectories from scRNA-seq data.

### Methods

| Method | Notes |
|--------|-------|
| Monocle3 | Graph-based, reversible |
| Palantir | Probabilistic, multi-lineage |
| PAGA | Graph abstraction, scalable |

### When to use

- Developmental biology: inferring progenitor → mature cell paths
- Identifying intermediate cell states
- Time-course experiments without actual time labels

### Example

```bash
python3 sc_pseudotime.py --input annotated.h5ad --root "stem_cell" --output results/trajectory/
python3 sc_pseudotime.py --input annotated.h5ad --method palantir --output results/trajectory/
```
