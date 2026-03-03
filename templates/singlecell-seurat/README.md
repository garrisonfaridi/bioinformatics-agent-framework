# [Project Title] — Single-Cell RNA-seq Analysis (Seurat v5)

## Description

[2–3 sentence description of the project, client, biological question, tissue/cell type, and number of samples/cells.]

## Requirements

- R 4.3+
- renv — restore environment: `renv::restore()`
- ≥64 GB RAM recommended for large datasets (>100k cells)

## Usage

```r
# 1. Restore R environment
renv::restore()

# 2. Edit config
# Modify config/config.R with sample paths and parameters

# 3. Run scripts in order
source("scripts/01_qc.R")
source("scripts/02_normalization.R")
source("scripts/03_clustering.R")
source("scripts/04_annotation.R")
```

## Inputs

| File/Directory | Description |
|----------------|-------------|
| `data/raw/{sample}/` | Cell Ranger output (10x format) |
| `config/config.R` | Sample list, QC thresholds, clustering resolution |

## Outputs

| Directory | Contents |
|-----------|----------|
| `results/qc/` | VlnPlots, FeatureScatter, doublet score plots |
| `results/processed/` | `seurat_processed.rds` |
| `results/clustered/` | `seurat_clustered.rds`, UMAP plots |
| `results/annotation/` | Cell type labels, SingleR heatmaps, marker DotPlots |
| `results/de/` | FindAllMarkers tables (per cluster) |

## Methods

See `METHODS.md` for publishable methods text.

## Contact

[Your name] — [email]
