"""
DebateResult: custom dataclass for kinesin's multi-agent debate output.

This is NOT a ScienceClaw type — it is defined and owned by kinesin.
ScienceClaw's run_deep_investigation() returns raw dicts; this dataclass
is the synthesized output produced by scienceclaw_bridge.py.
"""

from dataclasses import dataclass, field


@dataclass
class DebateResult:
    """
    Synthesized output of multi-agent ScienceClaw investigation.

    Populated by scienceclaw_bridge.run_hypothesis_debate() from 3
    run_deep_investigation() calls (skeptic, synthesizer, pragmatist agents).

    Fields:
        validated_hypotheses:          Hypotheses where ≥2/3 agents agree ("accept").
        disputed_hypotheses:           Hypotheses where agents disagree (accept vs reject/revise).
        recommended_experiment_design: From synthesizer agent's result["method"] dict.
        open_questions:                Union of weaknesses/uncertainties across all agents.
        consensus_score:               Float 0.0-1.0; mean of agent confidence scores ÷ 5.
        raw_agent_results:             Original dicts from run_deep_investigation() calls.
    """

    validated_hypotheses: list[str] = field(default_factory=list)
    disputed_hypotheses: list[str] = field(default_factory=list)
    recommended_experiment_design: dict = field(default_factory=dict)
    open_questions: list[str] = field(default_factory=list)
    consensus_score: float = 0.0
    raw_agent_results: list[dict] = field(default_factory=list)

    def is_actionable(self) -> bool:
        """
        True if validated_hypotheses is non-empty and consensus_score >= 0.5.

        Called by run.py before proceeding to plan gate. If False, run.py raises
        ValueError with a human-readable dispute summary rather than writing plan_context.md.
        """
        return bool(self.validated_hypotheses) and self.consensus_score >= 0.5

    def dispute_summary(self) -> str:
        """
        Return human-readable summary for surface-to-user display when is_actionable() is False.
        """
        lines = [
            "Multi-agent debate did not reach actionable consensus.",
            f"  Consensus score: {self.consensus_score:.2f} (threshold: >=0.50)",
            f"  Validated hypotheses: {len(self.validated_hypotheses)}",
            f"  Disputed hypotheses: {len(self.disputed_hypotheses)}",
        ]
        if self.disputed_hypotheses:
            lines.append("  Disputed:")
            for h in self.disputed_hypotheses[:5]:
                lines.append(f"    - {h}")
        if self.open_questions:
            lines.append("  Open questions preventing consensus:")
            for q in self.open_questions[:5]:
                lines.append(f"    - {q}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to plain dict (for kinesin_session.json)."""
        return {
            "validated_hypotheses": self.validated_hypotheses,
            "disputed_hypotheses": self.disputed_hypotheses,
            "recommended_experiment_design": self.recommended_experiment_design,
            "open_questions": self.open_questions,
            "consensus_score": self.consensus_score,
            "agent_count": len(self.raw_agent_results),
        }
