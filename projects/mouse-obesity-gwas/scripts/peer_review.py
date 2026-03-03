"""
peer_review.py — Claude API scientific peer review agent.

Reads all pipeline outputs, performs a structured 4-section audit, and
produces review_report.md, issues.json, and proposed_changes.md.

If significant issues are found, proposed_changes.md is formatted as a
mini-plan for user approval before any corrections are made.

Snakemake inputs:  (see Snakefile)
Snakemake outputs: results/peer_review/review_report.md
                   results/peer_review/issues.json
                   results/peer_review/proposed_changes.md
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Snakemake injected variables
# ---------------------------------------------------------------------------
sig_json_path    = snakemake.input.sig_json        # noqa: F821
lambda_txt_path  = snakemake.input.lambda_txt      # noqa: F821
biomni_rpt_path  = snakemake.input.biomni_report   # noqa: F821
branch_files     = snakemake.input.branch_files    # noqa: F821
pheno_summary    = snakemake.input.pheno_summary   # noqa: F821
qc_summary       = snakemake.input.qc_summary      # noqa: F821

out_review   = snakemake.output.review    # noqa: F821
out_issues   = snakemake.output.issues    # noqa: F821
out_proposed = snakemake.output.proposed  # noqa: F821

model      = snakemake.params.model      # noqa: F821
max_tokens = snakemake.params.max_tokens # noqa: F821
results_dir = snakemake.params.results_dir  # noqa: F821
log_path   = snakemake.log[0]            # noqa: F821

LOG = open(log_path, "w")


def log(msg: str) -> None:
    print(msg, file=LOG, flush=True)
    print(msg, flush=True)


def safe_read(path: str, max_chars: int = 3000) -> str:
    try:
        text = Path(path).read_text()
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... [truncated at {max_chars} chars]"
        return text
    except Exception as exc:
        return f"(Could not read {path}: {exc})"


def collect_context() -> dict[str, str]:
    """Collect text from all key result files."""
    ctx = {
        "phenotype_summary":  safe_read(pheno_summary),
        "qc_summary":         safe_read(qc_summary),
        "significance_json":  safe_read(sig_json_path),
        "lambda_stats":       safe_read(lambda_txt_path),
        "biomni_qc_report":   safe_read(biomni_rpt_path),
    }

    # Branch-specific files
    for f in branch_files:
        fpath = Path(f)
        ctx[fpath.name] = safe_read(str(fpath))

    # Try to also read step summaries scattered across results/
    results_path = Path(results_dir)
    for summary_file in results_path.rglob("step_summary.txt"):
        key = str(summary_file.relative_to(results_path))
        ctx[key] = safe_read(str(summary_file))

    return ctx


REVIEW_SYSTEM_PROMPT = """You are a senior statistical geneticist and peer reviewer with
expertise in mouse genetics, GWAS methodology, mixed models (LMM/BSLMM), and functional
genomics. You are reviewing a computational GWAS pipeline output for scientific rigor."""


def build_review_prompt(ctx: dict[str, str]) -> str:
    sections = "\n\n".join(
        f"### {k}\n```\n{v}\n```" for k, v in ctx.items()
    )

    return f"""Please perform a rigorous scientific peer review of this mouse obesity GWAS pipeline.

## Pipeline Outputs

{sections}

---

## Review Structure

Please structure your review with the following four sections. For each issue found,
assign a severity: **CRITICAL** (would invalidate results), **MODERATE** (weakens
conclusions, should be addressed), or **MINOR** (cosmetic / optional improvement).

### 1. Statistical Validity
Review:
- Is λ (genomic inflation factor) in an acceptable range (ideally 0.95–1.10)?
- Was the kinship matrix (centered relatedness, -gk 1) correctly applied in the LMM?
- Is the Bonferroni threshold correctly calculated from post-QC SNP count (not original)?
- Were MAF (≥0.05), missingness (geno ≤0.05, mind ≤0.10) filters appropriate for outbred mice?
- Are QC sample sizes consistent across steps (phenotype N, QC N, LMM N)?
- Was inverse-normal transformation appropriate for body weight?

### 2. Biological Plausibility
Review:
- Are any identified GO terms biologically relevant to obesity (lipid metabolism, appetite
  regulation, insulin signaling, adipogenesis, etc.)?
- Are GWAS Catalog overlaps from appropriate trait categories?
- Is the BSLMM architecture interpretation correct given the PVE/PGE values reported?
- Are any gene names, pathways, or citations potentially hallucinated or misattributed?
- Do the top GWAS hits fall in biologically plausible genomic regions?

### 3. Scientific Nuances
Review:
- Was sex included as a covariate? (Mouse body weight is strongly sex-dimorphic — failure
  to include sex could inflate associations or miss sex-specific effects.)
- Were MCMC chains converged? (Assess from BSLMM trace plot descriptions if available.)
- Are lead SNP loci genuinely independent (1 Mb clumping applied)?
- Was the pilot subset (N=300) size sufficient for the analyses performed?
- Any concerns about population structure in CFW outbred mice?

### 4. Missed Analyses
Flag any important analyses not performed:
- Should stratified analysis by sex be recommended?
- Should conditional analysis be run at top loci (for any hits)?
- Are QQ plot diagnostics sufficient?
- Should a sensitivity analysis (e.g., excluding outlier samples) be recommended?
- Are there published CFW BW GWAS results (e.g., Nicod et al. 2016) to compare against?

---

## Output Format

After the four review sections, provide:

### Issues Summary (JSON-formatted list)
```json
[
  {{
    "section": "Statistical Validity",
    "severity": "CRITICAL|MODERATE|MINOR",
    "issue": "Brief description",
    "details": "Detailed explanation",
    "recommendation": "What should be changed"
  }}
]
```

