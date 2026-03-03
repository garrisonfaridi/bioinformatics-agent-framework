# Scientific Peer Review — CFW Mouse Body Weight GWAS

**Model**: claude-opus-4-6  
**Critical issues**: 2  
**Moderate issues**: 10  
**Minor issues**: 3  

---



# Peer Review: Mouse Obesity GWAS Pipeline (CFW Outbred Mice)

---

## 1. Statistical Validity

### Genomic Inflation Factor (λ_GC = 1.0935)

The reported λ_GC of 1.0935 is **outside the ideal range of 0.95–1.10**, though only marginally so. For a sample of N~453 with 16,710 SNPs in outbred mice, this value warrants attention. The pipeline's own warning flag reads "NO," but λ > 1.05 in a mixed-model analysis (which should already account for relatedness) suggests either (a) the kinship matrix is not fully correcting for population structure, (b) there is residual confounding (e.g., unmeasured covariate such as sex, batch, cage effects), or (c) the QC pipeline has introduced subtle biases. In fairness, λ = 1.09 is not catastrophic and is sometimes observed in outbred populations even with LMM correction, but the absence of covariates (see Section 3) makes this more concerning. **Severity: MODERATE.**

### Bonferroni Threshold Calculation

The Bonferroni threshold is reported as 2.992 × 10⁻⁶ = 0.05 / 16,710. This is **correctly calculated** from the post-QC SNP count (16,710), not the pre-QC count (92,734). This is appropriate. **No issue.**

### QC Filters

The applied filters are:
- **MAF > 0.05**: Standard and appropriate for outbred mice.
- **Genotype missingness (geno ≤ 5%)**: Appropriate.
- **Individual missingness (mind ≤ 30%)**: This is **extremely lenient**. The standard threshold for individual-level missingness in both human and mouse GWAS is ≤ 10% (mind ≤ 0.10), and many studies use ≤ 5%. A 30% threshold means individuals missing nearly one-third of their genotypes are retained. This can introduce substantial noise, inflate type I error through differential missingness, and degrade kinship matrix estimation. The fact that 47 samples were removed even at this lenient threshold (47/500 = 9.4%) suggests there may be serious genotyping quality issues in a subset of samples. **Severity: CRITICAL.**

### Dramatic SNP Attrition

The QC summary shows a striking pattern: from 92,734 input SNPs, 61,954 pass MAF > 0.05 and 34,321 pass geno ≤ 5%, but only 16,710 survive the combined filter. This means **82% of SNPs were removed during QC**. While some attrition is expected, losing >80% of variants is unusual and suggests either (a) the genotyping platform had substantial quality issues, (b) the input data contained many monomorphic or near-monomorphic markers inappropriate for this population, or (c) the joint filtering is overly aggressive. Notably, 61,954 + 34,321 > 92,734 (i.e., these are not disjoint sets), so the intersection yielding only 16,710 implies ~45,000 SNPs failed geno ≤ 5% among the MAF-passing set — indicating widespread missingness at the variant level. This level of attrition reduces genomic coverage and power substantially. The pipeline should report whether the surviving 16,710 SNPs provide adequate genome-wide coverage (e.g., average inter-SNP distance). **Severity: MODERATE.**

### Sample Size Consistency Across Steps

There is an inconsistency that requires careful tracking:
- FAM file: N = 500
- Valid phenotype: N = 481 (19 missing phenotype)
- Post-QC (mind filter): N = 453 (47 removed for missingness)
- BSLMM architecture summary references "N~300" as a "pilot subset"

The first three numbers are internally consistent (500 → 453 after mind, of which some also lack phenotype). However, the architecture summary states "pilot sample size (N~300)" and recommends re-running with "full N=1,200." This raises the question: **was the BSLMM actually run on only ~300 samples**, a further subset of the 453 post-QC individuals? If so, this is nowhere documented in the pipeline outputs, and it would mean the BSLMM and LMM may have been run on different sample sets. The reference to N=1,200 suggests this entire dataset is a pilot subset of a larger study (likely the Parker/Nicod CFW cohort). This should be made explicit. **Severity: MODERATE.**

