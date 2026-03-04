# Bioinformatics Agent Framework

## 1. Identity and Scope

Freelance analyst and pipeline developer. Primary workflows: bulk RNA-seq, scRNA-seq,
WGS/WES variant calling, ATAC-seq/ChIP-seq, GWAS. Pipeline frameworks: Nextflow DSL2
(preferred), Snakemake, WDL. Languages: Python 3.11+, R 4.3+. Containers: Docker/Singularity
for HPC portability. Client deliverables: reproducible pipelines, QC reports, statistical
analysis, publishable methods sections.

**HPC awareness:** Some analyses cannot run locally. See Section 5 (HPC Pipeline Mode).

**Hard rules (always apply):**
1. Pin all tool versions — conda envs, Dockerfiles, nextflow.config/config.yaml
2. Use containers — every pipeline process gets Docker/Singularity; no bare conda in rules
3. Standard directories — `data/`, `results/`, `logs/`, `scripts/`, `envs/`, `containers/`
4. Set random seeds — `set.seed(42)` R, `random_state=42` Python
5. README + METHODS.md per deliverable
6. Never hard-code paths — config files, params blocks, or env vars
7. MultiQC as final step on every pipeline

---

## 2. Session Start Protocol (mandatory)

Run at the start of every new analysis session:

```bash
# 1. Check tool versions are consistent with knowhow docs
python scripts/check_knowhow_versions.py

# 2. Initialize run trace
RUN_ID=$(date +%Y%m%d_%H%M%S)_<short_description>
python scripts/trace_logger.py init-run \
  --run-id $RUN_ID \
  --project-dir <project_dir> \
  --task-description "<one sentence>"

# 3. Load relevant knowhow doc (see Section 9)
# e.g.: @knowhow/gwas.md
```

If version checker reports MISMATCH: update the knowhow doc frontmatter OR base-env.yml —
do not proceed with mismatched tools central to the current analysis.

---

## 3. Three-Phase Model Protocol

### Phase 1 — Research (Biomni + Opus)

```bash
claude --model claude-opus-4-6
```

| Task | Tool |
|------|------|
| Find papers on a method or phenotype | Biomni (PubMed) |
| Query known gene/variant associations | Biomni (GWAS Catalog, UniProt, ClinVar) |
| Check public datasets | Biomni (literature + database search) |
| GO/pathway enrichment interpretation | Biomni (clusterProfiler + narrative) |
| Drug-gene or protein interaction lookup | Biomni (STRING, DrugBank) |
| Synthesize findings into a design decision | Opus + Sequential Thinking |
| Choose between statistical approaches | Opus + Sequential Thinking |
| Write plan.md / experimental design | Opus |

**Rule:** Biomni provides grounded database facts. Opus reasons over them. Never ask Opus to
recall specific papers or gene lists from memory — run Biomni first.

**Biomni invocation:**
```bash
cd [repo root]
python biomni_run.py "your task with specific databases and output fields"
# Results in ./results/
```

### Phase 2 — Planning (Opus, EnterPlanMode)

Opus writes plan.md covering: experimental design rationale, tool selection with justification,
expected failure modes, QC checkpoints, file structure, config schema.

Run sequential thinking (Section 4) before `ExitPlanMode`. Require user approval before
any implementation begins.

### Phase 3 — Implementation (Sonnet, default)

After plan approval, Sonnet handles all scripting, debugging, and pipeline execution.
Sequential thinking fires at ambiguous decision points per Section 4 triggers.

```bash
alias claude-plan='claude --model claude-opus-4-6'   # Phases 1+2
# Plain 'claude' = Sonnet for Phase 3
```

---

## 4. Sequential Thinking Protocol

The `sequential-thinking` MCP is available and **must be invoked** whenever reasoning involves
ambiguity, competing hypotheses, or cascading design decisions. Use the tool to make reasoning
explicit, revisable, and auditable — do not rely on inline reasoning at decision points.

### Mandatory triggers

Call `mcp__sequential-thinking__sequentialthinking` when ANY of the following apply:

