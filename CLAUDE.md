# Bioinformatics Claude Code — Global Context

## Background

[YOUR_DEGREE_AND_SPECIALTY]. Freelance analyst and pipeline developer. Primary workflows:
[YOUR_PRIMARY_WORKFLOWS]. Pipeline frameworks: Nextflow DSL2 (preferred), Snakemake, WDL.
Languages: Python 3.11+, R 4.3+. Containers: Docker/Singularity for HPC portability.
Client deliverables include reproducible pipelines, QC reports, statistical analysis, and
written methods sections.

---

## Hard Rules

1. **Pin all tool versions** — in conda envs, Dockerfiles, and nextflow.config/config.yaml.
2. **Use containers** — every process in a Nextflow/Snakemake pipeline gets a Docker/Singularity
   container. No bare conda in pipeline processes.
3. **Standard directory structure** — `data/`, `results/`, `logs/`, `scripts/`, `envs/`,
   `containers/` in every project root.
4. **Set random seeds** — `set.seed(42)` in R, `random_state=42` in Python, for all stochastic
   steps (clustering, UMAP, permutation tests).
5. **README + methods per deliverable** — every project gets a `README.md` (usage, inputs,
   outputs) and a `METHODS.md` (2–3 sentence publishable methods blurb per analysis step).
6. **Never hard-code paths** — use config files, params blocks, or environment variables.
7. **MultiQC on every pipeline** — generate an aggregated QC report as the final step.

---

## Tool Preferences

| Step | Preferred tool |
|------|---------------|
| Short-read alignment (RNA) | STAR 2.7+ |
| Short-read alignment (DNA) | BWA-MEM2 |
| Transcript quantification | salmon (quasi-mapping); featureCounts for legacy |
| Differential expression | DESeq2 (primary), edgeR, limma-voom |
| Batch correction | ComBat-seq (counts); limma::removeBatchEffect (log-normalized) |
| scRNA-seq (Python) | scanpy + anndata |
| scRNA-seq (R) | Seurat v5 |
| Variant calling | GATK4 (HaplotypeCaller → VQSR or hard filters) |
| Variant annotation | VEP (Ensembl) |
| QC aggregation | MultiQC |
| Trimming/QC | fastp (preferred over Trimmomatic) |
| Pipeline framework | Nextflow DSL2 + nf-core modules |

---

## Biomni (Agentic Bioinformatics)

For complex tasks requiring multi-database queries, literature mining, cross-tool evidence
synthesis, or autonomous multi-step analysis, **proactively use the biomni MCP server**
rather than writing custom code. Read `@[PATH_TO_KNOWHOW]/biomni.md` to determine
whether a task qualifies and how to invoke it.

Biomni handles: database lookups (UniProt, NCBI, ClinVar, TCGA), pathway/GO enrichment with
biological interpretation, variant evidence synthesis, cell type annotation, drug-gene queries,
and literature mining. Do not use it for standard pipeline steps (alignment, DE, variant calling)
where containers and pinned tools are required.

### Biomni-First Search Rule

**When the user asks to find, search for, or locate any of the following, use Biomni BEFORE
falling back to generic web search:**

| User intent | Biomni action |
|-------------|--------------|
| "Find a dataset for X" | Literature + database search via biomni_run.py |
| "Search for papers on X" | PubMed mining via biomni_run.py |
| "What public data exists for X analysis?" | Database + literature search via biomni_run.py |
| "Find genes/variants associated with X" | GWAS Catalog + PubMed via biomni_run.py |
| "Look up tools/methods for X" | Literature search via biomni_run.py |
| "Summarize what is known about X gene/protein" | UniProt + PubMed via biomni_run.py |

**How to invoke for literature/dataset search (library mode):**
```bash
cd [PATH_TO_REPO]
python biomni_run.py "your search task description with specific databases and output fields requested"
```
Results land in `./results/`. Run in background when combined with other tasks.

**Only fall back to generic web search when:**
- Biomni runner is unavailable or errors out
- The query is about software installation, CLI tools, or non-biological topics
- The user explicitly asks for a web search

### New Topic Protocol

When the user introduces a bioinformatics topic not covered by an existing know-how doc,
**create a new know-how file at `[PATH_TO_KNOWHOW]/<topic>.md`** covering:
1. Method overview and key concepts
2. Mouse/human-specific considerations if applicable
3. Preferred tools with versions and justification
4. Standard analysis workflow steps
5. Key databases and data sources
6. Compute/memory requirements and scaling considerations
7. Common pitfalls and QC checkpoints
8. Publishable methods template

Then add the new file to the Know-How Docs list below.

---

## Sequential Thinking Protocol

The `sequential-thinking` MCP is available and **must be invoked** whenever reasoning involves
ambiguity, competing hypotheses, or cascading design decisions. Do not rely on inline reasoning
for these cases — use the tool to make reasoning explicit, revisable, and auditable.

### Mandatory triggers

Call `mcp__sequential-thinking__sequentialthinking` when ANY of the following apply:

**1. Competing hypotheses (≥2 plausible explanations exist)**
A result, error, or discrepancy has more than one plausible cause. Work through all branches
before acting — do not pick one and proceed.
- Unexpected pipeline output (counts, p-values, fold changes, plots) that contradicts expectations or literature
- A bug where root cause is ambiguous (parsing, wrong input, tool version, logic error, env issue)
- A QC metric outside expected range (λ_GC, duplication rate, mapping rate, cluster resolution)