### Inverse-Normal Transformation

The INT was correctly applied — mean 0.0000 and SD 0.9995 are consistent with proper rank-based inverse-normal transformation. This is an appropriate choice for body weight, which can exhibit right skew, particularly in populations with potential obesity outliers (max = 53.2 g). However, INT discards information about effect sizes in natural units (grams), making beta coefficients less interpretable biologically. A sensitivity analysis using untransformed or log-transformed phenotype would be valuable. **Severity: MINOR.**

### Kinship Matrix

The review prompt references "-gk 1" (centered relatedness matrix), which is the standard GEMMA approach and appropriate for CFW outbred mice. However, the pipeline outputs do not explicitly confirm that the kinship matrix was computed on the same QC-filtered SNP set and sample set used for association testing. If the kinship matrix was computed pre-QC (on 92,734 SNPs and 500 samples) but association was run post-QC (16,710 SNPs, 453 samples), this mismatch could affect LMM performance. **Severity: MODERATE (conditional — would be CRITICAL if confirmed).**

---

## 2. Biological Plausibility

### GWAS Hits and Genomic Context

No SNPs reached genome-wide significance (Bonferroni). Four SNPs reached suggestive significance, with the two lead SNPs both on **chromosome 15** at positions 47.9 Mb and 46.0 Mb (~1.9 Mb apart). Key observations:

- **Proximity of lead signals**: The two lead SNPs are ~1.9 Mb apart on chr15. Whether these represent one or two independent signals cannot be determined without LD information or conditional analysis. In CFW mice (with short LD blocks, typically 0.5–2 Mb), these could plausibly be independent, but this must be verified.

- **Chr15:46–48 Mb region**: This region in the mouse genome contains several genes. Without explicit functional annotation provided in the outputs, I cannot fully assess biological plausibility. However, this region does not overlap with the major body weight QTLs identified in the landmark CFW GWAS by **Nicod et al. (2016, Cell Systems)** and **Parker et al. (2016, Nature Genetics)**, which identified body weight loci on chromosomes 1, 4, 6, and others. The absence of overlap with known loci could mean (a) these are false positives (they are only suggestive), (b) they are novel signals not previously detected, or (c) the reduced SNP panel has different tagging properties. **Severity: MODERATE — suggestive hits should not be over-interpreted without replication.**

### BSLMM Architecture

The BSLMM results deserve careful interpretation:

- **PVE = 0.053 [0.002, 0.184]**: This estimate is dramatically lower than published SNP-heritability for body weight in CFW mice. Parker et al. (2016) reported h² ≈ 0.20–0.40 for body weight. The architecture summary correctly identifies this discrepancy and attributes it to sample size, reduced SNP panel, and uninformative priors. This self-critique is appropriate and well-reasoned.

- **PGE = 0.509 [0.034, 0.981]**: The 95% CI spans nearly the entire [0, 1] interval, making this estimate **completely uninformative**. The pipeline cannot distinguish between a purely polygenic and a purely sparse architecture. The summary correctly flags this.

- **n_γ = 16.7 [6, 34]**: The expected number of sparse-effect loci is consistent with moderate polygenicity, but given the uninformative PGE, this number has limited interpretive value.

- **The architecture summary's self-assessment is commendably honest** about the limitations. However, the "CONCLUSION" line stating "moderate sparse component" is potentially misleading given that the same paragraph immediately disclaims it. The conclusion should lead with the uninformative nature of the posteriors. **Severity: MINOR.**

### Missing Functional Annotation

The pipeline does not appear to include:
- Gene-level annotation of lead/suggestive SNPs
- GO term enrichment analysis
- GWAS Catalog overlap analysis
- Pathway analysis

