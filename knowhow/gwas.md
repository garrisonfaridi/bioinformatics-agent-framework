# GWAS & Mouse QTL Mapping — Know-How

## Overview

Genome-Wide Association Studies (GWAS) identify statistical associations between genetic variants
(SNPs, indels) and phenotypes across a population. In mice, the equivalent is often called
**QTL mapping** (Quantitative Trait Locus) when using inbred or recombinant inbred panels.
The two frameworks are complementary and share the same core linear model.

**Key distinction:**
- **Strain-level QTL** — strain means as the unit of analysis (BXD, HMDP); N = 50–200 strains;
  lower power but isogenic replication within strains removes environmental noise
- **Individual-level GWAS** — individual animals as units (CFW, DO mice); N = hundreds to
  thousands; standard GWAS mixed-model framework; requires population structure correction

---

## Mouse Genetic Reference Populations

| Panel | Type | N units | Markers | Best for |
|-------|------|---------|---------|----------|
| BXD (GeneNetwork) | Recombinant inbred (RI) | 55–198 strains | 7K–74K | Classic QTL, metabolic traits, HFD studies |
| HMDP | Inbred + RI mix | ~104 strains | ~200K informative | GWAS resolution, eQTL co-mapping |
| Collaborative Cross (CC) | RI from 8 founders | ~50–70 lines available | GigaMUGA (110K+) | Complex trait dissection |
| Diversity Outbred (DO) | Outbred from 8 founders | 200–1,000 individuals | GigaMUGA (110K+) | Fine mapping, individual-level GWAS |
| CFW | Outbred (colony) | 1,200 individuals | 92K (MegaMUGA) | Individual GWAS, behavioral/physiology |
| Classical inbred | Inbred strains | 50–450 strains | Sanger WGS VCFs | Cross-panel replication, eQTL |

**For a laptop pilot:** BXD (strain-level, <10 MB) or CFW subset (PLINK-ready, ~300 MB).

---

## Statistical Framework

### Core model (linear mixed model)
```
y = Xβ + Zu + ε
```
- `y` — phenotype vector (body weight, fat mass, etc.)
- `X` — genotype at test SNP + covariates (sex, age, diet, batch)
- `β` — fixed effects
- `u ~ N(0, σ²_g K)` — polygenic random effect; K = kinship/relatedness matrix
- `ε ~ N(0, σ²_e I)` — residual error

The kinship matrix `K` controls for population structure and cryptic relatedness — **critical
for inbred panels and outbred populations alike**.

### For strain-level QTL (BXD, HMDP)
Use **interval mapping** or **genome scan** approach:
- R/qtl or R/qtl2 for RI panels
- LOD score = log10(likelihood ratio)
- Significance threshold via 1,000 permutations (genome-wide α = 0.05 → LOD ~3.5 for mouse)

### For individual-level GWAS (CFW, DO)
Use linear mixed model (LMM) with kinship correction:
- **GEMMA** (preferred for mouse GWAS; BSLMM and LMM modes)
- **EMMAX** — efficient mixed model
- **R/qtl2** with `scan1` function for DO/CC
- Output: beta, SE, p-value, MAF per SNP

---

## Tools

| Tool | Purpose | Version | Install |
|------|---------|---------|---------|
| PLINK 2 | Data QC, format conversion, basic association | 2.0-alpha | `conda install -c bioconda plink2` |
| GEMMA 0.98+ | LMM GWAS with kinship; mouse gold standard | 0.98.5 | `conda install -c bioconda gemma` |
| R/qtl2 | QTL mapping for RI/CC/DO; R-native | 0.36+ | `install.packages("qtl2")` |
| PLINK 1.9 | Legacy format support, LD analysis | 1.90 | `conda install -c bioconda plink` |
| bcftools | VCF subsetting, filtering | 1.18+ | `conda install -c bioconda bcftools` |
| liftOver | Genome build conversion (mm10 → mm39) | — | UCSC download |
| qqman (R) | Manhattan and QQ plots | 0.1.9 | `install.packages("qqman")` |
| CMplot (R) | Publication-quality circular Manhattan plots | 4.4+ | `install.packages("CMplot")` |

