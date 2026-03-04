# Adversarial test: corrupted GEMMA association file

## What was injected

The GEMMA `.assoc.txt` output file is truncated at 50% of its rows, simulating
a partial HPC job failure.

## What the agent should detect

- SNP count check shows fewer SNPs than expected
- Peer review flags a `computational` issue
- Agent does not attempt to interpret a partial result as valid

## How to run

```bash
bash tests/adversarial/corrupted_gemma_output/run_test.sh
```
