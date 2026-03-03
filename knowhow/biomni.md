# Biomni — Agentic Bioinformatics MCP

Biomni is an autonomous biomedical AI agent with 150+ tools across 20 domains.
It is registered as an MCP server and should be used when a task genuinely
requires multi-tool synthesis, cross-database evidence, or biological interpretation
beyond what standard pipeline tools can provide.

---

## When to Use Biomni (Use Proactively)

**Use biomni MCP when the task involves:**
- Database lookups across UniProt, NCBI, Ensembl, ClinVar, PDB, GWAS Catalog, TCGA
- Literature mining — finding papers, extracting methods, summarizing gene/protein context
- Pathway/network analysis — KEGG, GO enrichment with biological interpretation
- Variant interpretation requiring cross-database evidence (ClinVar + gnomAD + literature)
- Cell type annotation with automated marker gene lookup
- Drug-gene interaction queries (pharmacogenomics context)
- Any analysis where 3+ specialized bioinformatics tools must be chained autonomously

**Do NOT use biomni when:**
- A standard pipeline step suffices (alignment, quantification, DE, variant calling)
- The task fits within a single Nextflow/Snakemake process
- Reproducibility in a container is the priority — use GATK/DESeq2/etc. directly

---

## Registration

Wrapper script: `/Users/garrisonfaridi/agent/bioinformatics-freelance/biomni_mcp_server.py`

Register once, then restart Claude Code:
```bash
claude mcp add biomni -- python /Users/garrisonfaridi/agent/bioinformatics-freelance/biomni_mcp_server.py
```

Verify:
```bash
claude mcp list
```

**Requires:** `ANTHROPIC_API_KEY` set in environment. First run downloads ~11 GB data lake.

---

## Exposed Tool Modules

| Module | Use for |
|--------|---------|
| `biomni.tool.genomics` | RNA-seq, WGS, alignment, variant calling workflows |
| `biomni.tool.genetics` | GWAS, variant interpretation, population genetics |
| `biomni.tool.cell_biology` | scRNA-seq, cell type annotation, Seurat/scanpy tasks |
| `biomni.tool.molecular_biology` | ChIP-seq, ATAC-seq, epigenomics |
| `biomni.tool.systems_biology` | KEGG, GO enrichment, gene network analysis |
| `biomni.tool.database` | UniProt, NCBI, Ensembl, ClinVar, PDB queries |
| `biomni.tool.literature` | PubMed mining, methods extraction, gene summaries |
| `biomni.tool.cancer_biology` | Somatic variants, tumor biology, TCGA data |
| `biomni.tool.pharmacology` | Drug-gene interactions, ADMET, repurposing |
| `biomni.tool.protocols` | Standard experimental protocols |

---

## Interactive Runner (Library Mode / Fallback)

For project-level agentic execution (or if MCP server is not registered),
use the runner script from the project directory:

```bash
cd ~/agent/bioinformatics-freelance/projects/scmultiomics-exploration
python ~/agent/bioinformatics-freelance/biomni_run.py "your task description"
```

Results land in `./results/` relative to where the script is run.
Override with `BIOMNI_PROJECT_PATH=/path/to/results`.

Example vague inputs biomni can handle:
```
"Find a suitable public PBMC Multiome dataset, download it, and run joint RNA+ATAC analysis"
"Perform full scRNA-seq analysis and annotate cell types using literature-supported markers"
"Suggest and execute a multi-omics strategy for studying the tumor microenvironment"
```

---

## Notes

- Default model: `claude-sonnet-4-5` (set in wrapper; change via `BIOMNI_LLM` env var)
- Biomni uses CodeAct — it reasons, writes code, and executes it autonomously
- Results are written to the `path` directory specified in A1()
- On HPC: activate miniforge3 env before starting Claude Code so `python` resolves correctly
