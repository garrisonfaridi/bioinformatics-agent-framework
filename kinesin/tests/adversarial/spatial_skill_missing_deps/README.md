# Adversarial Test: Spatial Skill Missing Dependencies

## What this tests

The `spatial-domains` skill must fail gracefully when optional DL dependencies
(SpaGCN, STAGATE, torch) are not installed:

1. Exit code 0 (not 1 — Leiden fallback is a valid result).
2. stderr contains `"WARNING: SpaGCN/STAGATE not available; falling back to Leiden"` (not a Python ImportError traceback).
3. Output JSON is valid (Leiden fallback produced output).

## Injected condition

The test creates a temporary virtualenv WITHOUT torch/SpaGCN installed, then runs
`spatial_domains.py` in it. In the absence of those packages, `_dl_available()` returns False
and the skill falls back to Leiden clustering with a WARNING.

## Expected behavior

- Script exits with code 0.
- stderr contains the expected WARNING string.
- stdout is valid JSON with `method_used: "leiden_fallback"` and `dl_available: false`.

## Note on trace log assertion

The plan specifies asserting that the trace log contains a `severity=warning` event for
`spatial_domains_fallback`. Since trace logging is handled by `scripts/trace_logger.py`
(external to the skill), this adversarial test only verifies the skill's own stderr output.
Full trace integration is covered by the integration tests.

## How to run

```bash
bash kinesin/tests/adversarial/spatial_skill_missing_deps/run_test.sh
```

Expected output: `PASS` on all assertions.

## How to test the DL path (after installing torch)

```bash
pip install omicsclaw[spatial-domains]
python3 kinesin/coordination/bio_skills/spatial-domains/scripts/spatial_domains.py \
  --input demo.h5ad --method auto --output /tmp/test_domains/
# Should NOT print the Leiden fallback WARNING
```
