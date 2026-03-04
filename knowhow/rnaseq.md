---
last_verified: 2026-03-04
tool_versions:
  fastp: "0.23.4"
  star: "2.7.11a"
  salmon: "1.10.0"
  deseq2: "1.42.0"
  multiqc: "1.21"
  featurecounts: "2.0.6"
---

# Bulk RNA-seq Know-How

## FastQC / fastp Flags to Watch

- **Per-base quality** — flag if median Phred <28 in last 10 bases; trim with fastp `--cut_right`
- **Adapter content** — fastp auto-detects; manually specify if not found
- **Duplication rate** — >60% suspicious for low-input; check library prep, not always a problem
- **GC content** — bimodal = contamination; narrow peak shift = systematic bias
- **Sequence length** — check uniformity post-trim; very short reads (<30 bp) → discard

## STAR vs HISAT2

| | STAR | HISAT2 |
|-|------|--------|
| Speed | Faster | Slower |
| Memory | ~32 GB (human) | ~8 GB |
| Novel splice sites | Excellent | Good |
| Recommendation | **Default for human/mouse** | Low-memory HPC nodes |

STAR key params: `--outSAMtype BAM SortedByCoordinate --outSAMattributes NH HI AS NM`
Index: `--genomeSAindexNbases 14` for small genomes (<1 Gb)

## salmon vs featureCounts

- **salmon** (quasi-mapping): fast, bias-corrected TPMs, outputs `quant.sf`; import with `tximeta`
- **featureCounts**: count-based, needs BAM; use `-p -B -C` for paired-end, stranded `-s 1/2`
- **When to use featureCounts**: legacy pipelines, when BAMs already generated, intron/exon split counts

## DESeq2 / edgeR / limma-voom Decision

| | DESeq2 | edgeR | limma-voom |
|-|--------|-------|-----------|
| Sample size | ≥3/group | ≥3/group | Scales to large |
| Recommended | **Primary** | Multi-group, GLM | Large cohorts, arrays |
| Import | `DESeqDataSetFromTximeta` | `DGEList` | `voom()` after DGEList |

DESeq2 flow: `DESeqDataSet → DESeq() → results(contrast=) → lfcShrink(type="ashr")`

## ComBat-seq Batch Correction

- Apply to **raw counts** before DESeq2 (pass corrected counts to `DESeqDataSetFromMatrix`)
- Requires batch vector; optionally preserve biological groups with `group=`
- For normalized data: `limma::removeBatchEffect(logcounts, batch=)`

## Filtering

- Remove genes with <10 counts across all samples before DE
- DESeq2 auto-filters via `independentFiltering=TRUE`; edgeR: `filterByExpr()`

## Multiple Testing

- Use **Benjamini-Hochberg** FDR (padj <0.05) as default threshold
- For exploratory: relax to padj <0.1 + |log2FC| >1
- Avoid p-value cutoffs without FDR adjustment