### Proposed Changes
If there are CRITICAL or MODERATE issues, describe each proposed correction as:
- **File to modify**: scripts/X.R or scripts/X.py
- **Change description**: What needs to change and why
- **Expected impact**: What the correction will fix

If no significant issues: state "No changes recommended — pipeline is statistically sound."
"""


def parse_issues_from_review(review_text: str) -> list[dict]:
    """Extract the JSON issues block from the review text."""
    import re
    # Look for a JSON array in a code block
    pattern = r"```json\s*(\[.*?\])\s*```"
    match = re.search(pattern, review_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            log(f"Could not parse issues JSON: {exc}")
    return []


def extract_proposed_changes(review_text: str) -> str:
    """Extract the Proposed Changes section."""
    marker = "### Proposed Changes"
    idx = review_text.find(marker)
    if idx >= 0:
        return review_text[idx:].strip()
    return "No proposed changes section found in review."


def format_proposed_changes_as_plan(changes_text: str, issues: list[dict]) -> str:
    """
    Wrap proposed changes as a mini-plan file for user approval.
    If no issues, clearly state that.
    """
    critical = [i for i in issues if i.get("severity") == "CRITICAL"]
    moderate = [i for i in issues if i.get("severity") == "MODERATE"]

    if not critical and not moderate:
        return (
            "# Peer Review: No Changes Recommended\n\n"
            "The pipeline passed all critical and moderate checks.\n\n"
            "Minor suggestions (if any) are documented in `review_report.md`.\n"
            "No script or result file modifications are required.\n"
        )

    lines = [
        "# Peer Review: Proposed Corrections",
        "",
        "> **IMPORTANT**: This file was auto-generated by the peer review agent.",
        "> Review it carefully and approve changes before implementation.",
        "> To implement: tell Claude Code to 'implement proposed_changes.md'.",
        "",
        f"## Summary: {len(critical)} critical, {len(moderate)} moderate issues",
        "",
        "## Issues Requiring Fixes",
        "",
    ]

    for i, issue in enumerate(critical + moderate, 1):
        lines += [
            f"### Issue {i}: [{issue.get('severity', 'UNKNOWN')}] {issue.get('issue', '')}",
            "",
            f"**Section**: {issue.get('section', '')}",
            f"**Details**: {issue.get('details', '')}",
            f"**Recommendation**: {issue.get('recommendation', '')}",
            "",
        ]

    lines += [
        "## Proposed Code / Config Changes",
        "",
        changes_text,
        "",
        "## Approval",
        "",
        "To approve and implement these changes, respond with:",
        "> 'Implement the proposed changes from proposed_changes.md'",
        "",
        "To reject, respond with:",
        "> 'Reject proposed changes — keep current pipeline'",
    ]

    return "\n".join(lines)


def main() -> None:
    log("Starting peer review agent")

    # ------------------------------------------------------------------
    # 1. Collect context
    # ------------------------------------------------------------------
    ctx = collect_context()
    log(f"Context collected: {len(ctx)} files/sections")
    for k in ctx:
        log(f"  {k}: {len(ctx[k])} chars")

    # ------------------------------------------------------------------
    # 2. Run Claude peer review
    # ------------------------------------------------------------------
    prompt = build_review_prompt(ctx)

    review_text = ""
    try:
        import anthropic
        log(f"Calling {model} for peer review (max_tokens={max_tokens})")
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=REVIEW_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        review_text = msg.content[0].text
        log(f"Peer review generated: {len(review_text)} chars")
    except Exception as exc:
        log(f"ERROR calling Claude API: {exc}")
        review_text = (
            f"# Peer Review Error\n\n"
            f"Claude API call failed: {exc}\n\n"
            "Please run the peer review manually using the prompt in logs/peer_review.log.\n"
        )

    # ------------------------------------------------------------------
    # 3. Parse issues and proposed changes
    # ------------------------------------------------------------------
    issues  = parse_issues_from_review(review_text)
    changes = extract_proposed_changes(review_text)
    plan_md = format_proposed_changes_as_plan(changes, issues)

    log(f"Issues parsed: {len(issues)}")
    critical_n = sum(1 for i in issues if i.get("severity") == "CRITICAL")
    moderate_n = sum(1 for i in issues if i.get("severity") == "MODERATE")
    minor_n    = sum(1 for i in issues if i.get("severity") == "MINOR")
    log(f"  Critical: {critical_n}, Moderate: {moderate_n}, Minor: {minor_n}")

    # ------------------------------------------------------------------
    # 4. Write outputs
    # ------------------------------------------------------------------
    Path(out_review).parent.mkdir(parents=True, exist_ok=True)

    header = (
        "# Scientific Peer Review — CFW Mouse Body Weight GWAS\n\n"
        f"**Model**: {model}  \n"
        f"**Critical issues**: {critical_n}  \n"
        f"**Moderate issues**: {moderate_n}  \n"
        f"**Minor issues**: {minor_n}  \n\n"
        "---\n\n"
    )

    Path(out_review).write_text(header + review_text)
    log(f"Review report written: {out_review}")

    with open(out_issues, "w") as fh:
        json.dump(issues, fh, indent=2)
    log(f"Issues JSON written: {out_issues}")

    Path(out_proposed).write_text(plan_md)
    log(f"Proposed changes written: {out_proposed}")

    if critical_n > 0:
        log(f"ACTION REQUIRED: {critical_n} critical issue(s) found. Review {out_proposed}")
    elif moderate_n > 0:
        log(f"REVIEW RECOMMENDED: {moderate_n} moderate issue(s) found. Review {out_proposed}")
    else:
        log("Peer review passed: no critical or moderate issues.")

    log("peer_review complete.")
    LOG.close()


if __name__ == "__main__":
    main()
