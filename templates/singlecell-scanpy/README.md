# [Project Title] — Single-Cell RNA-seq Analysis (scanpy)

## Description

[2–3 sentence description of the project, client, biological question, tissue/cell type, and number of samples/cells.]

## Requirements

- Python 3.11+
- conda/mamba — install environment: `conda env create -f environment.yml`
- ≥64 GB RAM recommended for large datasets (>100k cells)

## Usage

```bash
# 1. Activate environment
conda activate sc-scanpy

# 2. Edit config
cp config/config.yaml.template config/config.yaml

# 3. Run notebooks in order
jupyter lab
# 01_qc.ipynb → 02_normalization.ipynb → 03_clustering.ipynb → 04_annotation.ipynb

# OR run as scripts
python scripts/01_qc.py
python scripts/02_normalization.py
python scripts/03_clustering.py
python scripts/04_annotation.py
```

## Inputs

| File/Directory | Description |
|----------------|-------------|
| `data/raw/{sample}/` | Cell Ranger output (barcodes, features, matrix) |
| `config/config.yaml` | Sample metadata, QC thresholds, resolution |

## Outputs

| Directory | Contents |
|-----------|----------|
| `results/qc/` | Violin plots, scatter plots, doublet scores |
| `results/processed/` | `adata_processed.h5ad` |
| `results/clustered/` | `adata_clustered.h5ad`, UMAP plots |
| `results/annotation/` | Cell type labels, dot plots, marker tables |
| `results/figures/` | All publication-ready figures |

## Methods

See `METHODS.md` for publishable methods text.

## Contact

[Your name] — [email]