**2. Method or tool selection with real tradeoffs**
Choosing between approaches with different statistical assumptions, failure modes, or downstream
consequences:
- Statistical model selection (LMM vs logistic, DESeq2 vs edgeR, VQSR vs hard filters, pseudobulk vs mixed model)
- Aligner or quantification strategy when sample characteristics are unusual
- QC threshold calibration (--mind, --maf, min_genes, min_cells, min_counts)
- Whether to apply batch correction, and which method

**3. Architectural decisions affecting ≥3 pipeline steps**
A single design choice (file format, processing order, checkpoint placement, intermediate output)
that propagates through multiple downstream rules or processes.

**4. Unexpected or counterintuitive results**
Any result that is surprising, internally inconsistent, or requires a judgment call before
reporting to a client:
- No significant hits in a well-powered study
- A cluster with no matching canonical marker set
- Heritability or variance explained far from published literature values
- DE results with implausibly uniform or extreme effect sizes
- Discrepancies between summary statistics and raw outputs

**5. Before every ExitPlanMode call**
Always run sequential thinking to stress-test the plan before presenting it for user approval.
Minimum questions to answer: What is the most likely failure mode? What assumption is most
likely wrong? Is there a simpler approach that achieves the same goal?

**6. Critical or ambiguous peer review issues**
When the automated peer review flags a critical-severity issue, use sequential thinking to
trace root cause before implementing any fix. Moderate issues with unclear origin also qualify.

### When NOT to invoke

- Scripting tasks where the spec is fully determined and unambiguous
- Reading or writing files with a clear, known purpose
- Running a pipeline step that has already been validated
- Formatting, documentation, or renaming work

### Usage pattern

Start with a conservative `totalThoughts` estimate and adjust upward as the problem evolves.
Use `isRevision=True` + `revisesThought=N` when a prior step needs to be reconsidered.
Branch with `branchFromThought` when two paths need separate exploration. Set
`nextThoughtNeeded=False` only when a clear, verified conclusion has been reached.

---

## Model Selection Protocol

### Three-phase workflow for every new project or research question

**Phase 1 — Research (Biomni + Opus together)**

Start a planning session with Opus:
```bash
claude --model claude-opus-4-6
```

Within that session, use Biomni *first* for grounded evidence gathering, then Opus to reason over the results:

| Task | Tool |
|------|------|
| Find papers on a method or phenotype | Biomni (PubMed) |
| Query known gene/variant associations | Biomni (GWAS Catalog, UniProt, ClinVar) |
| Check what public datasets exist | Biomni (literature + database search) |
| Pathway/GO enrichment interpretation | Biomni (clusterProfiler + narrative) |
| Drug-gene or protein interaction lookup | Biomni (STRING, DrugBank) |
| Synthesize findings into a design decision | Opus |
| Choose between statistical approaches | Opus + Sequential Thinking |
| Write the plan.md / experimental design | Opus |
| Identify what could go wrong architecturally | Opus + Sequential Thinking |

**Rule:** Biomni provides grounded database facts. Opus reasons over them. Sequential thinking
makes that reasoning explicit at high-stakes decision points. Sonnet executes.

**Phase 2 — Planning (Opus, `EnterPlanMode`)**

Opus writes the plan.md. It should cover:
- Experimental design rationale (informed by Biomni literature output)
- Tool and method selection with justification
- Expected failure modes and QC checkpoints
- File structure and config schema

Run sequential thinking before calling `ExitPlanMode` to stress-test assumptions.
Require user approval before any implementation begins.

**Phase 3 — Implementation (Sonnet, default)**

After plan approval, switch to a standard Sonnet session for all scripting, debugging, and
pipeline execution. Sequential thinking fires automatically at ambiguous decision points per
the triggers above.

### Shell aliases

```bash
alias claude-plan='claude --model claude-opus-4-6'   # Phase 1+2: research + planning
# Plain 'claude' uses default Sonnet for Phase 3: implementation
```

---

## Know-How Docs

Load these manually with `@file` when working on the relevant analysis:

- `@[PATH_TO_KNOWHOW]/rnaseq.md` — Bulk RNA-seq QC, alignment, DE analysis
- `@[PATH_TO_KNOWHOW]/singlecell.md` — scRNA-seq QC thresholds, clustering, annotation
- `@[PATH_TO_KNOWHOW]/variant_calling.md` — GATK best practices, hard filter vs VQSR
- `@[PATH_TO_KNOWHOW]/pipeline_dev.md` — Nextflow vs Snakemake, nf-core, CI
- `@[PATH_TO_KNOWHOW]/freelance_methods.md` — Publishable methods templates
- `@[PATH_TO_KNOWHOW]/biomni.md` — Biomni MCP setup, when to use, tool modules
- `@[PATH_TO_KNOWHOW]/gwas.md` — Mouse/human GWAS, QTL mapping, mixed models, tools (PLINK2, GEMMA, R/qtl2)

---

## Project Templates

Starter templates live in `[PATH_TO_REPO]/templates/`:
- `nextflow-rnaseq/` — Nextflow + STAR + salmon + DESeq2
- `nextflow-wgs/` — Nextflow + BWA-MEM2 + GATK4 + VEP
- `snakemake-rnaseq/` — Snakemake + STAR + featureCounts + DESeq2
- `singlecell-scanpy/` — Python scanpy workflow
- `singlecell-seurat/` — R Seurat v5 workflow

## Active Projects

<!-- Add active project entries here as you start new analyses -->
<!-- Format: path — description (tools used) -->
