"""
Peer review round differ.

Compares two issues.json files (from consecutive peer review rounds) and
produces a structured diff: what was resolved, what persisted, what regressed,
and what is new. Also emits a quality score.

Usage
-----
    python scripts/review_diff.py \
        --round1 results/peer_review/round1/issues.json \
        --round2 results/peer_review/round2/issues.json \
        --output results/peer_review/review_diff_R1_R2.md

Schema expected in issues.json
-------------------------------
{
  "review_round": 1,
  "run_id": "...",
  "issues": [
    {
      "id": "R1-001",
      "severity": "critical|major|minor|note",
      "category": "statistical|biological|computational|reproducibility",
      "description": "...",
      "location": "...",
      "proposed_fix": "...",
      "status": "open|resolved"
    }
  ]
}
"""

import argparse
import json
import sys
from pathlib import Path
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

def _sig(issue: dict) -> str:
    """Canonical signature for fuzzy matching (category + description stub)."""
    cat = issue.get("category", "")
    desc = (issue.get("description") or "")[:120].lower()
    return f"{cat}::{desc}"


def _similar(a: dict, b: dict, threshold: float = 0.65) -> bool:
    """Return True if two issues are likely the same underlying problem."""
    ratio = SequenceMatcher(None, _sig(a), _sig(b)).ratio()
    return ratio >= threshold


# Module-level threshold — overridden by CLI arg before diff_rounds is called
_similarity_threshold: float = 0.65


# ---------------------------------------------------------------------------
# Diff logic
# ---------------------------------------------------------------------------

def diff_rounds(issues_r1: list[dict], issues_r2: list[dict]) -> dict:
    """
    Classify R1 issues relative to R2.

    Returns
    -------
    dict with keys: resolved, persisted, regressed, new_issues, score
    """
    resolved: list[dict] = []
    persisted: list[dict] = []

    r2_matched: set[int] = set()

    for r1_issue in issues_r1:
        matched_idx = None
        for i, r2_issue in enumerate(issues_r2):
            if i in r2_matched:
                continue
            if _similar(r1_issue, r2_issue, threshold=_similarity_threshold):
                matched_idx = i
                break
        if matched_idx is not None:
            persisted.append({
                "r1": r1_issue,
                "r2": issues_r2[matched_idx],
            })
            r2_matched.add(matched_idx)
        else:
            resolved.append(r1_issue)

    new_issues = [issues_r2[i] for i in range(len(issues_r2)) if i not in r2_matched]

    # Regressed: new issues in R2 whose category matches something that was "fixed" in R1
    resolved_categories = {r.get("category", "") for r in resolved}
    regressed = [n for n in new_issues if n.get("category", "") in resolved_categories]
    regressed_ids = {r.get("id") for r in regressed}
    truly_new = [n for n in new_issues if n.get("id") not in regressed_ids]

    total_r1 = len(issues_r1)
    score = round(len(resolved) / total_r1, 3) if total_r1 > 0 else 1.0

    return {
        "resolved": resolved,
        "persisted": persisted,
        "regressed": regressed,
        "new_issues": truly_new,
        "score": score,
        "total_r1": total_r1,
    }


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _sev_badge(issue: dict) -> str:
    sev = issue.get("severity", "note").upper()
    return f"[{sev}]"


def format_issue(issue: dict, indent: str = "  ") -> str:
    lines = [
        f"{indent}{_sev_badge(issue)} {issue.get('id', '?')} — {issue.get('description', '')}",
        f"{indent}  category: {issue.get('category', '?')}",
    ]
    if issue.get("location"):
        lines.append(f"{indent}  location: {issue['location']}")
    if issue.get("proposed_fix"):
        lines.append(f"{indent}  fix: {issue['proposed_fix']}")
    return "\n".join(lines)


