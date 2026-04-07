# Adversarial Test: ARC Hallucinated Citations

## What this tests

Stage 23 (CITATION_VERIFY) should catch hallucinated DOIs and cause `run_paper_phase()` to
raise `RuntimeError` before writing any deliverables to `stage-22/`.

## Injected condition

A `failed_citations.txt` file is written into the ARC run directory's `stage-23/` directory
containing a fake DOI (`10.9999/fake.doi.2026`). This simulates Stage 23 detecting an
unverifiable citation.

## Expected behavior

1. `arc_writer_bridge.run_paper_phase()` calls `_verify_citation_stage()`.
2. `_verify_citation_stage()` finds `stage-23/failed_citations.txt` with content.
3. `RuntimeError` is raised with message mentioning the failed citation.
4. No `stage-22/paper_draft.md` is written.

## How to run

```bash
bash kinesin/tests/adversarial/arc_hallucinated_citations/run_test.sh
```

Expected output: `PASS` on all assertions.

## How to run the full DL path (after passing this test)

This test requires no API calls (pure stub injection). After passing, the integration test
`test_paper_bridge.py` exercises the real ARC paper phase.
