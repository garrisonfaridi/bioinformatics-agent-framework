"""
ARC writer bridge: Layer 4 adapter.

Injects experiment results into ARC run directory format, then runs ARC Stages 16-23
(PAPER_OUTLINE → EXPORT_PUBLISH).

Schema mismatch note:
    Stage 16 reads analysis.md and decision.md (plain markdown) from the run directory.
    We write these via experiment_injector.py before calling execute_pipeline().
"""

from pathlib import Path

from kinesin.coordination.debate_result import DebateResult
from kinesin.writing.experiment_injector import inject_experiment_results


def run_paper_phase(
    results_dir: str,
    arc_run_dir: Path,
    debate_result: DebateResult,
    config: dict,
) -> str:
    """
    Run ARC Stages 16-23 to produce a paper draft.

    Steps:
        1. inject_experiment_results(results_dir, arc_run_dir)
        2. execute_pipeline(from_stage=Stage.PAPER_OUTLINE, auto_approve_gates=True)
        3. Return path to stage-22/ (EXPORT_PUBLISH artifacts)

    Expected deliverables in stage-22/:
        paper_draft.md, paper.tex, references.bib, reviews.md

    Args:
        results_dir:   Path to framework results/ directory.
        arc_run_dir:   ARC run directory (from Stages 1-8; stage-NN/ subdirs must exist).
        debate_result: DebateResult from Layer 2 (prepended to analysis context).
        config:        Kinesin config dict.

    Returns:
        Path string to stage-22/ deliverables directory.

    Raises:
        ImportError:   If researchclaw is not installed.
        RuntimeError:  If Stage 23 (CITATION_VERIFY) returns status != DONE.
                       Citation failure is surfaced explicitly — never silently passed.
    """
    try:
        from researchclaw.pipeline.runner import execute_pipeline
        from researchclaw.pipeline.stages import Stage, StageStatus
    except ImportError as e:
        raise ImportError(
            "researchclaw is not installed. Run: pip install researchclaw==0.3.1"
        ) from e

    arc_run_dir = Path(arc_run_dir)

    # Step 1: Write analysis.md and decision.md (Stage 16 reads these)
    inject_experiment_results(results_dir, arc_run_dir)

    # Enrich analysis.md with DebateResult context
    _append_debate_context(arc_run_dir, debate_result)

    # Step 2: Build RCConfig for the writing phase
    writing_config = config.get("writing", {})
    target_conference = writing_config.get("target_conference", "biorxiv")
    authors = writing_config.get("authors", "")

    from researchclaw.config import RCConfig

    rc_dict = {
        "project": {"name": "kinesin-paper", "mode": "docs-first"},
        "research": {"topic": "paper-phase", "domains": []},
        "runtime": {"timezone": "UTC", "auto_approve_gates": True},
        "notifications": {"email": "", "slack_webhook": "", "channel": "none"},
        "knowledge_base": {"path": "./kb", "root": "./kb"},
        "openclaw_bridge": {},
        "llm": {
            "provider": "anthropic",
            "primary_model": "claude-sonnet-4-6",
            "temperature": 0.3,
            "max_tokens": 4096,
            "base_url": "https://api.anthropic.com",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
        "writing": {
            "target_venue": target_conference,
            "authors": authors,
        },
    }
    try:
        rc_config = RCConfig.from_dict(rc_dict, check_paths=False)
    except Exception:
        rc_config = None   # execute_pipeline will fail; surface error clearly

    # Pre-flight: fail fast if a prior ARC run already flagged bad citations
    _verify_citation_stage([], arc_run_dir)

    # Step 2: Run Stages 16-23
    try:
        from researchclaw.adapters import AdapterBundle
    except ImportError:
        AdapterBundle = None

    pipeline_kwargs = dict(
        run_dir=arc_run_dir,
        from_stage=Stage.PAPER_OUTLINE,
        config=rc_config,
        auto_approve_gates=True,
    )
    if AdapterBundle is not None:
        import uuid as _uuid
        pipeline_kwargs["run_id"] = f"kinesin-paper-{_uuid.uuid4().hex[:8]}"
        pipeline_kwargs["adapters"] = AdapterBundle()

    results = execute_pipeline(**pipeline_kwargs)

    # Step 3: Verify Stage 23 (CITATION_VERIFY) completed successfully
    _verify_citation_stage(results, arc_run_dir)

    deliverables_dir = arc_run_dir / "stage-22"
    return str(deliverables_dir)


def _append_debate_context(arc_run_dir: Path, debate_result: DebateResult) -> None:
    """
    Append DebateResult summary to analysis.md so Stage 16 incorporates it.
    """
    analysis_path = arc_run_dir / "analysis.md"
    if not analysis_path.exists():
        return

    debate_section = [
        "\n## Multi-Agent Hypothesis Validation (Kinesin Layer 2)\n",
        f"Consensus Score: {debate_result.consensus_score:.2f} ({len(debate_result.raw_agent_results)} agents)\n",
        "\n### Validated Hypotheses\n",
    ]

    for h in debate_result.validated_hypotheses:
        debate_section.append(f"- {h}\n")

    if debate_result.recommended_experiment_design:
        debate_section.append("\n### Recommended Approach\n")
        for k, v in debate_result.recommended_experiment_design.items():
            debate_section.append(f"- **{k}:** {v}\n")

    existing = analysis_path.read_text(encoding="utf-8")
    analysis_path.write_text(existing + "".join(debate_section), encoding="utf-8")


def _verify_citation_stage(results: list, arc_run_dir: Path) -> None:
    """
    Check Stage 23 (CITATION_VERIFY) status in pipeline results.
    Raises RuntimeError if citations failed verification.

    Citation verification failure is non-silent: it surfaces to user before
    writing any deliverables.
    """
    try:
        from researchclaw.pipeline.stages import Stage, StageStatus
    except ImportError:
        return  # If we can't import, skip check (should not happen here)

    stage23_result = None
    for r in (results or []):
        stage = getattr(r, "stage", None)
        if stage is not None and str(stage) in ("Stage.CITATION_VERIFY", "23", "CITATION_VERIFY"):
            stage23_result = r
            break

    # Also check stage-23/ directory directly
    stage23_dir = arc_run_dir / "stage-23"
    if stage23_dir.exists():
        failed_citations = list(stage23_dir.glob("failed_citations*.txt"))
        if failed_citations:
            failed_text = failed_citations[0].read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(
                f"Stage 23 (CITATION_VERIFY) failed: unverified DOIs found.\n"
                f"See {failed_citations[0]}\nFailed entries:\n{failed_text[:500]}"
            )

    if stage23_result is not None:
        status = getattr(stage23_result, "status", None)
        if status is not None and str(status) not in ("StageStatus.DONE", "DONE", "done"):
            raise RuntimeError(
                f"Stage 23 (CITATION_VERIFY) returned status={status}. "
                "Check stage-23/ for failed citation details before submitting."
            )
