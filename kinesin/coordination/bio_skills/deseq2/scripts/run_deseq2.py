"""
run_deseq2.py — DESeq2 differential expression analysis skill.

Stub implementation. Full implementation invokes R subprocess running DESeq2.
"""

import argparse
import json
import sys


def main(counts: str, metadata: str, contrast: str, output: str) -> dict:
    """
    Run DESeq2 differential expression analysis.

    Args:
        counts:   Path to raw counts CSV (genes × samples).
        metadata: Path to sample metadata CSV.
        contrast: Contrast string (e.g. "condition:treatment_vs_control").
        output:   Output directory path.

    Returns:
        Dict with status, contrast, output path, and summary stats.
    """
    return {
        "status": "stub",
        "counts": counts,
        "metadata": metadata,
        "contrast": contrast,
        "output": output,
        "results": {
            "total_genes_tested": 0,
            "significant_genes_padj05": 0,
            "significant_genes_padj01": 0,
            "output_files": [
                f"{output}/deseq2_results.csv",
                f"{output}/MA_plot.png",
                f"{output}/volcano_plot.png",
            ],
            "note": "Requires R ≥ 4.3 with DESeq2 and apeglm installed",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DESeq2 differential expression.")
    parser.add_argument("--counts", required=False, default="counts.csv")
    parser.add_argument("--metadata", required=False, default="metadata.csv")
    parser.add_argument("--contrast", required=False, default="condition:A_vs_B")
    parser.add_argument("--output", default="/tmp/deseq2_output")
    parser.add_argument("--demo", action="store_true", help="Run demo/stub mode.")
    args = parser.parse_args()

    result = main(
        counts=args.counts,
        metadata=args.metadata,
        contrast=args.contrast,
        output=args.output,
    )
    print(json.dumps(result, indent=2))
