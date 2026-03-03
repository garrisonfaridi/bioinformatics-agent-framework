"""
biomni_qc.py — Biological QC using Biomni (or Claude API fallback).

Validates:
  1. CFW mouse body weight distribution vs. MPD strain means
  2. Biological plausibility of the phenotype range
  3. Literature context for CFW body weight GWAS

Snakemake inputs:  results/01_phenotype/step_summary.txt
                   results/03_lmm/output/cfw_qc.assoc.txt
Snakemake outputs: results/07_biomni_qc/biomni_qc_report.md
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Snakemake injected variables
# ---------------------------------------------------------------------------
pheno_summary_path = snakemake.input.pheno_summary   # noqa: F821
assoc_path         = snakemake.input.assoc           # noqa: F821
out_report         = snakemake.output.report         # noqa: F821
log_path           = snakemake.log[0]                # noqa: F821

LOG = open(log_path, "w")


def log(msg: str) -> None:
    print(msg, file=LOG, flush=True)
    print(msg, flush=True)


def read_pheno_summary(path: str) -> str:
    try:
        return Path(path).read_text()
    except Exception as exc:
        return f"(Could not read phenotype summary: {exc})"


def get_top_hits(assoc_path: str, n: int = 10) -> str:
    """Return top N hits from the association file as a formatted string."""
    try:
        import pandas as pd
        assoc = pd.read_csv(assoc_path, sep="\t")
        assoc.columns = [c.lower() for c in assoc.columns]
        if "p_wald" in assoc.columns:
            top = assoc.nsmallest(n, "p_wald")[
                ["chr", "rs", "ps", "af", "beta", "se", "p_wald"]
            ].to_string(index=False)
        else:
            top = assoc.head(n).to_string(index=False)
        return top
    except Exception as exc:
        return f"(Could not read association results: {exc})"


def build_prompt(pheno_summary: str, top_hits: str) -> str:
    return f"""You are an expert in mouse genetics and phenotyping, with deep knowledge of
the Collaborative Cross (CC), CFW (Crl:CFW(SW)-US_P08) outbred mice, and the Mouse
Phenome Database (MPD).

Please perform a biological quality control review of the following mouse obesity GWAS:

## Phenotype Summary (inverse-normal transformed body weight)
{pheno_summary}

## Top 10 GWAS Hits (by Wald p-value)
{top_hits}

### Your QC tasks:

1. **Plausibility check**: CFW outbred mice typically have body weights of 25–45 g (males
   heavier than females). Based on the phenotype summary, is the body weight distribution
   biologically plausible? Flag any values that seem anomalous.

2. **MPD comparison**: The Mouse Phenome Database (MPD) has published body weight means
   for many inbred and outbred strains. Do the statistics in this summary align with what
   is known for CFW outbred mice from Jackson Labs / Charles River? Cite specific MPD
   records if relevant.

3. **Literature context**: What published GWAS or QTL mapping studies have been performed
   in CFW mice for body weight? Key reference: Nicod et al. 2016 (Nat Genet) used 1,900
   CFW mice for GWAS. Are any of the top hits consistent with loci reported in that study
   or other CFW body weight studies?

4. **Known loci validation**: Known mouse body weight QTL/GWAS regions include loci near:
   Lepr (chr4), Mc4r (chr18), Fto (chr8), Pomc (chr12). Do any of the top hits fall in
   or near these regions?

5. **Critical flags**: List any biological red flags — e.g., implausible p-value
   distribution, hits on sex chromosomes (check for correct X/Y handling), unexpected
   chromosomal clustering suggesting technical artifact.

6. **Recommendations**: What additional biological QC steps or analyses would you recommend
   before submitting these results for peer review?

Format your response as a structured Markdown report with numbered sections matching the
tasks above. Be scientifically rigorous and clearly distinguish confirmed facts from
inferences.
"""


def main() -> None:
    log("Starting Biomni biological QC")

    pheno_summary = read_pheno_summary(pheno_summary_path)
    top_hits      = get_top_hits(assoc_path)

    log("Phenotype summary loaded")
    log(f"Top hits preview:\n{top_hits[:200]}")

    prompt = build_prompt(pheno_summary, top_hits)

    # ------------------------------------------------------------------
    # Run Biomni (preferred) or Claude API (fallback)
    # ------------------------------------------------------------------
    report_text = ""

    try:
        from biomni.agent import A1
        log("Attempting Biomni A1 agent")
        agent = A1()
        result = agent.run(prompt)
        report_text = str(result).strip()
        if not report_text:
            raise ValueError("Biomni returned empty result")
        log("Biomni QC report generated")
    except BaseException as exc:
        # Catch BaseException (not just Exception) to handle SystemExit /
        # KeyboardInterrupt that Biomni's internal runner may raise on failure
        log(f"Biomni not available or failed ({type(exc).__name__}: {exc}) — falling back to Anthropic API")
        report_text = ""

    if not report_text:
        try:
            import anthropic
            log("Using Anthropic claude-sonnet-4-6 for biological QC")
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            report_text = msg.content[0].text
            log("Anthropic API QC report generated")
        except Exception as exc:
            log(f"Anthropic API failed: {exc}")
            report_text = (
                "# Biomni QC Report\n\n"
                "**ERROR**: Both Biomni and Anthropic API calls failed.\n\n"
                f"Error details: {exc}\n\n"
                "## Phenotype Summary\n"
                f"```\n{pheno_summary}\n```\n\n"
                "## Top GWAS Hits\n"
                f"```\n{top_hits}\n```\n\n"
                "Please run manual biological QC using the data above."
            )

    # ------------------------------------------------------------------
    # Write report
    # ------------------------------------------------------------------
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text(
        "# Biomni Biological QC Report — CFW Mouse Body Weight GWAS\n\n"
        + report_text
    )
    log(f"Biomni QC report written: {out_report}")
    log("biomni_qc complete.")
    LOG.close()


if __name__ == "__main__":
    main()
