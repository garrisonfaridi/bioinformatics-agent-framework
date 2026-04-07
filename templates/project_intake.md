# Project Intake

> Fill this out at session start. Load it with `@templates/project_intake.md` in the planning
> session alongside the relevant knowhow doc(s). Delete sections for inapplicable analysis types.

---

## Session Identity

```
run_id:          <YYYYMMDD_analysistype_descriptor>
                 # e.g. 20260310_gwas_cfwbodyweight, 20260310_rnaseq_colitis_timepoint
                 # format: date _ analysis type _ short project noun

analysis_type:   <gwas | rnaseq | singlecell | wgs | atac | custom>

project_dir:     ~/agent/bioinformatics-freelance/projects/<project-slug>/
```

---

## Organism & Reference

```
organism:        <Mus musculus | Homo sapiens | Arabidopsis thaliana | other>

genome_build:    <GRCm39/mm39 | GRCm38/mm10 | GRCh38/hg38 | GRCh37/hg19 | TAIR10 | other>
                 # GWAS note: confirm build matches annotation files; use liftOver if mismatched
                 # cfwMegaMUGA genotype files are mm10/GRCm38

annotation_release: <Ensembl release NNN | GENCODE vNN | RefSeq YYYY-MM>
```

---

## Data

```
data_location:   <local path, Dryad DOI, GEO accession, SRA project, internal server path>
                 # e.g. doi:10.5061/dryad.2rs41  |  /data/raw/project_name/  |  GSE123456

input_files:
  - <cfw.bed / cfw.bim / cfw.fam>         # GWAS: PLINK binary triad
  - <pheno.csv>                            # GWAS/RNA: phenotype table
  - <sample_R1.fastq.gz, sample_R2.fastq.gz>  # RNA-seq / WGS: FASTQ pairs
  - <filtered_feature_bc_matrix.h5>        # single-cell: Cell Ranger output
  - <tumor.bam, normal.bam>               # WGS somatic: tumor-normal BAM pair

n_samples_preqc:  <integer or range, e.g. 1200 | 24 samples across 4 conditions | ~500k cells>
n_samples_expected_postqc: <estimate, or "unknown — check after QC">
```

---

## Scientific Question

```
primary_question: >
  <One sentence. Specific trait/phenotype, population/tissue, expected direction of effect.>
  # e.g. "Which genomic loci in CFW outbred mice associate with sacrifice body weight (sacweight)
  #       after correcting for kinship and population structure?"
  # e.g. "Which genes are differentially expressed between colon biopsies of IBD patients
  #       at week 0 vs week 12 of treatment, after batch correction for sequencing run?"

secondary_questions:
  - <e.g. "Does the genetic architecture indicate polygenic or sparse-effect trait?">
  - <e.g. "Are any significant loci co-localized with published CFW body weight QTLs?">
  - <e.g. "Which cell types drive the DE signal in the inflamed tissue?">
  # Remove or add lines; keep to ≤3 secondary questions
```

---

## Analysis-Type Parameters

### If analysis_type = gwas

```
population_type: <CFW | BXD | HMDP | DO | CC | inbred strains | custom outbred>
                 # drives QC strategy: HWE filter OFF for inbred/RI; individual vs strain-level model

n_snps_raw:      <integer, e.g. 92734>
n_snps_expected_postqc: <estimate or "unknown">

phenotype_column: <exact column name in pheno.csv, e.g. sacweight>
phenotype_transform: <inverse_normal | log | none | rank>
                     # INT is standard for body weight and continuous physiological traits

covariates:      <sex | age_weeks | cage | batch | diet | none>
                 # CFW body weight: sex is mandatory; cage strongly recommended

qc_thresholds:
  maf:   <0.05>   # standard; lower (0.01) only for large N >5000
  geno:  <0.05>   # per-SNP missingness
  mind:  <0.10 | 0.30>
         # 0.10 = standard; 0.30 only if dataset has documented high missingness
         # (e.g. CFW MegaMUGA ~20% median per-sample missingness)
         # document justification in METHODS.md if using >0.10
  hwe_pval: <1e-6 | omit_for_inbred>

association_model: <gemma_lmm | gemma_bslmm | rqtl2_scan1 | emmax | plink2_glm>
kinship_method:    <gemma_gk1_centered | gemma_gk2_standardized | rqtl2_loco>
                   # gemma -gk 1 (centered) is recommended for individual GWAS

significance_strategy: <bonferroni | permutation_1000 | fdr_bh | lindley_local_score>
                       # bonferroni = 0.05 / n_snps_postqc; permutation for RI panels
                       # add lindley if expecting sub-threshold polygenic signal

bslmm_if_no_hits:
  burnin:   <25000>    # 10K = exploratory; 25K = practical; 100K = publication
  sampling: <25000>
  seed:     42

review_round: <1>    # increment for each rerun; drives round{N}/ output directory
```

