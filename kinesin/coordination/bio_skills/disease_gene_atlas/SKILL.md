---
name: disease_gene_atlas
description: "Query disease-gene associations from OMIM and DisGeNET. Input: --gene <symbol>
  [--disease <name>] --output <dir>. Output: omim_associations.json, disgenet_associations.csv,
  summary.md. Distinct from built-in UniProt skill (protein function); this skill focuses on
  disease genetics databases (OMIM + DisGeNET)."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## disease_gene_atlas — OMIM + DisGeNET Disease-Gene Associations

Query OMIM and DisGeNET for disease-gene association evidence.

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| Gene → diseases | `--gene CFTR` | omim_associations.json, disgenet_associations.csv |
| Disease → genes | `--disease "cystic fibrosis"` | ranked gene list by GDA score |
| Variant context | `--gene BRCA1 --disease "breast cancer"` | variant + disease evidence |

### When to use

- Candidate gene prioritization for Mendelian disease
- Enriching GWAS hits with known OMIM phenotypes
- Building disease-gene network for pathway analysis

### When NOT to use

- Protein function/structure queries (use UniProt built-in)
- Drug-target associations (use open_targets skill)
- Expression evidence (use geo or deseq2 skills)

### Example

```bash
python3 disease_gene_query.py --gene BRCA1 --output /tmp/dga/
python3 disease_gene_query.py --disease "Alzheimer disease" --output /tmp/dga/
```
