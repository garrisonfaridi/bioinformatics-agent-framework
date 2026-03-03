# CFW Mouse Obesity GWAS — Pilot Run

A genome-wide association study for body weight in outbred CFW mice, implemented as a
Snakemake pipeline with AI-assisted debugging, automated biological QC, and Claude Opus peer review.
This project serves as a documented pilot demonstrating the bioinformatics agent framework.

## Dataset

| Parameter | Value |
|-----------|-------|
| Population | Crl:CFW(SW)-US_P08 outbred mice |
| Source | Dryad doi:10.5061/dryad.2rs41 (Nicod et al. 2016) |
| Input samples | 500 |
| Post-QC samples | 453 (all male; 47 removed by --mind 0.30) |
| Input SNPs | 92,734 (MegaMUGA array) |
| Post-QC SNPs | 16,710 (MAF ≥ 0.05 AND geno ≤ 5%) |
| Phenotype | Sacrifice body weight (`sacweight`), inverse-normal transformed |
| Body weight | Mean 38.41 ± 4.74 g; range 25.00–53.20 g |

## Pipeline Architecture

```
Step 0:  Download data (Dryad DOI)
Step 1:  Phenotype preparation (INT transform)
Step 2:  Genotype QC (PLINK2 --maf 0.05 --geno 0.05 --mind 0.30)
Step 2b: QC report (MAF histogram, missingness plots, summary)
Step 3:  Kinship matrix (GEMMA -gk 1; centered relatedness)
Step 4:  LMM association (GEMMA -lmm 4; Wald test)
Step 5:  Significance check [checkpoint → branch A or B]
         ├── Branch A (has_hits = true):  GO/KEGG enrichment + GWAS Catalog overlap
         └── Branch B (has_hits = false): BSLMM genetic architecture (GEMMA -bslmm 1)
Step 6:  QQ + Manhattan + SNP density plots; λ_GC calculation
Step 7:  Gene annotation (Ensembl REST API; ±500 kb around lead SNPs)
Step 8:  Biomni biological QC (Biomni A1 agent; Claude API fallback)
Step 9:  Claude Opus peer review → review_report.md + proposed_changes.md
```

**Branching logic:** `check_significance` (Snakemake checkpoint) reads the post-association JSON
and routes to enrichment analysis if any SNP clears the Bonferroni threshold, or to BSLMM if none
do. In this pilot, no SNP reached genome-wide significance → Branch B (BSLMM).

## Key Results

### Significance

| Threshold | Value | Hits |
|-----------|-------|------|
| Bonferroni (genome-wide) | p < 2.99×10⁻⁶ (0.05/16,710) | 0 |
| Suggestive (1 FP/scan) | p < 5.98×10⁻⁵ | 4 SNPs |

No genome-wide significant associations at pilot N=453 — consistent with the polygenic
architecture of body weight and the power requirements of individual-level GWAS.

### Lead Suggestive Loci

| SNP | Chr | Position (mm10) | p-value | Nearest gene |
|-----|-----|-----------------|---------|--------------|
| cfw-15-47930863 | 15 | 47,930,863 | 2.11×10⁻⁵ | *Csmd3* (ENSMUSG00000022311) |
| rs31551218 | 15 | 46,034,785 | 2.88×10⁻⁵ | No annotated gene ±500 kb |

Both lead loci cluster on Chr15 (46–48 Mb), suggesting a possible regional signal. Neither
overlaps known murine obesity loci (*Lepr* chr4, *Mc4r* chr18, *Fto* chr8, *Pomc* chr12).

### Model Calibration

| Metric | Value | Interpretation |
|--------|-------|----------------|
| λ_GC | 1.0935 | Acceptable for CFW LMM with kinship correction (threshold: 1.10) |
| Kinship model | GEMMA centered relatedness (-gk 1) | Accounts for outbred population structure |

### Genetic Architecture (BSLMM)

Branch B was taken (no significant hits), triggering GEMMA BSLMM to characterize overall
genetic architecture:

| Parameter | Posterior mean | 95% CI |
|-----------|---------------|--------|
| PVE (SNP-heritability) | 0.053 | [0.0016, 0.184] |
| PGE (sparse component fraction) | 0.509 | [0.034, 0.981] |
| n_γ (sparse loci count) | 16.7 | [6, 34] |

**Interpretation:** All CIs span nearly the full parameter space — the pilot sample is too small
for informative BSLMM posteriors. Published CFW body weight h²=0.20–0.40 (Parker et al. 2016;
Nicod et al. 2016), 4–8× higher than the observed PVE. This reflects power limitations at N≈300
effective samples, not low heritability. Full N=1,200 is required for interpretable architecture
estimates.

### Peer Review Findings

The automated Claude Opus peer review (`results/peer_review/`) identified:

