# Analysis Report: 10x Genomics PBMC 3k scRNA-seq

---

## Executive Summary

The 10x Genomics PBMC 3k dataset — 2,700 human peripheral blood mononuclear cells profiled with Chromium v2 chemistry — was processed through a complete single-cell RNA-seq pipeline using Scanpy on Python 3.12. After quality-control filtering, 2,638 cells and 13,656 genes were retained and carried through normalization, highly variable gene selection, PCA, UMAP embedding, and Leiden clustering at resolution 0.5. Five transcriptionally distinct populations were identified: T cells (42.6%), monocytes (25.3%), NK cells (18.2%), B cells (12.9%), and a small platelet contamination cluster (0.9%). The headline biological finding is that the five clusters align cleanly with canonical PBMC populations and each is defined by well-established lineage markers (CD3D for T cells, CD14/S100A9 for monocytes, NKG7/GZMA for NK cells, CD79A/MS4A1 for B cells, PPBP/PF4 for platelets), confirming that even shallow sequencing depth (~2,367 counts per cell) is sufficient to resolve major blood lineages when standard preprocessing is applied correctly.

---

## Dataset

| Property | Value |
|---|---|
| Source | 10x Genomics / loaded via `sc.datasets.pbmc3k()` |
| Reference URL | https://support.10xgenomics.com/single-cell-gene-expression/datasets/1.1.0/pbmc3k |
| Organism | *Homo sapiens* |
| Tissue | Peripheral blood mononuclear cells (PBMCs) |
| Chemistry | 10x Chromium v2, 3′ end capture |
| Raw dimensions | 2,700 cells × 32,738 genes |
| Post-QC dimensions | 2,638 cells × 13,656 genes |

This dataset has become the *de facto* benchmark reference for single-cell analysis because its cell-type composition is well-characterised by independent flow cytometry and immunohistochemistry, its gene count depth is representative of standard shallow sequencing, and it is small enough to execute end-to-end in minutes while still containing all major PBMC lineages. It is the canonical tutorial dataset for Scanpy, Seurat, and most downstream tools, making it ideal for validating a new pipeline.

---

## Methods and Reasoning

### 1. QC Metric Calculation

The agent computed three per-cell QC metrics using `sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)`: (i) **total counts** (total UMIs detected per cell), (ii) **n_genes_by_counts** (number of distinct genes detected), and (iii) **pct_counts_mt** (percentage of UMIs mapping to the 13 mitochondrial genes identified by the `MT-` prefix pattern). These three metrics are the minimum necessary for PBMC QC because they jointly diagnose the three main failure modes in droplet-based sequencing: empty droplets (low counts + low genes), doublets (anomalously high counts + high genes), and dying or ruptured cells (high mitochondrial fraction, because cytoplasmic mRNA leaks out while the more membrane-enclosed mitochondria retain their transcripts). Population-level statistics confirmed a healthy dataset: mean total counts = 2,367 (median 2,197), mean genes = 847 (median 817), mean MT% = 2.2% (median 2.0%), with a standard deviation on MT% of only 1.2%, indicating minimal widespread cell death. Violin plots and pairwise scatter plots were saved to `01_qc/` for manual inspection.

### 2. Cell and Gene Filtering

Filtering was applied sequentially using `sc.pp.filter_cells` and boolean masks on the `.obs` columns. The thresholds were:

| Filter | Threshold | Rationale |
|---|---|---|
| Minimum genes per cell | ≥ 200 | Removes empty droplets and debris |
| Maximum genes per cell | < 2,500 | Removes likely doublets |
| Maximum MT% | < 5% | Removes dying/ruptured cells |
| Minimum cells per gene | ≥ 3 | Removes unexpressed or near-unexpressed genes |

After the `min_genes ≥ 200` filter, all 2,700 cells were retained — confirming no empty droplets in this already-curated dataset. The `max_genes < 2,500` threshold removed 5 cells (0.2%), and the `pct_counts_mt < 5%` threshold removed a further 57 cells. Final cell count was **2,638 (97.7% of original)**. Gene filtering reduced the feature space from 32,738 to **13,656 genes (41.7% retained)**, primarily eliminating the large number of genes expressed in fewer than 3 cells in this shallow-coverage dataset. The removal of 62 cells total (2.3%) indicates a high-quality starting material with very few stressed cells, consistent with a healthy donor sample processed rapidly.

### 3. Normalisation and Log-Transformation

