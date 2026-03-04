---
last_verified: 2026-03-04
tool_versions:
  scanpy: "1.12"
  anndata: "0.12.10"
  seurat: "5.0.0"
  harmony: "1.2.0"
  scvi-tools: "1.1.0"
  cellranger: "8.0.0"
---

# Single-Cell RNA-seq Know-How

## QC Thresholds (adjust per dataset)

| Metric | Typical range | Flag if |
|--------|--------------|---------|
| nCount_RNA | 500–50,000 | <200 (empty) or >80k (doublet) |
| nFeature_RNA | 200–8,000 | <200 or >10k |
| pct_mito | <20% (human) <10% (mouse) | >25% (dying cells) |
| pct_ribo | 5–50% | Depends on cell type; note but rarely filter |

Use `scDblFinder` or `DoubletFinder` for doublet detection before downstream analysis.

## Normalization Choices

- **LogNormalize** (Seurat default): `NormalizeData(normalization.method="LogNormalize", scale.factor=1e4)` — fast, adequate for most
- **scran pooling**: better for datasets with very unequal library sizes; use `computeSumFactors()`
- **SCTransform v2**: regularized NB regression; handles sequencing depth better; use for integrations

## Highly Variable Genes (HVG)

- Seurat: `FindVariableFeatures(nfeatures=2000–3000, selection.method="vst")`
- scanpy: `sc.pp.highly_variable_genes(n_top_genes=2000, flavor="seurat_v3")`
- Exclude MT/RP genes from HVG list before PCA

## Clustering Resolution

- Start at `resolution=0.5`; sweep 0.2–2.0 and assess with `clustree`
- Biological sanity check: known marker genes must separate expected populations
- Over-clustering preferred → merge later with marker evidence

## Cell Type Annotation

- **Automated**: `SingleR` (R) with HumanPrimaryCellAtlasData or celldex references; `sc.tl.ingest` (scanpy)
- **Manual**: `FindAllMarkers(only.pos=TRUE, min.pct=0.25, logfc.threshold=0.25)` → cross-ref CellMarker/PanglaoDB
- Always validate automated labels with marker dot plots

## Trajectory / Pseudotime

- **RNA velocity**: scVelo (Python); requires spliced/unspliced counts from STARsolo or velocyto
- **Pseudotime**: Monocle3 (R) or PAGA + diffusion pseudotime (scanpy)
- Only apply if biological question involves differentiation/dynamics

## Integration

- **Harmony**: fast, good for same-species/platform batches; `RunHarmony(group.by.vars="sample")`
- **scVI**: deep learning; best for large atlas-scale (>100k cells)
- **Seurat CCA/RPCA**: RPCA preferred for large datasets

---

## Multi-Omics Extensions

### Modality combinations

| Assay | Modalities | Key tool |
|-------|-----------|----------|
| 10x Multiome | RNA + ATAC | Seurat WNN, ArchR + Seurat, muon |
| CITE-seq | RNA + surface protein | Seurat WNN (protein + RNA) |
| Spatial | RNA + spatial coords | Squidpy, Seurat |
| SHARE-seq / SNARE-seq | RNA + ATAC | SnapATAC2, muon |

### scATAC-seq QC thresholds

| Metric | Flag if |
|--------|---------|
| TSS enrichment | <4 (human), <6 (high quality) |
| Nucleosome signal | >4 (poor fragment size distribution) |
| Unique fragments | <1,000 |
| Fraction reads in peaks (FRiP) | <0.15 |

### Multi-omics integration frameworks

- **Seurat WNN** (R): weighted nearest-neighbour integrates any two modalities; `FindMultiModalNeighbors()`
- **muon** (Python): AnnData-based multi-omics; stores modalities as `.mod['rna']`, `.mod['atac']`; `muu.pp.intersect_obs()`
- **MOFA+**: factor analysis across modalities; identifies latent factors driving variance; works with R or Python
- **ArchR** (R): gold-standard scATAC-seq; integrates with Seurat via `addGeneIntegrationMatrix()`

### Typical 10x Multiome workflow (RNA + ATAC)

```
1. Alignment: cellranger-arc (joint RNA + ATAC)
2. QC: filter on both RNA and ATAC metrics independently
3. RNA processing: standard Seurat/scanpy pipeline
4. ATAC processing: ArchR or Signac — TF-IDF, SVD, peak calling (MACS2)
5. Integration: Seurat WNN or muon
6. Joint UMAP on WNN graph
7. Annotation: transfer labels from RNA to ATAC peaks
8. TF motif enrichment: chromVAR (per cluster)
```

### Key public datasets for learning

| Dataset | Modalities | Source | Size |
|---------|-----------|--------|------|
| PBMC 3k | scRNA-seq | 10x Genomics | ~100 MB |
| PBMC 10k Multiome | RNA + ATAC | 10x Genomics | ~2 GB |
| Human Cell Atlas PBMC | scRNA-seq | cellxgene | varies |
| 10x PBMC CITE-seq | RNA + protein | 10x Genomics | ~500 MB |

### Python multi-omics stack

```python
import muon as mu
import scanpy as sc
import anndata as ad

mdata = mu.read_10x_h5("filtered_feature_bc_matrix.h5")
mu.pp.intersect_obs(mdata)  # keep cells present in all modalities
```
