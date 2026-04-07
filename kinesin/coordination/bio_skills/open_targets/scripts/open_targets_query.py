"""
open_targets_query.py — Open Targets Platform query skill.

Stub implementation. Full implementation uses Open Targets GraphQL API
(platform.opentargets.org/api/v4/graphql).
"""

import argparse
import json
import sys


def main(disease: str, gene: str, output: str) -> dict:
    """
    Query Open Targets Platform.

    Args:
        disease: Disease name or EFO accession (e.g. "EFO_0000270" or "Parkinson disease").
        gene:    Gene symbol (optional; narrows query to gene-disease pair).
        output:  Output directory path.

    Returns:
        Dict with status, associations, and output files.
    """
    query_desc = f"{gene} × {disease}" if gene else disease

    return {
        "status": "stub",
        "query": query_desc,
        "output": output,
        "results": {
            "disease": disease,
            "gene": gene or "all",
            "association_count": 0,
            "top_associations": [],
            "output_files": [
                f"{output}/associations.json",
                f"{output}/evidence_summary.csv",
            ],
            "note": "Requires requests>=2.28. Run against platform.opentargets.org GraphQL API.",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open Targets Platform query.")
    parser.add_argument("--disease", default="neuroblastoma", help="Disease name or EFO ID.")
    parser.add_argument("--gene", default="", help="Gene symbol (optional).")
    parser.add_argument("--output", default="/tmp/open_targets_output")
    parser.add_argument("--demo", action="store_true", help="Run demo/stub mode.")
    args = parser.parse_args()

    result = main(disease=args.disease, gene=args.gene, output=args.output)
    print(json.dumps(result, indent=2))