| Severity | Count | Key issues |
|----------|-------|------------|
| Critical | 2 | (1) Misleading QC summary SNP labels [corrected]; (2) Sex covariate documentation [corrected — all-male cohort confirmed] |
| Moderate | 10 | BSLMM CI width; no PCA/MDS; no multi-chain MCMC; no comparison to Parker/Nicod; no outlier sensitivity |
| Minor | 3 | Minor labeling and documentation gaps |

Both critical issues were resolved in a correction cycle. See
`results/peer_review/proposed_changes.md` and `results/peer_review/review_report.md`.

## What the AI Framework Accomplished

This pilot demonstrates the agentic capabilities of the framework across the full
research-to-publication-ready pipeline lifecycle:

### 1. Research & Planning (Opus + Biomni)
- Identified CFW as the appropriate model for outbred individual-level GWAS at laptop scale
- Selected GEMMA over alternatives (EMMAX, fastLMM) for kinship + BSLMM capability in one tool
- Designed checkpoint branching to handle both the "hits" and "no hits" outcomes

### 2. Pipeline Debugging (Sonnet, autonomous)

Three blocking failures were diagnosed and resolved without user escalation:

**Bug 1 — R `fread` tab/space parsing (`bslmm_interpret.R`)**
GEMMA's `.hyp.txt` pads numeric values with spaces and adds a trailing tab per line. `fread`'s
default auto-separator detection splits on both spaces and tabs, producing 11 columns instead of
6. All named header columns (`pve`, `pge`, `n_gamma`, etc.) were being silently discarded, leaving
only anonymous `V1`–`V11` columns. Trace plots then crashed on empty data. Fix: forced `sep = "\t"`
+ `strip.white = TRUE` + post-read column cleanup.

**Bug 2 — Silent Biomni exception swallowing (`biomni_qc.py`)**
`A1().run()` raised `SystemExit` (not a subclass of `Exception`), which was not caught by the
`except Exception` handler. The script hung at "Attempting Biomni A1 agent" indefinitely. Fix:
changed to `except BaseException` with an empty-result guard before API fallback.

