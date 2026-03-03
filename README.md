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
              └────────────────┬────────────────┘
                               │
   ┌───────────────────────────▼─────────────────────────────────┐
   │                    Snakemake Pipeline                        │
   │                                                              │
   │  QC → Kinship → LMM → [checkpoint] → Branch A (enrichment) │
   │                                    → Branch B (BSLMM)       │
   │                                                              │
   │              ↓  (always runs last)                           │
   │         Claude Opus Peer Review                              │
   │   (review_report.md, proposed_changes.md)                    │
   └──────────────────────────────────────────────────────────────┘
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
├── base-env.yml                 # base conda environment (Python 3.11, R 4.4+, Snakemake, NGS tools)
├── biomni_mcp_server.py         # Biomni MCP server wrapper — register once with Claude Code
├── biomni_run.py                # Biomni library-mode runner for standalone tasks
├── .gitignore
│
├── templates/                   # Starter pipeline templates
│   ├── nextflow-rnaseq/         # STAR + salmon + DESeq2
│   ├── nextflow-wgs/            # BWA-MEM2 + GATK4 + VEP
│   ├── snakemake-rnaseq/        # STAR + featureCounts + DESeq2
│   ├── singlecell-scanpy/       # Python scanpy + anndata
│   └── singlecell-seurat/       # R Seurat v5
│
├── knowhow/                     # Domain-specific reference docs
│   ├── gwas.md                  # Mouse/human GWAS, mixed models, GEMMA, R/qtl2
│   ├── rnaseq.md                # Bulk RNA-seq QC, alignment, DE analysis
│   ├── singlecell.md            # scRNA-seq thresholds, clustering, annotation
│   ├── variant_calling.md       # GATK4 best practices, hard filter vs VQSR
│   ├── pipeline_dev.md          # Nextflow vs Snakemake, nf-core, CI/CD
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

### 4. First Biomni run (downloads data lake)

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
