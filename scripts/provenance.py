"""
Provenance chain tracker.

Writes and queries a machine-readable manifest linking agent decisions
to their evidence sources and generated artifacts. Stored alongside
reasoning_traces as provenance.json.

Subcommands
-----------
link    Register a decision → evidence → artifact chain
trace   Show what decisions led to an artifact
report  Generate a full provenance Markdown report for the run

Usage
-----
    python scripts/provenance.py link \\
        --run-id 20250101_120000_gwas \\
        --project-dir projects/mouse-obesity-gwas \\
        --decision-id DEC-001 \\
        --decision "Use GEMMA LMM with kinship matrix" \\
        --evidence-type biomni_query \\
        --evidence-ref BIOMNI-001 \\
        --output-artifact pipeline/gemma_run.sh

    python scripts/provenance.py trace \\
        --run-id 20250101_120000_gwas \\
        --project-dir projects/mouse-obesity-gwas \\
        --artifact results/gwas/gemma_output.assoc.txt

    python scripts/provenance.py report \\
        --run-id 20250101_120000_gwas \\
        --project-dir projects/mouse-obesity-gwas \\
        --output results/provenance_report.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _prov_path(project_dir: str, run_id: str) -> Path:
    d = Path(project_dir) / "reasoning_traces" / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "provenance.json"


def _load(project_dir: str, run_id: str) -> dict:
    path = _prov_path(project_dir, run_id)
    if not path.exists():
        return {"run_id": run_id, "decisions": [], "artifact_index": {}}
    with path.open() as fh:
        return json.load(fh)


def _save(data: dict, project_dir: str, run_id: str) -> None:
    path = _prov_path(project_dir, run_id)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_link(args: argparse.Namespace) -> None:
    data = _load(args.project_dir, args.run_id)

    record = {
        "decision_id": args.decision_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": args.decision,
        "evidence_type": args.evidence_type,
        "evidence_ref": args.evidence_ref,
        "output_artifact": args.output_artifact,
        "notes": args.notes or "",
    }

    data["decisions"].append(record)

    # Update artifact index for fast trace lookup
    artifact = args.output_artifact
    if artifact not in data["artifact_index"]:
        data["artifact_index"][artifact] = []
    data["artifact_index"][artifact].append(args.decision_id)

    _save(data, args.project_dir, args.run_id)
    print(f"[provenance] Linked {args.decision_id} → {artifact}")


def cmd_trace(args: argparse.Namespace) -> None:
    data = _load(args.project_dir, args.run_id)
    artifact = args.artifact

    decision_ids = data["artifact_index"].get(artifact, [])
    if not decision_ids:
        print(f"[provenance] No decisions linked to: {artifact}")
        return

    decisions_by_id = {d["decision_id"]: d for d in data["decisions"]}
    print(f"\nDecision chain for: {artifact}")
    print("=" * 60)
    for did in decision_ids:
        d = decisions_by_id.get(did)
        if not d:
            print(f"  {did}: (record missing)")
            continue
        print(f"\n  [{did}] {d['decision']}")
        print(f"    evidence: [{d['evidence_type']}] {d['evidence_ref']}")
        if d.get("notes"):
            print(f"    notes: {d['notes']}")
        print(f"    logged: {d['timestamp']}")


def cmd_report(args: argparse.Namespace) -> None:
    data = _load(args.project_dir, args.run_id)
    decisions = data.get("decisions", [])

    lines = [
        f"# Provenance Report: {args.run_id}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Project: {args.project_dir}",
        "",
        "This document traces the decision chain for this analysis run.",
        "Each decision is linked to its evidence source and the artifact it produced.",
        "",
        f"## Summary",
        "",
        f"Total decisions recorded: {len(decisions)}",
        "",
    ]

    # Group decisions by evidence type
    by_type: dict[str, list] = {}
    for d in decisions:
        et = d.get("evidence_type", "unknown")
        by_type.setdefault(et, []).append(d)

    if by_type:
        lines.append("| Evidence type | Count |")
        lines.append("|---------------|-------|")
        for et, items in sorted(by_type.items()):
            lines.append(f"| {et} | {len(items)} |")
        lines.append("")

    lines.append("## Decision Chain")
    lines.append("")

    if not decisions:
        lines.append("*(no decisions recorded)*")
    else:
        for d in decisions:
            lines += [
                f"### {d['decision_id']}",
                "",
                f"**Decision:** {d['decision']}",
                "",
                f"**Evidence:** [{d['evidence_type']}] `{d['evidence_ref']}`",
                "",
                f"**Output artifact:** `{d['output_artifact']}`",
            ]
            if d.get("notes"):
                lines.append(f"\n**Notes:** {d['notes']}")
            lines += [f"\n*Logged: {d['timestamp']}*", ""]

    # Artifact index
    lines += ["## Artifact Index", ""]
    artifact_index = data.get("artifact_index", {})
    if artifact_index:
        lines.append("| Artifact | Decision IDs |")
        lines.append("|----------|-------------|")
        for artifact, dids in sorted(artifact_index.items()):
            lines.append(f"| `{artifact}` | {', '.join(dids)} |")
    else:
        lines.append("*(no artifacts indexed)*")

    report = "\n".join(lines) + "\n"

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"[provenance] Report written to {out_path}")
    print(f"  {len(decisions)} decisions, {len(artifact_index)} artifacts")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--run-id", required=True)
    p.add_argument("--project-dir", required=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Provenance chain tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_link = sub.add_parser("link", help="Register a decision → evidence → artifact chain")
    _common(p_link)
    p_link.add_argument("--decision-id", required=True, help="e.g. DEC-001")
    p_link.add_argument("--decision", required=True)
    p_link.add_argument("--evidence-type", required=True,
                        choices=["biomni_query", "literature", "qc_result", "peer_review", "user_input"])
    p_link.add_argument("--evidence-ref", required=True,
                        help="ID or description of the evidence (e.g. BIOMNI-001)")
    p_link.add_argument("--output-artifact", required=True,
                        help="File path of the artifact this decision produced")
    p_link.add_argument("--notes", default="")

    p_trace = sub.add_parser("trace", help="Show decisions that led to an artifact")
    _common(p_trace)
    p_trace.add_argument("--artifact", required=True)

    p_report = sub.add_parser("report", help="Generate full provenance Markdown report")
    _common(p_report)
    p_report.add_argument("--output", required=True, help="Output .md file path")

    args = parser.parse_args()
    dispatch = {"link": cmd_link, "trace": cmd_trace, "report": cmd_report}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
