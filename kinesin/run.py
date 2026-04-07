"""
kinesin/run.py — Orchestration entry point for the Kinesin autonomous research system.

Usage:
    python kinesin/run.py \\
        --topic "pioneer TFs in pediatric neurological disease" \\
        --mode full|literature-only|debate-only|write-only \\
        --config kinesin/config.yaml \\
        --project-dir projects/my-project/

Modes:
    full             Layers 1 → 2 → [gate] → 4
    literature-only  Layers 1 + 2 only (no plan.approved gate required)
    debate-only      Layer 2 only (requires research_brief.json in project-dir)
    write-only       Layer 4 only (requires results/ and ARC run dir)
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path


def main(topic: str, mode: str, config_path: str, project_dir: str) -> None:
    """
    Orchestrate Layer 1 → 2 → (gate) → 4. Writes kinesin_session.json.

    Execution flow:
        1.  Init trace (scripts/trace_logger.py init-run)
        2.  Narrate session_start
        3.  Layer 1: run_literature_phase() → research_brief.json
        4.  Narrate literature_finding
        5.  Layer 2: run_hypothesis_debate() → DebateResult
        6.  Narrate method_selected (debate consensus)
        7.  Write debate_result_to_plan_context() → prepend to project_dir/plan_context.md
        8.  GATE: check plan.approved sentinel (block until file exists)
            [Layer 3: existing framework runs externally — kinesin does not touch it]
        9.  Layer 4: run_paper_phase() → deliverables/
        10. Narrate review_started
        11. If metaclaw.enabled: extract + register lessons
        12. Write kinesin_session.json summary
    """
    config = _load_config(config_path)
    project_path = Path(project_dir)
    project_path.mkdir(parents=True, exist_ok=True)

    run_id = str(uuid.uuid4())[:8]
    session_artifacts: dict = {"run_id": run_id, "topic": topic, "mode": mode, "layers": {}}

    _narrate(f"[kinesin:{run_id}] session_start | topic={topic!r} mode={mode}")

    # Determine ARC run directory (shared across Layers 1 and 4)
    arc_run_dir = project_path / "arc_run"
    arc_run_dir.mkdir(parents=True, exist_ok=True)

    research_brief: dict = {}
    debate_result = None

    # --- Layer 1: Literature phase ---
    if mode in ("full", "literature-only"):
        from kinesin.literature.arc_bridge import run_literature_phase, kb_to_research_brief

        _narrate(f"[kinesin:{run_id}] layer_start | layer=1 desc='ARC literature Stages 1-8'")
        kb, arc_run_dir = run_literature_phase(topic, config, arc_run_dir)
        research_brief = kb_to_research_brief(kb, topic, arc_run_dir)

        # Copy research_brief.json to project dir for user visibility
        brief_path = project_path / "research_brief.json"
        brief_path.write_text(json.dumps(research_brief, indent=2), encoding="utf-8")

        _narrate(
            f"[kinesin:{run_id}] literature_finding | "
            f"hypotheses={len(research_brief.get('hypotheses', []))} "
            f"papers={len(research_brief.get('key_papers', []))}"
        )
        _write_session_artifact(project_path, run_id, "layer1", research_brief)
        session_artifacts["layers"]["1"] = {"status": "done", "brief": str(brief_path)}

    # --- Layer 2: Hypothesis debate ---
    if mode in ("full", "literature-only", "debate-only"):
        if mode == "debate-only":
            # Load existing research_brief.json from project dir
            brief_path = project_path / "research_brief.json"
            if not brief_path.exists():
                print(
                    f"ERROR: --mode debate-only requires {brief_path} to exist.\n"
                    "Run literature-only first.",
                    file=sys.stderr,
                )
                sys.exit(1)
            research_brief = json.loads(brief_path.read_text(encoding="utf-8"))

        from kinesin.coordination.scienceclaw_bridge import (
            run_hypothesis_debate,
            debate_result_to_plan_context,
        )

        _narrate(f"[kinesin:{run_id}] layer_start | layer=2 desc='ScienceClaw 3-agent debate'")

        try:
            debate_result = run_hypothesis_debate(research_brief, config)
        except ValueError as e:
            # is_actionable() returned False
            print(
                f"\n[kinesin:{run_id}] DEBATE NOT ACTIONABLE\n{e}\n\n"
                "Review research_brief.json and adjust topic or increase quality_threshold "
                "in arc_config.biology.yaml before proceeding.",
                file=sys.stderr,
            )
            _write_session_artifact(
                project_path, run_id, "layer2_failed",
                {"error": str(e), "status": "not_actionable"}
            )
            sys.exit(2)

        plan_context_text = debate_result_to_plan_context(debate_result)
        plan_context_path = project_path / "plan_context.md"

        # Prepend — preserve any existing content
        existing = plan_context_path.read_text(encoding="utf-8") if plan_context_path.exists() else ""
        plan_context_path.write_text(plan_context_text + "\n---\n\n" + existing, encoding="utf-8")

        _narrate(
            f"[kinesin:{run_id}] method_selected | "
            f"consensus={debate_result.consensus_score:.2f} "
            f"validated={len(debate_result.validated_hypotheses)}"
        )
        _write_session_artifact(project_path, run_id, "layer2", debate_result.to_dict())
        session_artifacts["layers"]["2"] = {
            "status": "done",
            "consensus_score": debate_result.consensus_score,
            "plan_context": str(plan_context_path),
        }

    # --- Gate: plan.approved ---
    if mode == "full":
        if not _check_plan_approved(project_dir):
            print(
                f"\n[kinesin:{run_id}] GATE: Waiting for plan approval.\n\n"
                f"  Review: {project_path}/plan_context.md\n"
                f"  Approve by running: touch {project_path}/plan.approved\n\n"
                "  After approval, re-run with --mode write-only to produce the paper draft.",
                file=sys.stdout,
            )
            _write_session_artifact(
                project_path, run_id, "gate",
                {"status": "waiting", "sentinel": str(project_path / "plan.approved")}
            )
            # Persist session state for resumption
            _flush_session(project_path, session_artifacts)
            return

    # --- Layer 4: Paper writing ---
    if mode in ("full", "write-only"):
        if debate_result is None and (project_path / "kinesin_session.json").exists():
            # Reload DebateResult from previous session
            session_data = json.loads(
                (project_path / "kinesin_session.json").read_text(encoding="utf-8")
            )
            layer2 = session_data.get("layers", {}).get("2", {})
            # Reconstruct minimal DebateResult for paper phase
            from kinesin.coordination.debate_result import DebateResult
            debate_result = DebateResult(
                validated_hypotheses=layer2.get("validated_hypotheses", []),
                consensus_score=layer2.get("consensus_score", 0.0),
            )

        if debate_result is None:
            from kinesin.coordination.debate_result import DebateResult
            debate_result = DebateResult()

        from kinesin.writing.arc_writer_bridge import run_paper_phase

        results_dir = str(project_path / "results")
        _narrate(f"[kinesin:{run_id}] layer_start | layer=4 desc='ARC paper Stages 16-23'")
        _narrate(f"[kinesin:{run_id}] review_started | results_dir={results_dir}")

        try:
            deliverables_dir = run_paper_phase(results_dir, arc_run_dir, debate_result, config)
        except RuntimeError as e:
            print(
                f"\n[kinesin:{run_id}] PAPER PHASE FAILED: {e}",
                file=sys.stderr,
            )
            sys.exit(3)

        _write_session_artifact(project_path, run_id, "layer4", {"deliverables": deliverables_dir})
        session_artifacts["layers"]["4"] = {"status": "done", "deliverables": deliverables_dir}
        _narrate(f"[kinesin:{run_id}] layer_done | layer=4 deliverables={deliverables_dir!r}")

    # --- Layer 5: MetaClaw (optional) ---
    arc_config = config.get("arc", {})
    if arc_config.get("metaclaw_enabled", False):
        from kinesin.metaclaw.lesson_extractor import (
            extract_lessons_from_trace,
            register_lessons_with_metaclaw,
        )
        trace_path = str(project_path / "trace.jsonl")
        evolution_path = str(project_path / "evolution_store.jsonl")
        lessons = extract_lessons_from_trace(trace_path)
        register_lessons_with_metaclaw(lessons, evolution_path)
        _narrate(f"[kinesin:{run_id}] metaclaw_done | lessons={len(lessons)}")

    _flush_session(project_path, session_artifacts)
    _narrate(f"[kinesin:{run_id}] session_done | project_dir={project_dir!r}")


def _check_plan_approved(project_dir: str) -> bool:
    """
    Returns True only if plan.approved sentinel file exists. Never bypasses.
    """
    return (Path(project_dir) / "plan.approved").exists()


def _load_config(config_path: str) -> dict:
    """Load and validate kinesin/config.yaml."""
    import yaml  # type: ignore[import]

    config_file = Path(config_path)
    if not config_file.exists():
        print(
            f"ERROR: Config file not found: {config_path}\n"
            "Copy kinesin/config.yaml to your working directory or pass --config path.",
            file=sys.stderr,
        )
        sys.exit(1)

    with config_file.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config or {}


def _write_session_artifact(
    project_dir: Path,
    run_id: str,
    layer: str,
    artifact: dict | str,
) -> None:
    """Append layer output to kinesin_session.json."""
    session_path = project_dir / "kinesin_session.json"
    if session_path.exists():
        try:
            session = json.loads(session_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            session = {}
    else:
        session = {}

    if "layers" not in session:
        session["layers"] = {}
    session["layers"][layer] = artifact
    session["run_id"] = run_id

    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")


def _flush_session(project_dir: Path, session_artifacts: dict) -> None:
    """Write final kinesin_session.json."""
    session_path = project_dir / "kinesin_session.json"
    session_path.write_text(json.dumps(session_artifacts, indent=2), encoding="utf-8")


def _narrate(message: str) -> None:
    """Print narration to stdout (picked up by trace logger if piped)."""
    print(message, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Kinesin autonomous research orchestrator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--topic", required=True, help="Research topic string.")
    parser.add_argument(
        "--mode",
        choices=["full", "literature-only", "debate-only", "write-only"],
        default="literature-only",
        help="Execution mode (default: literature-only).",
    )
    parser.add_argument(
        "--config",
        default="kinesin/config.yaml",
        help="Path to kinesin config.yaml (default: kinesin/config.yaml).",
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Project directory for outputs (research_brief.json, plan_context.md, etc.).",
    )

    args = parser.parse_args()
    main(
        topic=args.topic,
        mode=args.mode,
        config_path=args.config,
        project_dir=args.project_dir,
    )