The review template asks about these, but the outputs contain no such results (the biomni_qc_report is truncated but does not appear to contain functional annotations). Without these, the biological relevance of the suggestive hits cannot be assessed. **Severity: MODERATE.**

---

## 3. Scientific Nuances

### Sex as a Covariate — CRITICAL Issue

The QC summary reports: **"453 male, 0 female, 0 unknown."** This clarifies that the cohort is entirely male, which resolves the biomni_qc_report's Flag 1 concern about sex composition. An all-male cohort eliminates the need for sex as a covariate. However, several issues remain:

1. **The biomni_qc_report was generated before or without access to the sex information from QC**, since it flags sex composition as unknown. This indicates a disconnect between pipeline stages — the biological QC module should have access to downstream QC outputs.

2. **The mean body weight of 38.41 g is consistent with an all-male CFW cohort** at standard age (8–12 weeks), validating the phenotype distribution.

3. **However**, an all-male cohort means these results are only generalizable to males. Sex-specific genetic effects on body weight are well-documented in mice, and loci with female-specific effects will be completely missed. This is not a flaw per se but should be explicitly stated as a limitation. **Severity: MINOR (limitation, not error, given the cohort is genuinely all-male).**

### MCMC Convergence

The pipeline outputs do not include:
- Trace plots for PVE, PGE, π, or n_γ
- Effective sample size (ESS) estimates
- Gelman-Rubin R̂ statistics from multiple chains
- Number of MCMC iterations, burn-in length, or thinning interval

Without these diagnostics, **MCMC convergence cannot be assessed**. The extremely wide posteriors for PGE could reflect either genuine uncertainty (given the sample size) or non-convergence. The architecture summary recommends running 2–3 independent chains, which implies this was **not done**. A single MCMC chain without convergence diagnostics is insufficient for publication-quality inference. **Severity: CRITICAL for BSLMM results; does not affect LMM association results.**

### Independence of Lead SNPs

The two lead SNPs on chr15 are ~1.9 Mb apart. The pipeline does not report:
- Whether LD-based clumping was applied
- The LD (r²) between these two SNPs
- Whether conditional analysis was performed

In CFW outbred mice, LD decays rapidly (r² < 0.2 within ~0.5–1 Mb; Nicod et al. 2016), so 1.9 Mb separation likely means these are in low LD. However, CFW mice can have longer-range LD in specific genomic regions due to founder haplotype structure. Without explicit LD calculation, independence cannot be confirmed. **Severity: MODERATE.**

### Pilot Sample Size Adequacy

The effective sample size for association testing is approximately N = 453 (or possibly ~300 for BSLMM, as suggested by the architecture summary). For a trait with h² ≈ 0.20–0.40 and a moderately polygenic architecture:

- **For GWAS discovery**: With N = 453 and 16,710 SNPs, power to detect individual loci explaining ≥2% of phenotypic variance is reasonable (~60–80% at Bonferroni threshold), but power for loci explaining <1% of variance is very low (<20%). The absence of genome-wide significant hits is therefore unsurprising and should not be interpreted as evidence of absence.

- **For BSLMM**: N = 300–453 is clearly insufficient for informative posterior estimation, as confirmed by the wide credible intervals. This is acknowledged in the pipeline output.

- **For comparison**: Parker et al. (2016) used N ≈ 1,200 CFW mice and ~500K SNPs. The current study has ~37% of the sample size and ~3% of the SNP density. **Severity: MODERATE — the pipeline acknowledges this but should quantify expected power more formally.**

### Population Structure in CFW Mice

CFW mice are an outbred stock with known population structure (Yalcin et al. 2010; Parker et al. 2016). The centered kinship matrix should capture relatedness, but:
- No PCA plot is provided to visualize population structure
- No assessment of whether the kinship matrix eigenvalue distribution suggests strong structure
- λ_GC = 1.09 post-LMM correction suggests possible residual structure

