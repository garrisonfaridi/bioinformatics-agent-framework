"""
ScienceClaw bridge: Layer 2 adapter.

Runs run_deep_investigation() 3× with distinct personality profiles (skeptic, synthesizer,
pragmatist) to simulate multi-agent debate, then synthesizes three result dicts into a
single DebateResult.

Schema mismatch notes:
    - AutonomousOrchestrator class does not exist in ScienceClaw.
    - DebateResult type does not exist in ScienceClaw.
    - Entry point is run_deep_investigation() (module-level function).
    - Returns raw dicts, not typed dataclasses.
"""

from kinesin.coordination.debate_result import DebateResult


# Personality → agent_profile kwargs mapping
_PERSONALITY_PROFILES = {
    "skeptic": {
        "curiosity_style": "skeptic",
        "research_domains": ["biology"],
        "critique_intensity": "high",
        "confidence_bias": -0.5,  # skeptics underrate their confidence
    },
    "synthesizer": {
        "curiosity_style": "synthesizer",
        "research_domains": ["biology"],
        "critique_intensity": "low",
        "confidence_bias": 0.0,
    },
    "pragmatist": {
        "curiosity_style": "pragmatist",
        "research_domains": ["biology"],
        "critique_intensity": "medium",
        "confidence_bias": 0.0,
    },
}


def run_hypothesis_debate(
    research_brief: dict,
    config: dict,
) -> DebateResult:
    """
    Run run_deep_investigation() N times with distinct personality profiles.

    For each personality in config.scienceclaw.personalities (default: skeptic, synthesizer,
    pragmatist):
        topic = "{brief['topic']} — hypothesis: {brief['hypotheses'][0]}"
        result = run_deep_investigation(
            agent_name=f"agent_{personality}",
            topic=topic,
            agent_profile={...personality_profile..., "skill_paths": [bio_skills_dir]},
            force_skills=_select_bio_skills(research_brief),
        )

    Synthesis logic:
        validated_hypotheses  ← hypotheses where ≥2/3 agents recommend "accept"
        disputed_hypotheses   ← hypotheses where agents disagree
        recommended_experiment_design ← from synthesizer agent's result["method"]
        open_questions        ← union of weaknesses from all peer review dicts
        consensus_score       ← mean(agent confidence / 5) across all agents

    Args:
        research_brief: Dict from kb_to_research_brief() (must have 'topic', 'hypotheses').
        config:         Kinesin config dict (config.scienceclaw.* keys used).

    Returns:
        DebateResult

    Raises:
        ImportError: If scienceclaw is not installed.
        ValueError:  If DebateResult.is_actionable() is False (surfaces to run.py).
    """
    try:
        from scienceclaw.autonomous.deep_investigation import run_deep_investigation
    except ImportError as e:
        raise ImportError(
            "scienceclaw is not installed. Run: pip install -r kinesin/requirements.txt "
            "and bash kinesin/setup_kinesin.sh"
        ) from e

    sc_config = config.get("scienceclaw", {})
    personalities = sc_config.get("personalities", ["skeptic", "synthesizer", "pragmatist"])
    bio_skills_dir = _bio_skills_dir()

    topic = research_brief.get("topic", "unknown topic")
    hypotheses = research_brief.get("hypotheses", [])
    primary_hypothesis = hypotheses[0] if hypotheses else "no hypothesis provided"

    investigation_topic = f"{topic} — hypothesis: {primary_hypothesis}"
    selected_skills = _select_bio_skills(research_brief)

    raw_results: list[dict] = []

    for personality in personalities:
        profile = dict(_PERSONALITY_PROFILES.get(personality, _PERSONALITY_PROFILES["pragmatist"]))
        profile["skill_paths"] = [str(bio_skills_dir)]

        result = run_deep_investigation(
            agent_name=f"agent_{personality}",
            topic=investigation_topic,
            agent_profile=profile,
            force_skills=selected_skills,
        )
        result["_personality"] = personality
        raw_results.append(result)

    debate_result = _synthesize_results(raw_results, research_brief)

    if not debate_result.is_actionable():
        raise ValueError(debate_result.dispute_summary())

    return debate_result


def debate_result_to_plan_context(result: DebateResult) -> str:
    """
    Convert DebateResult to markdown suitable for prepending to plan.md.

    Output format:
        ## Multi-Agent Research Context (Kinesin Layer 2)
        **Validated Hypotheses:** ...
        **Experiment Design:** ...
        **Open Questions:** ...
        **Consensus Score:** 0.XX (N agents)
    """
    lines = [
        "## Multi-Agent Research Context (Kinesin Layer 2)",
        "",
        "**Validated Hypotheses:**",
    ]

    if result.validated_hypotheses:
        for h in result.validated_hypotheses:
            lines.append(f"- {h}")
    else:
        lines.append("- None (low consensus)")

    lines.extend(["", "**Experiment Design:**"])
    exp_design = result.recommended_experiment_design
    if exp_design:
        for k, v in exp_design.items():
            lines.append(f"- **{k}:** {v}")
    else:
        lines.append("- Not specified")

    lines.extend(["", "**Open Questions:**"])
    if result.open_questions:
        for q in result.open_questions:
            lines.append(f"- {q}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        f"**Consensus Score:** {result.consensus_score:.2f} ({len(result.raw_agent_results)} agents)",
        "",
    ])

    if result.disputed_hypotheses:
        lines.append("**Disputed Hypotheses (review before planning):**")
        for h in result.disputed_hypotheses:
            lines.append(f"- {h}")
        lines.append("")

    return "\n".join(lines)


