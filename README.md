# Bioinformatics Agent Framework

An agentic bioinformatics workflow system built on [Claude Code](https://claude.ai/claude-code),
integrating autonomous AI planning, Snakemake pipeline execution, and automated scientific peer review.

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

The result is a system where you describe a bioinformatics question in plain language and receive
a reproducible, peer-reviewed analysis pipeline.

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

## Repository Contents

```
bioinformatics-freelance/
├── README.md                    # this file
├── CLAUDE.md                    # agent instructions: rules, protocols, tool preferences
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
│   └── provenance.py            # Records input file hashes and tool versions per run
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
│   └── PROJECT_README_TEMPLATE.md
│
├── knowhow/                     # Domain-specific reference docs (load with @file)
│   ├── gwas.md                  # Mouse/human GWAS, mixed models, GEMMA, Lindley score
│   ├── rnaseq.md                # Bulk RNA-seq QC, alignment, DE analysis
│   ├── singlecell.md            # scRNA-seq thresholds, clustering, annotation
│   ├── variant_calling.md       # GATK4 best practices, hard filter vs VQSR
│   ├── pipeline_dev.md          # Nextflow vs Snakemake, nf-core, HPC/SLURM, CI
│   ├── biomni.md                # Biomni MCP setup, tool modules, when to use
│   └── freelance_methods.md     # Publishable methods templates per workflow type
│
└── projects/
    └── mouse-obesity-gwas/      # Documented pilot: CFW mouse body weight GWAS
```

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

A `CLAUDE.md` template is included at the repo root. Copy it to your preferred location
(`~/agent/CLAUDE.md` or `~/.claude/CLAUDE.md`) and replace the bracketed fields:

```bash
cp CLAUDE.md ~/agent/CLAUDE.md   # or ~/.claude/CLAUDE.md for global scope
```

Fields to customize:
- `[YOUR_DEGREE_AND_SPECIALTY]` — your background
- `[YOUR_PRIMARY_WORKFLOWS]` — the analysis types you run most
- `[PATH_TO_KNOWHOW]` — absolute path to your `knowhow/` directory
- `[PATH_TO_REPO]` — absolute path to this repo root

The template covers:
- Background (your specialty areas and languages)
- Hard rules (pin versions, use containers, random seeds, README+methods per project)
- Tool preferences table
- Biomni invocation patterns
- Sequential thinking protocol with mandatory trigger rules
- Three-phase model selection protocol
- Know-how doc references

### 4. Session start checklist

Run at the start of every new analysis session:

```bash
cd ~/agent/bioinformatics-freelance

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

The agent never executes a pipeline without the sentinel. The Snakemake template also checks for
it at the Python level as a second guard:

```python
if not os.path.exists("plan.approved"):
    raise SystemExit("ERROR: plan.approved not found. Review plan.md first.")
```

---

## Observability

### Run traces

Every analysis session is traced to `reasoning_traces/<run_id>/trace.jsonl`. The trace captures
decisions, sequential thinking invocations, Biomni queries, and pipeline executions — providing
an audit trail for every choice that shaped the result.

Initialize a trace at the start of each session:

```bash
RUN_ID=$(date +%Y%m%d_%H%M%S)_<short_description>
python scripts/trace_logger.py init-run \
  --run-id $RUN_ID \
  --project-dir projects/my-project/ \
  --task-description "CFW mouse GWAS: QC and association testing"
```

Log key events as the session progresses:

```bash
# Method/tool selection
python scripts/trace_logger.py log-decision \
  --run-id $RUN_ID --project-dir projects/my-project/ \
  --phase planning --decision "GEMMA LMM" \
  --rationale "relatedness matrix accounts for CFW population structure" \
  --alternatives-considered "PLINK logistic,SAIGE"

# Biomni query result
python scripts/trace_logger.py log-biomni \
  --run-id $RUN_ID --project-dir projects/my-project/ \
  --query "GWAS hits for mouse body weight" --tool-used "gwas_catalog" \
  --summary "3 loci on chr2, chr4, chr12" \
  --downstream-decision "prioritize Lepr, Mc4r for annotation"

# Summarize at session end
python scripts/trace_logger.py summarize \
  --run-id $RUN_ID --project-dir projects/my-project/
```

### Sequential thinking audit log

The `.claude/hooks/post-sequential-thinking.sh` hook fires after every sequential thinking
invocation and appends a timestamped record to `.claude/st_invocations.log`. This provides a
filesystem-level audit of every structured reasoning event, independent of the trace system.

### Trace validation

Run after any session to check that logging requirements were met:

```bash
python tests/trace_quality/validate_trace.py \
  --run-id $RUN_ID --project-dir projects/my-project/
# Exit 0 = all checks passed
# Exit 1 = quality warnings (non-blocking)
# Exit 2 = critical failures (e.g. no init-run entry)
```

Checks include: run initialized, at least one sequential thinking entry, no unclosed branches,
all Biomni queries have downstream decisions recorded, planning decision logged before ExitPlanMode.

### Session harvesting

To reconstruct what happened in a past session from the Claude Code JSONL file:

```bash
python scripts/harvest_session.py \
  --session-file ~/.claude/projects/<project>/<session_id>.jsonl \
  --output-dir reasoning_traces/retro/
```

Outputs `session_summary.json` with tool call counts, bash commands, file operations, and
sequential thinking blocks extracted from the raw session.

---

## Version Consistency

The `check_knowhow_versions.py` script compares tool version pins in `knowhow/*.md` frontmatter
against the active conda environment. Run it at the start of every session:

```bash
python scripts/check_knowhow_versions.py
# Exit 0 = all MATCH or NOT_FOUND
# Exit 1 = at least one MISMATCH (use --strict for CI)
```

If a MISMATCH is reported for a tool central to the current analysis, update the knowhow doc
frontmatter or `base-env.yml` before proceeding. Mismatched versions in key tools (GATK, PLINK2,
GEMMA) can silently change filter behavior and invalidate results.

---

## Adversarial Tests

`tests/adversarial/` contains deliberately broken inputs designed to verify the agent detects
and handles common failure modes before they reach results:

| Test | What it checks |
|------|---------------|
| `inflated_lambda/` | Agent flags λ_GC = 2.1 and triggers sequential thinking before reporting |
| `batch_effect/` | Unlabeled batch structure is identified via PCA before DE analysis |
| `wrong_genome_build/` | hg19/GRCh38 mismatch detected from BAM header before alignment |
| `corrupted_gemma_output/` | Truncated association file caught before downstream annotation |

Run any test with its `run_test.sh` script. Each test has a `README.md` describing the injected
fault and the expected agent response.

---

## Peer Review Agent Pattern

Every pipeline in this framework ends with an automated Claude Opus peer review step. The
`peer_review` rule (Snakemake) or `peer_review` process (Nextflow) runs last and:

1. Collects all analysis outputs (QC stats, results summaries, key metrics)
2. Calls Claude Opus with a domain-specific review prompt
3. Writes three files:
   - `results/peer_review/review_report.md` — full narrative review with section scores
   - `results/peer_review/issues.json` — structured issue list with severity tags
   - `results/peer_review/proposed_changes.md` — actionable corrections requiring user approval

**The approve-before-execute contract:** proposed changes are never auto-applied. The user reads
`proposed_changes.md`, then explicitly approves: *"Implement the proposed changes from
proposed_changes.md"*. This keeps humans in the loop for all scientifically significant corrections.

---

## Sequential Thinking Pattern

The agent uses the `sequential-thinking` MCP to make reasoning explicit at high-stakes decision
points. This is **automatic** — not user-initiated — and fires based on uncertainty thresholds
defined in `CLAUDE.md`.

### Why this matters for complex analyses

Inline reasoning (thinking while writing a response) is invisible and irreversible. When a
bioinformatics decision has real consequences — choosing a normalization method, diagnosing a
discrepancy, setting a QC threshold — unstructured reasoning can commit to a wrong branch too
early without exploring alternatives.

Sequential thinking enforces:
- **Explicit branching** — every plausible explanation is enumerated before any is acted on
- **Revision** — earlier steps can be marked wrong and reconsidered (`isRevision=True`)
- **Verifiable conclusions** — reasoning terminates only when a position can be defended, not when it feels right

### Example: SNP count discrepancy (mouse GWAS pilot)

Without sequential thinking, the agent saw "61,954 post-QC SNPs" in the QC summary vs "16,710"
in the Bonferroni threshold and immediately investigated the most salient hypothesis (label bug).
That happened to be correct — but three other hypotheses (wrong BIM, PLINK filter ordering bug,
calculation error in check_significance.py) were never formally enumerated or ruled out.

With sequential thinking configured, the agent would have opened all four branches, read the
relevant source for each, and closed them with evidence before committing to the fix. The result
is the same, but the reasoning is traceable and less likely to miss a branch on harder problems.

### When it fires

See the trigger table in the [Three-Phase AI Workflow](#three-phase-ai-workflow) section above.
Full specification is in `CLAUDE.md` under *Sequential Thinking Protocol*.

---

## Example Project: Mouse Obesity GWAS

`projects/mouse-obesity-gwas/` is a fully documented pilot run of a genome-wide association study
for body weight in outbred CFW mice (N=453, 16,710 SNPs). It demonstrates:

- Snakemake pipeline with checkpoint-based dynamic branching (enrichment vs. BSLMM)
- Biomni biological QC step with Claude API fallback
- Claude Opus peer review with 2-round correction cycle
- Agent-driven debugging of real pipeline failures (R fread parsing bug, conda env reference)
- Gene annotation via Ensembl REST API

See `projects/mouse-obesity-gwas/README.md` for full documentation.

---

## Know-How Library

The `knowhow/` directory contains dense reference docs for the most common bioinformatics workflows.
Load them into a Claude Code session with `@file` syntax:

```bash
# In Claude Code, when starting a GWAS project:
@~/path/to/knowhow/gwas.md

# For scRNA-seq:
@~/path/to/knowhow/singlecell.md
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