**Bug 3 — Wrong conda env reference in `Snakefile`**
Three rules referenced `conda: "envs/biomni-gwas"` (a directory path that doesn't exist) rather
than `conda: "envs/biomni.yml"` (the YAML spec file). Snakemake raised `EnvironmentLocationNotFound`.
Fix: corrected all three occurrences.

### 3. Automated Biological QC (Biomni/Claude API)
The `biomni_qc` step queried the Biomni agent (Claude API fallback) to validate:
- Body weight distribution against MPD/CFW literature values
- Top GWAS hits against known murine obesity loci (Lepr, Mc4r, Fto, Pomc)
- Literature context (Nicod et al. 2016, Parker et al. 2016)
- Critical flags (sex chromosome handling, p-value distribution, batch effects)

Result: `results/07_biomni_qc/biomni_qc_report.md` — a structured biological validity assessment.

### 4. Automated Peer Review + Correction Cycle
After the pipeline completed, Claude Opus reviewed all outputs and produced:
- A detailed 4-section review (statistical validity, biological plausibility, scientific nuances,
  missed analyses)
- A structured `issues.json` with severity classification
- A `proposed_changes.md` formatted as an implementation plan requiring explicit user approval

On user approval, the following corrections were implemented:
- Fixed misleading QC summary SNP count labels (revealed: 16,710 is the correct post-filter count;
  "61,954" in old summary was a per-filter count from pre-filter data, not the final retained total)
- Documented all-male cohort (confirmed sex code = 1 for all 453 samples; no sex covariate needed)
- Corrected sample exclusion count (47 removed by `--mind 0.30`, not 3 as the old report implied)
- Revised BSLMM interpretation to acknowledge uninformative CIs and cite literature h²
- Added gene annotation rule (new Snakemake step + Ensembl REST API script)

### 5. Gene Annotation (Ensembl REST API, automated)
The new `annotate_loci` rule queries Ensembl for protein-coding and lincRNA genes within ±500 kb
of each lead SNP, producing a TSV and markdown summary. Chr15:47.9 Mb overlaps *Csmd3*, a
complement component gene with roles in synaptic pruning and neuroinflammation (not a canonical
obesity gene — consistent with this being a pilot-N suggestive hit requiring replication).

## Files Included

```
projects/mouse-obesity-gwas/
├── Snakefile                          # 12-rule pipeline with checkpoint branching
├── config.yaml                        # All parameters (no hard-coded paths)
├── README.md                          # this file
├── METHODS.md                         # Publishable methods for each analysis step
├── envs/
│   ├── gwas.yml                       # PLINK2, GEMMA, R, qqman, clusterProfiler
│   └── biomni.yml                     # Python + biomni + anthropic SDK
├── scripts/
│   ├── download_data.py               # Dryad DOI download + pilot subset
│   ├── phenotype_prep.R               # INT transform, distribution plot
│   ├── attach_pheno_to_fam.py         # Attach phenotype to PLINK FAM col 6
│   ├── genotype_qc_report.R           # QC summary with true SNP/sample counts
│   ├── check_significance.py          # Checkpoint: Bonferroni/suggestive hit detection
│   ├── qc_plots.R                     # Manhattan, QQ, SNP density, λ_GC
│   ├── bslmm_interpret.R              # BSLMM posterior summaries + trace plots
│   ├── go_enrichment.R                # GO/KEGG enrichment (Branch A)
│   ├── gwas_catalog_overlap.py        # GWAS Catalog overlap (Branch A)
│   ├── annotate_top_loci.py           # Ensembl REST gene annotation (new)
│   ├── biomni_qc.py                   # Biological QC via Biomni/Claude API
│   └── peer_review.py                 # Claude Opus automated peer review
├── results/
│   ├── 01_phenotype/step_summary.txt  # Phenotype stats (N, mean, SD, range)
│   ├── 01_phenotype/pheno_dist.png    # Body weight distribution plot
│   ├── 02_qc/qc_summary.txt          # SNP/sample QC summary (corrected labels)
│   ├── 02_qc/maf_histogram.png        # MAF, missingness QC plots
│   ├── 03_lmm/significance_check.json # Lead SNPs, thresholds, has_hits flag
│   ├── 04_bslmm/hyperparameters.csv   # BSLMM posterior means + 95% CIs
│   ├── 04_bslmm/architecture_summary.txt  # Genetic architecture interpretation
│   ├── 04_bslmm/trace_plots.png       # MCMC trace plots (pve, pge, rho, pi, n_gamma)
│   ├── 06_qc_plots/manhattan_plot.png # Genome-wide Manhattan plot
│   ├── 06_qc_plots/qq_plot.png        # QQ plot with λ_GC annotation
│   ├── 06_qc_plots/lambda.txt         # λ_GC value + warning flag
│   ├── 07_biomni_qc/biomni_qc_report.md  # Biological plausibility report
│   ├── 08_annotation/top_loci_genes.tsv  # Ensembl gene annotation for lead SNPs
│   ├── 08_annotation/annotation_summary.md
│   └── peer_review/
│       ├── review_report.md           # Full Claude Opus peer review (4 sections)
│       ├── issues.json                # Structured issue list with severity
│       └── proposed_changes.md        # Approved correction plan
```

## How to Reproduce

```bash
# 1. Install conda environments
conda env create -f envs/gwas.yml
conda env create -f envs/biomni.yml

# 2. Set API key (required for biomni_qc and peer_review steps)
export ANTHROPIC_API_KEY=your_key_here

# 3. Dry run to verify DAG
snakemake -n --cores 4 --use-conda

# 4. Full run
snakemake --cores 4 --use-conda

# Runtime: ~30–60 min on a laptop (BSLMM is the bottleneck at burnin=10K, sampling=10K)
# For a proper BSLMM run: increase config.yaml bslmm.burnin and bslmm.sampling to 100K each
```

## Limitations of This Pilot

1. **Sample size (N=453)** — Individual-level GWAS for body weight requires N>1,000 for reasonable
   power. No loci reached genome-wide significance; all four suggestive hits should be treated as
   hypothesis-generating only.
2. **BSLMM posteriors uninformative** — Wide CIs on all hyperparameters; only interpret with N≥1,200.
3. **Single MCMC chain** — BSLMM was run with one chain (burnin=10K, sampling=10K). Multi-chain
   validation with Gelman-Rubin diagnostics is required for publishable results.
4. **No LD pruning for Bonferroni** — 16,710 SNPs include correlated markers; effective M is lower.
   Permutation-based thresholds are more appropriate for publication.
5. **No age/batch covariates** — Only kinship is modeled. Adding cage/batch covariates would
   reduce residual variance and improve power.

## Next Steps for Full-Scale Analysis

1. Scale to full N=1,200 CFW dataset (same Dryad DOI)
2. Run BSLMM with 3 independent chains (burnin=100K, sampling=100K each); compute Rhat + ESS
3. Add PCA/MDS step to visualize population structure
4. Add sensitivity analysis: re-run excluding samples with BW > 3 SD from mean
5. Compare Chr15 loci to Parker et al. 2016 (Nat Genet) published hits
6. Generate LocusZoom-style regional plots for Chr15:45–50 Mb

## References

- Nicod J et al. (2016). Genome-wide association of multiple complex traits in outbred mice by
  ultra-low-coverage sequencing. *Nature Genetics* 48:912–918.
- Parker CC et al. (2016). Genome-wide association study of behavioral, physiological and gene
  expression traits in outbred CFW mice. *Nature Genetics* 48:919–926.
- Zhou X & Stephens M (2012). Genome-wide efficient mixed-model analysis for association studies.
  *Nature Genetics* 44:821–824. [GEMMA]
- Chang CC et al. (2015). Second-generation PLINK: rising to the challenge of larger and richer
  datasets. *GigaScience* 4:7. [PLINK2]
