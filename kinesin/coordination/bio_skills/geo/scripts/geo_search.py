"""
geo_search.py — NCBI GEO search and download skill.

Stub implementation. Returns placeholder results for ScienceClaw skill discovery.
Full implementation uses GEOparse + NCBI E-utilities.
"""

import argparse
import json
import sys


def main(query: str = "", accession: str = "", output: str = "/tmp/geo_output") -> dict:
    """
    Search GEO or download a specific series.

    Args:
        query:     Keyword search string.
        accession: GEO series accession (e.g. GSE12345). Takes priority over query.
        output:    Output directory path.

    Returns:
        Dict with status, results list, and output path.
    """
    if accession:
        return {
            "status": "stub",
            "accession": accession,
            "output": output,
            "results": [
                {
                    "accession": accession,
                    "title": f"Stub series for {accession}",
                    "organism": "Homo sapiens",
                    "samples": 0,
                    "note": "Install GEOparse and run with real accession",
                }
            ],
        }

    return {
        "status": "stub",
        "query": query,
        "output": output,
        "results": [
            {
                "accession": "GSE000001",
                "title": f"Stub result for: {query}",
                "organism": "Homo sapiens",
                "samples": 0,
                "note": "Install GEOparse for real GEO search results",
            }
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NCBI GEO search and download.")
    parser.add_argument("--query", default="", help="Keyword search string.")
    parser.add_argument("--accession", default="", help="GEO series accession (e.g. GSE12345).")
    parser.add_argument("--output", default="/tmp/geo_output", help="Output directory.")
    parser.add_argument("--demo", action="store_true", help="Run demo/stub mode.")
    args = parser.parse_args()

    result = main(query=args.query, accession=args.accession, output=args.output)
    print(json.dumps(result, indent=2))