---

## Standard Pilot GWAS Workflow (Mouse, Laptop-Scale)

### 1. Data acquisition
```bash
# Option A: BXD strain-level (smallest, quickest)
wget http://gn1.genenetwork.org/genotypes/BXD.geno          # <2 MB genotypes
# Download phenotype CSV from phenome.jax.org (Auwerx1 or HMDPpheno5)

# Option B: CFW individual-level (PLINK-ready)
# From Dryad: doi:10.5061/dryad.2rs41
# Files: cfw.bed, cfw.bim, cfw.fam (PLINK binary)
```

### 2. Genotype QC (PLINK2)
```bash
plink2 \
  --bfile cfw \
  --maf 0.05 \          # minor allele frequency filter
  --geno 0.05 \         # max per-SNP missingness
  --mind 0.10 \         # max per-sample missingness
  --hwe 1e-6 \          # Hardy-Weinberg (outbred panels only)
  --make-bed \
  --out cfw_qc
```
For inbred/RI panels, skip HWE filter (inbreds violate HWE by design).

### 3. Compute kinship matrix (GEMMA)
```bash
gemma -bfile cfw_qc -gk 1 -o cfw_kinship
# -gk 1 = centered relatedness matrix (recommended)
# -gk 2 = standardized relatedness matrix
```

### 4. Run LMM association (GEMMA)
```bash
gemma -bfile cfw_qc \
  -k output/cfw_kinship.cXX.txt \
  -lmm 4 \              # -lmm 4 = Wald, LRT, score tests (use Wald p-value)
  -n 1 \                # phenotype column index in .fam file (or -p pheno.txt)
  -o cfw_obesity_gwas
# Output: output/cfw_obesity_gwas.assoc.txt
```

### 5. For R/qtl2 (BXD or DO panels)
```r
library(qtl2)

# Load cross object (BXD example)
bxd <- read_cross2("bxd_control.yaml")  # from GeneNetwork .geno + phenotype CSV
gmap <- insert_pseudomarkers(bxd$gmap, step = 1)

# Calculate genotype probabilities
pr <- calc_genoprob(bxd, gmap, error_prob = 0.002)

# Compute kinship (LOCO method — leave one chromosome out)
kin <- calc_kinship(pr, type = "loco")

# Run genome scan
out <- scan1(pr, bxd$pheno[, "body_weight_g"], kinship = kin,
             addcovar = model.matrix(~sex, data = bxd$covar)[, -1])

# Permutation threshold
perm <- scan1perm(pr, bxd$pheno[, "body_weight_g"], kinship = kin,
                  n_perm = 1000, cores = 4)
threshold <- summary(perm, alpha = 0.05)
```

### 6. Results visualization
```r
library(qqman)

# Manhattan plot
manhattan(results, chr = "chr", bp = "ps", snp = "rs", p = "p_wald",
          suggestiveline = -log10(1e-5), genomewideline = -log10(5e-8))

# QQ plot — check inflation (lambda)
qq(results$p_wald)
lambda <- median(qchisq(1 - results$p_wald, 1)) / qchisq(0.5, 1)
```

### 7. Significance thresholds (mouse)
| Method | Threshold |
|--------|-----------|
| Genome-wide (Bonferroni) | p < 0.05 / N_SNPs |
| Mouse conventional (individual GWAS) | p < 5×10⁻⁸ (GRCm38, ~92K to 202K SNPs → adjust) |
| LOD score (permutation, RI panels) | LOD > 3.5 (permutation-derived at α=0.05) |
| Suggestive | 1 false positive expected per genome scan |
| FDR (BH) | q < 0.05 for exploratory |
| Lindley local score | Permutation-derived (99th–99.9th percentile of max null score) |

For a panel of 92K SNPs (CFW), Bonferroni threshold = 0.05 / 92,000 ≈ **5.4×10⁻⁷**.

---

## Multi-Phenotype GWAS via Phenotype PCA

### Rationale

