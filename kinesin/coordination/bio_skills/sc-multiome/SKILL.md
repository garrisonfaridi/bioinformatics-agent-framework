---
name: sc-multiome
description: "Joint analysis of paired scRNA-seq and scATAC-seq (10x Multiome) data.
  Input: --rna <rna.h5ad> --atac <atac.h5ad> [--fragments <fragments.tsv.gz>] --output <dir>.
  Output: multiome.h5ad, joint_umap.png, peak_gene_links.csv.
  Note: Stub if sc-multiome not present in OmicsClaw; functional placeholder."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## sc-multiome — Single-Cell Multiome (RNA + ATAC)

Joint analysis of scRNA-seq and scATAC-seq from 10x Genomics Multiome or paired experiments.

### Capabilities

| Task | Output |
|------|--------|
| Joint embedding | WNN (Weighted Nearest Neighbor) UMAP |
| Peak-gene links | Regulatory element → gene correlations |
| TF binding activity | ChromVAR motif scores |
| Cluster annotation | Combined RNA + ATAC labels |

### When to use

- 10x Multiome data (paired RNA+ATAC per cell)
- Linking regulatory elements to gene expression
- Chromatin accessibility + expression integration

### Note

This skill is a stub. If OmicsClaw sc-multiome skill directory is not present in the repo,
this stub provides the full argparse interface. Install omicsclaw[singlecell] for the
full implementation if available.

### Example

```bash
python3 sc_multiome.py --rna rna.h5ad --atac atac.h5ad --output results/multiome/
python3 sc_multiome.py --rna rna.h5ad --atac atac.h5ad --fragments fragments.tsv.gz --output results/
```
