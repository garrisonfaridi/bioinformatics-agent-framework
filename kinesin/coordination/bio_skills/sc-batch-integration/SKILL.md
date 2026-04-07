---
name: sc-batch-integration
description: "Batch effect correction and integration of multiple scRNA-seq datasets using
  Harmony, scVI, or BBKNN. Input: --input <.h5ad with batch column> --batch-key <col>
  --output <dir>. Output: integrated.h5ad, integration_umap.png, batch_mixing_score.csv."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-batch-integration — scRNA-seq Batch Integration

Correct technical batch effects and integrate scRNA-seq datasets from multiple experiments.

### Methods

| Method | Notes |
|--------|-------|
| Harmony | Fast, linear correction on PCA |
| scVI | Deep learning, preserves biology well |
| BBKNN | Graph-based, scalable |
| scANVI | Semi-supervised, uses cell type labels |

### When to use

- Merging datasets from multiple sequencing runs or labs
- Atlas-building from heterogeneous sources
- Multi-patient cohort analysis

### Example

```bash
python3 sc_batch_integration.py --input merged.h5ad --batch-key "batch" --method harmony --output results/integrated/
python3 sc_batch_integration.py --input merged.h5ad --batch-key "patient_id" --method scvi --output results/integrated/
```
