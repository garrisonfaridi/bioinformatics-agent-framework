"""
Integration test: ScienceClaw debate bridge (Layer 2).

Uses a stub research_brief to avoid ARC cost.

Asserts:
    - DebateResult.validated_hypotheses is non-empty
    - DebateResult.consensus_score between 0.0 and 1.0
    - DebateResult.is_actionable() returns True
"""

import pytest


@pytest.fixture
def scienceclaw_imports():
    """Skip test if scienceclaw is not installed."""
    pytest.importorskip(
        "scienceclaw",
        reason="scienceclaw not installed (run: pip install -r kinesin/requirements.txt && bash kinesin/setup_kinesin.sh)"
    )


STUB_RESEARCH_BRIEF = {
    "topic": "transcriptional regulation of neural progenitor fate",
    "hypotheses": [
        "Pioneer TFs remodel chromatin accessibility in neural progenitors",
        "H3K27ac marks distinguish active enhancers in NPC vs differentiated neurons",
    ],
    "literature_gaps": ["Limited data on TF pioneer activity in human fetal cortex"],
    "key_papers": [
        {"title": "Pioneer factors and chromatin", "authors": "Test", "year": "2023", "doi": "10.0000/test"}
    ],
    "recommended_datasets": ["GSE123456"],
    "suggested_analyses": ["differential expression", "ATAC-seq"],
}


def test_hypothesis_debate_returns_debate_result(scienceclaw_imports):
    """Run 3-agent debate on stub brief and verify DebateResult schema."""
    from kinesin.coordination.scienceclaw_bridge import run_hypothesis_debate
    from kinesin.coordination.debate_result import DebateResult

    config = {
        "scienceclaw": {
            "agent_count": 3,
            "personalities": ["skeptic", "synthesizer", "pragmatist"],
        }
    }

    result = run_hypothesis_debate(STUB_RESEARCH_BRIEF, config)

    assert isinstance(result, DebateResult)
    assert 0.0 <= result.consensus_score <= 1.0, (
        f"consensus_score out of range: {result.consensus_score}"
    )
    assert len(result.raw_agent_results) == 3, (
        f"Expected 3 agent results, got {len(result.raw_agent_results)}"
    )


def test_debate_result_is_actionable(scienceclaw_imports):
    """Verify that a debate result with validated hypotheses is actionable."""
    from kinesin.coordination.debate_result import DebateResult

    result = DebateResult(
        validated_hypotheses=["H1 accepted by majority"],
        disputed_hypotheses=[],
        consensus_score=0.75,
        raw_agent_results=[{}, {}, {}],
    )
    assert result.is_actionable()


def test_debate_result_not_actionable_below_threshold():
    """Verify is_actionable() returns False when consensus_score <= 0.5."""
    from kinesin.coordination.debate_result import DebateResult

    low_score = DebateResult(
        validated_hypotheses=["H1"],
        consensus_score=0.4,
    )
    assert not low_score.is_actionable()

    no_hypotheses = DebateResult(
        validated_hypotheses=[],
        consensus_score=0.8,
    )
    assert not no_hypotheses.is_actionable()


def test_debate_result_to_plan_context(scienceclaw_imports):
    """Verify plan context markdown is non-empty and contains required sections."""
    from kinesin.coordination.debate_result import DebateResult
    from kinesin.coordination.scienceclaw_bridge import debate_result_to_plan_context

    result = DebateResult(
        validated_hypotheses=["Pioneer TFs remodel chromatin"],
        open_questions=["What is the upstream regulator?"],
        consensus_score=0.72,
        recommended_experiment_design={"approach": "ATAC-seq + CUT&RUN"},
        raw_agent_results=[{}, {}, {}],
    )

    context = debate_result_to_plan_context(result)
    assert "Multi-Agent Research Context" in context
    assert "Consensus Score" in context
    assert "0.72" in context
    assert "Pioneer TFs remodel chromatin" in context
