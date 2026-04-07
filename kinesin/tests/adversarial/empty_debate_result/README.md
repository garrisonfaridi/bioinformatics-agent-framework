# Adversarial Test: Empty Debate Result

## What this tests

When `run_hypothesis_debate()` returns a `DebateResult` where `is_actionable()` is False
(zero validated hypotheses or consensus_score <= 0.5), `run.py` must:

1. Print a human-readable dispute summary to stderr (not a Python traceback).
2. Exit with code 2 before writing `plan_context.md`.
3. Not write `plan.approved` sentinel.

## Injected condition

The test monkey-patches `run_hypothesis_debate()` to return a `DebateResult` with
`validated_hypotheses=[]` and `consensus_score=0.3`.

## Expected behavior

- `run.py` exits with code 2.
- stderr contains "DEBATE NOT ACTIONABLE" (human-readable summary).
- `plan_context.md` does NOT exist in the project directory.

## How to run

```bash
bash kinesin/tests/adversarial/empty_debate_result/run_test.sh
```

Expected output: `PASS` on all assertions.
