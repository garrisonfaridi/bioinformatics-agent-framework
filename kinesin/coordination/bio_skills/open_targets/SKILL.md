---
name: open_targets
description: "Query Open Targets Platform for disease-gene associations, drug targets, and
  genetic evidence. Input: --disease <EFO_ID or name> [--gene <gene_symbol>] --output <dir>.
  Output: associations.json, evidence_summary.csv. Distinct from built-in gwas-database
  skill (GWAS Catalog); this skill uses Open Targets Platform GraphQL API."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## open_targets — Open Targets Platform Query

Query the Open Targets Platform for disease-gene associations and drug target evidence.

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| Disease associations | `--disease "neuroblastoma"` | top gene associations by score |
| Gene-disease evidence | `--gene MYCN --disease neuroblastoma` | evidence types + scores |
| Drug targets | `--disease "type 2 diabetes" --drugs` | druggable targets + clinical phase |

### When to use

- Prioritizing candidate genes by disease association score
- Identifying approved drugs for target repurposing
- Integrating genetic + expression + functional evidence

### When NOT to use

- GWAS summary statistics download (use gwas-database built-in)
- Variant-level queries (use variant-query skill)
- ClinVar variant interpretation (use clinvar skill)

### Example

```bash
python3 open_targets_query.py --disease "Parkinson disease" --output /tmp/ot_results/
python3 open_targets_query.py --gene LRRK2 --disease "Parkinson disease" --output /tmp/ot_results/
```