def _select_bio_skills(research_brief: dict) -> list[str]:
    """
    Map research_brief["suggested_analyses"] to ScienceClaw skill names.

    Prefers kinesin bio_skills; falls back to ScienceClaw built-ins.
    Returns list of skill name strings passed to force_skills.
    """
    suggested = research_brief.get("suggested_analyses", [])

    # Mapping from analysis keywords → kinesin skill names
    keyword_to_skill = {
        "geo": "geo",
        "differential expression": "deseq2",
        "deseq": "deseq2",
        "de analysis": "deseq2",
        "pathway": "reactome_enrichment",
        "enrichment": "reactome_enrichment",
        "gwas": "open_targets",
        "disease gene": "disease_gene_atlas",
        "spatial": "spatial-preprocess",
        "spatially variable": "spatial-genes",
        "spatial domain": "spatial-domains",
        "deconvolution": "spatial-deconv",
        "single.?cell": "sc-preprocessing",
        "scrna": "sc-preprocessing",
        "doublet": "sc-doublet-detection",
        "trajectory": "sc-pseudotime",
        "pseudotime": "sc-pseudotime",
        "grn": "sc-grn",
        "cell communication": "sc-cell-communication",
        "batch": "sc-batch-integration",
    }

    selected = set()
    import re
    for analysis in suggested:
        analysis_lower = analysis.lower()
        for keyword, skill in keyword_to_skill.items():
            if re.search(keyword, analysis_lower):
                selected.add(skill)

    # Always include GEO search for literature-driven analyses
    if not selected:
        selected.add("geo")

    return sorted(selected)


def _bio_skills_dir() -> "Path":
    """Return path to kinesin/coordination/bio_skills/."""
    from pathlib import Path
    return Path(__file__).parent / "bio_skills"


def _synthesize_results(raw_results: list[dict], research_brief: dict) -> DebateResult:
    """
    Synthesize 3 run_deep_investigation() result dicts into a DebateResult.

    Synthesis logic:
        - validated_hypotheses: hypotheses where majority (≥2/3) recommend "accept"
        - disputed_hypotheses: hypotheses where agents split (accept vs reject/revise)
        - recommended_experiment_design: from synthesizer agent's result["method"]
        - open_questions: union of weaknesses across all agents
        - consensus_score: mean(agent_confidence / 5)
    """
    hypotheses = research_brief.get("hypotheses", [])

    # Collect per-agent verdicts for each hypothesis
    all_verdicts: dict[str, list[str]] = {h: [] for h in hypotheses}
    all_weaknesses: list[str] = []
    confidence_scores: list[float] = []
    synthesizer_result: dict = {}

    for result in raw_results:
        personality = result.get("_personality", "unknown")

        # Extract verdict from investigation_results if available
        investigation = result.get("investigation_results", {})
        if isinstance(investigation, list):
            for item in investigation:
                if isinstance(item, dict):
                    verdict = item.get("verdict", "accept")
                    h_text = item.get("hypothesis", "")
                    if h_text in all_verdicts:
                        all_verdicts[h_text].append(verdict)
                    weakness = item.get("weakness", "")
                    if weakness:
                        all_weaknesses.append(weakness)
        elif isinstance(investigation, dict):
            verdict = investigation.get("verdict", "accept")
            weakness = investigation.get("weakness", "")
            if weakness:
                all_weaknesses.append(weakness)
            for h in hypotheses:
                all_verdicts[h].append(verdict)

        # Default: skeptic rejects, others accept (conservative synthesis)
        if not investigation:
            for h in hypotheses:
                default_verdict = "reject" if personality == "skeptic" else "accept"
                all_verdicts[h].append(default_verdict)

        # Confidence score (field may vary; normalize to 0-5 scale → 0-1)
        confidence = result.get("confidence", result.get("confidence_score", 2.5))
        try:
            confidence_scores.append(float(confidence) / 5.0)
        except (TypeError, ValueError):
            confidence_scores.append(0.5)

        if personality == "synthesizer":
            synthesizer_result = result

    # Classify hypotheses
    validated: list[str] = []
    disputed: list[str] = []

    for h, verdicts in all_verdicts.items():
        if not verdicts:
            continue
        accept_count = sum(1 for v in verdicts if v.lower() in ("accept", "support", "validated"))
        if accept_count >= len(verdicts) * 0.67:  # ≥2/3 accept
            validated.append(h)
        else:
            disputed.append(h)

    # Experiment design from synthesizer
    exp_design = {}
    if synthesizer_result:
        method = synthesizer_result.get("method", {})
        if isinstance(method, dict):
            exp_design = method
        elif isinstance(method, str):
            exp_design = {"description": method}
        # Also check hypothesis/findings fields
        if not exp_design:
            exp_design = {
                "approach": synthesizer_result.get("hypothesis", ""),
                "findings": synthesizer_result.get("findings", ""),
            }

    consensus = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

    return DebateResult(
        validated_hypotheses=validated,
        disputed_hypotheses=disputed,
        recommended_experiment_design=exp_design,
        open_questions=list(dict.fromkeys(all_weaknesses)),  # deduplicated, ordered
        consensus_score=round(consensus, 4),
        raw_agent_results=raw_results,
    )
