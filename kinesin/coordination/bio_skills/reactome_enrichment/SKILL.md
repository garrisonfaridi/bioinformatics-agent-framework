---
name: reactome_enrichment
description: "Pathway enrichment analysis using Reactome via gseapy. Input: --gene-list
  <genes.txt or comma-separated> --organism <human|mouse|rat> --output <dir>. Output:
  reactome_enrichment.csv (pathway, NES, padj), dot_plot.png. Distinct from built-in
  gene-enrichment skill (GO terms); this skill uses Reactome pathway database only."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## reactome_enrichment — Reactome Pathway Enrichment

Run over-representation analysis (ORA) or GSEA against the Reactome pathway database using gseapy.

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| ORA | gene list (DEGs) | reactome_enrichment.csv |
| GSEA | ranked gene list (log2FC) | gsea_reactome_results.csv |
| Multi-organism | human, mouse, rat, zebrafish | organism-specific Reactome sets |

### When to use

- Interpreting DESeq2 results for pathway context
- Identifying mechanistic pathways (signaling, metabolism)
- Reactome is preferred over GO for mechanistic pathway interpretation

### When NOT to use

- GO term enrichment (use gene-enrichment built-in skill)
- KEGG pathways (use kegg-enrichment skill)
- Phenotype ontology (HPO/MPO) enrichment

### Example

```bash
python3 reactome_query.py --gene-list BRCA1,TP53,PTEN --organism human --output /tmp/reactome/
python3 reactome_query.py --gene-list degs.txt --organism mouse --output /tmp/reactome/
```
