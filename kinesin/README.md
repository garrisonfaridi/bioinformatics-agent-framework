# Kinesin

BioResearch End-to-End Autonomous Research System. Integrates AutoResearchClaw (ARC), ScienceClaw,
and OmicsClaw on top of the existing bioinformatics agent framework.

## Installation

```bash
pip install -r kinesin/requirements.txt
bash kinesin/setup_kinesin.sh   # one-time ScienceClaw initialization
```

For spatial-domains deep learning support (SpaGCN/STAGATE):
```bash
pip install omicsclaw[spatial-domains]
```

## Usage

```bash
# Full pipeline (literature → debate → [gate] → paper)
python kinesin/run.py \
  --topic "pioneer TFs in pediatric neurological disease" \
  --mode full \
  --config kinesin/config.yaml \
  --project-dir projects/my-project/

# Literature only (Layers 1+2, cheapest — no plan.approved needed)
python kinesin/run.py \
  --topic "genetic basis of stomatal aperture control in Arabidopsis" \
  --mode literature-only \
  --config kinesin/config.yaml \
  --project-dir projects/my-project/

# Paper writing only (Layer 4 — requires existing results/ directory)
python kinesin/run.py \
  --topic "..." \
  --mode write-only \
  --config kinesin/config.yaml \
  --project-dir projects/my-project/
```

## Modes

| Mode | Layers | Cost | Gate required |
|------|--------|------|---------------|
| `literature-only` | 1+2 | ~$0.70-1.40 | No |
| `debate-only` | 2 | ~$0.30-0.60 | No |
| `write-only` | 4 | ~$0.60-1.20 | No |
| `full` | 1+2+4 | ~$1.30-2.60 | Yes (plan.approved) |

## Layers

1. **literature/** — ARC Stages 1-8 (topic init → hypothesis generation). Writes `research_brief.json`.
2. **coordination/** — ScienceClaw 3-agent debate (skeptic/synthesizer/pragmatist). Writes `plan_context.md`.
3. **[external]** — Existing framework (Nextflow pipelines, peer review). Writes `results/`.
4. **writing/** — ARC Stages 16-23 (paper outline → draft → citations). Writes `deliverables/`.
5. **metaclaw/** — Optional cross-run learning via EvolutionStore (default off).

## Plan Gate

In `full` mode, after Layer 2, Kinesin blocks until `plan.approved` exists in the project directory.
Create this file manually after reviewing `plan_context.md`:

```bash
touch projects/my-project/plan.approved
```

## OmicsClaw Skills

24 spatial and single-cell skills are available in `kinesin/coordination/bio_skills/`:
- 15 spatial transcriptomics skills (`spatial-preprocess`, `spatial-domains`, etc.)
- 9 single-cell RNA-seq skills (`sc-preprocessing`, `sc-doublet-detection`, etc.)

Skills can be invoked via ScienceClaw debate layer or as standalone scripts:

```bash
python3 kinesin/coordination/bio_skills/spatial-preprocess/scripts/spatial_preprocess.py --demo
python3 kinesin/coordination/bio_skills/sc-preprocessing/scripts/sc_preprocessing.py --demo
python3 kinesin/coordination/bio_skills/spatial-domains/scripts/spatial_domains.py --demo
# Last: prints WARNING if SpaGCN/STAGATE not installed, then succeeds with Leiden fallback
```

## Tests

```bash
# Integration tests (requires API keys)
pytest kinesin/tests/integration/ -v

# Adversarial tests (no API calls)
bash kinesin/tests/adversarial/arc_hallucinated_citations/run_test.sh
bash kinesin/tests/adversarial/empty_debate_result/run_test.sh
bash kinesin/tests/adversarial/spatial_skill_missing_deps/run_test.sh
```

## ScienceClaw setup note

ScienceClaw is installed from git (`setup_kinesin.sh` handles initialization). It creates
`~/.scienceclaw/` on first run. If initialization fails, run manually:

```bash
python3 -m scienceclaw.setup --quick --profile biology --name "KinesinAgent"
```
