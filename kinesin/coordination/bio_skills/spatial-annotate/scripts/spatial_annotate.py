"""
spatial_annotate.py — Cell type annotation for spatial transcriptomics.

OmicsClaw-sourced skill. Stub implementation.
"""

import argparse
import json
import sys


def main(input_path: str, reference: str, output: str) -> dict:
    return {
        "status": "stub",
        "input": input_path,
        "reference": reference or "marker_based",
        "output": output,
        "results": {
            "cell_types_assigned": 0,
            "output_files": [
                f"{output}/annotated.h5ad",
                f"{output}/annotation_plot.png",
                f"{output}/cell_type_fractions.csv",
            ],
            "note": "Install omicsclaw[spatial] for full implementation",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spatial cell type annotation.")
    parser.add_argument("--input", default="domains.h5ad")
    parser.add_argument("--reference", default="", help="Reference scRNA-seq .h5ad (optional)")
    parser.add_argument("--output", default="/tmp/spatial_annotate")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    result = main(args.input, args.reference, args.output)
    print(json.dumps(result, indent=2))
