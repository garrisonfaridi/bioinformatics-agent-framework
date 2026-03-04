# Adversarial test: wrong genome build in BIM file

## What was injected

The BIM file contains SNP positions on hg19/GRCh37 coordinates, but the annotation
files reference mm10/GRCm38. This creates systematic position mismatches when
annotating top hits.

## What the agent should detect

- Annotation step produces no gene hits near top SNPs
- Sequential thinking should be triggered when GWAS hits have no nearby genes
- Peer review should flag this as a `computational` or `reproducibility` issue

## How to run

```bash
bash tests/adversarial/wrong_genome_build/run_test.sh
```
