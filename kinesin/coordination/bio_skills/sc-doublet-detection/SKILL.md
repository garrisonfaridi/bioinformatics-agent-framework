---
name: sc-doublet-detection
description: "Doublet detection in scRNA-seq data using Scrublet or DoubletFinder.
  Input: --input <.h5ad> --output <dir> [--expected-doublet-rate <float>].
  Output: doublet_scores.h5ad (obs column added), doublet_summary.csv."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-doublet-detection — Doublet Detection

Identify and flag likely doublets (two cells captured together) in scRNA-seq data.

### Methods

| Tool | Notes |
|------|-------|
| Scrublet | Fast, simulation-based |
| DoubletFinder | KNN-based, needs pre-clustering |

### When to use

- Standard QC step after initial filtering, before clustering
- When dropout rate is high (>5%) or library preparation is microfluidic

### Example

```bash
python3 sc_doublet_detection.py --input filtered.h5ad --output results/doublet_detection/
python3 sc_doublet_detection.py --input filtered.h5ad --expected-doublet-rate 0.06 --output results/
```