When a project measures multiple correlated phenotypes (e.g., plant defense traits such as
glucosinolate content, trichome density, leaf chlorosis score), running independent GWAS for
each trait inflates multiple-testing burden and ignores shared genetic architecture. PCA on
the phenotype matrix captures dominant axes of covariation; the leading PCs become surrogate
traits for GWAS and can reveal loci controlling the **syndrome** rather than any single trait.

### Workflow

```python
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# 1. Load phenotype matrix (samples × traits); impute missing values before PCA
pheno = pd.read_csv("phenotypes.csv", index_col=0)
pheno_scaled = StandardScaler().fit_transform(pheno)

# 2. PCA
pca = PCA(n_components=10, random_state=42)
pcs = pca.fit_transform(pheno_scaled)

# 3. Select PCs explaining ≥5% variance (or elbow criterion)
explained = pca.explained_variance_ratio_
keep = [i for i, v in enumerate(explained) if v >= 0.05]

# 4. Write PC phenotype files for GEMMA (-p flag)
for i in keep:
    pd.Series(pcs[:, i], index=pheno.index).to_csv(f"pc{i+1}_pheno.txt",
                                                     header=False)
```

```bash
# GEMMA LMM for each PC (column index is 1-based for -n; use -p for external file)
for PC in 1 2 3; do
    gemma -bfile genotypes_qc \
          -k output/kinship.cXX.txt \
          -lmm 4 \
          -p pc${PC}_pheno.txt \
          -o gwas_pc${PC}
done
```

**GEMMA column indexing:** When phenotypes are embedded in the `.fam` file, `-n` is **1-based**
(column 6 = trait 1 = `-n 1`). When supplying an external file via `-p`, the file contains a
single column (one value per sample in the same order as `.fam`).

### Biological interpretation of PCs

- **PC1** (highest variance) typically captures the dominant syndrome axis — often a
  constitutive-vs-induced defense gradient in plant immunity studies
- Loadings (eigenvectors) show which traits drive each PC; large positive + negative loadings
  indicate antagonistic trait modules
- Report PC hits alongside per-trait GWAS for overlap; a locus significant for PC1 but not
  any single trait is a **pleiotropic syndrome locus**

### BSLMM on PCs vs. raw traits

BSLMM run on PC phenotypes characterizes the **genetic architecture of the syndrome axis**,
not of any single trait. `pge` close to 0 on PC1 indicates the syndrome is highly polygenic
even if individual traits appear to have moderate-effect QTL.

---

## Key Databases

| Database | URL | Content |
|----------|-----|---------|
| Mouse Phenome Database (MPD) | phenome.jax.org | Phenotype data for 100s of strains; SNP retrieval |
| GeneNetwork | genenetwork.org | BXD genotypes, 5,000+ phenotypes, browser QTL mapper |
| HMDP / Lusis lab | systems.genetics.ucla.edu/HMDP | HMDP genotypes, metabolic GWAS data |
| Dryad (CFW) | datadryad.org doi:10.5061/dryad.2rs41 | CFW PLINK files, 1,200 mice, 92K SNPs |
| Mouse Genome Informatics | informatics.jax.org | QTL/gene annotations, JAX strain info |
| GWAS Catalog (mouse) | ebi.ac.uk/gwas | Published mouse GWAS hits |
| Sanger MGP | mousegenomes.org | 52-strain WGS VCFs (GRCm38/39) |
| eLife 2022 DO dataset | elifesciences.org/articles/64329 | 946 DO mice, body weight GWAS |

---

## Compute Requirements

| Task | RAM | CPU | Time (laptop) |
|------|-----|-----|--------------|
| BXD strain QTL (R/qtl2, 1000 perms) | 2–4 GB | 1–4 cores | 5–30 min |
| CFW subset 300 mice, 92K SNPs (GEMMA) | 4–8 GB | 1 core | 10–20 min |
| CFW full 1,200 mice, 92K SNPs (GEMMA) | 8–16 GB | 1 core | 1–2 hours |
| HMDP 104 strains, 200K SNPs (GEMMA) | 4–8 GB | 1 core | 30–60 min |
| DO 946 mice, 110K SNPs (R/qtl2 LOCO) | 16–32 GB | 4–8 cores | 4–12 hours |