CFW mice from the Parker/Nicod studies were bred from a specific supplier colony, and batch/cage/litter effects can create environmental confounding correlated with genetic structure. The absence of any covariates beyond kinship (no cage, no litter, no batch, no age) is concerning. **Severity: MODERATE.**

---

## 4. Missed Analyses

### Recommended Additional Analyses

1. **Covariate inclusion**: Age at weighing, cage/litter, and batch should be included as covariates if available. Body weight in mice is strongly influenced by cage environment (social hierarchy, food competition) and age. The absence of any covariates beyond the kinship matrix is a significant gap. **Priority: HIGH.**

2. **Sensitivity analysis excluding phenotypic outliers**: The biomni_qc_report correctly flags the maximum of 53.2 g. Samples >3 SD from the mean (>52.6 g in raw units) should be identified and the analysis re-run excluding them. **Priority: MEDIUM.**

3. **QQ plot diagnostics**: While λ_GC is reported, the actual QQ plot should be visually inspected for systematic early departure (suggesting confounding) versus late departure (suggesting true signal). The pipeline should provide this plot. **Priority: HIGH.**

4. **Comparison with published CFW body weight GWAS results**: Nicod et al. (2016, Cell Systems) and Parker et al. (2016, Nature Genetics) identified specific body weight QTLs in CFW mice. The suggestive hits on chr15 should be explicitly compared against these published loci. If there is no overlap, this should be discussed. **Priority: HIGH.**

5. **Conditional analysis at suggestive loci**: Given two suggestive hits on chr15, a conditional analysis (fitting the lead SNP as a covariate and re-testing the second) would clarify whether these are independent signals. **Priority: MEDIUM.**

6. **LD decay and SNP coverage assessment**: Given the dramatic SNP attrition (82% lost in QC), the pipeline should assess whether the remaining 16,710 SNPs provide adequate coverage across the genome. Average inter-SNP distance should be reported, and any large gaps (>5 Mb) should be flagged. **Priority: HIGH.**

7. **HWE filtering**: No Hardy-Weinberg equilibrium filter is mentioned in the QC summary. While HWE deviations are more complex in outbred populations, extreme departures (p < 1 × 10⁻⁶) typically indicate genotyping error and should be filtered. **Priority: MEDIUM.**

8. **Sex-stratified analysis**: Not applicable here (all males), but should be performed if female data become available.

9. **BSLMM convergence diagnostics**: Multiple independent chains, ESS, R̂ statistics, and trace plots are essential before any BSLMM result is reported. **Priority: HIGH.**

10. **Polygenic score cross-validation**: As suggested in the architecture summary, a leave-one-out or k-fold cross-validation of polygenic prediction accuracy would provide a more robust estimate of SNP-heritability than the single-chain BSLMM. **Priority: MEDIUM.**

---

## Issues Summary