---

### If analysis_type = rnaseq

```
design:          <condition_vs_control | timepoint_series | multi_factor>
                 # e.g. treated_vs_untreated | week0_week4_week12 | treatment*timepoint

conditions:
  - <condition_name: n_replicates>   # e.g. "colitis_week0: 6"
  - <condition_name: n_replicates>   # e.g. "colitis_week12: 6"

library_type:    <paired_end | single_end>
strandedness:    <forward | reverse | unstranded>
                 # check with infer_experiment.py (RSeQC) if unknown

aligner:         <STAR | HISAT2>
                 # STAR default for human/mouse; HISAT2 for low-memory HPC (<8 GB)

quantification:  <salmon_quasimapping | featureCounts | htseq>
                 # salmon preferred; featureCounts if BAMs already generated

de_tool:         <DESeq2 | edgeR | limma_voom>
                 # DESeq2 primary; limma-voom for large cohorts (>50 samples/group)

batch_correction: <combat_seq | limma_removeBatchEffect | none>
                  # ComBat-seq on raw counts before DESeq2; limma on log-normalized

contrasts:
  - <treated_vs_untreated>    # DESeq2 contrast vector: c("condition","treated","untreated")
  - <add more if multi-group>

significance_thresholds:
  padj:     <0.05>    # BH FDR; relax to 0.1 for exploratory
  log2fc:   <1.0>     # absolute log2 fold change cutoff
```

---

### If analysis_type = singlecell

```
platform:        <10x_Chromium_3prime | 10x_Chromium_5prime | 10x_Multiome | CITE-seq | Spatial | other>

processing_tool: <Seurat_v5 | scanpy | both>
                 # Seurat for R-native; scanpy for Python; "both" for cross-validation

n_cells_raw:     <estimate, e.g. ~15000 per sample>
n_samples:       <integer>
integration_needed: <yes | no | unknown>
                    # yes if multiple samples/batches; specify method below if yes

qc_thresholds:
  nFeature_RNA_min: <200>
  nFeature_RNA_max: <8000 | dataset-specific upper bound>
  nCount_RNA_min:   <500>
  pct_mito_max:     <20  # human | 10 # mouse>
  doublet_removal:  <scDblFinder | DoubletFinder | none>

normalization:   <LogNormalize | SCTransform_v2 | scran_pooling>
                 # SCTransform v2 recommended for integrations
                 # scran for datasets with very unequal library sizes

n_hvg:           <2000 | 3000>
integration_method: <Harmony | scVI | Seurat_RPCA | Seurat_CCA | none>
                    # Harmony: fast, same-species batches
                    # scVI: large atlas-scale (>100k cells)
                    # RPCA preferred over CCA for large datasets

clustering_resolution: <0.5>   # sweep 0.2–2.0; start at 0.5
annotation_method:     <SingleR | manual_markers | both>

modalities:      <RNA_only | RNA+ATAC | RNA+protein_CITE | RNA+spatial>
                 # for multiome: ArchR or Signac for ATAC; Seurat WNN for integration
```

---

### If analysis_type = wgs

```
variant_type:    <germline | somatic | both>

calling_strategy: <HaplotypeCaller_GVCF_joint | Mutect2_tumor_normal | both>

n_samples:       <integer>
cohort_size_for_vqsr: <≥30_use_VQSR | <30_use_hard_filters>
                      # VQSR requires ≥30 WGS samples for reliable training

bqsr_known_sites:
  - <dbSNP_vXXX>
  - <Mills_1000G_gold_standard_indels>
  - <1000G_phase1_SNPs>

annotation_tool: <VEP_v111 | ANNOVAR | SnpEff>
                 # VEP preferred; include CADD + SpliceAI plugins for clinical

somatic_extras:  <PON_n_normals | GetPileupSummaries_CalculateContamination | none>
                 # PON: build from ≥40 unmatched normals with CreateSomaticPanelOfNormals

target_regions:  <WGS_whole_genome | WES_exome_bait_BED | panel_BED_path>

qc_targets:
  mean_depth:       <≥30x>
  pct_bases_gte20x: <>90%>
  titv_ratio:       <~2.0_WGS | ~3.0_WES>
```

