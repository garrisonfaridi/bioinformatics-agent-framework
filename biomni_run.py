#!/usr/bin/env python
"""
Biomni interactive pipeline runner.

Accepts a plain-language task description and lets the A1 agent
autonomously plan and execute the bioinformatics analysis.

Usage:
    python biomni_run.py "analyze the scRNA-seq data in ./data and suggest a multi-omics strategy"
    python biomni_run.py                   # prompts interactively if no argument given
    python biomni_run.py --no-datalake "..." # skip ~11 GB data lake download (scRNA-seq POC)
    python biomni_run.py --no-report   "..." # skip post-run analysis report generation

Results are written to ./results/ by default.
Set BIOMNI_PROJECT_PATH to override.

Requirements:
    ANTHROPIC_API_KEY set in environment
    biomni >= 0.0.8 installed (miniforge3 env)
"""

import io
import os
import sys
from pathlib import Path

from biomni.agent import A1


# ---------------------------------------------------------------------------
# Stdout tee — captures agent output into a buffer while still printing it
# ---------------------------------------------------------------------------

class TeeIO:
    """Write to both a StringIO buffer and the original stream simultaneously."""

    def __init__(self, original):
        self._buf = io.StringIO()
        self._orig = original

    def write(self, s):
        self._buf.write(s)
        return self._orig.write(s)

    def flush(self):
        self._buf.flush()
        self._orig.flush()

    def fileno(self):
        return self._orig.fileno()

    def isatty(self):
        return self._orig.isatty()

    def get_content(self):
        return self._buf.getvalue()


# ---------------------------------------------------------------------------
# Post-run report generator
# ---------------------------------------------------------------------------

def generate_report(log_content: str, task: str, project_path: Path, api_key: str) -> Path:
    """
    Synthesise a structured Markdown analysis report from the full biomni run log.

    Makes one direct Anthropic API call after the agent finishes, so it can
    draw on the complete audit trail — every code block, output, and the agent's
    own summary — to produce biological and statistical reasoning at each step.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # Keep log within token budget (~80 k chars ≈ 20 k tokens, leaving room for response).
    # Preserve both the start (plan) and the end (solution / cell type results).
    MAX_LOG_CHARS = 80_000
    if len(log_content) > MAX_LOG_CHARS:
        half = MAX_LOG_CHARS // 2
        log_content = (
            log_content[:half]
            + "\n\n[... log truncated for brevity — middle section omitted ...]\n\n"
            + log_content[-half:]
        )

    prompt = f"""You are a senior bioinformatics analyst reviewing the full execution log of an \
autonomous bioinformatics agent (Biomni/CodeAct). Your job is to write a comprehensive, \
scientifically rigorous analysis report that a biologist or client could read to understand \
exactly what was done and why.

Task given to the agent:
---
{task}
---

