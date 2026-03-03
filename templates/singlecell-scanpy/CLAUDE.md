# Single-Cell RNA-seq (scanpy) Template — Claude Context

## Purpose
scRNA-seq analysis in Python: QC → normalization → clustering → annotation → visualization.

## Key Tools (pin versions in environment.yml)
- **Python** 3.11+
- **scanpy** ≥1.10 — core single-cell analysis framework
- **anndata** ≥0.10 — data structure
- **scran** (via rpy2 or scran Python) — pooling-based normalization
- **scDblFinder** (via rpy2) or **scrublet** — doublet detection
- **cellxgene** ≥1.1 — interactive exploration

## Expected Inputs
- `data/raw/` — Cell Ranger output dirs (barcodes.tsv.gz, features.tsv.gz, matrix.mtx.gz)
  OR pre-built AnnData `.h5ad` files
- `config/config.yaml` — sample metadata, QC thresholds, clustering resolution

## Expected Outputs
- `results/qc/` — violin plots, scatter plots, doublet scores
- `results/processed/` — `adata_processed.h5ad` (post-QC, normalized, HVG, PCA)
- `results/clustered/` — `adata_clustered.h5ad` (UMAP, Louvain clusters)
- `results/annotation/` — marker gene dot plots, cell type labels
- `results/figures/` — publication-ready matplotlib/seaborn figures

## Know-How Reference
Load before starting: `@~/bioinformatics-knowhow/singlecell.md`

## Notes
- Set `random_state=42` for all stochastic steps (PCA, UMAP, neighbors)
- Always run `sc.pp.scrublet()` or scDblFinder before QC filtering
- Use `sc.settings.figdir` to redirect all figure output to `results/figures/`
- Python 3.11 required; avoid 3.12+ until scanpy dependencies catch up
