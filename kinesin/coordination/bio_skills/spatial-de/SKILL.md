---
name: spatial-de
description: "Differential expression between spatial domains or conditions in spatial
  transcriptomics. Input: --input <annotated.h5ad> --contrast <domainA_vs_domainB or
  conditionA_vs_conditionB> --output <dir>. Output: spatial_de_results.csv, volcano_plot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-de — Spatial Differential Expression

Test for DE genes between spatial domains, tissue regions, or experimental conditions.

### Capabilities

| Comparison | Method |
|-----------|--------|
| Domain A vs Domain B | Wilcoxon rank-sum or DESeq2 pseudo-bulk |
| Condition A vs B (within domain) | Mixed model |
| Spatial gradient | Moran's I + LR test |

### When to use

- After spatial-domains/spatial-annotate: compare expression between regions
- Identifying region-specific marker genes
- Spatial condition comparisons (treated vs control tissue sections)

### Example

```bash
python3 spatial_de.py --input annotated.h5ad --contrast "tumor_core_vs_margin" --output results/spatial_de/
```
