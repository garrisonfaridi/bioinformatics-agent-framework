---
name: spatial-condition
description: "Spatial condition comparison between multiple tissue samples or experimental
  groups. Input: --input <sample1.h5ad,sample2.h5ad,...> --groups <group_labels>
  --output <dir>. Output: condition_de.csv, spatial_composition_plot.png.
  User alias: spatial-condition-comparison."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-condition — Spatial Condition Comparison

Compare spatial transcriptomics data across experimental conditions or patient groups.

### Capabilities

| Task | Notes |
|------|-------|
| Multi-sample DE | Pseudo-bulk DE across conditions |
| Domain composition shifts | Cell type proportion changes |
| Spatial pattern changes | SVG changes between conditions |

### When to use

- Comparing disease vs healthy tissue sections
- Drug treatment spatial response
- Multi-patient cohort spatial analysis

### Example

```bash
python3 spatial_condition.py \
  --input "disease.h5ad,control.h5ad" \
  --groups "disease,control" \
  --output results/condition_comparison/
```