**Laptop pilot recommendation:** Start with BXD (R/qtl2, strain-level) to validate the pipeline,
then scale to CFW subset (300 mice, GEMMA LMM) for individual-level GWAS experience.

---

## Common Pitfalls

1. **Not controlling for kinship** — inflated p-values (genomic inflation λ >> 1); always compute
   and include kinship matrix in LMM
2. **HWE filter on inbred strains** — inbred strains violate HWE by definition; omit this filter
3. **Confounding by sex** — always include sex as a covariate; mouse body weight is strongly
   sex-dimorphic
4. **Genome build mismatch** — confirm genotype file build (mm10/GRCm38 vs mm39/GRCm39) matches
   annotation files; use liftOver if needed
5. **LOD vs p-value threshold** — don't apply Bonferroni to RI panel LOD scores; use permutations
6. **Underpowered pilot** — 50–100 strains gives 80% power only for large-effect QTL (>15%
   variance explained); interpret results as discovery, not confirmation
7. **Multiple phenotype testing** — if testing body weight + fat mass + glucose, apply Bonferroni
   across phenotypes or use FDR

---

## Publishable Methods Template

> Genome-wide association mapping was performed using a linear mixed model (LMM) implemented in
> GEMMA v0.98.5 [Zhou & Stephens 2012] to account for population structure and cryptic
> relatedness. A centered genetic relatedness matrix was computed from all autosomal SNPs passing
> QC filters (MAF ≥ 0.05, missingness ≤ 5%). Phenotype values were inverse-normal transformed
> prior to association testing. Genome-wide significance was assessed using a Bonferroni-corrected
> threshold of p < [threshold] based on the number of independent SNPs after LD pruning. QQ plots
> and genomic inflation factors (λ) were computed to assess model calibration.

---

## BSLMM Architecture Interpretation

GEMMA's Bayesian Sparse Linear Mixed Model (`-bslmm 1`) estimates hyperparameters that
characterize the genetic architecture of a trait. Key outputs from `.hyp.txt` MCMC chains:

| Parameter | Meaning | Typical range |
|-----------|---------|---------------|
| `pve` | Proportion of variance explained by all genotyped SNPs (SNP-heritability) | 0–1 |
| `pge` | Proportion of `pve` due to sparse (large-effect) component | 0–1 |
| `n_gamma` | Expected number of SNPs with sparse effects | 0–n_snps |
| `rho` | Proportion of phenotypic variance due to sparse effects directly | 0–1 |

**Architecture interpretation rules:**
- `pve < 0.05` → Low heritability in this sample; increase N before mapping
- `pve ≥ 0.05, pge < 0.10` → Highly polygenic; hundreds/thousands of small-effect variants;
  standard GWAS needs >> 5,000 individuals; consider polygenic scores
- `pve ≥ 0.05, pge ≥ 0.10` → Moderate sparse component; some detectable loci may emerge
  with ~2,000+ animals

**MCMC diagnostics:**
- Assess convergence via trace plots (post-burn-in chains should be stationary)
- Typical burnin: 10,000; sampling: 10,000 (increase to 100K/100K for publication)
- Check `n_gamma` posterior — if near 0 with very low `pge`, trait is near-entirely polygenic

---

## Lindley Process Local Score Analysis

### Problem solved

Standard Bonferroni/permutation significance requires an individual SNP to clear a genome-wide
threshold. A genomic locus may harbor many SNPs with modest, sub-threshold p-values that
collectively constitute strong evidence for association. The **Lindley process local score**
detects contiguous regions of accumulated signal where no single SNP would pass individually.
It complements Manhattan-style analysis rather than replacing it.

**Key contrast:**
- Bonferroni → single-SNP signal, controls FWER
- Lindley local score → regional cumulative signal, detects dense polygenic loci

### The Lindley recursion

