# Kinesin — Autonomous Research System

End-to-end research orchestrator integrating ARC (literature + paper writing), ScienceClaw
(multi-agent hypothesis debate), and OmicsClaw (spatial + single-cell skill library) on top
of the existing bioinformatics agent framework.

## When to invoke Kinesin

Use Kinesin when:

- Client presents a novel topic with no existing knowhow doc and asks "what should we study?"
- Exploratory research: no clear pipeline exists, need literature-informed hypothesis generation
- Client asks for a paper draft from completed analysis results
- Need hypothesis validation from multiple analytical perspectives before committing to a plan

Do NOT use Kinesin for:
- Established workflows with existing knowhow (bulk RNA-seq, WGS) — use templates directly
- Reanalysis of known data with known methods — overhead is not justified
- Quick one-off scripts — Kinesin is for multi-layer research projects

## Layer-by-Layer Decision Guide

### Mode: `literature-only` (recommended starting point)

Runs Layers 1+2. Cost: ~$0.70-1.40. Does not require `plan.approved`.

Use when: Client asks "find relevant literature and suggest hypotheses for [topic]".
Output: `research_brief.json` + `plan_context.md` with DebateResult prepended.

### Mode: `debate-only`

Runs Layer 2 only. Requires `research_brief.json` in project dir from a prior `literature-only` run.
Use when: Literature phase is complete but debate needs to be re-run (e.g. after updating topic).

### Mode: `write-only`

Runs Layer 4 only. Requires `results/` directory with peer review output.
Use when: Analysis is complete, need to draft a manuscript without re-running literature.

### Mode: `full`

Runs Layers 1+2, gate, then Layer 4. Requires `plan.approved` for Layer 4.
Use when: End-to-end run for a new research project.

## research_brief.json Field Guide

```json
{
  "topic": "your research topic",
  "hypotheses": ["H1", "H2"],       // ARC-generated; verify against literature
  "literature_gaps": ["gap1"],      // extracted from synthesis.md
  "key_papers": [{"title": ...}],   // screened_papers.md parse; verify DOIs
  "recommended_datasets": ["GSExxxxxx"],  // regex-extracted accessions; may be incomplete
  "suggested_analyses": ["DESeq2 DE analysis"]  // drives skill selection in Layer 2
}
```

**Low-confidence fields:** `recommended_datasets` uses regex extraction and will miss datasets
mentioned in prose. Manually supplement with GEO search if coverage is sparse.

**hypotheses field:** Always review before plan.approved. ARC hypotheses can be generic
(mechanism-of-action phrasing). Refine to testable predictions before planning.

## DebateResult Interpretation

Consensus score thresholds:
- `>0.7` — High confidence. Proceed directly to planning.
- `0.4-0.7` — Proceed with caveats. Review disputed_hypotheses before plan.approved.
- `<0.4` — Surface to user. Run.py will raise ValueError before writing plan_context.md.
  Ask client to refine topic or lower ARC quality_threshold.

```json
{
  "consensus_score": 0.68,
  "validated_hypotheses": ["..."],   // ≥2/3 agents accept
  "disputed_hypotheses": ["..."],    // agents split; review these
  "open_questions": ["..."],         // union of agent weaknesses
  "recommended_experiment_design": {} // from synthesizer agent
}
```

## Known Failure Modes

### ARC returning low-quality papers for niche plant biology topics

Symptom: `research_brief.json` has `key_papers: []` or papers with no DOI.

Mitigation: In `arc_config.biology.yaml`, set:
```yaml
research:
  quality_threshold: 5.0    # was 4.5
  daily_paper_count: 5      # was 12
```
Lower daily_paper_count forces stricter selection.

### ScienceClaw agents hallucinating database results

Symptom: `debate_result.validated_hypotheses` contains specific gene names or p-values that are
not in `research_brief.json["key_papers"]`.

Mitigation:
1. Never pass unvalidated DB results from Layer 2 directly to planning phase.
2. Cross-check any specific claims against Biomni or PubMed before plan.approved.
3. The debate result should be treated as a research direction, not a citation.

### Stage 16 producing generic methods section when analysis.md is sparse

Symptom: `stage-22/paper_draft.md` methods section says "data were analyzed using standard methods"
with no specifics.

Mitigation: Ensure peer review round ≥2 exists before calling `run_paper_phase`. A single round
of review often produces sparse analysis.md content. If round 1 is all that exists, manually
append key methods to `arc_run/analysis.md` before invoking Layer 4.

### ScienceClaw debate returns is_actionable() False

Symptom: `run.py` exits with code 2 and dispute summary.

Mitigation:
1. Check `plan_context.md` — if it was written from a previous run, `debate-only` mode can be
   re-run after refining research_brief.json hypotheses manually.
2. Increase `agent_count` to 5 (config.yaml) to reduce consensus variance.
3. Lower consensus threshold by editing `DebateResult.is_actionable()` temporarily.

## Cost Estimates (Approximate)

These are per-run estimates with default config (claude-sonnet-4-6, 12 papers):

| Layer | Description | Estimated Cost |
|-------|-------------|---------------|
| 1 (ARC Stages 1-8) | 12 papers × extraction | $0.40-0.80 |
| 2 (ScienceClaw ×3) | 3 investigation runs | $0.30-0.60 |
| 4 (ARC Stages 16-23) | paper draft + peer review loop | $0.60-1.20 |
| **Full run total** | | **~$1.30-2.60** |

Reduce costs by:
- Using `literature-only` mode for scoping (cheapest full-layer run)
- Setting `daily_paper_count: 5` for niche topics
- Setting `agent_count: 2` instead of 3 for faster debate

## Skill Selection in Layer 2

ScienceClaw skill selection is driven by `research_brief.json["suggested_analyses"]`.
The `_select_bio_skills()` function in `scienceclaw_bridge.py` maps analysis keywords to
kinesin skill names. If mapping is wrong (e.g., wrong skills selected for topic), manually
edit `research_brief.json["suggested_analyses"]` before re-running in `debate-only` mode.

Available kinesin skills (29 total):
- **Custom (5):** geo, deseq2, reactome_enrichment, open_targets, disease_gene_atlas
- **Spatial (15):** spatial-preprocess, spatial-domains, spatial-annotate, spatial-deconv,
  spatial-statistics, spatial-genes, spatial-de, spatial-condition, spatial-communication,
  spatial-velocity, spatial-trajectory, spatial-enrichment, spatial-cnv, spatial-integrate,
  spatial-register
- **Single-cell (9):** sc-preprocessing, sc-doublet-detection, sc-cell-annotation, sc-de,
  sc-pseudotime, sc-grn, sc-cell-communication, sc-batch-integration, sc-multiome
