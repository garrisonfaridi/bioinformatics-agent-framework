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