```json
[
  {
    "section": "Statistical Validity",
    "severity": "CRITICAL",
    "issue": "Individual missingness threshold excessively lenient (mind ≤ 30%)",
    "details": "The pipeline uses a 30% individual-level missingness threshold, far exceeding the standard 10% (or stricter 5%) used in GWAS. 47 samples were removed even at this lenient threshold, suggesting serious genotyping quality issues. Retaining individuals with up to 30% missing genotypes introduces noise, degrades kinship estimation, and may inflate type I error through differential missingness patterns.",
    "recommendation": "Re-run QC with mind ≤ 0.10 (10%). Investigate the 47 removed samples and any samples retained with 10-30% missingness. Report per-sample missingness distribution and justify any threshold above 10%."
  },
  {
    "section": "Statistical Validity",
    "severity": "MODERATE",
    "issue": "Genomic inflation factor λ_GC = 1.094 exceeds ideal range after LMM correction",
    "details": "Post-LMM λ_GC should be close to 1.00 if relatedness and population structure are adequately controlled. A value of 1.094 suggests residual confounding, possibly from unmeasured covariates (cage, litter, batch, age) or inadequate kinship correction. The pipeline's own warning threshold appears set too high.",
    "recommendation": "Include available covariates (age, cage, batch, litter). Verify kinship matrix was computed on post-QC SNP and sample sets. Re-assess λ_GC after covariate inclusion. Consider lowering the warning threshold to λ > 1.05."
  },
  {
    "section": "Statistical Validity",
    "severity": "MODERATE",
    "issue": "Extreme SNP attrition (82% of input SNPs removed during QC)",
    "details": "Only 16,710 of 92,734 input SNPs survived QC, suggesting either widespread genotyping quality issues or an inappropriate SNP panel. This dramatically reduces genomic coverage and statistical power. The pipeline does not report whether surviving SNPs provide adequate genome-wide coverage.",
    "recommendation": "Report per-chromosome SNP density and average inter-SNP distance post-QC. Identify genomic regions with no coverage. Investigate whether the high attrition reflects platform issues or data quality problems. Consider less aggressive QC or imputation to recover variants."
  },
  {
    "section": "Statistical Validity",
    "severity": "MODERATE",
    "issue": "Sample size discrepancy: BSLMM references N~300 but QC yields N=453",
    "details": "The architecture summary references 'pilot sample size (N~300)' and recommends re-running with 'full N=1,200'. It is unclear whether BSLMM was run on a further subset of the 453 post-QC samples or on all of them. This inconsistency undermines reproducibility.",
    "recommendation": "Clarify and document the exact sample size used for each analysis step. If BSLMM was run on a subset, explain the subsetting rationale and ensure LMM and BSLMM used the same samples."
  },
  {
    "section": "Statistical Validity",
    "severity": "MODERATE",
    "issue": "Kinship matrix computation details not documented",
    "details": "The pipeline does not confirm whether the kinship matrix was computed on the post-QC SNP set and sample set. Mismatch between kinship computation and association testing sets can lead to incorrect variance component estimation.",
    "recommendation": "Explicitly document the SNP set and sample set used for kinship matrix computation. Ensure kinship is computed on post-QC data."
  },
  {
    "section": "Scientific Nuances",
    "severity": "CRITICAL",
    "issue": "No MCMC convergence diagnostics for BSLMM",
    "details": "The BSLMM was apparently run as a single chain without reporting trace plots, effective sample size (ESS), Gelman-Rubin R-hat statistics, number of iterations, burn-in, or thinning interval. Without convergence diagnostics, BSLMM posteriors are unreliable. Wide credible intervals could reflect non-convergence rather than genuine uncertainty.",
    "recommendation": "Run at minimum 3 independent MCMC chains with different random seeds. Report ESS for all key parameters (PVE, PGE, π, n_γ). Compute Gelman-Rubin R-hat (target <1.1). Provide trace plots. Report total iterations, burn-in, and thinning."
  },
  {
    "section": "Scientific Nuances",
    "severity": "MODERATE",
    "issue": "No covariates included beyond kinship matrix",
    "details": "The pipeline does not include any covariates (age, cage, litter, batch, diet) in the association model. Mouse body weight is strongly influenced by environmental factors, and cage effects in particular can be substantial. CFW studies typically include cage as a covariate. Omitted covariates may explain the elevated λ_GC.",
    "recommendation": "Include all available environmental covariates (age at weighing, cage, litter, batch, diet condition) in the LMM. Re-assess λ_GC and association results."
  },
  {
    "section": "Scientific Nuances",
    "severity": "MODERATE",
    "issue": "No LD assessment or clumping for lead SNPs",
    "details": "Two lead suggestive SNPs on chr15 are ~1.9 Mb apart, but no LD (r²) calculation or formal clumping procedure is reported. Independence of signals cannot be confirmed without this.",
    "recommendation": "Compute pairwise LD between all suggestive SNPs. Apply LD clumping (e.g., r² < 0.1, 1 Mb window). Perform conditional analysis to assess independence."
  },
  {
    "section": "Biological Plausibility",
    "severity": "MODERATE",
    "issue": "No functional annotation or pathway analysis of suggestive hits",
    "details": "The pipeline does not report genes near suggestive SNPs, GO term enrichment, GWAS Catalog overlap, or pathway analysis. Biological plausibility of chr15:46-48 Mb hits cannot be assessed.",
    "recommendation": "Annotate all suggestive SNPs with nearby genes (±500 kb). Perform GO/pathway enrichment if sufficient genes are implicated. Compare lead loci against Nicod et al. (2016) and Parker et al. (2016) CFW body weight QTLs."
  },
  {
    "section": "Biological Plausibility",
    "severity": "MODERATE",
    "issue": "No comparison with published CFW body weight GWAS loci",
    "details": "Parker et al. (2016, Nature Genetics) and Nicod et al. (2016, Cell Systems) published body weight QTLs from larger CFW cohorts. The pipeline does not compare suggestive hits against these known loci, missing an opportunity for validation or informative null results.",
    "recommendation": "Compile a table of published CFW body weight QTLs and compare with current suggestive and nominally significant loci. Discuss concordance or lack thereof."
  },
  {
    "section": "Missed Analyses",
    "severity": "MODERATE",
    "issue": "No HWE filtering applied",
    "details": "The QC pipeline does not include Hardy-Weinberg equilibrium testing. Extreme HWE deviations often indicate genotyping errors (e.g., cluster separation issues) and should be filtered even in outbred populations.",
    "recommendation": "Apply HWE filter (p < 1e-6 is standard for outbred populations). Report the number of SNPs removed."
  },
  {
    "section": "Missed Analyses",
    "severity": "MODERATE",
    "issue": "No sensitivity analysis for phenotypic outliers",
    "details": "The maximum body weight of 53.2 g is extreme (~3.1 SD above mean). No sensitivity analysis excluding potential outliers is performed. Extreme values can disproportionately influence association results, especially after INT (where they are mapped to distribution tails).",
    "recommendation": "Identify all samples >3 SD from mean in raw phenotype. Re-run association excluding these samples. Compare results with and without outliers."
  },
  {
    "section": "Missed Analyses",
    "severity": "MINOR",
    "issue": "No power analysis reported",
    "details": "Given the modest sample size and reduced SNP panel, a formal power analysis would contextualize the null result (no genome-wide significant hits) and inform whether this is expected.",
    "recommendation": "Calculate expected power for detecting QTLs of various effect sizes (1%, 2%, 5% PVE) at the Bonferroni threshold given N=453 and 16,710 SNPs."
  },
  {
    "section": "Missed Analyses",
    "severity": "MINOR",
    "issue": "No assessment of genomic coverage post-QC",
    "details": "With only 16,710 SNPs remaining, genome-wide coverage may be inadequate in some regions. No per-chromosome SNP density or coverage metrics are reported.",
    "recommendation": "Report per-chromosome SNP counts, average and maximum inter-SNP distances, and flag any regions >5 Mb without markers."
  },
  {
    "section": "Statistical Validity",
    "severity": "MINOR",
    "issue": "Disconnect between biomni_qc_report and actual cohort metadata",
    "details": "The biomni_qc_report flags sex composition as unknown and raises it as a major concern, but the QC summary clearly shows 453 males, 0 females. This indicates the biological QC module does not integrate downstream QC outputs, reducing its utility.",
    "recommendation": "Ensure the biological QC module receives and integrates sex and covariate information from the genotype QC step before generating its report."
  }
]
```

