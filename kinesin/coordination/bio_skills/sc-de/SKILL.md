---
name: sc-de
description: "Differential expression analysis for scRNA-seq using Wilcoxon rank-sum or
  MAST. Input: --input <annotated.h5ad> --contrast <celltype:condA_vs_condB> --output <dir>.
  Output: sc_de_results.csv (log2FC, padj), volcano_plot.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-de — scRNA-seq Differential Expression

Test for DE genes between cell types or conditions in single-cell RNA-seq data.

### Methods

| Method | Notes |
|--------|-------|
| Wilcoxon | Fast, recommended for cell type DE |
| MAST | Hurdle model, accounts for dropout |
| Pseudo-bulk | DESeq2 on aggregated counts per donor |

### When to use

- Identifying cell-type-specific DE genes across conditions
- Marker gene discovery between clusters
- Client needs DEGs for downstream pathway analysis

### When NOT to use

- Bulk RNA-seq (use deseq2 skill)
- Spatial DE between domains (use spatial-de skill)

### Example

```bash
python3 sc_de.py --input annotated.h5ad --contrast "T_cells:treatment_vs_control" --output results/sc_de/
```