```python
import numpy as np

def local_score(p_values: np.ndarray, xi: float) -> np.ndarray:
    """
    Compute per-SNP Lindley local scores.

    Parameters
    ----------
    p_values : array of per-SNP p-values (genome-order, chromosome-concatenated)
    xi       : cost parameter (natural log scale); see table below

    Returns
    -------
    s : array of local score values, same length as p_values
    """
    s = np.zeros(len(p_values))
    s[0] = max(0.0, -np.log(p_values[0]) - xi)
    for i in range(1, len(p_values)):
        s[i] = max(0.0, s[i - 1] - np.log(p_values[i]) - xi)
    return s
```

- `np.log` is **natural log** (ln); xi is on the ln scale — do NOT use log10
- Each SNP increments the score by `-ln(p_i) - xi`
- When p_i < e^{-xi}: increment is positive (signal SNP)
- When p_i > e^{-xi}: increment is negative (noise SNP decays the score)
- Score clamps at 0 — equivalent to a reflected random walk; resets after uninformative regions

### xi parameter (natural log scale)

| xi | ln threshold | ~p value | -log10(p) equiv | Interpretation |
|----|-------------|----------|-----------------|----------------|
| 2.5 | e^{-2.5} | 0.082 | 1.09 | Permissive: detects diffuse, spread-out signals |
| 3.0 | e^{-3.0} | 0.050 | 1.30 | Moderate |
| 3.5 | e^{-3.5} | 0.030 | 1.52 | Moderate-stringent |
| 4.0 | e^{-4.0} | 0.018 | 1.74 | Stringent: only concentrated, peaked signals |

The xi threshold is NOT per-SNP significance — it is the per-SNP cost. Many modest p-values
below the threshold accumulate a high regional score.

### Grid search strategy

Run all xi values (2.5, 3.0, 3.5, 4.0) for every trait. Interpret robustness as follows:

- **Significant at all xi (2.5–4.0):** Concentrated signal — a few SNPs drive the region;
  most confident finding
- **Significant only at low xi (2.5–3.0), not at 4.0:** Diffuse signal spread across many
  modest SNPs; treat with caution; may reflect LD block structure rather than a single causal locus
- **Not significant at any xi:** No regional accumulation above null expectation

Report the xi range over which each region is significant as a robustness descriptor.

### Permutation design and thresholds

```python
from numpy.random import SeedSequence, default_rng

def permutation_thresholds(p_values, xi, n_perm=2000, base_seed=42,
                            trait_name="", percentiles=(99, 99.5, 99.9)):
    """Genome-wide permutation null for Lindley max score."""
    seed_int = hash(trait_name) % (2**31)
    ss = SeedSequence((base_seed, seed_int, int(xi * 1000)))
    rng = default_rng(ss)

    null_maxima = np.zeros(n_perm)
    for b in range(n_perm):
        p_shuf = rng.permutation(p_values)
        null_maxima[b] = local_score(p_shuf, xi).max()

    return {f"p{pc}": np.percentile(null_maxima, pc) for pc in percentiles}
```

- Shuffling breaks spatial correlation; null captures max score expected by chance genome-wide
- 2,000 permutations gives stable 99th/99.5th percentile estimates; use 5,000 for publication
- `SeedSequence` from `(base_seed, hash(trait), int(xi*1000))` ensures reproducibility across
  traits and xi values while keeping seeds distinct

### Output files (per trait, per xi)

```
{out_root}/{trait}/xi{xi}/
  {trait}_local_scores_xi{xi}.tsv        # chr, pos, snp_id, p_wald, local_score
  {trait}_perm_maxima_xi{xi}.npz         # array of n_perm null maxima
  {trait}_thresholds_xi{xi}.csv          # threshold at 99th, 99.5th, 99.9th percentile

{out_root}/{trait}/
  grid_summary.csv                       # xi × threshold summary; one row per xi
```

### Interpreting local score vs. standard Manhattan

1. Cross-reference local score peaks with Manhattan p-values; a region with max local score
   above threshold but no sub-genome-wide Manhattan hit is a **sub-threshold polygenic locus**
2. Regions significant on Manhattan AND local score are doubly confirmed
3. Check LD structure of local score peaks (plink --ld-window) — a score plateau spanning a
   strong LD block is less informative than a narrow peak flanked by score resets
4. Local score boundaries (where score resets to 0) approximate the genomic extent of the
   associated region — useful for defining the candidate gene search window

