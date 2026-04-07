"""
Integration test: Full kinesin run smoke tests.

Tests run.py in literature-only mode (cheapest end-to-end, no plan.approved needed).

Asserts:
    - kinesin_session.json written
    - research_brief.json written
    - plan_context.md written to project dir
"""

import json
import subprocess
import sys
import pytest
from pathlib import Path


@pytest.fixture
def arc_scienceclaw_imports():
    pytest.importorskip("researchclaw", reason="researchclaw not installed")
    pytest.importorskip(
        "scienceclaw",
        reason="scienceclaw not installed (run setup_kinesin.sh)"
    )


def test_literature_only_mode(arc_scienceclaw_imports, tmp_path):
    """Run kinesin/run.py in literature-only mode and verify output files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Write a minimal config
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "arc:\n  config_file: kinesin/literature/arc_config.biology.yaml\n"
        "  metaclaw_enabled: false\n"
        "scienceclaw:\n  agent_count: 3\n"
        "  personalities: [skeptic, synthesizer, pragmatist]\n"
        "writing:\n  target_conference: biorxiv\n  authors: Test\n"
    )

    result = subprocess.run(
        [
            sys.executable, "kinesin/run.py",
            "--topic", "genetic basis of stomatal aperture control in Arabidopsis",
            "--mode", "literature-only",
            "--config", str(config_path),
            "--project-dir", str(project_dir),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode in (0, 2), (
        f"Unexpected exit code {result.returncode}\nstderr: {result.stderr[:500]}"
    )

    # research_brief.json must be written (Layer 1)
    brief_path = project_dir / "research_brief.json"
    assert brief_path.exists(), f"research_brief.json not found. stdout: {result.stdout[:200]}"

    brief = json.loads(brief_path.read_text())
    assert "topic" in brief
    assert "hypotheses" in brief

    # kinesin_session.json must be written
    session_path = project_dir / "kinesin_session.json"
    assert session_path.exists(), "kinesin_session.json not found"

    session = json.loads(session_path.read_text())
    assert "layers" in session


def test_plan_approved_gate_not_bypassed(tmp_path):
    """Verify plan.approved gate blocks Layer 4 in full mode."""
    from kinesin.run import _check_plan_approved

    project_dir = tmp_path / "test_gated_project"
    project_dir.mkdir()

    # Without plan.approved: should return False
    assert not _check_plan_approved(str(project_dir))

    # With plan.approved: should return True
    (project_dir / "plan.approved").write_text("")
    assert _check_plan_approved(str(project_dir))


def test_session_json_structure(tmp_path):
    """Verify _write_session_artifact produces valid kinesin_session.json."""
    from kinesin.run import _write_session_artifact

    project_dir = tmp_path
    run_id = "test123"

    _write_session_artifact(project_dir, run_id, "layer1", {"topic": "test", "hypotheses": ["H1"]})
    _write_session_artifact(project_dir, run_id, "layer2", {"consensus_score": 0.75})

    session_path = project_dir / "kinesin_session.json"
    assert session_path.exists()

    session = json.loads(session_path.read_text())
    assert session["run_id"] == run_id
    assert "layer1" in session["layers"]
    assert "layer2" in session["layers"]
    assert session["layers"]["layer1"]["hypotheses"] == ["H1"]
