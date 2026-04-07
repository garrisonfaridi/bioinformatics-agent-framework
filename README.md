# Bioinformatics Agent Framework

An agentic bioinformatics workflow system built on [Claude Code](https://claude.ai/claude-code),
integrating autonomous AI planning, Snakemake/Nextflow pipeline execution, automated scientific
peer review, and end-to-end autonomous research via the Kinesin system.

## What This Is

This framework wraps standard bioinformatics pipelines (Snakemake, Nextflow) with four layers of
AI capability:

1. **Biomni** — 150+ specialized bioinformatics tools (database lookups, literature mining, GO
   enrichment, pathway analysis, variant interpretation) exposed via MCP
2. **Claude Opus** — used for research synthesis, experimental design, and generating structured
   implementation plans
3. **Claude Sonnet** — handles all scripting, debugging, and pipeline execution in the implementation loop
4. **Sequential Thinking MCP** — structured multi-step reasoning invoked automatically at decision
   points involving competing hypotheses, method tradeoffs, or unexpected results; makes reasoning
   explicit and auditable rather than buried in inline inference

For fully autonomous research (literature → debate → analysis → paper), see [Kinesin](#kinesin-autonomous-research-system) below.

---

## Framework Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User (Claude Code)                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
     ┌─────────────────────────┼─────────────────────────┐
     │                         │                         │
┌────▼────────┐       ┌────────▼───────┐       ┌────────▼────────┐
│   Biomni    │       │  Claude Opus   │       │  Claude Sonnet  │
│  MCP Server │       │   (Planning)   │       │(Implementation) │
│             │       │                │       │                 │
│ 150+ tools: │       │ Synthesizes    │       │ Writes scripts, │
│ databases,  │       │ Biomni output  │       │ debugs, runs    │
│ literature, │       │ into plan.md   │       │ pipelines       │
│ GO/KEGG,    │       │ with ExitPlan  │       │                 │
│ drug-gene,  │       │ Mode approval  │       │                 │
│ protocols   │       │                │       │                 │
└─────────────┘       └────────────────┘       └─────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │     Sequential Thinking MCP      │
              │                                  │
              │  Invoked automatically at any    │
              │  decision point involving:       │
              │  · Competing hypotheses (≥2)     │
              │  · Method/tool tradeoffs         │
              │  · Unexpected results            │
              │  · Cascading architecture choices│
              │  · Before every plan approval    │
              │  · Critical peer review issues   │
              │                                  │
              │  Makes reasoning explicit and    │
              │  revisable — not buried in       │
              │  inline inference                │
              └──────────┬──────────────┬──────────────┬──────────┘
                         │              │              │
          ┌──────────────▼──┐  ┌────────▼────────┐  ┌▼────────────────┐
          │ Nextflow DSL2   │  │    Snakemake     │  │   Python / R    │
          │   Pipeline      │  │    Pipeline      │  │    Pipeline     │
          │                 │  │                  │  │                 │
          │ STAR + salmon   │  │ QC → Kinship     │  │ scanpy / Seurat │
          │ BWA-MEM2 + GATK │  │ → LMM →          │  │ DESeq2 / edgeR  │
          │ nf-core modules │  │ [checkpoint]     │  │ custom analysis │
          │ containerized   │  │ enrichment /     │  │ ad-hoc scripts  │
          │ processes       │  │ BSLMM            │  │                 │
          └────────┬────────┘  └────────┬─────────┘  └───────┬─────────┘
                   │                    │                     │
                   └────────────────────┼─────────────────────┘
                                        │
                          ┌─────────────▼─────────────┐
                          │   Claude Opus Peer Review  │
                          │   (always runs last)       │
                          │                            │
                          │  review_report.md          │
                          │  proposed_changes.md       │
                          └────────────────────────────┘
```

### Three-Phase AI Workflow

| Phase | Model | Purpose |
|-------|-------|---------|
| **1 — Research** | Biomni + Opus | Biomni queries databases and literature; Opus synthesizes evidence into design decisions |
| **2 — Planning** | Opus + `EnterPlanMode` + Sequential Thinking | Sequential thinking stress-tests the plan before `ExitPlanMode`; user approves before any code is written |
| **3 — Implementation** | Sonnet + Sequential Thinking | Scripting and pipeline execution; sequential thinking invoked automatically at ambiguous decision points |

**Rule:** Biomni provides grounded database facts. Opus reasons over them. Sequential thinking makes that reasoning explicit at high-stakes decision points. Sonnet executes.

### Sequential Thinking Triggers

The agent invokes the sequential thinking MCP automatically — without being asked — when any of
these conditions are met:

| Condition | Example |
|-----------|---------|
| ≥2 competing hypotheses for a result or error | SNP count discrepancy: filter label bug vs calculation error vs wrong input file |
| Method selection with real statistical tradeoffs | LMM vs logistic GWAS; VQSR vs hard filters at small N; pseudobulk vs mixed model |
| Unexpected or counterintuitive pipeline output | λ_GC = 1.8 when < 1.1 expected; 0 annotated T cells in PBMC data |
| Architectural decision affecting ≥3 steps | Checkpoint placement; processing order; intermediate file format |
| Before finalizing any implementation plan | Stress-test assumptions, identify most likely failure mode |
| Critical-severity peer review issues | Trace root cause before implementing any correction |

---

## Kinesin: Autonomous Research System

`kinesin/` is an end-to-end autonomous research system that integrates three specialized subsystems
on top of the bioinformatics framework:

- **ARC (AutoResearchClaw)** — literature mining, hypothesis generation, and scientific paper writing (Stages 1–23)
- **ScienceClaw** — 3-agent debate layer (skeptic / synthesizer / pragmatist) that stress-tests hypotheses and generates `plan_context.md`
- **OmicsClaw** — 24 spatial transcriptomics and single-cell RNA-seq skills invoked by the debate layer or as standalone scripts

### Installation

```bash
pip install -r kinesin/requirements.txt
bash kinesin/setup_kinesin.sh   # one-time ScienceClaw initialization
```

For spatial deep learning support (SpaGCN/STAGATE):
```bash
pip install omicsclaw[spatial-domains]
```

### Modes

| Mode | Layers | Approx cost | Gate required |
|------|--------|-------------|---------------|
| `literature-only` | Literature + debate | ~$0.70–1.40 | No |
| `debate-only` | Debate only | ~$0.30–0.60 | No |
| `write-only` | Paper writing | ~$0.60–1.20 | No |
| `full` | All layers | ~$1.30–2.60 | Yes (`plan.approved`) |

```bash
# Full pipeline (literature → debate → [gate] → paper)
python kinesin/run.py \
  --topic "pioneer TFs in pediatric neurological disease" \
  --mode full \
  --config kinesin/config.yaml \
  --project-dir projects/my-project/

# Literature only (cheapest, no approval gate)
python kinesin/run.py \
  --topic "genetic basis of stomatal aperture control in Arabidopsis" \
  --mode literature-only \
  --config kinesin/config.yaml \
  --project-dir projects/my-project/
```

### Layers

1. **`literature/`** — ARC Stages 1–8: topic initialization → hypothesis generation → `research_brief.json`
2. **`coordination/`** — ScienceClaw 3-agent debate: stress-tests hypotheses → `plan_context.md`
3. **[external]** — Existing framework pipelines (Nextflow, Snakemake, peer review) → `results/`
4. **`writing/`** — ARC Stages 16–23: outline → draft → citations → `deliverables/`
5. **`metaclaw/`** — Optional cross-run learning via EvolutionStore (off by default)

The plan gate in `full` mode blocks between layers 2 and 3 until `touch projects/my-project/plan.approved`.

### OmicsClaw Bio Skills

24 skills in `kinesin/coordination/bio_skills/`:

- **15 spatial transcriptomics:** `spatial-preprocess`, `spatial-domains`, `spatial-deconvolution`, `spatial-trajectory`, and more
- **9 single-cell RNA-seq:** `sc-preprocessing`, `sc-doublet-detection`, `sc-de`, `sc-batch-integration`, `sc-cell-annotation`, `sc-grn`, `sc-cell-communication`, `sc-multiome`, and more

Skills run standalone with `--demo` for testing:

```bash
python3 kinesin/coordination/bio_skills/sc-preprocessing/scripts/sc_preprocessing.py --demo
python3 kinesin/coordination/bio_skills/spatial-domains/scripts/spatial_domains.py --demo
```

---

## Repository Contents

```
bioinformatics-freelance/
├── README.md                    # this file
├── base-env.yml                 # base conda environment (Python 3.11, R 4.4+, NGS tools)
├── biomni_mcp_server.py         # Biomni MCP server wrapper — register once with Claude Code
├── biomni_run.py                # Biomni library-mode runner for standalone tasks
├── .gitignore
│
├── .claude/
│   ├── hooks/
│   │   ├── pre-bash.sh          # Blocks pipeline execution without plan.approved sentinel
│   │   └── post-sequential-thinking.sh  # Appends every ST invocation to st_invocations.log
│   └── settings.json            # Hook registration
│
├── scripts/                     # Framework utility scripts
│   ├── trace_logger.py          # Structured run trace logging (init, decisions, ST, Biomni)
│   ├── check_knowhow_versions.py # Compares knowhow doc version pins vs. active conda env
│   ├── review_diff.py           # Diffs consecutive peer review rounds (resolved/regressed/new)
│   ├── harvest_session.py       # Extracts tool calls and ST blocks from session JSONL files
│   ├── provenance.py            # Records input file hashes and tool versions per run
│   └── narrate.py               # Fire-and-forget terminal narration for phase/event logging
│
├── ldsc/                        # LD Score Regression (Bulik-Sullivan et al.) — heritability,
│                                #   genetic correlation, and partitioned heritability analysis
│
├── kinesin/                     # Autonomous end-to-end research system (ARC + ScienceClaw + OmicsClaw)
│   ├── run.py                   # Entry point — modes: full, literature-only, debate-only, write-only
│   ├── config.yaml              # Default configuration
│   ├── literature/              # ARC Stages 1–8: literature mining and hypothesis generation
│   ├── coordination/            # ScienceClaw 3-agent debate + 24 OmicsClaw bio skills
│   │   └── bio_skills/          # 15 spatial + 9 scRNA-seq standalone skills
│   ├── writing/                 # ARC Stages 16–23: paper outline → draft → citations
│   ├── metaclaw/                # Optional cross-run learning via EvolutionStore
│   └── tests/                   # Integration + adversarial tests
│
├── tests/
│   ├── adversarial/             # Deliberately broken inputs to verify agent error detection
│   │   ├── batch_effect/        # Unlabeled batch structure in expression matrix
│   │   ├── inflated_lambda/     # λ_GC = 2.1 GWAS summary stats
│   │   ├── wrong_genome_build/  # hg19 BAM aligned to GRCh38 reference
│   │   └── corrupted_gemma_output/ # Truncated GEMMA association output
│   ├── regression/
│   │   └── cfwmouse_gwas/       # Expected outputs from the mouse obesity GWAS pilot
│   └── trace_quality/
│       └── validate_trace.py    # Checks trace.jsonl for required logging events
│
├── templates/                   # Starter pipeline templates
│   ├── nextflow-rnaseq/         # STAR + salmon + DESeq2
│   ├── nextflow-wgs/            # BWA-MEM2 + GATK4 + VEP
│   ├── snakemake-rnaseq/        # STAR + featureCounts + DESeq2
│   ├── singlecell-scanpy/       # Python scanpy + anndata
│   ├── singlecell-seurat/       # R Seurat v5
│   ├── hpc/                     # SLURM submission package templates
│   │   ├── slurm_header_template.sh
│   │   ├── transfer_instructions.md
│   │   ├── expected_outputs_template.md
│   │   └── local_postprocess_template.sh
│   ├── project_intake.md        # Session intake form — fill at analysis start
│   └── PROJECT_README_TEMPLATE.md
│
└── knowhow/                     # Domain-specific reference docs (load with @file)
    ├── gwas.md                  # Mouse/human GWAS, mixed models, GEMMA, Lindley score
    ├── rnaseq.md                # Bulk RNA-seq QC, alignment, DE analysis
    ├── singlecell.md            # scRNA-seq thresholds, clustering, annotation
    ├── variant_calling.md       # GATK4 best practices, hard filter vs VQSR
    ├── pipeline_dev.md          # Nextflow vs Snakemake, nf-core, HPC/SLURM, CI
    ├── biomni.md                # Biomni MCP setup, tool modules, when to use
    └── freelance_methods.md     # Publishable methods templates per workflow type
```

> **Note:** `projects/` is gitignored — analysis outputs, genotype files, and large results live
> locally only.

---

## Integrated MCP Servers

| Server | Purpose |
|--------|---------|
| **Biomni** | 150+ bioinformatics tools across 20 domains; database queries, literature mining, GO/KEGG enrichment, variant interpretation, protocols |
| **GitHub** | Issue and PR management, code search across repositories |
| **Sequential Thinking** | Structured multi-step reasoning for complex analysis decisions |
| **Filesystem** | Scoped file access for reading/writing analysis artifacts |

### Biomni Tool Coverage (20 domains)

Genomics, Genetics (GWAS), Cell Biology, Molecular Biology, Systems Biology, Database (UniProt/NCBI/Ensembl/ClinVar/PDB/GWAS Catalog), Literature (PubMed), Cancer Biology (TCGA), Immunology, Pathology, Pharmacology, Biochemistry, Bioimaging (microscopy/spatial), Biophysics (structural), Physiology, Microbiology, Bioengineering, Synthetic Biology, Lab Automation, Protocols.

---

## Setup

### Prerequisites

- macOS or Linux
- [miniforge3](https://github.com/conda-forge/miniforge) or miniconda3
- `ANTHROPIC_API_KEY` in environment
- [Claude Code](https://claude.ai/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Node.js ≥ 18 (required for MCP servers via npx)

### 1. Create the base conda environment

```bash
conda env create -f base-env.yml
conda activate bioinfo-base
```

The `base-env.yml` includes Python 3.11, R 4.4+, Snakemake, Nextflow, STAR, BWA-MEM2, GATK4,
samtools, bcftools, fastp, MultiQC, DESeq2, Seurat, scanpy, and biomni.

### 2. Register MCP servers with Claude Code

```bash
# Biomni (bioinformatics agent)
claude mcp add biomni -- python ~/path/to/biomni_mcp_server.py

# Sequential thinking
claude mcp add sequential-thinking -- npx @modelcontextprotocol/server-sequential-thinking

# Filesystem (scoped to home)
claude mcp add filesystem -- npx @modelcontextprotocol/server-filesystem ~

# GitHub (requires PAT)
claude mcp add github-mcp-server -- npx @modelcontextprotocol/server-github
# Set GITHUB_PERSONAL_ACCESS_TOKEN in environment
```

Then restart Claude Code. Verify with `claude mcp list`.

### 3. Configure CLAUDE.md

Copy the `CLAUDE.md` template from `~/agent/CLAUDE.md` (or use your own) to your preferred
location and replace the bracketed fields:

Fields to customize:
- `[YOUR_DEGREE_AND_SPECIALTY]` — your background
- `[YOUR_PRIMARY_WORKFLOWS]` — the analysis types you run most
- `[PATH_TO_KNOWHOW]` — absolute path to your `knowhow/` directory
- `[PATH_TO_REPO]` — absolute path to this repo root

### 4. Session start checklist

```bash
cd ~/agent/bioinformatics-freelance

# Fill out session intake
# cp templates/project_intake.md projects/my-project/intake.md
# edit intake.md, then load it: @projects/my-project/intake.md

# Check tool versions match knowhow docs
python scripts/check_knowhow_versions.py

# Initialize run trace
RUN_ID=$(date +%Y%m%d_%H%M%S)_<short_description>
python scripts/trace_logger.py init-run \
  --run-id $RUN_ID \
  --project-dir projects/<your-project>/ \
  --task-description "<one sentence>"

# Load relevant knowhow doc in Claude Code
# e.g.:  @knowhow/gwas.md
```

### 5. First Biomni run (downloads data lake)

The first `biomni` invocation downloads ~11 GB of reference data to `biomni_data/`. Run once on
a good connection before starting analyses:

```bash
python biomni_run.py "list available tools" --no-report
```

---

## Pipeline Templates

Each template in `templates/` is a minimal, runnable Snakemake or Nextflow pipeline with:
- `config.yaml` — all parameters, no hard-coded paths
- `envs/` — pinned conda environments per rule
- `scripts/` — modular R/Python analysis scripts
- `README.md` — inputs, outputs, usage

| Template | Framework | Tools |
|----------|-----------|-------|
| `nextflow-rnaseq` | Nextflow DSL2 | STAR + salmon + DESeq2 + MultiQC |
| `nextflow-wgs` | Nextflow DSL2 | BWA-MEM2 + GATK4 HaplotypeCaller + VEP |
| `snakemake-rnaseq` | Snakemake | STAR + featureCounts + DESeq2 |
| `singlecell-scanpy` | Python | scanpy + scVI + celltypist |
| `singlecell-seurat` | R | Seurat v5 + SingleR + DoubletFinder |

### Project Intake Template

`templates/project_intake.md` is a structured session intake form covering:

- Session identity (run_id, analysis_type, project_dir)
- Organism and genome build
- Dataset description (samples, covariates, known confounders)
- Analysis-type-specific parameters (GWAS QC thresholds, scRNA-seq cell counts, etc.)
- Deliverables and methods template target

Load it at the start of any analysis session alongside the relevant knowhow doc:

```bash
@templates/project_intake.md
@knowhow/gwas.md
```

---

## LD Score Regression (`ldsc/`)

`ldsc/` contains the standard LDSC tool (Bulik-Sullivan et al.) for:
- **SNP heritability** — `ldsc.py --h2`
- **Genetic correlation** — `ldsc.py --rg`
- **Partitioned heritability** — annotation-stratified h² enrichment analysis
- **Munge summary stats** — `munge_sumstats.py` for harmonizing GWAS summary statistics

```bash
conda env create -f ldsc/environment.yml
conda activate ldsc

# Munge and estimate heritability
python ldsc/munge_sumstats.py --sumstats gwas.txt --out gwas_munged
python ldsc/ldsc.py --h2 gwas_munged.sumstats.gz --ref-ld-chr eur_w_ld_chr/ --w-ld-chr eur_w_ld_chr/ --out h2_output
```

---

## Narration (`scripts/narrate.py`)

`narrate.py` provides fire-and-forget terminal narration for multi-step analyses. It prints
phase-labeled, colored output to the terminal and optionally appends a JSON event record to
the active run trace.

```bash
python scripts/narrate.py \
  --phase research \
  --event biomni_query \
  --message "GWAS Catalog query returned 3 loci on chr2, chr4, chr12 for body weight" \
  --flag ok
```

Phases: `research` (cyan), `planning` (magenta), `execute` (green), `review` (blue).
Flags: `ok` (✓), `warn` (⚠), `st` (🔀 sequential thinking triggered).

Mandatory trigger points are defined in `CLAUDE.md` under *Narration Protocol*.

---

## Approval Gate

Pipeline execution is gated on explicit user approval. The `.claude/hooks/pre-bash.sh` hook
intercepts every Bash tool call and blocks `snakemake`, `nextflow run`, `sbatch`, `srun`, and
`qsub` unless a `plan.approved` sentinel file exists in the current working directory.

```bash
# Workflow for every pipeline run:
# 1. Agent generates plan.md in the project directory
# 2. You review it
# 3. Approve:  touch plan.approved
# 4. Revoke:   rm plan.approved   (forces re-planning before next execution)
```

---

## Observability

### Run traces

Every analysis session is traced to `reasoning_traces/<run_id>/trace.jsonl`. The trace captures
decisions, sequential thinking invocations, Biomni queries, and pipeline executions.

```bash
RUN_ID=$(date +%Y%m%d_%H%M%S)_<short_description>
python scripts/trace_logger.py init-run \
  --run-id $RUN_ID \
  --project-dir projects/my-project/ \
  --task-description "CFW mouse GWAS: QC and association testing"

# Method/tool selection
python scripts/trace_logger.py log-decision \
  --run-id $RUN_ID --project-dir projects/my-project/ \
  --phase planning --decision "GEMMA LMM" \
  --rationale "relatedness matrix accounts for population structure" \
  --alternatives-considered "PLINK logistic,SAIGE"

# Summarize at session end
python scripts/trace_logger.py summarize \
  --run-id $RUN_ID --project-dir projects/my-project/
```

### Sequential thinking audit log

The `.claude/hooks/post-sequential-thinking.sh` hook fires after every sequential thinking
invocation and appends a timestamped record to `.claude/st_invocations.log`.

### Trace validation

```bash
python tests/trace_quality/validate_trace.py \
  --run-id $RUN_ID --project-dir projects/my-project/
# Exit 0 = all checks passed
# Exit 1 = quality warnings (non-blocking)
# Exit 2 = critical failures (e.g. no init-run entry)
```

### Session harvesting

```bash
python scripts/harvest_session.py \
  --session-file ~/.claude/projects/<project>/<session_id>.jsonl \
  --output-dir reasoning_traces/retro/
```

---

## Version Consistency

```bash
python scripts/check_knowhow_versions.py
# Exit 0 = all MATCH or NOT_FOUND
# Exit 1 = at least one MISMATCH (use --strict for CI)
```

If a MISMATCH is reported for a tool central to the current analysis, update the knowhow doc
frontmatter or `base-env.yml` before proceeding.

---

## Adversarial Tests

`tests/adversarial/` contains deliberately broken inputs to verify the agent detects common
failure modes before they reach results:

| Test | What it checks |
|------|---------------|
| `inflated_lambda/` | Agent flags λ_GC = 2.1 and triggers sequential thinking before reporting |
| `batch_effect/` | Unlabeled batch structure identified via PCA before DE analysis |
| `wrong_genome_build/` | hg19/GRCh38 mismatch detected from BAM header before alignment |
| `corrupted_gemma_output/` | Truncated association file caught before downstream annotation |

Run any test with its `run_test.sh` script. Each test has a `README.md` describing the injected
fault and expected agent response.

Kinesin adversarial tests live in `kinesin/tests/adversarial/`:

| Test | What it checks |
|------|---------------|
| `arc_hallucinated_citations/` | ARC fabricated reference detection |
| `empty_debate_result/` | Debate layer graceful handling of no consensus |
| `spatial_skill_missing_deps/` | Spatial skill fallback when SpaGCN/STAGATE absent |

---

## Peer Review Agent Pattern

Every pipeline ends with an automated Claude Opus peer review step that:

1. Collects all analysis outputs (QC stats, results summaries, key metrics)
2. Calls Claude Opus with a domain-specific review prompt
3. Writes:
   - `results/peer_review/review_report.md` — full narrative review with section scores
   - `results/peer_review/issues.json` — structured issue list with severity tags
   - `results/peer_review/proposed_changes.md` — actionable corrections requiring user approval

Proposed changes are never auto-applied. The user reads `proposed_changes.md` and explicitly
approves before any correction is implemented.

---

## Sequential Thinking Pattern

The agent uses the `sequential-thinking` MCP to make reasoning explicit at high-stakes decision
points. This is **automatic** — not user-initiated — and fires based on uncertainty thresholds
defined in `CLAUDE.md`.

Inline reasoning is invisible and irreversible. Sequential thinking enforces:
- **Explicit branching** — every plausible explanation is enumerated before any is acted on
- **Revision** — earlier steps can be marked wrong and reconsidered (`isRevision=True`)
- **Verifiable conclusions** — reasoning terminates only when a position can be defended

See trigger conditions in the [Three-Phase AI Workflow](#three-phase-ai-workflow) section.
Full specification is in `CLAUDE.md` under *Sequential Thinking Protocol*.

---

## Know-How Library

The `knowhow/` directory contains dense reference docs for the most common bioinformatics workflows.
Load them into a Claude Code session with `@file` syntax:

```bash
@~/agent/bioinformatics-freelance/knowhow/gwas.md
@~/agent/bioinformatics-freelance/knowhow/singlecell.md
```

Each doc covers: method overview, preferred tools with versions, standard workflow, key databases,
compute requirements, common pitfalls, and a publishable methods template.

---

## Requirements Summary

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| R | 4.3+ |
| Snakemake | ≥ 8.0 |
| Nextflow | ≥ 23.10 |
| biomni | ≥ 0.0.8 |
| Claude Code | latest |
| Node.js | ≥ 18 (for npx MCP servers) |

---

## License

MIT
