# Adversarial test: batch effect injection

## What was injected

A systematic batch effect is added to phenotype values for samples in batch 2:
all body weight values shift by +5g. This creates a spurious association signal
that should inflate lambda GC and trigger the peer review agent's statistical
validity check.

## What the agent should detect

- Lambda GC > 1.1 flagged in `issues.json` as `severity: critical`
- QQ plot showing systematic departure from the null line
- Peer review category: `statistical`

## How to run

```bash
bash tests/adversarial/batch_effect/run_test.sh
```

Checks that `results/peer_review/round1/issues.json` contains at least one entry
with `category: statistical` and `severity: critical` or `major`.
