---
name: spatial-enrichment
description: "Spatial gene set enrichment analysis mapping pathway activity scores onto
  tissue coordinates. Input: --input <.h5ad> --gene-sets <gmt_file_or_name> --output <dir>.
  Output: enrichment_scores.h5ad, spatial_pathway_plots.png."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-enrichment — Spatial Gene Set Enrichment

Score spatial spots for pathway or gene set activity using AUCell or decoupleR.

### When to use

- Mapping signaling pathway activity onto tissue
- Spatial visualization of hallmark gene sets
- Identifying spatially enriched biological processes

### Example

```bash
python3 spatial_enrichment.py --input preprocessed.h5ad --gene-sets MSigDB_Hallmarks --output results/enrichment/
python3 spatial_enrichment.py --input preprocessed.h5ad --gene-sets custom_pathways.gmt --output results/enrichment/
```