---

## Pipeline Framework

```
framework:       <Nextflow_DSL2 | Snakemake | WDL | script_only>
                 # Nextflow DSL2 default for new pipelines; Snakemake for quick/Python users

template_base:   <nextflow-rnaseq | nextflow-wgs | snakemake-rnaseq | singlecell-scanpy | singlecell-seurat | none>
                 # starter templates in ~/agent/bioinformatics-freelance/templates/

execution_target: <local_laptop | HPC_SLURM | AWS_Batch | GCP_GLS>

container_strategy: <Docker_local_Singularity_HPC | biocontainers | custom_Dockerfile>
                    # quay.io/biocontainers/ for standard tools; custom for uncommon combos
```

---

## Know-How Docs to Load

```
# Add @filepath for each relevant doc at session start (one per line)

knowhow_docs:
  - <@~/agent/bioinformatics-knowhow/gwas.md>              # GWAS, QTL, BSLMM, Lindley
  - <@~/agent/bioinformatics-knowhow/rnaseq.md>            # bulk RNA-seq QC, DE, batch
  - <@~/agent/bioinformatics-knowhow/singlecell.md>        # scRNA-seq, multi-omics, ATAC
  - <@~/agent/bioinformatics-knowhow/variant_calling.md>   # GATK4, Mutect2, VEP
  - <@~/agent/bioinformatics-knowhow/pipeline_dev.md>      # Nextflow vs Snakemake, nf-core
  - <@~/agent/bioinformatics-knowhow/freelance_methods.md> # publishable methods templates
  - <@~/agent/bioinformatics-knowhow/biomni.md>            # when/how to use Biomni MCP
  # Remove lines for docs not relevant to this project
```

---

## Prior Projects to Reference

```
# Projects whose patterns, configs, or results should inform this run

prior_projects:
  - path: <~/agent/bioinformatics-freelance/projects/mouse-obesity-gwas/>
    relevance: <e.g. "same dataset CFW + GEMMA; config.yaml and QC thresholds carry over">

  - path: <~/agent/bioinformatics-freelance/projects/project-slug/>
    relevance: <e.g. "same DE design with ComBat-seq — reuse batch correction code">

  # Remove section if no prior projects are relevant
```

---

## Deliverables

```
client_deliverables:
  - <QC report (MultiQC HTML)>
  - <Association results table (TSV + Manhattan/QQ plots)>
  - <METHODS.md (publishable methods paragraph per step)>
  - <Annotated results (VEP/GO enrichment)>
  - <Peer review report (review_report.md, issues.json)>
  # Edit to match actual contract scope

methods_md_required: <yes | no>
readme_required:      <yes | no>
peer_review_required: <yes | no>
```

---

## Narration & Trace Session Init

```
# Run these at session start after filling in run_id and project_dir above

trace_init_cmd: >
  python ~/agent/bioinformatics-freelance/scripts/trace_logger.py init-run \
    --run-id "$RUN_ID" \
    --project-dir "$PROJECT_DIR" \
    --task-description "<one-line description matching primary_question above>"

narrate_planning_cmd: >
  python ~/agent/bioinformatics-freelance/scripts/narrate.py \
    --phase planning --event decision \
    --message "<key design decision, e.g. N=1200, BSLMM 25K chains, mind=0.30 retained>" \
    --run-id "$RUN_ID" --project-dir "$PROJECT_DIR"

# Omit both if this is a quick exploratory session without a traced run
```

---

## Notes & Collaborator Context

```
collaborator:    <name / institution / contact — or "internal">

data_provenance: <"downloaded from Dryad DOI:XX by GF 2026-03-04" | "received from collaborator via Globus" | etc.>

known_issues:    <e.g. "high per-sample missingness in MegaMUGA (~20% median) — mind threshold justified in METHODS.md"
                       "batch confound between sequencing runs 1–3 and 4–6 — ComBat-seq required"
                       "sex not recorded for 12 samples — exclude from sex-stratified analysis">

prior_attempts:  <"pilot run N=500 established working Snakemake pipeline; no Bonferroni hits; BSLMM PVE=0.053">

open_questions:  <e.g. "Should Lindley local score be added to this run?"
                        "Is sex available in pheno.csv? Check column names before pipeline start.">

notes: |
  <Free text. Paste client emails, experimental design notes, known data quirks,
  or anything that doesn't fit the structured fields above.>
```
