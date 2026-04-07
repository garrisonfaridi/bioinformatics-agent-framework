---
name: spatial-register
description: "Spatial registration and alignment of tissue sections to reference atlases
  or 3D reconstruction. Input: --input <.h5ad> [--atlas <reference>] --output <dir>.
  Output: registered.h5ad, alignment_plot.png.
  User alias: spatial-registration."
license: MIT
metadata:
    skill-author: Garrison Faridi
---

## spatial-register — Spatial Registration

Align spatial transcriptomics sections to anatomical reference atlases or other sections.

### When to use

- Mapping Visium data to Allen Brain Atlas coordinates
- 3D reconstruction from serial tissue sections
- Cross-sample spatial alignment for comparison

### Example

```bash
python3 spatial_register.py --input visium.h5ad --atlas allen_brain --output results/registered/
python3 spatial_register.py --input section1.h5ad --reference section2.h5ad --output results/registered/
```
