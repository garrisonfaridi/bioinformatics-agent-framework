---
name: spatial-integrate
description: "Integration of multiple spatial transcriptomics datasets (same or different
  platforms). Input: --input <sample1.h5ad,sample2.h5ad,...> --method <harmony|scvi|bbknn>
  --output <dir>. Output: integrated.h5ad, integration_umap.png.
  User alias: spatial-integration."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-integrate — Spatial Dataset Integration

Integrate multiple spatial transcriptomics slides or platforms into a joint embedding.

### Methods

| Method | Notes |
|--------|-------|
| Harmony | Fast, works on PCA embedding |
| scVI | Deep learning, handles batch well |
| BBKNN | Graph-based, scalable |

### When to use

- Multi-slide spatial analysis (different sections or patients)
- Cross-platform integration (Visium + Slide-seq)
- Batch correction before domain calling

### Example

```bash
python3 spatial_integrate.py \
  --input "slide1.h5ad,slide2.h5ad,slide3.h5ad" \
  --method harmony \
  --output results/integrated/
```
