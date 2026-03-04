# Expected outputs for CFW mouse GWAS regression test

These are the reference values the regression test checks against.
Update them when the pipeline or dataset changes intentionally.

## Expected values

| Check | Expected |
|-------|----------|
| Post-QC SNP count | 15,000 – 18,000 |
| Top hit chromosome | chr2 |
| Lambda GC | 0.98 – 1.05 |

## How to update

If the pipeline is updated and outputs change intentionally:
1. Run the full pipeline on the reference CFW dataset
2. Record new expected values in this file
3. Update `run_test.sh` thresholds to match
4. Commit with message: `test(regression): update cfwmouse expected values`
