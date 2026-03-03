"""
gwas_catalog_overlap.py — Query EBI GWAS Catalog for published associations
near each lead SNP and synthesize a biological narrative via Biomni.

Only runs if check_significance produced has_hits = true.

Snakemake inputs:  results/03_lmm/significance_check.json
                   results/05_enrichment/go/enrichment_table.csv
Snakemake outputs: results/05_enrichment/catalog/catalog_overlap.csv
                   results/05_enrichment/catalog/biomni_narrative.md
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Snakemake injected variables
# ---------------------------------------------------------------------------
sig_json_path = snakemake.input.sig_json    # noqa: F821
enrich_path   = snakemake.input.enrich      # noqa: F821
out_csv       = snakemake.output.overlap    # noqa: F821
out_narrative = snakemake.output.narrative  # noqa: F821
window_kb     = snakemake.params.window_kb  # noqa: F821
log_path      = snakemake.log[0]            # noqa: F821

LOG = open(log_path, "w")


def log(msg: str) -> None:
    print(msg, file=LOG, flush=True)
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# EBI GWAS Catalog REST API
# ---------------------------------------------------------------------------
CATALOG_API = "https://www.ebi.ac.uk/gwas/rest/api"

OBESITY_TRAITS = {
    "body weight", "body mass index", "obesity", "adiposity",
    "fat mass", "waist circumference", "hip circumference",
    "body fat", "overweight", "metabolic syndrome",
}


def query_catalog_region(chrom: int, start: int, end: int) -> list[dict]:
    """Query GWAS Catalog for associations in a chromosomal region."""
    url = (
        f"{CATALOG_API}/singleNucleotidePolymorphisms/search/findByChromBpLocationRange"
        f"?chrom={chrom}&bpLocationMin={start}&bpLocationMax={end}&size=200"
    )
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        snps = data.get("_embedded", {}).get("singleNucleotidePolymorphisms", [])
        return snps
    except Exception as exc:
        log(f"  Catalog query failed for chr{chrom}:{start}-{end}: {exc}")
        return []


def extract_associations(snp_records: list[dict], trait_filter: bool = False) -> list[dict]:
    rows = []
    for snp in snp_records:
        rsid = snp.get("rsId", "")
        for assoc in snp.get("associations", []):
            for ef_trait in assoc.get("efoTraits", []):
                trait = ef_trait.get("trait", "").lower()
                if trait_filter and not any(t in trait for t in OBESITY_TRAITS):
                    continue
                rows.append({
                    "rsid":          rsid,
                    "trait":         ef_trait.get("trait", ""),
                    "p_value":       assoc.get("pvalue"),
                    "or_beta":       assoc.get("orPerCopyNum"),
                    "mapped_gene":   assoc.get("mappedGene", ""),
                    "pubmed_id":     assoc.get("pubmedId", ""),
                    "study_acces":   assoc.get("studyAccession", ""),
                })
    return rows


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Load lead SNPs
    # ------------------------------------------------------------------
    log(f"Loading significance_check.json: {sig_json_path}")
    with open(sig_json_path) as fh:
        sig = json.load(fh)

    if not sig.get("has_hits") or not sig.get("lead_snps"):
        log("No hits — writing empty catalog overlap")
        pd.DataFrame().to_csv(out_csv, index=False)
        Path(out_narrative).write_text("No significant GWAS hits to query.")
        LOG.close()
        return

    leads = sig["lead_snps"]
    log(f"Querying GWAS Catalog for {len(leads)} lead SNPs (±{window_kb} kb)")

    # ------------------------------------------------------------------
    # 2. Query catalog for each locus
    # ------------------------------------------------------------------
    window_bp = window_kb * 1000
    all_rows: list[dict] = []

    for snp in leads:
        chrom = snp["chr"]
        ps    = snp["ps"]
        start = max(1, ps - window_bp)
        end   = ps + window_bp
        log(f"  Querying chr{chrom}:{start}-{end} (lead: {snp.get('rsid', 'unknown')})")

        records = query_catalog_region(chrom, start, end)
        rows    = extract_associations(records, trait_filter=False)
        for row in rows:
            row["lead_rsid"] = snp.get("rsid", "")
            row["lead_chr"]  = chrom
            row["lead_ps"]   = ps
        all_rows.extend(rows)
        time.sleep(0.3)  # be polite to the API

    log(f"Total catalog associations found: {len(all_rows)}")

    # ------------------------------------------------------------------
    # 3. Filter to obesity-relevant traits
    # ------------------------------------------------------------------
    if all_rows:
        catalog_df = pd.DataFrame(all_rows)
        obesity_mask = catalog_df["trait"].str.lower().apply(
            lambda t: any(ot in t for ot in OBESITY_TRAITS)
        )
        obesity_df = catalog_df[obesity_mask]
        log(f"Obesity-relevant associations: {len(obesity_df)}")
    else:
        catalog_df = pd.DataFrame()
        obesity_df = pd.DataFrame()

    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    catalog_df.to_csv(out_csv, index=False)
    log(f"Catalog overlap table written: {out_csv}")

    # ------------------------------------------------------------------
    # 4. Biomni biological narrative
    # ------------------------------------------------------------------
    # Load GO enrichment summary for context
    try:
        go_summary = pd.read_csv(enrich_path).head(20).to_string(index=False)
    except Exception:
        go_summary = "(GO enrichment table not available)"

    catalog_summary = (
        obesity_df.head(20).to_string(index=False)
        if len(obesity_df) > 0 else "No obesity-relevant overlaps found in GWAS Catalog"
    )

    prompt = f"""You are a mouse genetics and obesity biology expert.
Interpret the following GWAS results in the context of mouse obesity biology.

## Lead SNP loci
{json.dumps(leads, indent=2)}

## Top GO/KEGG enrichment results
{go_summary}

## GWAS Catalog overlaps (obesity-relevant traits, ±{window_kb} kb)
{catalog_summary}

Please provide:
1. A biological interpretation of the enriched pathways in the context of body weight regulation
2. Assessment of whether the GWAS Catalog overlaps support known obesity biology
3. Any novel or unexpected findings
4. Recommended follow-up analyses

Be concise (300-400 words) and scientifically precise. Cite specific genes or pathways.
"""

    narrative = ""
    try:
        from biomni.agent import A1
        agent = A1()
        result = agent.run(prompt)
        narrative = str(result)
        log("Biomni narrative generated successfully")
    except ImportError:
        log("Biomni not available — falling back to Anthropic API")
        try:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            narrative = msg.content[0].text
            log("Anthropic API narrative generated")
        except Exception as exc:
            log(f"Anthropic API also failed: {exc}")
            narrative = (
                "Biological narrative unavailable (Biomni and Anthropic API both failed).\n\n"
                f"Prompt was:\n{prompt}"
            )
    except Exception as exc:
        log(f"Biomni run failed: {exc}")
        narrative = f"Biomni run failed: {exc}\n\nCatalog overlap written to {out_csv}"

    Path(out_narrative).write_text(narrative)
    log(f"Biomni narrative written: {out_narrative}")
    log("gwas_catalog_overlap complete.")
    LOG.close()


if __name__ == "__main__":
    main()
