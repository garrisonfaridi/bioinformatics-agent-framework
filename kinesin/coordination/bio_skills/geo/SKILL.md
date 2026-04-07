---
name: geo
description: "Search and download datasets from NCBI GEO (Gene Expression Omnibus). Input:
  --query <search_string> [--accession <GSExxxxxx>] --output <dir>. Output: metadata.json,
  sample_table.csv, series_matrix.txt (if --accession provided). Uses GEOparse + NCBI E-utilities."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## geo — NCBI GEO Search and Download

Search NCBI GEO for datasets matching a keyword query, or download a specific GEO series by accession.

### Capabilities

| Task | Input | Output |
|------|-------|--------|
| Keyword search | `--query "neuroblastoma RNA-seq"` | metadata.json (list of matching series) |
| Series download | `--accession GSE12345` | series_matrix.txt, sample_table.csv |
| Full download | `--accession GSE12345 --download` | raw data files + metadata |

### When to use

- Client asks "find RNA-seq datasets for X disease"
- Need public training data for a model
- Literature review mentions a GEO dataset

### When NOT to use

- Downloading SRA raw FASTQ files (use SRA-tools / sra-download skill)
- ENCODE data (use encode-search skill)
- GTEx data (use gtex-query skill)

### Example

```bash
python3 geo_search.py --query "Arabidopsis stomata drought" --output /tmp/geo_results/
python3 geo_search.py --accession GSE123456 --output /tmp/gse123456/
```
