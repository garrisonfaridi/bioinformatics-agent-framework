# Adversarial test: inflated lambda GC

## What was injected

Synthetic data with lambda GC = 1.8, simulating population stratification
that was not corrected by the kinship matrix (e.g., kinship matrix computed
from a different dataset than the phenotype file).

## What the agent should detect

- Lambda GC >> 1.1 flagged as `severity: critical` in `issues.json`
- QQ plot showing systematic upward departure
- Peer review recommends checking kinship matrix sample overlap

## How to run

```bash
bash tests/adversarial/inflated_lambda/run_test.sh
```
