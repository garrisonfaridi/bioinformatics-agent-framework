# Methods — CFW Mouse Obesity GWAS Pilot

Publishable-quality methods text for each analysis step. Customize bracketed values before
use in a manuscript or report.

---

## Genotype Quality Control

Genotype data for [N_INPUT] Crl:CFW(SW)-US_P08 outbred mice were obtained from Dryad
(doi:10.5061/dryad.2rs41). Quality control was performed using PLINK v2.00a5
(Chang et al. 2015). SNPs were filtered on minor allele frequency (MAF ≥ 0.05) and
per-variant genotype missingness (≤ 5%). Samples with per-sample missingness > 30% were
excluded (reflecting the high missingness characteristic of MegaMUGA array data for this
cohort). Following QC, [N_QC] samples and [N_SNPS] SNPs were retained for association
analysis. All retained samples were male.

---

## Phenotype Preparation

Sacrifice body weight (g) was extracted from published phenotype data for the corresponding
samples. Raw values were inverse-normal transformed (INT) to reduce the influence of outliers
and improve normality assumptions for the linear model. INT was applied using the rank-based
transformation: Φ⁻¹((rank − 0.5) / N), where Φ is the standard normal CDF.

---

## Kinship Matrix Estimation

A centered genetic relatedness matrix (GRM) was computed from all post-QC SNPs using GEMMA
v0.98.5 (`-gk 1`; Zhou & Stephens 2012). The GRM captures pairwise genetic similarity
across all samples and is used as a random effect in the association model to control for
population stratification and cryptic relatedness.

---

## Linear Mixed Model Association Analysis

Genome-wide association testing was performed using GEMMA v0.98.5 implementing a linear
mixed model (LMM):

```
y = Wα + xβ + u + ε
```

where y is the vector of inverse-normal transformed body weights, W contains fixed-effect
covariates, x is the genotype vector for the tested SNP, β is the SNP effect size, u is
the polygenic random effect (u ~ MVN(0, λτ⁻¹K)), and ε is the residual error. The kinship
matrix K was estimated as described above. All four test statistics (Wald, likelihood ratio,
score, and REML) were computed (`-lmm 4`); Wald p-values are reported. Genomic inflation
was assessed by computing λ_GC = median(χ²_observed) / median(χ²_expected).

---

## Significance Thresholds

Genome-wide significance was assessed using a Bonferroni-corrected threshold of
p < α / M, where α = 0.05 and M is the number of post-QC SNPs (p < [BONF_THRESH]).
A suggestive threshold of 1 expected false positive per genome scan was also applied
(p < 1 / M = [SUGG_THRESH]). Lead SNPs were defined by 1-Mb greedy clumping: the
most significant SNP in each region was retained as the lead, and all SNPs within
1 Mb on the same chromosome were merged into a single locus.

---

## Genetic Architecture Estimation (BSLMM)

Given the absence of genome-wide significant associations (consistent with pilot
sample size), genetic architecture was characterized using GEMMA's Bayesian Sparse
Linear Mixed Model (BSLMM; `-bslmm 1`). BSLMM decomposes phenotypic variance into
a polygenic component and a sparse large-effect component, estimating three key
hyperparameters via MCMC:

- **PVE** — proportion of phenotypic variance explained by all genotyped SNPs (approximating SNP-heritability)
- **PGE** — proportion of PVE attributable to sparse (large-effect) loci
- **n_γ** — expected number of SNPs with large sparse effects

MCMC was run for [BURNIN] burn-in and [SAMPLING] sampling iterations (seed = 42).
Posterior means and 95% credible intervals were computed from retained samples.
Trace plots were inspected for stationarity. **Note:** Single-chain estimates with
these burn-in/sampling parameters are appropriate for exploratory pilot analysis
only; multi-chain validation (≥3 chains; Gelman-Rubin R̂ < 1.05) is required
before drawing architectural conclusions.

---

## Gene Annotation

Lead SNPs were annotated with nearby protein-coding and lincRNA genes using the
Ensembl REST API (GRCm38/mm10). Genes within a ±500 kb window around each lead
SNP were retrieved and reported. Proximity to known murine obesity loci (*Lepr*
chr4:132 Mb, *Mc4r* chr18:66 Mb, *Fto* chr8:108 Mb, *Pomc* chr12:3 Mb) was
assessed manually.

---

## Biological Quality Control

Biological plausibility of the phenotype distribution and top association results
was assessed using an automated review prompt delivered to a large language model
(Claude Sonnet; Anthropic). The review assessed: (1) body weight distribution
against published CFW means from the Mouse Phenome Database; (2) literature
context from CFW GWAS (Nicod et al. 2016; Parker et al. 2016); (3) co-localization
of top hits with known murine obesity QTLs; and (4) critical technical flags.

---

## Automated Peer Review

Following pipeline completion, an automated peer review was conducted using Claude
Opus (Anthropic). A structured review prompt covering statistical validity,
biological plausibility, scientific nuances, and missed analyses was submitted
along with key pipeline outputs. Issues were classified by severity (critical,
moderate, minor) and documented in machine-readable JSON format. Corrections
identified as critical were implemented before final reporting.

---

## Software Versions

| Tool | Version | Reference |
|------|---------|-----------|
| PLINK2 | 2.00a5.12 | Chang et al. 2015 |
| GEMMA | 0.98.5 | Zhou & Stephens 2012 |
| R | 4.3.3 | R Core Team 2024 |
| qqman | 0.1.9 | Turner 2018 |
| clusterProfiler | 4.10.0 | Yu et al. 2012 |
| org.Mm.eg.db | 3.18.0 | Carlson 2023 |
| Snakemake | ≥ 8.0 | Mölder et al. 2021 |
| Python | 3.11 | — |
| pandas | 2.1.0 | — |
| requests | 2.31.0 | — |

## References

- Chang CC et al. (2015). Second-generation PLINK: rising to the challenge of larger and richer
  datasets. *GigaScience* 4:7.
- Zhou X & Stephens M (2012). Genome-wide efficient mixed-model analysis for association studies.
  *Nature Genetics* 44:821–824.
- Nicod J et al. (2016). Genome-wide association of multiple complex traits in outbred mice by
  ultra-low-coverage sequencing. *Nature Genetics* 48:912–918.
- Parker CC et al. (2016). Genome-wide association study of behavioral, physiological and gene
  expression traits in outbred CFW mice. *Nature Genetics* 48:919–926.
- Mölder F et al. (2021). Sustainable data analysis with Snakemake. *F1000Research* 10:33.
- Yu G et al. (2012). clusterProfiler: an R package for comparing biological themes among gene
  clusters. *OMICS* 16:284–287.
