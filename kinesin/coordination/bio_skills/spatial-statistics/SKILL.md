---
name: spatial-statistics
description: "Spatial statistics for transcriptomics data: Moran's I, Ripley's K, spatial
  autocorrelation, and co-localization. Input: --input <.h5ad> --output <dir>. Output:
  spatial_stats.csv, morans_i_plot.png, autocorrelation_report.md."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-statistics — Spatial Statistics

Compute spatial statistics to assess spatial structure and gene co-localization patterns.

### Capabilities

| Statistic | Purpose |
|-----------|---------|
| Moran's I | Global spatial autocorrelation per gene |
| Ripley's K | Point pattern analysis (cell clustering) |
| Spatial lag | Neighbor gene expression correlation |
| Co-localization | Cell type co-occurrence patterns |

### When to use

- Quantifying spatial structure before domain calling
- Testing whether cell types co-localize or exclude
- Hypothesis testing for spatial gene expression patterns

### Example

```bash
python3 spatial_statistics.py --input preprocessed.h5ad --output results/spatial_stats/
```
