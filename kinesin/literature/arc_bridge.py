"""
ARC bridge: Layer 1 adapter.

Runs ARC Stages 1-8 (TOPIC_INIT → HYPOTHESIS_GEN) and stops before Stage 9
(EXPERIMENT_DESIGN). Converts filesystem artifacts to a structured research_brief dict.

Schema mismatch notes:
    - StageRange class does not exist in researchclaw. Gate control is done via
      stop_on_gate=True + a wrapper that re-invokes execute_pipeline() after the
      Stage 5 (LITERATURE_SCREEN) gate auto-approves.
    - KnowledgeBase class does not exist. ARCFilesystemKB is the filesystem shim.
"""

import json
import re
import uuid
from pathlib import Path

from kinesin.literature.arc_filesystem import ARCFilesystemKB


def arc_config_for_biology(topic: str) -> dict:
    """
    Return ARC RCConfig dict tuned for biology, no experiment stages.

    Key settings:
        project.name          — kinesin-pilot
        research.topic        — passed-in topic string (required by 0.3.1+)
        research.domains      — genomics, molecular_biology, cell_biology
        research.quality_threshold — 4.5
        experiment            — None (disables Stages 9-13 config block)
        runtime.auto_approve_stage5 — True
    """
    return {
        "project": {"name": "kinesin-pilot", "mode": "docs-first"},
        "research": {
            "topic": topic,
            "domains": ["genomics", "molecular_biology", "cell_biology"],
            "daily_paper_count": 12,
            "quality_threshold": 4.5,
            "max_papers_per_query": 50,
            "language": "english",
        },
        "experiment": None,
        "runtime": {
            "timezone": "UTC",
            "stop_on_gate": True,
            "auto_approve_stage5": True,
            "log_level": "INFO",
            "trace_events": True,
        },
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
    }


def run_literature_phase(
    topic: str,
    config: dict,
    run_dir: Path,
) -> tuple["ARCFilesystemKB", Path]:
    """
    Execute ARC Stages 1-8 only. Stops before Stage 9 (EXPERIMENT_DESIGN gate).

    Gate control strategy:
        - execute_pipeline() called with stop_on_gate=True
        - Stage 5 (LITERATURE_SCREEN) gate auto-approved by re-calling
          execute_pipeline(from_stage=Stage.SYNTHESIS) after Stage 5 stops
        - Stage 9 gate is never reached because experiment config block is None
        - Returns when Stage 8 (HYPOTHESIS_GEN) StageResult is present with status DONE

    Args:
        topic:    Research topic string.
        config:   Kinesin config dict (from config.yaml).
        run_dir:  Directory where ARC will write stage-NN/ subdirectories.

    Returns:
        (ARCFilesystemKB wrapping run_dir, run_dir Path)

    Raises:
        RuntimeError: If ARC pipeline fails before completing Stage 8.
        ImportError: If researchclaw is not installed.
    """
    try:
        from researchclaw.pipeline.runner import execute_pipeline
        from researchclaw.pipeline.stages import Stage
        from researchclaw.config import RCConfig
    except ImportError as e:
        raise ImportError(
            "researchclaw is not installed. Run: pip install researchclaw"
        ) from e

    import uuid as _uuid
    from researchclaw.adapters import AdapterBundle

    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    rc_config = RCConfig.from_dict(arc_config_for_biology(topic), check_paths=False)

    run_id = f"kinesin-lit-{_uuid.uuid4().hex[:8]}"
    adapters = AdapterBundle()

    # Phase 1: Stages 1-4 (TOPIC_INIT → PAPER_COLLECT)
    results_phase1 = execute_pipeline(
        run_dir=run_dir,
        run_id=run_id,
        config=rc_config,
        adapters=adapters,
        from_stage=Stage.TOPIC_INIT,
        stop_on_gate=True,
    )

    # Stage 5 gate (LITERATURE_SCREEN) auto-approves; resume from Stage 5
    results_phase2 = execute_pipeline(
        run_dir=run_dir,
        run_id=run_id,
        config=rc_config,
        adapters=adapters,
        from_stage=Stage.LITERATURE_SCREEN,
        stop_on_gate=True,
    )

    # Stages 6-8 (KNOWLEDGE_EXTRACT → SYNTHESIS → HYPOTHESIS_GEN)
    results_phase3 = execute_pipeline(
        run_dir=run_dir,
        run_id=run_id,
        config=rc_config,
        adapters=adapters,
        from_stage=Stage.KNOWLEDGE_EXTRACT,
        stop_on_gate=True,
    )

    # Verify Stage 8 completed
    kb = ARCFilesystemKB(run_dir)
    if not kb.stage_completed("stage-08"):
        completed_stages = kb.list_stages()
        raise RuntimeError(
            f"ARC Stage 8 (HYPOTHESIS_GEN) did not complete. "
            f"Stages present: {completed_stages}"
        )

    return kb, run_dir


