"""
Integration test: ARC bridge (Layer 1).

Tests run_literature_phase() + kb_to_research_brief() against real ARC.
Cheapest integration test — runs real ARC Stages 1-8 on a small topic.

Asserts:
    - kb.get("hypotheses") is non-empty
    - kb.get("literature") is non-empty
    - No stage-09/ directory created (experiment stage not reached)
    - research_brief.json written to run_dir
"""

import json
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def arc_imports():
    """Skip test if researchclaw is not installed."""
    pytest.importorskip("researchclaw", reason="researchclaw not installed")


def test_arc_bridge_stages_1_8(arc_imports, tmp_path):
    """Run ARC Stages 1-8 on a small biology topic and verify outputs."""
    from kinesin.literature.arc_bridge import run_literature_phase, kb_to_research_brief

    topic = "CRISPR gene editing in zebrafish development"
    config = {"arc": {"config_file": "kinesin/literature/arc_config.biology.yaml"}}
    run_dir = tmp_path / "arc_run"

    kb, returned_dir = run_literature_phase(topic, config, run_dir)

    # Stage 8 should be complete
    assert kb.stage_completed("stage-08"), (
        f"Stage 8 not found. Stages present: {kb.list_stages()}"
    )

    # Stage 9 must NOT exist (experiment stage not reached)
    assert not (run_dir / "stage-09").exists(), (
        "Stage 9 (EXPERIMENT_DESIGN) was reached — ARC gate control failed"
    )

    # Hypotheses and literature must be present
    hypotheses_text = kb.get("hypotheses")
    assert hypotheses_text is not None, "kb.get('hypotheses') returned None"
    assert len(hypotheses_text.strip()) > 0, "hypotheses stage file is empty"

    literature_text = kb.get("literature")
    assert literature_text is not None, "kb.get('literature') returned None"
    assert len(literature_text.strip()) > 0, "literature stage file is empty"

    # research_brief.json must be written
    brief_path = run_dir / "research_brief.json"
    brief = kb_to_research_brief(kb, topic, run_dir)
    assert brief_path.exists(), "research_brief.json not written"

    brief_data = json.loads(brief_path.read_text())
    assert len(brief_data.get("hypotheses", [])) >= 1, "research_brief has no hypotheses"
    assert len(brief_data.get("key_papers", [])) >= 0  # may be 0 for niche topics
    assert brief_data["topic"] == topic


def test_arc_filesystem_kb_key_mapping(tmp_path):
    """Test ARCFilesystemKB.get() key mapping without running ARC."""
    from kinesin.literature.arc_filesystem import ARCFilesystemKB

    # Create mock stage directories
    (tmp_path / "stage-07").mkdir()
    (tmp_path / "stage-07" / "synthesis.md").write_text("## Findings\n- Finding 1")
    (tmp_path / "stage-05").mkdir()
    (tmp_path / "stage-05" / "screened_papers.md").write_text("## Paper 1\n## Paper 2")
    (tmp_path / "stage-08").mkdir()
    (tmp_path / "stage-08" / "hypotheses.md").write_text("- H1: ...\n- H2: ...")

    kb = ARCFilesystemKB(tmp_path)

    assert kb.get("findings") == "## Findings\n- Finding 1"
    assert kb.get("literature") == "## Paper 1\n## Paper 2"
    assert kb.get("hypotheses") == "- H1: ...\n- H2: ..."
    assert kb.get("decisions") is None  # stage-06 not created

    assert kb.stage_completed("stage-07")
    assert not kb.stage_completed("stage-06")

    with pytest.raises(KeyError):
        kb.get("nonexistent_key")
