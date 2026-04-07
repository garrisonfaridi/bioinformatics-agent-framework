"""
experiment_injector: writes framework results into ARC run directory for Stage 16 ingestion.

Schema mismatch note:
    ARC Stage 16 (PAPER_OUTLINE) reads analysis.md and decision.md from the run directory
    via _build_context_preamble(). These are plain markdown files, NOT JSON dicts.
    This module translates our framework's peer_review/ outputs into that format.
"""

import re
from pathlib import Path


def inject_experiment_results(
    results_dir: str,
    arc_run_dir: Path,
) -> None:
    """
    Read our framework outputs and write analysis.md + decision.md to arc_run_dir.

    Stage 16 (PAPER_OUTLINE) reads these via _build_context_preamble(). Both files
    must be plain markdown — not JSON dicts.

    Reads from results_dir:
        peer_review/round*/review_report.md → findings + QC metrics summary
        *.assoc.txt, *.csv (GEMMA, DE results) → key statistical results
        *.png paths → figure references (listed by name only)

    Writes to arc_run_dir:
        analysis.md  — "## Experimental Analysis\n{findings}\n## QC Metrics\n{qc}"
        decision.md  — "## Research Decision\n{rationale}\n## Next Steps\n{plan}"

    Args:
        results_dir:  Path to framework results directory (e.g. projects/my-project/results/).
        arc_run_dir:  ARC run directory (stage-NN/ subdirs exist here from Stages 1-8).
    """
    results_path = Path(results_dir)
    arc_run_dir = Path(arc_run_dir)
    arc_run_dir.mkdir(parents=True, exist_ok=True)

    findings, qc_metrics = _extract_peer_review_content(results_path)
    statistical_summary = _extract_statistical_results(results_path)
    figures = _list_figures(results_path)

    analysis_md = _build_analysis_md(findings, qc_metrics, statistical_summary, figures)
    decision_md = _build_decision_md(findings, statistical_summary)

    (arc_run_dir / "analysis.md").write_text(analysis_md, encoding="utf-8")
    (arc_run_dir / "decision.md").write_text(decision_md, encoding="utf-8")


def _extract_peer_review_content(results_path: Path) -> tuple[list[str], list[str]]:
    """
    Read peer_review/round*/review_report.md files and extract findings + QC notes.
    Returns (findings_lines, qc_lines).
    """
    findings: list[str] = []
    qc: list[str] = []

    peer_review_dir = results_path / "peer_review"
    if not peer_review_dir.exists():
        return findings, qc

    # Gather all review reports sorted by round number (prefer latest round)
    reports = sorted(peer_review_dir.glob("round*/review_report.md"))
    if not reports:
        reports = list(peer_review_dir.glob("*.md"))

    for report_path in reports:
        text = report_path.read_text(encoding="utf-8", errors="replace")
        in_findings = False
        in_qc = False

        for line in text.splitlines():
            stripped = line.strip()

            if re.match(r"^#{1,3}\s.*(finding|result|conclusion|summary)", stripped, re.I):
                in_findings = True
                in_qc = False
                continue
            elif re.match(r"^#{1,3}\s.*(qc|quality|metric|stat)", stripped, re.I):
                in_qc = True
                in_findings = False
                continue
            elif re.match(r"^#{1,3}\s", stripped):
                in_findings = False
                in_qc = False

            if in_findings and stripped:
                findings.append(stripped)
            elif in_qc and stripped:
                qc.append(stripped)

    # Deduplicate while preserving order
    seen: set[str] = set()
    findings = [f for f in findings if not (f in seen or seen.add(f))]  # type: ignore[func-returns-value]
    qc = [q for q in qc if not (q in seen or seen.add(q))]  # type: ignore[func-returns-value]

    return findings, qc


