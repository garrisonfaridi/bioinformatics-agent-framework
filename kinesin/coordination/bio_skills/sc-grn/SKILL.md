---
name: sc-grn
description: "Gene regulatory network inference from scRNA-seq using SCENIC or GRNBoost2.
  Input: --input <.h5ad> --output <dir>. Output: regulons.json, grn_network.csv,
  regulon_activity_heatmap.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-grn — Gene Regulatory Network Inference

Infer transcription factor regulons and gene regulatory networks from single-cell RNA-seq.

### Methods

| Method | Notes |
|--------|-------|
| SCENIC (pySCENIC) | TF → target gene regulons |
| GRNBoost2 | Fast tree-based GRN |
| CellOracle | TF perturbation simulation |

### When to use

- Identifying master regulators driving cell identity
- TF activity analysis for differentiation studies
- Linking GWAS TF hits to downstream targets

### Example

```bash
python3 sc_grn.py --input annotated.h5ad --output results/grn/
```