---

## Proposed Changes

### Change 1: Tighten Individual Missingness Threshold
- **File to modify**: QC script (e.g., `scripts/02_qc.sh` or equivalent PLINK call)
- **Change description**: Change `--mind 0.30` to `--mind 0.10`. This is the standard threshold for individual-level genotype missingness. Optionally, implement a two-stage QC: first remove individuals with >10% missingness, then re-calculate per-SNP missingness before applying `--geno 0.05`.
- **Expected impact**: Will remove additional low-quality samples (likely 10–30 more). May slightly reduce sample size but will substantially improve data quality and kinship estimation. May also recover some SNPs that currently fail geno ≤ 5% due to missingness concentrated in low-quality individuals.

### Change 2: Include Environmental Covariates in LMM
- **File to modify**: Association analysis script (e.g., `scripts/03_gwas.sh` or GEMMA command)
- **Change description**: Add a covariate file (`-c covariates.txt`) to the GEMMA LMM call containing age at weighing, cage ID, and batch/cohort as fixed effects. If cage has many levels, consider using cage as a random effect or including litter instead.
- **Expected impact**: Should reduce λ_GC closer to 1.00 and reduce residual confounding. May alter the significance of suggestive hits. Essential for valid inference.

### Change 3: Add HWE Filter to QC Pipeline
- **File to modify**: QC script
- **Change description**: Add `--hwe 1e-6` to the PLINK QC command (after sample-level QC).
- **Expected impact**: Will remove SNPs with extreme HWE deviation indicative of genotyping error. Typically removes a small number of SNPs but prevents spurious associations.