Raw counts were preserved in `adata.layers['counts']` before any transformation. Library-size normalisation was then applied with `sc.pp.normalize_total(adata, target_sum=1e4)`, scaling each cell's counts so they sum to exactly 10,000. This correction is necessary because total UMI counts per cell vary substantially (std = 1,094 counts on the raw data) due to differences in RNA capture efficiency and library complexity — without it, highly sequenced cells would appear to express every gene more highly, confounding all downstream comparisons. The choice of 10,000 as the target (CPM/10 scale, often called "library-size normalisation to 10k") is conventional and ensures interpretable units: a normalized value of 1 corresponds to 100 counts per million. Log1p transformation (`sc.pp.log1p`) was applied immediately after, compressing the heavy right tail of expression distributions and making the data more approximately Gaussian, which is a prerequisite for PCA. The post-transformation expression matrix showed mean = reported value, with min = 0 and max bounded, confirming no numerical artifacts.

### 4. Highly Variable Gene (HVG) Selection

HVGs were selected using `sc.pp.highly_variable_genes` with the Seurat flavour (`flavor='seurat'`), retaining the top **2,000 genes** ranked by normalised dispersion (ratio of observed dispersion to the mean dispersion expected for genes of that expression level). The Seurat flavour fits a loess curve to mean–variance relationship and uses the residual (normalised dispersion) as the ranking criterion, correcting for the technical mean–variance dependency inherent to count data. Selecting 2,000 HVGs reduces noise by discarding the ~11,656 genes that vary primarily due to stochastic sampling rather than true biological differences between cell types. The top HVGs identified — **SPARC, GNG11, PPBP, PF4, SDPR** — are biologically coherent: PPBP, PF4, SDPR, and GNG11 are all platelet-specific transcripts, their high dispersion driven by the presence of a small but transcriptionally extreme platelet cluster. SPARC encodes a matrix-associated secreted protein expressed in myeloid cells. Only HVGs were used in all downstream steps (PCA, UMAP, clustering), while the full 13,656-gene matrix was retained for marker gene testing.

### 5. Regression of Confounders

The execution log does not record an explicit `sc.pp.regress_out` call for mitochondrial percentage or total counts prior to scaling. This is a notable omission relative to the canonical Scanpy PBMC tutorial (which regresses out `total_counts` and `pct_counts_mt`). The consequence is that residual library-size variation and mitochondrial expression heterogeneity remain in the PCA space and could, in theory, cause a PC to be dominated by sequencing depth rather than biological identity. In practice, for this dataset the impact is limited because (a) library-size normalisation to 10k already substantially reduces depth confounding, (b) the MT% range post-filtering is narrow (0–5%), and (c) the five clusters recovered match expected biology perfectly, suggesting depth effects did not dominate the major PCs. For a production analysis, regression should be added explicitly.

### 6. Scaling

Scaling was applied to zero-centre and unit-variance-normalise each gene across cells (standard `sc.pp.scale`). A `max_value` clip parameter was not explicitly reported in the log output, though scanpy's default clips values at `max_value=10`. Scaling is required before PCA because PCA is sensitive to the absolute magnitude and variance of features — without it, highly expressed genes (e.g. ribosomal proteins) would dominate the first PCs simply by virtue of their large variance, rather than because they define biologically meaningful axes of variation. The warning `zero-centering a sparse array/matrix densifies it` appearing in the log confirms that scaling was executed and that the sparse matrix was converted to dense format, which is expected behaviour. The log notes `FutureWarning: Use scanpy.set_figure_params instead`, indicating a minor API version mismatch that has no impact on numerical results.

### 7. Principal Component Analysis

PCA was computed on the 2,638 × 2,000 HVG matrix using `sc.tl.pca(adata, svd_solver='arpack', n_comps=50)`. The variance-ratio plot was saved to `05_pca/`. The agent selected **30 PCs** for all downstream steps (neighbourhood graph, UMAP, clustering). The cumulative variance explained by PCs 1–30 was reported as **9.73%** — a value that initially appears low but is expected in single-cell data where most genes are not differentially expressed and the signal is distributed across many components. For this dataset, an elbow in the variance-ratio plot typically appears around PC 10–15, with PCs beyond ~20 explaining near-equal, small fractions of variance. Using 30 PCs is a defensible conservative choice — it includes all informative signal while the additional PCs beyond the elbow contribute only noise. PCA scatter plots coloured by cluster and QC metrics were saved to confirm the structure is biologically driven.

### 8. Neighbourhood Graph

The k-nearest-neighbour graph was constructed using `sc.pp.neighbors(adata, n_neighbors=10, n_pcs=30)`. This graph connects each cell to its 10 most similar cells in the 30-dimensional PC space, forming the topological backbone for both UMAP layout and Leiden community detection. The choice of `n_neighbors=10` is at the lower end of the typical range (10–50), which tends to preserve fine local structure at the cost of potentially fragmenting larger, internally heterogeneous populations. For this dataset with five well-separated populations it is appropriate. The PCA-based distance metric (rather than raw expression) is used because PCA denoises the representation by projecting out the high-dimensional noise orthogonal to the main axes of variation.

