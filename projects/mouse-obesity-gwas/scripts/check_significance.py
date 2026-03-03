"""
check_significance.py — Checkpoint script that determines whether LMM
results contain Bonferroni-significant hits, and writes a JSON branch file.

Snakemake inputs:  results/03_lmm/output/cfw_qc.assoc.txt
                   results/02_qc/cfw_qc.bim
Snakemake outputs: results/03_lmm/significance_check.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Snakemake injected variables
# ---------------------------------------------------------------------------
assoc_file  = snakemake.input.assoc    # noqa: F821
bim_file    = snakemake.input.bim      # noqa: F821
out_json    = snakemake.output.json    # noqa: F821
bonf_alpha  = snakemake.params.bonf_alpha   # noqa: F821
sugg_alpha  = snakemake.params.sugg_alpha   # noqa: F821
log_path    = snakemake.log[0]         # noqa: F821

LOG = open(log_path, "w")


def log(msg: str) -> None:
    print(msg, file=LOG, flush=True)
    print(msg, flush=True)


def clump_lead_snps(df: pd.DataFrame, window_bp: int = 1_000_000) -> list[dict]:
    """
    Simple greedy clumping: sort by p_wald, iterate; any subsequent SNP within
    window_bp of an already-chosen lead SNP is skipped.
    Returns list of lead SNP dicts.
    """
    df_sorted = df.sort_values("p_wald").copy()
    leads: list[dict] = []
    claimed: set[int] = set()

    for _, row in df_sorted.iterrows():
        idx = row.name
        if idx in claimed:
            continue
        leads.append({
            "rsid":   str(row.get("rs", row.get("SNP", row.get("snps", idx)))),
            "chr":    int(row["chr"]),
            "ps":     int(row["ps"]),
            "p_wald": float(row["p_wald"]),
        })
        # Mark all SNPs on the same chromosome within window as claimed
        same_chr = df_sorted[df_sorted["chr"] == row["chr"]].index
        for j in same_chr:
            if abs(df_sorted.loc[j, "ps"] - row["ps"]) <= window_bp:
                claimed.add(j)

    return leads


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load GEMMA association output
    # ------------------------------------------------------------------
    log(f"Loading GEMMA output: {assoc_file}")
    try:
        assoc = pd.read_csv(assoc_file, sep="\t")
    except Exception as exc:
        log(f"ERROR reading assoc file: {exc}")
        # Write fallback JSON so pipeline doesn't hang
        result = {
            "has_hits": False,
            "n_bonferroni": 0,
            "n_suggestive": 0,
            "threshold_bonferroni": None,
            "threshold_suggestive": None,
            "lead_snps": [],
            "error": str(exc),
        }
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w") as fh:
            json.dump(result, fh, indent=2)
        LOG.close()
        return

    log(f"Loaded {len(assoc)} SNPs from assoc file")
    log(f"Columns: {list(assoc.columns)}")

    # Normalise column names (GEMMA uses lowercase)
    assoc.columns = [c.lower() for c in assoc.columns]
    required = {"chr", "ps", "p_wald"}
    if not required.issubset(set(assoc.columns)):
        log(f"WARNING: expected columns {required}, found {set(assoc.columns)}")

    # Remove rows with missing p-values
    assoc = assoc.dropna(subset=["p_wald"])
    assoc = assoc[assoc["p_wald"] > 0]

    # ------------------------------------------------------------------
    # 2. Compute thresholds from post-QC SNP count (use bim file)
    # ------------------------------------------------------------------
    log(f"Loading BIM file to count post-QC SNPs: {bim_file}")
    try:
        bim = pd.read_csv(bim_file, sep="\t", header=None,
                          names=["chr", "snp", "cm", "bp", "a1", "a2"])
        n_snps = len(bim)
    except Exception as exc:
        log(f"WARNING: could not read BIM ({exc}), using assoc row count")
        n_snps = len(assoc)

    log(f"Post-QC SNP count: {n_snps}")

    thresh_bonf = bonf_alpha / n_snps
    thresh_sugg = sugg_alpha / n_snps
    log(f"Bonferroni threshold : {thresh_bonf:.3e}")
    log(f"Suggestive threshold : {thresh_sugg:.3e}")

    # ------------------------------------------------------------------
    # 3. Count hits
    # ------------------------------------------------------------------
    hits_bonf = assoc[assoc["p_wald"] <= thresh_bonf]
    hits_sugg = assoc[assoc["p_wald"] <= thresh_sugg]

    n_bonf = len(hits_bonf)
    n_sugg = len(hits_sugg)
    log(f"Bonferroni hits: {n_bonf}")
    log(f"Suggestive hits: {n_sugg}")

    # ------------------------------------------------------------------
    # 4. Extract lead SNPs (clump at 1 Mb)
    # ------------------------------------------------------------------
    if n_bonf > 0:
        lead_snps = clump_lead_snps(hits_bonf, window_bp=1_000_000)
        log(f"Lead SNPs after 1 Mb clumping: {len(lead_snps)}")
    elif n_sugg > 0:
        lead_snps = clump_lead_snps(hits_sugg, window_bp=1_000_000)
        log(f"Lead suggestive SNPs after clumping: {len(lead_snps)}")
    else:
        lead_snps = []

    # ------------------------------------------------------------------
    # 5. Write JSON
    # ------------------------------------------------------------------
    result = {
        "has_hits":            n_bonf > 0,
        "n_bonferroni":        n_bonf,
        "n_suggestive":        n_sugg,
        "n_snps_post_qc":      n_snps,
        "threshold_bonferroni": thresh_bonf,
        "threshold_suggestive": thresh_sugg,
        "lead_snps":           lead_snps,
    }

    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as fh:
        json.dump(result, fh, indent=2)

    log(f"significance_check.json written → has_hits = {result['has_hits']}")
    log("check_significance complete.")
    LOG.close()


if __name__ == "__main__":
    main()
