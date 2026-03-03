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

For a panel of 92K SNPs (CFW), Bonferroni threshold = 0.05 / 92,000 ≈ **5.4×10⁻⁷**.

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
