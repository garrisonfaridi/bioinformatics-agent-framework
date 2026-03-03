# Freelance Methods Templates

Copy-paste and adapt these for client reports and manuscript methods sections.
Adjust tool versions, genome builds, and parameter specifics to match your run.

---

## Bulk RNA-seq

Raw reads were quality-assessed with FastQC (v0.12) and adapter-trimmed using fastp (v0.23).
Trimmed reads were aligned to the GRCh38 reference genome (Ensembl release 110) using STAR
(v2.7.11a) with default parameters and gene-level expression quantified using salmon (v1.10)
in quasi-mapping mode. Differential expression analysis was performed in R (v4.3) using DESeq2
(v1.42) with the Wald test; results were shrunk using the ashr method and genes with Benjamini-
Hochberg adjusted p-value <0.05 and |log2 fold change| >1 were considered significant.

---

## Single-Cell RNA-seq

Raw FASTQ files were processed with Cell Ranger (v8.0) against the GRCh38-2024-A reference.
Cells were filtered using quality thresholds (nFeature_RNA: 200–8,000; percent mitochondrial
reads <20%) and doublets removed with scDblFinder (v1.16). Data were normalized with
SCTransform v2, dimensionality-reduced via PCA (50 PCs) and UMAP, and clusters identified
using the Louvain algorithm (resolution = 0.5) in Seurat (v5.0). Cell types were annotated
by SingleR (v2.4) using HumanPrimaryCellAtlasData and validated against canonical marker genes.

---

## WGS / WES Variant Calling

Paired-end reads were aligned to GRCh38 with BWA-MEM2 (v2.2.1) and processed following
GATK4 (v4.5) best practices: duplicate marking with Picard MarkDuplicates, base quality score
recalibration using dbSNP (v138) and Mills/1000G gold-standard indels, and variant calling
per-sample with HaplotypeCaller in GVCF mode followed by joint genotyping with GenotypeGVCFs.
Variants were filtered using VQSR (cohort ≥30) or GATK-recommended hard filters (small
cohort) and functionally annotated with Ensembl VEP (v111) including CADD and SpliceAI scores.

---

## ATAC-seq / ChIP-seq

Raw reads were trimmed with fastp (v0.23) and aligned to GRCh38 using BWA-MEM2 (v2.2.1);
duplicates were removed with Picard MarkDuplicates. For ATAC-seq, peaks were called with
MACS3 (v3.0) using the `--nomodel --extsize 200 --shift -100` parameters; for ChIP-seq,
narrow peaks were called with MACS3 in paired-end mode. Signal tracks (bigWig) were generated
with deepTools (v3.5) bamCoverage normalized by RPKM, and peak annotation and differential
accessibility/enrichment analysis were performed with DiffBind (v3.10) and ChIPseeker (v1.38).

---

## Generic QC Paragraph (add to all)

Quality control metrics across all samples were aggregated and visualized using MultiQC (v1.21).
All analyses were performed in a containerized environment (Docker/Singularity) to ensure
reproducibility; pipeline code and container definitions are available at [REPO_URL].
