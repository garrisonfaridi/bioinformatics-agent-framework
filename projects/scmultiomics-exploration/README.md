# scRNA-seq + Multi-Omics Exploration

Personal learning project. Goal: use biomni to autonomously generate and execute
scRNA-seq and multi-omics analyses from vague inputs.

## Directory Structure

```
data/        — raw or downloaded input data (FASTQs, count matrices, h5ad files)
results/     — biomni and pipeline outputs
logs/        — execution logs
scripts/     — any custom scripts generated during analysis
notebooks/   — Jupyter notebooks for exploration
```

## Running biomni on this project

From this directory:
```bash
cd ~/bioinformatics-freelance/projects/scmultiomics-exploration
python ~/bioinformatics-freelance/biomni_run.py "your analysis description here"
```

Results will be written to `./results/`.

## Example starter prompts

```
"Download a public human PBMC scRNA-seq dataset and perform full QC, clustering, and cell type annotation"

"Suggest a multi-omics analysis strategy for studying T cell activation and execute it on a suitable public dataset"

"Find a 10x Multiome (RNA + ATAC) dataset, download it, and run a joint chromatin accessibility and gene expression analysis"

"Identify the best publicly available scRNA-seq dataset for studying tumor microenvironment and begin analysis"
```

## Modalities of interest

- scRNA-seq (gene expression)
- scATAC-seq (chromatin accessibility)
- CITE-seq (surface proteomics)
- Spatial transcriptomics
- Multi-omics integration (MOFA+, WNN, muon)