### Change 4: Run Multiple BSLMM Chains with Convergence Diagnostics
- **File to modify**: BSLMM script (e.g., `scripts/04_bslmm.sh`)
- **Change description**: Run GEMMA BSLMM with at least 3 independent chains using different `-seed` values. Increase burn-in and total iterations if needed (recommend ≥1M iterations with 250K burn-in, or verify ESS > 200 for all parameters). Add a post-processing script to compute Gelman-Rubin R̂ and ESS across chains.
- **Expected impact**: Will provide essential convergence diagnostics. If chains have not converged, current BSLMM results are unreliable. If they have converged, this validates the (admittedly wide) posterior intervals.

### Change 5: Add Functional Annotation and Literature Comparison
- **File to modify**: Post-GWAS analysis script (e.g., `scripts/05_annotation.R` or new script)
- **Change description**: For all SNPs with p < 5 × 10⁻⁵: (1) annotate nearest genes within ±500 kb using a mouse gene annotation database (Ensembl/GENCODE for mm10/mm39); (2) compare loci against Parker et al. (2016) and Nicod et al. (2016) published QTLs; (3) perform LD-based clumping and conditional analysis.
- **Expected impact**: Will contextualize suggestive hits biologically and against prior literature. Essential for manuscript quality.

### Change 6: Sensitivity Analysis for Outliers
- **File to modify**: Phenotype processing script (e.g., `scripts/01_phenotype.R`)
- **Change description**: Add a step that flags samples with raw phenotype values >3 SD from the mean. Re-run the full association pipeline excluding these samples and compare results.
- **Expected impact**: Will assess robustness of suggestive signals to extreme phenotype values. If results change substantially, the outlier influence must be reported.

---

## Overall Assessment

This pipeline represents a reasonable first-pass analysis of a pilot CFW mouse body weight GWAS, but it has **two critical issues** (excessively lenient individual missingness threshold; absent BSLMM convergence diagnostics) and **multiple moderate issues** (missing covariates, no functional annotation, elevated λ_GC, no HWE filter, no comparison to published CFW QTLs) that must be addressed before the results can be considered publication-ready. The pipeline's self-awareness regarding BSLMM limitations is commendable, but this self-awareness needs to be paired with corrective action (multiple chains, convergence diagnostics). The suggestive hits on chromosome 15 are interesting but should not be emphasized without functional annotation, conditional analysis, and replication in the full N=1,200 cohort. The fundamental limitation remains the dramatically reduced SNP panel (16,710 from 92,734) which warrants investigation of the underlying cause and consideration of genotype imputation.