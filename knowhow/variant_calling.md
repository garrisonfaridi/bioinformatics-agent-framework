# Variant Calling Know-How

## GATK4 Best Practices — Germline

1. **Alignment**: BWA-MEM2 → `SortSam` → `MarkDuplicates` → `BaseQualityScoreRecalibration (BQSR)`
2. **Calling**: `HaplotypeCaller -ERC GVCF` per sample
3. **Joint genotyping**: `GenomicsDBImport` → `GenotypeGVCFs`
4. **Filtering**: VQSR (≥30 WGS samples) or hard filters (<30 samples)

BQSR requires known sites: dbSNP + Mills_and_1000G_gold_standard indels + 1000G_phase1 SNPs

## Hard Filter Thresholds (germline, small cohorts)

SNPs: `QD < 2.0 || FS > 60.0 || MQ < 40.0 || MQRankSum < -12.5 || ReadPosRankSum < -8.0`
Indels: `QD < 2.0 || FS > 200.0 || ReadPosRankSum < -20.0`

## Germline vs Somatic

| | Germline | Somatic |
|-|----------|---------|
| Tool | HaplotypeCaller | Mutect2 |
| Input | Single/cohort normal | Tumor + matched normal |
| Filtering | VQSR / hard filter | `FilterMutectCalls` + PON |
| VAF | ~0.5 or 1.0 | Any (0.01+) |

Mutect2 extras: `GetPileupSummaries → CalculateContamination → FilterMutectCalls`
Panel of Normals (PON): build with `CreateSomaticPanelOfNormals` from ≥40 unmatched normals

## VEP Annotation

```bash
vep --input_file variants.vcf --output_file annotated.vcf \
    --format vcf --vcf --everything \
    --cache --offline --assembly GRCh38 \
    --plugin CADD,whole_genome_SNVs.tsv.gz \
    --plugin SpliceAI,snv=spliceai_scores.masked.snv.hg38.vcf.gz
```

Key fields: `IMPACT`, `Consequence`, `SIFT`, `PolyPhen`, `AF`, `gnomADg_AF`

## QC Metrics

| Metric | Expected (WGS 30x) | Flag if |
|--------|-------------------|---------|
| Ti/Tv ratio | ~2.0 (WGS), ~3.0 (WES) | <1.8 = likely false positives |
| Mean depth | ≥30x | <15x for germline |
| % bases ≥20x | >90% | <80% |
| Het/Hom ratio | ~1.5–2.5 | >3 = contamination |
| dbSNP overlap | >95% known SNPs | <90% = QC failure |

## Structural Variants

- Short-read SV: `Manta` (recommended) + `Lumpy`; merge with `SURVIVOR`
- Long-read SV: `Sniffles2` (ONT/PacBio)
