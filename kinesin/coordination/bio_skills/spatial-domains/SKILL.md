---
name: spatial-domains
description: "Spatial domain identification in spatial transcriptomics data using graph-based
  or deep learning methods. Input: --input <processed.h5ad> --output <dir>. Output: domains.h5ad,
  domain_plot.png, report.md. Falls back to Leiden clustering if SpaGCN/STAGATE/torch not
  installed; emits WARNING to trace log. Install DL support: pip install omicsclaw[spatial-domains]"
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-domains — Spatial Domain Identification

Identify spatially coherent tissue domains using SpaGCN, STAGATE, or Leiden clustering fallback.

### Capabilities

| Method | Requirements | Notes |
|--------|-------------|-------|
| SpaGCN | torch, SpaGCN | Graph convolutional, uses histology image |
| STAGATE | torch, STAGATE | Attention-based spatial domain |
| Leiden (fallback) | scanpy only | Always available; less spatially aware |

### Dependency note

SpaGCN and STAGATE require `pip install omicsclaw[spatial-domains]` (includes torch).
Without them, skill falls back to Leiden clustering and emits a WARNING to the trace log.
The --demo flag always runs Leiden fallback path.

### When to use

- Identifying tissue layers, tumor microenvironment zones
- Spatially coherent cell type niches
- Prior to spatial DE between domains

### When NOT to use

- Cell type annotation (use spatial-annotate after domains)
- Single-cell data without spatial coordinates

### Example

```bash
python3 spatial_domains.py --input preprocessed.h5ad --output results/domains/
python3 spatial_domains.py --input preprocessed.h5ad --method leiden --output results/domains/
```
