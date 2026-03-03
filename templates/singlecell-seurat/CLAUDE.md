# Single-Cell RNA-seq (Seurat v5) Template — Claude Context

## Purpose
scRNA-seq analysis in R: QC → normalization → clustering → annotation → integration.

## Key Tools (pin versions in renv.lock or sessionInfo snapshot)
- **R** 4.3+
- **Seurat** v5 — core single-cell analysis
- **SingleR** ≥2.4 — automated cell type annotation
- **harmony** ≥1.2 — batch correction / integration
- **scDblFinder** ≥1.16 — doublet detection
- **ggplot2**, **patchwork**, **pheatmap** — visualization

## Expected Inputs
- `data/raw/` — Cell Ranger output dirs (10x format)
  OR pre-built Seurat RDS objects
- `config/config.R` — sample list, QC thresholds, resolution, contrast metadata

## Expected Outputs
- `results/qc/` — VlnPlots, FeatureScatter, doublet score plots
- `results/processed/` — `seurat_processed.rds` (post-QC, normalized, HVG, PCA)
- `results/clustered/` — `seurat_clustered.rds` (UMAP, Seurat clusters)
- `results/annotation/` — DotPlots, SingleR heatmaps, UMAP colored by cell type
- `results/de/` — FindAllMarkers output tables

## Know-How Reference
Load before starting: `@~/bioinformatics-knowhow/singlecell.md`

## Notes
- Use `set.seed(42)` before FindNeighbors, RunUMAP, and any stochastic step
- Prefer `SCTransform(vst.flavor="v2")` over LogNormalize for integration
- `renv::init()` + `renv::snapshot()` for reproducible R package versions
- For large datasets (>100k cells), use RPCA integration instead of CCA