### Compute requirements (HPC)

For large studies, submit as a Slurm array: one job per (trait × xi) combination.

```bash
# Array size = n_traits × n_xi_values (e.g., 20 traits × 4 xi = 80 jobs)
#SBATCH --array=0-79
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00   # 2000 permutations × 200K SNPs ~ 20–40 min per job
```

Each job loads the genome-wide p-value vector for one trait (~few MB), runs 2000 permutations
(pure Python/numpy loop; no external dependencies), and writes thresholds + npz to disk.

### Publishable methods template

> Contiguous genomic regions of accumulated association signal were identified using the
> Lindley process local score [Guedj et al. 2006; Bonhomme et al. 20XX]. For each trait,
> the per-SNP Wald p-values from GEMMA LMM were converted to local scores using the
> recursion s_i = max(0, s_{i-1} − ln(p_i) − ξ), evaluated across a grid of cost parameters
> ξ ∈ {2.5, 3.0, 3.5, 4.0} (natural log scale). Significance thresholds were empirically
> derived from 2,000 genome-wide permutations of the p-value vector (99th, 99.5th, and 99.9th
> percentiles of the null maximum score distribution). Permutation seeds were fixed per
> (trait, ξ) combination using NumPy SeedSequence for reproducibility. Regions exceeding the
> 99th percentile threshold at all four ξ values were classified as concentrated signals;
> regions significant only at ξ ≤ 3.0 were classified as diffuse signals warranting
> independent replication.

---

## Claude API Peer Review Agent Pattern

For GWAS pipelines, a post-analysis peer review step using Claude API provides automated
scientific audit before reporting. Implementation pattern:

```python
# peer_review.py (Snakemake script, always runs last)
import anthropic

client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system="You are a senior statistical geneticist and peer reviewer...",
    messages=[{"role": "user", "content": review_prompt}]
)
```

**Four mandatory review sections:**
1. Statistical validity — λ, kinship, thresholds, QC consistency
2. Biological plausibility — GO terms, catalog overlaps, gene hallucinations
3. Scientific nuances — sex covariate, MCMC convergence, locus independence
4. Missed analyses — stratification, conditional analysis, power

**Outputs**: `review_report.md`, `issues.json` (severity: critical/moderate/minor),
`proposed_changes.md` (formatted as mini-plan requiring user approval before implementation).

**Review → correction cycle:** User reads `proposed_changes.md` → approves → tells Claude Code
to implement. This enforces the approve-before-execute contract for all review-driven fixes.

---

## Key References

- Zhou X & Stephens M (2012) Genome-wide efficient mixed-model analysis for association studies.
  *Nature Genetics* 44:821–824. (GEMMA)
- Broman KW et al. (2019) R/qtl2: Software for mapping quantitative trait loci with high-dimensional
  data and multi-parent populations. *Genetics* 211:495–502.
- Parks BW et al. (2013) Genetic control of obesity and gut microbiota composition in response to
  HFHS diet in mice. *Cell Metabolism* 17:141–152. (HMDP obesity GWAS)
- Parker CC et al. (2016) Genome-wide association study of behavioral, physiological and gene
  expression traits in outbred CFW mice. *Nature Genetics* 48:919–926.
- Nicod J et al. (2022) Age and diet shape the genetic architecture of body weight in diversity
  outbred mice. *eLife* 11:e64329.
- Bennett BJ et al. (2015) High-density genotypes of inbred mouse strains. *G3* 5:1793–1806.
- Guedj M et al. (2006) A scored AUC metric reveals hidden efficacy improvements in head-to-head
  antibiotic trials. *Statistical Applications in Genetics and Molecular Biology* — original
  formalization of the local score for biological sequence analysis (Lindley recursion).
- Bonhomme M et al. — application of Lindley local score to plant GWAS (Arabidopsis); demonstrates
  detection of sub-threshold polygenic loci in defense trait mapping.
- *Implementation note:* Lindley recursion details (xi grid, permutation design, SeedSequence
  seeding) are documented from the plant_defense_syndrome_gwas project notebook
  (`lind_cons_grid_seed.py`); see Lindley Process section above.