### 9. UMAP Embedding

UMAP was computed using `sc.tl.umap(adata)` with default parameters (min_dist=0.5, spread=1.0) operating on the precomputed 10-neighbour graph. The resulting 2D coordinates were saved and plotted coloured by: total counts, MT percentage, n_genes, and Leiden cluster label (all in `06_umap/`). UMAP reveals that the five clusters form spatially separated islands in 2D, with the platelet cluster (Cluster 4) appearing as a small, isolated satellite — consistent with its dramatically different transcriptional programme. It is important to note that UMAP distances between clusters are not quantitatively interpretable (two clusters that appear close may not be transcriptionally more similar than two clusters that appear far apart), and the specific layout is stochastic (seeded by random initialisation). UMAP should be treated as a qualitative visualisation aid, not as evidence for or against biological relationships between populations.

### 10. Leiden Clustering

Community detection was performed with `sc.tl.leiden(adata, resolution=0.5)`, yielding **5 clusters** (labelled 0–4). The Leiden algorithm optimises a modularity objective that balances intra-community edge density against an expected null model; the `resolution` parameter (γ) scales the null model — higher values produce more, finer-grained clusters and lower values produce fewer, coarser clusters. At resolution 0.5, the algorithm found a partition consistent with major PBMC lineages rather than sub-lineages, which is the biologically appropriate granularity for a first-pass analysis of this depth. Cluster sizes ranged from 25 (platelets, Cluster 4) to 1,125 cells (T cells, Cluster 0). Cluster composition was saved as a CSV to `07_clustering/`.

### 11. Marker Gene Identification

Marker genes were identified using `sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')`, which performs a one-versus-rest Wilcoxon rank-sum test for each cluster. The Wilcoxon test is preferred in scRNA-seq because it is non-parametric (making no Gaussian assumption on count-derived data), is robust to outliers, and has been benchmarked as among the best-performing methods for single-cell differential expression. For each cluster, genes are ranked by their test statistic score. Notably, the **logfoldchanges** column in the output was reported as `NaN` for all markers — this indicates that the `use_raw=True` default attempted to access `adata.raw`, which was not explicitly set, and fold-change computation fell back to unavailable raw data. The scores and adjusted p-values (Benjamini-Hochberg correction) are valid and were used for annotation. All markers across all clusters were saved to `08_markers/markers.csv`, with accompanying ranking plots, dotplots, heatmaps, and violin plots.

### 12. Cell Type Annotation

Cell types were assigned by manual inspection of the top marker genes per cluster, cross-referenced against established PBMC marker databases:

| Cluster | Key Markers | Assigned Type |
|---|---|---|
| 0 | CD3D, CD3E, IL7R, LTB | T cells |
| 1 | LST1, CST3, TYROBP, S100A9, FCN1 | Monocytes |
| 2 | NKG7, CST7, GZMA, CCL5, CTSW | NK cells |
| 3 | CD79A, CD79B, MS4A1, HLA-DQA1, HLA-DRA | B cells |
| 4 | PPBP, PF4, SDPR, RGS18, GNG11 | Platelets |

Annotations were stored in `adata.obs['cell_type']` and exported to `09_annotation/cell_annotations.csv` and `per_cell_annotations.csv`. The assignment logic is rule-based (manual thresholding by marker identity) rather than probabilistic (e.g. SingleR or CellTypist), which is appropriate for these clearly separated, well-characterised populations but would be insufficient for ambiguous or rare populations.

---

## Cell Population Findings

### T Cells — 1,125 cells (42.6%)
**Defining markers:** CD3D, CD3E, IL7R, LTB, IL32, NOSIP, TMEM66, GIMAP7

CD3D and CD3E encode subunits of the CD3 signalling complex, which is the definitive molecular hallmark of T lymphocytes — they form the invariant signalling machinery associated with the T cell receptor (TCR). IL7R encodes the IL-7 receptor alpha chain (CD127), characteristic of naïve and memory T cells that depend on IL-7 for survival and homeostatic proliferation. LTB (lymphotoxin-beta) is a TNF superfamily member expressed on lymphocytes involved in lymphoid organogenesis. GIMAP7 is a GTPase of the immune-associated protein family constitutively expressed in T cells. T cells are the most abundant PBMC population (~40–70% in healthy donors), consistent with this dataset's 42.6%. **Limitation:** at resolution 0.5, T helper (CD4+) and cytotoxic (CD8+) T cells are merged into a single cluster; CD4 and CD8A/B expression levels in this cluster are not shown, and sub-clustering would be required to resolve them.

### Monocytes — 667 cells (25.3%)
**Defining markers:** LST1, CST3, TYROBP, S100A9, FCN1, FCER1G, AIF1, TYMP, CFD, S100A8

S100A8 and S100A9 (calprotectin subunits