**1. Competing hypotheses (≥2 plausible explanations exist)**
A result, error, or discrepancy has more than one plausible cause. Work through all branches
before acting.
- Unexpected pipeline output (counts, p-values, fold changes, plots) contradicting expectations
- A bug with ambiguous root cause (parsing, wrong input, tool version, logic error, env issue)
- A QC metric outside expected range (λ_GC, duplication rate, mapping rate, cluster resolution)

**2. Method or tool selection with real tradeoffs**
- Statistical model selection (LMM vs logistic, DESeq2 vs edgeR, VQSR vs hard filters)
- Aligner or quantification strategy when sample characteristics are unusual
- QC threshold calibration (--mind, --maf, min_genes, min_cells, min_counts)
- Whether to apply batch correction, and which method

**3. Architectural decisions affecting ≥3 pipeline steps**
A single design choice (file format, processing order, checkpoint placement) that propagates
through multiple downstream rules or processes.

**4. Unexpected or counterintuitive results**
- No significant hits in a well-powered study
- A cluster with no matching canonical marker set
- Heritability far from published values
- DE results with implausibly uniform or extreme effect sizes

**5. Before every ExitPlanMode call**
Stress-test the plan: What is the most likely failure mode? What assumption is most likely wrong?
Is there a simpler approach?

**6. Critical or ambiguous peer review issues**
When peer review flags a critical-severity issue, use sequential thinking to trace root cause
before implementing any fix.

### When NOT to invoke
- Scripting tasks where the spec is fully determined
- Reading or writing files with a clear, known purpose
- Running a pipeline step that has already been validated
- Formatting, documentation, or renaming work

### Usage pattern
Start with a conservative `totalThoughts` estimate; adjust upward as needed.
Use `isRevision=True` + `revisesThought=N` when reconsidering a prior step.
Branch with `branchFromThought` for separate path exploration.
Set `nextThoughtNeeded=False` only when a verified conclusion is reached.

**Note:** The `.claude/hooks/post-sequential-thinking.sh` hook automatically records
every invocation to `.claude/st_invocations.log` as a filesystem-level audit.

---

## 5. HPC Pipeline Mode

Some analyses require HPC execution (large WGS cohorts, genome-wide imputation,
GWAS N > 500, scRNA-seq > 100k cells, etc.).

**When HPC is required:**
1. NEVER attempt to run the pipeline locally
2. Generate all pipeline files but do NOT execute them
3. Create `hpc/` in the project with:
   - `submit.sh` — master SLURM submission script
   - `job_configs/` — per-step SLURM headers (use `templates/hpc/slurm_header_template.sh`)
   - `transfer_instructions.md` — what to rsync to the cluster (use `templates/hpc/transfer_instructions.md`)
   - `expected_outputs.md` — expected files with size thresholds (use `templates/hpc/expected_outputs_template.md`)
   - `local_postprocess.sh` — steps to run locally after retrieval (use `templates/hpc/local_postprocess_template.sh`)
4. Deliverable = validated pipeline code + complete submission package
   The human submits, monitors, and retrieves results.

**Auto-trigger HPC mode for:**
- Nextflow or Snakemake pipeline with >50 samples
- GWAS with N > 500
- WGS variant calling (any N)
- Imputation with any reference panel
- scRNA-seq with >100k cells
- Any step requiring >32 GB RAM or >8 cores sustained

See `knowhow/pipeline_dev.md` → HPC/SLURM section for Nextflow executor config,
`-resume` patterns, file staging, and memory tier guidance.

---

## 6. Trace Logging Protocol

Every analysis run MUST have a `run_id` (format: `YYYYMMDD_HHMMSS_<short_description>`).

### Session start (mandatory)
```bash
python scripts/trace_logger.py init-run \
  --run-id $(date +%Y%m%d_%H%M%S)_<short_description> \
  --project-dir <project_dir> \
  --task-description "<one sentence>"
```

### Mandatory logging calls

| Event | Command | When |
|-------|---------|------|
| Sequential thinking | `log-sequential` | Before every ST invocation |
| Biomni query | `log-biomni` | After every query that informs a decision |
| Method/tool selection | `log-decision` | At every model, tool, or QC threshold choice |
| Plan finalized | `log-decision --phase planning` | Before ExitPlanMode |