def _extract_statistical_results(results_path: Path) -> list[str]:
    """
    Summarize key statistics from *.assoc.txt (GEMMA) and *.csv (DE) files.
    Returns list of summary strings.
    """
    summaries: list[str] = []

    for assoc_file in sorted(results_path.rglob("*.assoc.txt"))[:3]:
        lines = assoc_file.read_text(encoding="utf-8", errors="replace").splitlines()
        # Count significant hits (p < 5e-8 GWAS threshold)
        sig_count = sum(
            1 for l in lines[1:]
            if l.strip() and _extract_pval(l) < 5e-8
        )
        summaries.append(f"GWAS ({assoc_file.stem}): {sig_count} hits at p<5e-8")

    for csv_file in sorted(results_path.rglob("*.csv"))[:3]:
        try:
            lines = csv_file.read_text(encoding="utf-8", errors="replace").splitlines()
            header = lines[0].lower() if lines else ""
            if "padj" in header or "fdr" in header or "log2foldchange" in header:
                sig_count = sum(
                    1 for l in lines[1:]
                    if l.strip() and _extract_csv_padj(l, header) < 0.05
                )
                summaries.append(f"DE ({csv_file.stem}): {sig_count} genes at FDR<0.05")
        except Exception:
            pass

    return summaries


def _list_figures(results_path: Path) -> list[str]:
    """Return list of figure filenames (PNG/PDF) found in results directory."""
    figures = []
    for ext in ("*.png", "*.pdf", "*.svg"):
        figures.extend(p.name for p in results_path.rglob(ext))
    return sorted(set(figures))[:20]  # cap at 20 to avoid bloating context


def _build_analysis_md(
    findings: list[str],
    qc_metrics: list[str],
    statistical_summary: list[str],
    figures: list[str],
) -> str:
    """Compose analysis.md in the format Stage 16 expects."""
    sections = ["## Experimental Analysis\n"]

    if findings:
        sections.append("### Key Findings\n")
        for f in findings[:20]:
            sections.append(f"- {f}\n")
    else:
        sections.append("No peer review findings found in results directory.\n")

    if statistical_summary:
        sections.append("\n### Statistical Results\n")
        for s in statistical_summary:
            sections.append(f"- {s}\n")

    if figures:
        sections.append("\n### Figures\n")
        for fig in figures:
            sections.append(f"- {fig}\n")

    sections.append("\n## QC Metrics\n")
    if qc_metrics:
        for q in qc_metrics[:15]:
            sections.append(f"- {q}\n")
    else:
        sections.append("No QC metrics extracted from peer review reports.\n")

    return "".join(sections)


def _build_decision_md(findings: list[str], statistical_summary: list[str]) -> str:
    """Compose decision.md in the format Stage 16 expects."""
    sections = ["## Research Decision\n"]

    has_significant_results = any(
        "hits" in s or "genes" in s for s in statistical_summary
    )

    if has_significant_results:
        rationale = (
            "Analysis identified significant associations warranting further investigation. "
            "Statistical results and peer review support proceeding to manuscript preparation."
        )
    else:
        rationale = (
            "Analysis complete. Results reviewed by peer review protocol. "
            "Proceeding to manuscript preparation based on available findings."
        )

    sections.append(f"{rationale}\n")

    if findings:
        sections.append("\n### Supporting Evidence\n")
        for f in findings[:10]:
            sections.append(f"- {f}\n")

    sections.append("\n## Next Steps\n")
    sections.append("- Draft manuscript sections based on experimental findings\n")
    sections.append("- Integrate statistical results into Methods and Results sections\n")
    sections.append("- Prepare figures for publication\n")
    sections.append("- Submit for citation verification (Stage 23)\n")

    return "".join(sections)


def _extract_pval(line: str) -> float:
    """Extract p-value from GEMMA assoc.txt line (last numeric field)."""
    parts = line.strip().split()
    for val in reversed(parts):
        try:
            return float(val)
        except ValueError:
            continue
    return 1.0


def _extract_csv_padj(line: str, header: str) -> float:
    """Extract padj or FDR from a CSV line given the header."""
    cols = line.strip().split(",")
    headers = header.split(",")
    for i, h in enumerate(headers):
        if "padj" in h.lower() or "fdr" in h.lower():
            if i < len(cols):
                try:
                    return float(cols[i])
                except ValueError:
                    return 1.0
    return 1.0
