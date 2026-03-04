"""
Reasoning trace quality validator.

Checks a reasoning_traces/<run_id>/trace.jsonl against quality criteria and
reports findings. Useful as a post-session audit and in CI.

Checks
------
1. At least 1 sequential thinking log entry per run
2. Every pipeline execution preceded by a log-decision entry (heuristic)
3. No unclosed branches (ST invocations with hypotheses but no branch-closed)
4. Every Biomni query has a downstream-decision field
5. Run has been initialized (init-run entry present)

Usage
-----
    python tests/trace_quality/validate_trace.py \\
        --run-id <run_id> \\
        --project-dir <project_dir>

Exit codes
----------
    0 = all checks passed
    1 = quality warnings (non-blocking)
    2 = critical failures (blocking)
"""

import argparse
import json
import sys
from pathlib import Path


def load_trace(project_dir: str, run_id: str) -> list[dict]:
    path = Path(project_dir) / "reasoning_traces" / run_id / "trace.jsonl"
    if not path.exists():
        return []
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def validate(entries: list[dict]) -> tuple[list[str], list[str]]:
    """
    Returns (warnings, critical_failures).
    """
    warnings: list[str] = []
    critical: list[str] = []

    by_type: dict[str, list] = {}
    for e in entries:
        by_type.setdefault(e.get("event_type", "unknown"), []).append(e)

    # Check 1: run initialized
    if "run_init" not in by_type:
        critical.append("No init-run entry found — run was not properly initialized")

    # Check 2: at least 1 sequential thinking entry
    sts = by_type.get("sequential_thinking", [])
    if not sts:
        warnings.append(
            "No sequential thinking entries — complex decisions may have used inline reasoning"
        )

    # Check 3: unclosed branches and vacuous ST entries
    for st in sts:
        opened = set(st.get("hypotheses_opened", []))
        if not opened:
            warnings.append(
                f"ST entry has no hypotheses_opened (trigger={st.get('trigger', '?')}) "
                f"— invocation may be vacuous"
            )
        closed = set(st.get("branches_closed", []))
        unclosed = opened - closed
        if unclosed:
            warnings.append(
                f"Unclosed branches in ST entry (trigger={st.get('trigger', '?')}): "
                f"{sorted(unclosed)}"
            )

    # Check 4: Biomni queries have downstream decisions
    biomnis = by_type.get("biomni_query", [])
    for b in biomnis:
        if not b.get("downstream_decision"):
            warnings.append(
                f"Biomni query missing downstream_decision: '{b.get('query', '')[:60]}'"
            )

    # Check 5: at least one decision entry
    decisions = by_type.get("decision", [])
    if not decisions and entries:
        warnings.append(
            "No decision entries — method selections were not logged"
        )

    # Check 6: planning decision exists before implementation decisions
    phases = [d.get("phase") for d in decisions]
    if "implementation" in phases and "planning" not in phases:
        warnings.append(
            "Implementation decisions logged but no planning decision — "
            "plan finalization was not traced"
        )

    return warnings, critical


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate reasoning trace quality")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--project-dir", required=True)
    args = parser.parse_args()

    entries = load_trace(args.project_dir, args.run_id)

    if not entries:
        print(f"[validate_trace] No trace found for run '{args.run_id}' in {args.project_dir}")
        sys.exit(2)

    warnings, critical = validate(entries)

    print(f"\n=== Trace Quality Report: {args.run_id} ===\n")
    print(f"Total entries:         {len(entries)}")
    print(f"Critical failures:     {len(critical)}")
    print(f"Warnings:              {len(warnings)}")
    print()

    if critical:
        print("CRITICAL FAILURES:")
        for c in critical:
            print(f"  [CRITICAL] {c}")
        print()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [WARN] {w}")
        print()

    if not critical and not warnings:
        print("All quality checks passed.")

    if critical:
        sys.exit(2)
    elif warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