These are non-negotiable. A run without a trace has no audit trail.

### Command patterns
```bash
# Sequential thinking
python scripts/trace_logger.py log-sequential \
  --run-id $RUN_ID --project-dir $PROJECT_DIR \
  --trigger "≥2 competing hypotheses" \
  --context "<ambiguity description>" \
  --hypotheses "hyp_a,hyp_b" \
  --evidence-used "<what was checked>" \
  --branch-closed "hyp_b" \
  --conclusion "<final decision>"

# Decision
python scripts/trace_logger.py log-decision \
  --run-id $RUN_ID --project-dir $PROJECT_DIR \
  --phase planning \
  --decision "<what was chosen>" \
  --rationale "<why>" \
  --alternatives-considered "alt1,alt2"

# Biomni query
python scripts/trace_logger.py log-biomni \
  --run-id $RUN_ID --project-dir $PROJECT_DIR \
  --query "<query text>" \
  --tool-used "<tool>" \
  --summary "<result summary>" \
  --downstream-decision "<decision informed>"

# Summarize at session end
python scripts/trace_logger.py summarize \
  --run-id $RUN_ID --project-dir $PROJECT_DIR
```

---

## 7. Approval Gate

Before any pipeline execution, a `plan.approved` sentinel file must exist in the project
directory. The `.claude/hooks/pre-bash.sh` hook enforces this structurally by blocking
`snakemake`, `nextflow run`, `sbatch`, `srun`, and `qsub` without it.

```bash
# Workflow:
# 1. Read plan.md
# 2. Approve: touch plan.approved
# 3. Revoke: rm plan.approved  (triggers re-planning)
```

The Snakemake template also checks for `plan.approved` at startup:
```python
if not os.path.exists("plan.approved"):
    raise SystemExit("ERROR: plan.approved not found. Review plan.md first.")
```

---

## 8. Peer Review Protocol

Peer review `issues.json` schema (round-prefixed IDs required):
```json
{
  "review_round": 1,
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "run_id": "20250101_120000_gwas_cfw",
  "issues": [{
    "id": "R1-001",
    "severity": "critical|major|minor|note",
    "category": "statistical|biological|computational|reproducibility",
    "description": "...",
    "location": "...",
    "proposed_fix": "...",
    "status": "open"
  }]
}
```

**Protocol:**
1. Run `python scripts/review_diff.py --round1 ... --round2 ... --output ...` before
   implementing any correction (shows resolved / persisted / regressed / new)
2. Prioritize CRITICAL → MAJOR
3. Implement corrections → trigger new pipeline run (do NOT edit results directly)
4. A correction is only "resolved" when the next review round marks it absent

Peer review outputs live in `results/peer_review/round{N}/`.

---

## 9. Knowhow References

Load with `@file` when working on the relevant analysis type:

| File | When to load |
|------|-------------|
| `@knowhow/rnaseq.md` | Bulk RNA-seq QC, alignment, DE |
| `@knowhow/singlecell.md` | scRNA-seq QC, clustering, annotation |
| `@knowhow/variant_calling.md` | GATK best practices, hard filter vs VQSR |
| `@knowhow/pipeline_dev.md` | Nextflow vs Snakemake, nf-core, HPC, CI |
| `@knowhow/gwas.md` | GWAS, QTL mapping, mixed models, Lindley score |
| `@knowhow/freelance_methods.md` | Publishable methods templates |
| `@knowhow/biomni.md` | Biomni MCP setup and tool inventory |

**New topic protocol:** If a topic has no knowhow doc, create `knowhow/<topic>.md` covering:
method overview, tool preferences + versions, workflow steps, databases, compute requirements,
pitfalls, and a publishable methods template. Add frontmatter version block.

---

## 10. Tool Preferences

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
| Trimming/QC | fastp |
| Pipeline framework | Nextflow DSL2 + nf-core modules |
| GWAS (mouse) | GEMMA 0.98.5 (LMM + BSLMM) |

---

## Active Projects

<!-- Format: path — description (tools used) -->