def kb_to_research_brief(
    kb: "ARCFilesystemKB",
    topic: str,
    run_dir: Path,
) -> dict:
    """
    Convert ARC filesystem artifacts to structured research_brief dict.

    Reads:
        kb.get("hypotheses")  → parses markdown bullet list → hypotheses[]
        kb.get("literature")  → parses paper entries → key_papers[]
        kb.get("findings")    → parses section text → literature_gaps[], suggested_analyses[]

    Args:
        kb:       ARCFilesystemKB wrapping ARC run directory.
        topic:    Research topic string (passed through).
        run_dir:  ARC run directory (for writing research_brief.json).

    Returns:
        Dict with fields: topic, hypotheses, literature_gaps, key_papers,
                          recommended_datasets, suggested_analyses

    Writes research_brief.json to run_dir/.
    """
    hypotheses = _parse_bullet_list(kb.get("hypotheses") or "")
    key_papers = _parse_paper_entries(kb.get("literature") or "")
    findings_text = kb.get("findings") or ""
    literature_gaps = _parse_section(findings_text, "gaps")
    suggested_analyses = _parse_section(findings_text, "analyses")

    brief = {
        "topic": topic,
        "hypotheses": hypotheses,
        "literature_gaps": literature_gaps,
        "key_papers": key_papers,
        "recommended_datasets": _extract_dataset_mentions(findings_text),
        "suggested_analyses": suggested_analyses,
    }

    output_path = Path(run_dir) / "research_brief.json"
    output_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")

    return brief


# --- parsing helpers ---

def _parse_bullet_list(text: str) -> list[str]:
    """Extract bullet list items from markdown text."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ", "+ ")):
            items.append(line[2:].strip())
        elif re.match(r"^\d+\.\s", line):
            items.append(re.sub(r"^\d+\.\s+", "", line).strip())
    return [i for i in items if i]


def _parse_paper_entries(text: str) -> list[dict]:
    """
    Parse screened_papers.md into list of {title, authors, year, doi} dicts.
    Expects entries starting with "##" or "**Title:**" patterns.
    """
    papers = []
    current: dict = {}

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            if current:
                papers.append(current)
            current = {"title": line[3:].strip(), "authors": "", "year": "", "doi": ""}
        elif line.lower().startswith("**authors:**"):
            current["authors"] = line.split(":", 1)[-1].strip(" *")
        elif line.lower().startswith("**year:**"):
            current["year"] = line.split(":", 1)[-1].strip(" *")
        elif line.lower().startswith("**doi:**"):
            current["doi"] = line.split(":", 1)[-1].strip(" *")

    if current and "title" in current:
        papers.append(current)

    return papers


def _parse_section(text: str, section_hint: str) -> list[str]:
    """
    Extract bullet items from a section matching section_hint keyword.
    Returns items after the first matching heading until the next heading.
    """
    lines = text.splitlines()
    in_section = False
    items = []

    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{1,3}\s", stripped):
            heading_lower = stripped.lower()
            in_section = section_hint.lower() in heading_lower
            continue
        if in_section and stripped.startswith(("- ", "* ", "+ ")):
            items.append(stripped[2:].strip())

    return [i for i in items if i]


def _extract_dataset_mentions(text: str) -> list[str]:
    """Heuristically extract GEO/SRA/ArrayExpress accessions from text."""
    patterns = [
        r"GSE\d{5,7}",
        r"SRP\d{6,9}",
        r"SRR\d{6,9}",
        r"E-[A-Z]+-\d{4,6}",
        r"PRJNA\d{5,9}",
    ]
    found = set()
    for pat in patterns:
        found.update(re.findall(pat, text, re.IGNORECASE))
    return sorted(found)
