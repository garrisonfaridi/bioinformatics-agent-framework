"""
spatial_genes.py — Spatially variable gene detection.

OmicsClaw-sourced skill. Stub implementation.
"""

import argparse
import json
import sys


def main(input_path: str, output: str, method: str = "morans_i", n_top: int = 200) -> dict:
    return {
        "status": "stub",
        "input": input_path,
        "method": method,
        "n_top_svgs": n_top,
        "output": output,
        "results": {
            "svgs_detected": 0,
            "output_files": [
                f"{output}/spatially_variable_genes.csv",
                f"{output}/svg_plot.png",
            ],
            "note": "Install omicsclaw[spatial] for full implementation",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spatially variable gene detection.")
    parser.add_argument("--input", default="preprocessed.h5ad")
    parser.add_argument("--output", default="/tmp/spatial_genes")
    parser.add_argument("--method", default="morans_i", choices=["spatialde", "spark", "morans_i"])
    parser.add_argument("--n-top", type=int, default=200)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    result = main(args.input, args.output, args.method, args.n_top)
    print(json.dumps(result, indent=2))