def build_report(diff: dict, r1_meta: dict, r2_meta: dict) -> str:
    lines: list[str] = []

    lines += [
        f"# Peer Review Diff: Round {r1_meta.get('review_round', '?')} → "
        f"Round {r2_meta.get('review_round', '?')}",
        "",
        f"Run ID (R1): `{r1_meta.get('run_id', '?')}`",
        f"Run ID (R2): `{r2_meta.get('run_id', '?')}`",
        "",
        f"**Quality score:** {diff['score']:.1%}  "
        f"({len(diff['resolved'])}/{diff['total_r1']} R1 issues resolved)",
        "",
    ]

    # RESOLVED
    lines.append(f"## RESOLVED ({len(diff['resolved'])})")
    if diff["resolved"]:
        for issue in diff["resolved"]:
            lines.append(format_issue(issue))
            lines.append("")
    else:
        lines += ["  *(none)*", ""]

    # PERSISTED
    lines.append(f"## PERSISTED ({len(diff['persisted'])})")
    if diff["persisted"]:
        for pair in diff["persisted"]:
            lines.append(f"  {_sev_badge(pair['r1'])} {pair['r1'].get('id')} persists as "
                         f"{pair['r2'].get('id', '?')}:")
            lines.append(f"    R1: {pair['r1'].get('description', '')}")
            lines.append(f"    R2: {pair['r2'].get('description', '')}")
            lines.append("")
    else:
        lines += ["  *(none)*", ""]

    # REGRESSED
    lines.append(f"## REGRESSED ({len(diff['regressed'])})")
    lines.append("  *New issues in the same category as a resolved R1 issue — "
                 "the fix may have introduced a new problem.*")
    if diff["regressed"]:
        for issue in diff["regressed"]:
            lines.append(format_issue(issue))
            lines.append("")
    else:
        lines += ["  *(none)*", ""]

    # NEW
    lines.append(f"## NEW ({len(diff['new_issues'])})")
    lines.append("  *Issues in R2 not related to any R1 fix.*")
    if diff["new_issues"]:
        for issue in diff["new_issues"]:
            lines.append(format_issue(issue))
            lines.append("")
    else:
        lines += ["  *(none)*", ""]

    # Action summary
    # Flatten all open issues: persisted uses {"r1":..,"r2":..} pairs, others are plain dicts
    open_issues: list[dict] = []
    for p in diff["persisted"]:
        open_issues.append(p["r2"])
    open_issues.extend(diff["regressed"])
    open_issues.extend(diff["new_issues"])
    critical_open = [i for i in open_issues if i.get("severity") == "critical"]
    if critical_open:
        lines += [
            "---",
            f"**{len(critical_open)} CRITICAL issue(s) still open — address before re-running.**",
        ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_issues_json(path: Path) -> tuple[dict, list[dict]]:
    with path.open() as fh:
        data = json.load(fh)
    return data, data.get("issues", [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff two peer review rounds")
    parser.add_argument("--round1", required=True,
                        help="Path to round 1 issues.json")
    parser.add_argument("--round2", required=True,
                        help="Path to round 2 issues.json")
    parser.add_argument("--output", required=True,
                        help="Output markdown diff file")
    parser.add_argument("--similarity-threshold", type=float, default=0.65,
                        help="Fuzzy match threshold for issue identity (default: 0.65)")
    args = parser.parse_args()

    global _similarity_threshold
    _similarity_threshold = args.similarity_threshold

    r1_path, r2_path = Path(args.round1), Path(args.round2)
    for p in (r1_path, r2_path):
        if not p.exists():
            print(f"ERROR: not found: {p}", file=sys.stderr)
            sys.exit(1)

    r1_meta, issues_r1 = load_issues_json(r1_path)
    r2_meta, issues_r2 = load_issues_json(r2_path)

    diff = diff_rounds(issues_r1, issues_r2)
    report = build_report(diff, r1_meta, r2_meta)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)

    print(report)
    print(f"[review_diff] Wrote {out_path}")
    print(f"  Score: {diff['score']:.1%} ({len(diff['resolved'])}/{diff['total_r1']} resolved)")
    if diff["regressed"]:
        print(f"  WARNING: {len(diff['regressed'])} regressed issue(s) detected")


if __name__ == "__main__":
    main()