Full execution log (contains the agent's reasoning, every code block it wrote, and every output):
---
{log_content}
---

Write the report in Markdown. Be specific — use the actual numbers, gene names, threshold values, \
and decisions from the log. Do not pad with generic text; every sentence should refer to \
something concrete from this run.

# Analysis Report

## Executive Summary
3–5 sentences: what data was analysed, what approach was taken, how many cell populations were \
found, and the headline biological finding.

## Dataset
Source and URL, dimensions before and after QC, species, and why this is a well-established \
reference dataset.

## Methods and Reasoning
For each step below write one focused paragraph covering:
(a) what was done and the specific code/parameter used,
(b) the biological or statistical rationale for that choice,
(c) the observed result (exact numbers where available).

Steps to cover:
1. QC metric calculation — which metrics, why those metrics matter biologically
2. Cell filtering — thresholds applied, cells and genes retained, what was removed and why
3. Normalisation and log-transformation — method and scale factor, why normalisation is necessary
4. Highly variable gene (HVG) selection — number selected, selection method, biological role of HVGs
5. Regression of confounders — which variables regressed out, why (e.g. sequencing depth, mito %)
6. Scaling — max_value clip, why scaling is required before PCA
7. PCA — number of components computed, how many used downstream, elbow / variance rationale
8. Neighbourhood graph — n_neighbours, n_pcs used, what this graph represents
9. UMAP — what it reveals, its limitations as a visualisation
10. Leiden clustering — resolution parameter, number of clusters found, how resolution affects granularity
11. Marker gene identification — statistical method (Wilcoxon / t-test), what makes a good marker
12. Cell type annotation — which marker genes defined each cluster, confidence in labels

## Cell Population Findings
For each identified population:
- **Name** — N cells (X %)
- Defining markers: list genes and their canonical biological role
- Physiological function of this cell type in peripheral blood
- Any notable features (e.g. cytotoxic signature, immunoglobulin expression)

## Statistical Commentary
Discuss the key parameter choices: QC thresholds (are they conservative or lenient?), \
number of PCs used (is the elbow clear?), clustering resolution (could it be higher or lower?). \
How sensitive are the results to these choices? Are the 5 clusters robust?

## Limitations and Recommended Follow-up
What this analysis cannot determine (e.g. T-cell subsets beyond CD4/CD8, activation state, \
clonality). List 3–5 concrete next steps a researcher could take (e.g. doublet detection, \
sub-clustering of T cells, trajectory analysis, integration with disease samples).
"""

    print("\nGenerating analysis report via Claude API …", flush=True)
    import time
    for attempt in range(4):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except Exception as exc:
            if "rate_limit" in str(exc).lower() and attempt < 3:
                wait = 60 * (attempt + 1)
                print(f"[report] Rate limit hit — retrying in {wait}s …", flush=True)
                time.sleep(wait)
            else:
                raise

    report_path = project_path / "analysis_report.md"
    report_path.write_text(response.content[0].text, encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Output structure preamble — prepended to every task prompt
# ---------------------------------------------------------------------------

# Each analysis step gets its own numbered subdirectory under the output root.
# This preamble is injected before the user's task so biomni creates and uses
# the correct folders when writing plots, CSVs, and summary files.
_STRUCTURE_PREAMBLE = """\
REQUIRED OUTPUT STRUCTURE — follow before writing any file.

At the very start of your analysis, create all of the following directories
using Path.mkdir(parents=True, exist_ok=True), then use them strictly:

  {out}/01_qc/            → QC metric plots and per-cell statistics CSV
  {out}/02_filtering/     → filter summary (cells retained, genes retained, thresholds)
  {out}/03_normalization/ → normalization parameter log
  {out}/04_hvg/           → HVG dispersion scatter plot and HVG gene list CSV
  {out}/05_pca/           → PCA variance-ratio plot, PCA scatter plots
  {out}/06_umap/          → UMAP plots coloured by QC metrics and by Leiden clusters
  {out}/07_clustering/    → cluster sizes CSV and composition summary
  {out}/08_markers/       → marker ranking plot, dotplot, heatmap, violin plots, markers.csv
  {out}/09_annotation/    → cell-type UMAP, annotated dotplot, cell_annotations.csv
  {out}/data/             → AnnData .h5ad objects and large CSVs (gitignored)

Strict rules:
1. Create ALL directories above at the very start, before any other code.
2. Never write to a flat "plots/" directory — every plot must go in its step folder.
3. Set sc.settings.figdir to the current step directory before each group of plots.
4. Number files within each step sequentially: 01_xxx.png, 02_xxx.png, …
5. Write a step_summary.txt to each step folder containing:
   step name, key parameters used, inputs, and a 2–4 sentence result summary.

Analysis task:
"""


def build_task_prompt(user_task: str, output_dir: str) -> str:
    """Wrap the user's task with the structured output preamble."""
    return _STRUCTURE_PREAMBLE.format(out=output_dir) + user_task


def init_gitignore(project_root: Path) -> None:
    """Write a .gitignore to project_root if one does not already exist."""
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        return
    gitignore.write_text(
        "# Large binary data — regenerate from scripts, do not commit\n"
        "results/data/\n"
        "data/\n"
        "biomni_data/\n"
        "logs/\n"
        "\n"
        "# Python\n"
        "__pycache__/\n"
        "*.pyc\n"
        "*.pyo\n"
        ".venv/\n"
        "*.egg-info/\n"
        "\n"
        "# System\n"
        ".DS_Store\n"
        "Thumbs.db\n",
        encoding="utf-8",
    )
    print(f"✓ Created {gitignore}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Parse flags (remove from argv before handing remainder to task assembly)
    no_datalake = "--no-datalake" in sys.argv
    if no_datalake:
        sys.argv.remove("--no-datalake")

    no_report = "--no-report" in sys.argv
    if no_report:
        sys.argv.remove("--no-report")

    # Results land in the current project directory, not a global location.
    # Run this script from your project root.
    project_path = os.environ.get(
        "BIOMNI_PROJECT_PATH",
        str(Path.cwd() / "results")
    )
    Path(project_path).mkdir(parents=True, exist_ok=True)
    init_gitignore(Path.cwd())

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Install the tee before initialising the agent so all startup output is captured.
    tee = TeeIO(sys.stdout)
    sys.stdout = tee

    agent = A1(
        path=project_path,
        llm="claude-sonnet-4-5",
        api_key=api_key,
        # --no-datalake: skip the ~11 GB data lake download for POC / scRNA-seq work.
        # Pass expected_data_lake_files=[] to signal biomni to skip the download entirely.
        expected_data_lake_files=[] if no_datalake else None,
    )

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        # Restore stdout briefly for the interactive prompt so it reads cleanly
        sys.stdout = tee._orig
        print("Biomni — agentic bioinformatics runner")
        print(f"Results directory: {project_path}")
        print()
        task = input("Describe your analysis task: ").strip()
        sys.stdout = tee
        if not task:
            sys.stdout = tee._orig
            print("No task provided. Exiting.")
            sys.exit(0)

    print(f"\nTask: {task}")
    print("-" * 60)
    agent.go(build_task_prompt(task, project_path))

    # Restore stdout before post-processing output
    sys.stdout = tee._orig

    if no_report:
        print("\n[--no-report] Skipping analysis report generation.")
    else:
        try:
            report_path = generate_report(
                log_content=tee.get_content(),
                task=task,
                project_path=Path(project_path),
                api_key=api_key,
            )
            print(f"✓ Analysis report saved to: {report_path}")
        except Exception as exc:
            print(f"[report] Failed to generate report: {exc}", file=sys.stderr)
            print("[report] The biomni run itself completed successfully.", file=sys.stderr)
