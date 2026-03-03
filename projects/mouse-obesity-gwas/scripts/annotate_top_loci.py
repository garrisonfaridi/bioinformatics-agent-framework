"""
annotate_top_loci.py — Annotate lead SNPs from significance_check.json
with nearby genes using the Ensembl REST API (GRCm38/mm10).

Queries a ±500 kb window around each lead SNP for protein-coding and
lincRNA genes, then writes a TSV and a markdown summary.

Snakemake inputs:  results/03_lmm/significance_check.json
Snakemake outputs: results/08_annotation/top_loci_genes.tsv
                   results/08_annotation/annotation_summary.md
"""

import json
import sys
import time
from pathlib import Path

import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Snakemake injected variables
# ---------------------------------------------------------------------------
sig_json_path = snakemake.input.sig_json   # noqa: F821
out_tsv       = snakemake.output.tsv       # noqa: F821
out_md        = snakemake.output.md        # noqa: F821
log_path      = snakemake.log[0]           # noqa: F821
window_bp     = snakemake.params.window_bp # noqa: F821

LOG = open(log_path, "w")


def log(msg: str) -> None:
    print(msg, file=LOG, flush=True)
    print(msg, flush=True)


ENSEMBL_REST = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json"}

# Map PLINK chromosome integers to Ensembl chromosome names for mouse
CHR_MAP = {str(i): str(i) for i in range(1, 20)}
CHR_MAP.update({"X": "X", "Y": "Y", "MT": "MT"})


def query_ensembl_region(chrom: str, start: int, end: int,
                         retries: int = 3) -> list[dict]:
    """
    Query Ensembl REST /overlap/region/mus_musculus for genes in a window.
    Returns list of gene dicts (empty on failure).
    """
    ens_chrom = CHR_MAP.get(str(chrom), str(chrom))
    url = (f"{ENSEMBL_REST}/overlap/region/mus_musculus/"
           f"{ens_chrom}:{start}-{end}"
           f"?feature=gene;biotype=protein_coding;biotype=lincRNA")
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 10))
                log(f"  Rate-limited; sleeping {wait}s")
                time.sleep(wait)
            else:
                log(f"  WARNING: Ensembl returned {resp.status_code} for {url}")
                return []
        except requests.RequestException as exc:
            log(f"  WARNING: request failed (attempt {attempt + 1}): {exc}")
            time.sleep(5)
    return []


def main() -> None:
    log("Starting top-loci gene annotation")

    # ------------------------------------------------------------------
    # Load lead SNPs
    # ------------------------------------------------------------------
    with open(sig_json_path) as fh:
        sig = json.load(fh)

    lead_snps = sig.get("lead_snps", [])
    if not lead_snps:
        log("No lead SNPs found in significance_check.json — writing empty outputs")
        Path(out_tsv).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["snp", "chr", "ps", "p_wald",
                               "gene_name", "gene_id", "biotype",
                               "gene_start", "gene_end", "distance_bp"]
                     ).to_csv(out_tsv, sep="\t", index=False)
        Path(out_md).write_text("# Top Loci Gene Annotation\n\nNo lead SNPs to annotate.\n")
        LOG.close()
        return

    log(f"Annotating {len(lead_snps)} lead SNP(s) with ±{window_bp:,} bp window")

    # ------------------------------------------------------------------
    # Query Ensembl for each lead SNP
    # ------------------------------------------------------------------
    rows = []
    for snp in lead_snps:
        chrom = snp["chr"]
        pos   = snp["ps"]
        start = max(1, pos - window_bp)
        end   = pos + window_bp

        log(f"  Querying Chr{chrom}:{start:,}–{end:,} for {snp['rsid']}")
        genes = query_ensembl_region(chrom, start, end)
        time.sleep(0.35)  # Ensembl REST rate limit: ~3 req/s

        if not genes:
            log(f"  No genes found in window for {snp['rsid']}")
            rows.append({
                "snp": snp["rsid"], "chr": chrom, "ps": pos,
                "p_wald": snp["p_wald"],
                "gene_name": "NONE", "gene_id": "NONE",
                "biotype": "NONE",
                "gene_start": None, "gene_end": None, "distance_bp": None,
            })
            continue

        for g in genes:
            gene_mid = (g["start"] + g["end"]) // 2
            dist = abs(pos - gene_mid)
            rows.append({
                "snp":        snp["rsid"],
                "chr":        chrom,
                "ps":         pos,
                "p_wald":     snp["p_wald"],
                "gene_name":  g.get("external_name", g.get("id", "unknown")),
                "gene_id":    g.get("id", "unknown"),
                "biotype":    g.get("biotype", "unknown"),
                "gene_start": g["start"],
                "gene_end":   g["end"],
                "distance_bp": dist,
            })
        log(f"  Found {len(genes)} genes near {snp['rsid']}")

    # ------------------------------------------------------------------
    # Write TSV
    # ------------------------------------------------------------------
    Path(out_tsv).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df = df.sort_values(["snp", "distance_bp"])
    df.to_csv(out_tsv, sep="\t", index=False)
    log(f"Annotation TSV written: {out_tsv}")

    # ------------------------------------------------------------------
    # Write Markdown summary
    # ------------------------------------------------------------------
    lines = [
        "# Top Loci Gene Annotation (mm10 / GRCm38)",
        "",
        f"Window: ±{window_bp:,} bp around each lead SNP  ",
        f"Gene biotypes queried: protein_coding, lincRNA  ",
        f"Source: Ensembl REST API (mus_musculus)",
        "",
    ]
    for snp in lead_snps:
        snp_df = df[df["snp"] == snp["rsid"]].copy()
        lines += [
            f"## {snp['rsid']} — Chr{snp['chr']}:{snp['ps']:,} (p = {snp['p_wald']:.2e})",
            "",
        ]
        if snp_df.empty or snp_df["gene_name"].eq("NONE").all():
            lines.append("No protein-coding or lincRNA genes found in window.\n")
        else:
            lines.append("| Gene | Ensembl ID | Biotype | Start | End | Distance (bp) |")
            lines.append("|------|-----------|---------|-------|-----|--------------|")
            for _, row in snp_df.iterrows():
                if row["gene_name"] == "NONE":
                    continue
                lines.append(
                    f"| {row['gene_name']} | {row['gene_id']} | {row['biotype']} "
                    f"| {int(row['gene_start']):,} | {int(row['gene_end']):,} "
                    f"| {int(row['distance_bp']):,} |"
                )
            lines.append("")

        # Known obesity loci cross-reference
        chrom = snp["chr"]
        pos   = snp["ps"]
        known = []
        if chrom == 4  and 132_000_000 <= pos <= 133_000_000: known.append("Lepr (chr4:132 Mb)")
        if chrom == 18 and  66_000_000 <= pos <=  67_500_000: known.append("Mc4r (chr18:66 Mb)")
        if chrom == 8  and 108_000_000 <= pos <= 109_000_000: known.append("Fto (chr8:108 Mb)")
        if chrom == 12 and   3_000_000 <= pos <=   4_000_000: known.append("Pomc (chr12:3 Mb)")
        if known:
            lines.append(f"**Known obesity locus proximity**: {', '.join(known)}")
        else:
            lines.append("**Known obesity locus proximity**: None of Lepr/Mc4r/Fto/Pomc")
        lines.append("")

    Path(out_md).write_text("\n".join(lines))
    log(f"Annotation markdown written: {out_md}")
    log("annotate_top_loci complete.")
    LOG.close()


if __name__ == "__main__":
    main()
