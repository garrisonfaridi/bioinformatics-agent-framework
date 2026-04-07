"""
reactome_query.py — Reactome pathway enrichment skill using gseapy.

Stub implementation. Full implementation uses gseapy.enrichr() with Reactome_2022 gene sets.
"""

import argparse
import json
import sys


def main(gene_list: str, organism: str, output: str) -> dict:
    """
    Run Reactome pathway enrichment.

    Args:
        gene_list: Comma-separated gene symbols or path to .txt file (one gene per line).
        organism:  Organism name (human, mouse, rat).
        output:    Output directory path.

    Returns:
        Dict with status, enriched pathways, and output files.
    """
    # Parse gene list
    if gene_list.endswith(".txt"):
        try:
            with open(gene_list) as f:
                genes = [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            genes = []
    else:
        genes = [g.strip() for g in gene_list.split(",") if g.strip()]

    return {
        "status": "stub",
        "organism": organism,
        "gene_count": len(genes),
        "output": output,
        "results": {
            "significant_pathways": 0,
            "top_pathway": "N/A (stub mode)",
            "output_files": [
                f"{output}/reactome_enrichment.csv",
                f"{output}/dot_plot.png",
            ],
            "note": "Requires gseapy>=1.1.3. Install: pip install gseapy",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reactome pathway enrichment via gseapy.")
    parser.add_argument("--gene-list", default="BRCA1,TP53", help="Genes (comma-sep or .txt file).")
    parser.add_argument("--organism", default="human", help="Organism (human, mouse, rat).")
    parser.add_argument("--output", default="/tmp/reactome_output")
    parser.add_argument("--demo", action="store_true", help="Run demo/stub mode.")
    args = parser.parse_args()

    result = main(gene_list=args.gene_list, organism=args.organism, output=args.output)
    print(json.dumps(result, indent=2))
