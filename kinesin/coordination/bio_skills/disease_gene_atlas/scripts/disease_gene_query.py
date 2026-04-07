"""
disease_gene_query.py — OMIM + DisGeNET disease-gene association skill.

Stub implementation. Full implementation uses DisGeNET REST API + OMIM API.
"""

import argparse
import json
import sys


def main(gene: str, disease: str, output: str) -> dict:
    """
    Query disease-gene associations from OMIM and DisGeNET.

    Args:
        gene:    Gene symbol (e.g. CFTR, BRCA1).
        disease: Disease name (optional; filters results).
        output:  Output directory path.

    Returns:
        Dict with status, associations, and output files.
    """
    query_desc = f"{gene}" + (f" in {disease}" if disease else "")

    return {
        "status": "stub",
        "query": query_desc,
        "output": output,
        "results": {
            "gene": gene,
            "disease": disease or "all",
            "omim_associations": [],
            "disgenet_associations": [],
            "gda_score_range": "N/A",
            "output_files": [
                f"{output}/omim_associations.json",
                f"{output}/disgenet_associations.csv",
                f"{output}/summary.md",
            ],
            "note": "Requires DisGeNET API key (free registration at disgenet.org) and requests>=2.28",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OMIM + DisGeNET disease-gene associations.")
    parser.add_argument("--gene", default="BRCA1", help="Gene symbol.")
    parser.add_argument("--disease", default="", help="Disease name (optional filter).")
    parser.add_argument("--output", default="/tmp/dga_output")
    parser.add_argument("--demo", action="store_true", help="Run demo/stub mode.")
    args = parser.parse_args()

    result = main(gene=args.gene, disease=args.disease, output=args.output)
    print(json.dumps(result, indent=2))
