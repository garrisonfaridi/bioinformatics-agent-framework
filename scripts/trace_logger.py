"""
Reasoning trace logger for the bioinformatics agent framework.
The agent calls this script at every structured reasoning event.
Output goes to <project_dir>/reasoning_traces/<run_id>/trace.jsonl

Subcommands
-----------
init-run        Start a new run trace
log-sequential  Log a sequential thinking invocation
log-decision    Log a planning/implementation decision
log-biomni      Log a Biomni query and its downstream decision
summarize       Print a summary of a trace.jsonl file
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trace_dir(project_dir: str, run_id: str) -> Path:
    d = Path(project_dir) / "reasoning_traces" / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _trace_file(project_dir: str, run_id: str) -> Path:
    return _trace_dir(project_dir, run_id) / "trace.jsonl"


def _append(record: dict, project_dir: str, run_id: str) -> None:
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    record["run_id"] = run_id
    with _trace_file(project_dir, run_id).open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def _load_trace(project_dir: str, run_id: str) -> list[dict]:
    path = _trace_file(project_dir, run_id)
    if not path.exists():
        return []
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_init_run(args: argparse.Namespace) -> None:
    record = {
        "event_type": "run_init",
        "task_description": args.task_description,
    }
    _append(record, args.project_dir, args.run_id)
    print(f"[trace_logger] Run '{args.run_id}' initialized in {args.project_dir}")


def cmd_log_sequential(args: argparse.Namespace) -> None:
    hypotheses = [h.strip() for h in args.hypotheses.split(",")] if args.hypotheses else []
    branch_closed = (
        [b.strip() for b in args.branch_closed.split(",")] if args.branch_closed else []
    )
    record = {
        "event_type": "sequential_thinking",
        "trigger": args.trigger,
        "context": args.context,
        "hypotheses_opened": hypotheses,
        "evidence_used": args.evidence_used,
        "branches_closed": branch_closed,
        "conclusion": args.conclusion,
    }
    _append(record, args.project_dir, args.run_id)
    unclosed = [h for h in hypotheses if h not in branch_closed]
    print(f"[trace_logger] sequential_thinking logged. Hypotheses: {hypotheses}. "
          f"Unclosed: {unclosed if unclosed else 'none'}")


def cmd_log_decision(args: argparse.Namespace) -> None:
    alternatives = (
        [a.strip() for a in args.alternatives_considered.split(",")]
        if args.alternatives_considered
        else []
    )
    record = {
        "event_type": "decision",
        "phase": args.phase,
        "decision": args.decision,
        "rationale": args.rationale,
        "alternatives_considered": alternatives,
        "biomni_query_id": args.biomni_query_id,
    }
    _append(record, args.project_dir, args.run_id)
    print(f"[trace_logger] decision logged (phase={args.phase}): {args.decision[:80]}")


def cmd_log_biomni(args: argparse.Namespace) -> None:
    record = {
        "event_type": "biomni_query",
        "query": args.query,
        "tool_used": args.tool_used,
        "summary": args.summary,
        "downstream_decision": args.downstream_decision,
    }
    _append(record, args.project_dir, args.run_id)
    print(f"[trace_logger] biomni_query logged: {args.query[:80]}")


def cmd_summarize(args: argparse.Namespace) -> None:
    entries = _load_trace(args.project_dir, args.run_id)
    if not entries:
        print(f"[trace_logger] No trace found for run '{args.run_id}' in {args.project_dir}")
        return

    by_type: dict[str, list] = {}
    for e in entries:
        by_type.setdefault(e["event_type"], []).append(e)

    print(f"\n=== Reasoning Trace Summary: {args.run_id} ===\n")

    # Run init
    inits = by_type.get("run_init", [])
    if inits:
        print(f"Task: {inits[0].get('task_description', '(none)')}")
        print(f"Started: {inits[0].get('timestamp', '?')}\n")

    # Sequential thinking
    sts = by_type.get("sequential_thinking", [])
    print(f"Sequential thinking invocations: {len(sts)}")
    trigger_counts: dict[str, int] = {}
    unclosed_branches: list[str] = []
    for st in sts:
        t = st.get("trigger", "unknown")
        trigger_counts[t] = trigger_counts.get(t, 0) + 1
        opened = set(st.get("hypotheses_opened", []))
        closed = set(st.get("branches_closed", []))
        unclosed_branches.extend(opened - closed)
    if trigger_counts:
        print("  Triggers fired:")
        for t, c in trigger_counts.items():
            print(f"    {c}x  {t}")
    if unclosed_branches:
        print(f"  [QUALITY FLAG] Unclosed branches: {unclosed_branches}")
    print()

    # Biomni queries
    biomnis = by_type.get("biomni_query", [])
    print(f"Biomni queries: {len(biomnis)}")
    for b in biomnis:
        print(f"  - [{b.get('tool_used', '?')}] {b.get('query', '')[:70]}")
        print(f"      -> {b.get('downstream_decision', '(none)')[:70]}")
    print()

    # Decisions
    decisions = by_type.get("decision", [])
    print(f"Key decisions: {len(decisions)}")
    for d in decisions:
        alts = d.get("alternatives_considered", [])
        alts_str = f" (vs. {', '.join(alts)})" if alts else ""
        print(f"  [{d.get('phase', '?')}] {d.get('decision', '')[:70]}{alts_str}")
        print(f"    rationale: {d.get('rationale', '')[:80]}")
    print()

    if unclosed_branches:
        print("[QUALITY FLAG] Some sequential thinking branches were opened but never "
              "formally closed. Review trace for completeness.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--run-id", required=True, help="Run identifier (YYYYMMDD_HHMMSS_desc)")
    p.add_argument("--project-dir", required=True, help="Project root directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bioinformatics agent reasoning trace logger"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init-run
    p_init = sub.add_parser("init-run", help="Start a new run trace")
    _common(p_init)
    p_init.add_argument("--task-description", required=True)

    # log-sequential
    p_seq = sub.add_parser("log-sequential", help="Log a sequential thinking invocation")
    _common(p_seq)
    p_seq.add_argument("--trigger", required=True)
    p_seq.add_argument("--context", required=True)
    p_seq.add_argument("--hypotheses", default="",
                       help="Comma-separated list of hypotheses opened")
    p_seq.add_argument("--evidence-used", default="")
    p_seq.add_argument("--branch-closed", default="",
                       help="Comma-separated hypotheses formally closed")
    p_seq.add_argument("--conclusion", default="")

    # log-decision
    p_dec = sub.add_parser("log-decision", help="Log a planning/implementation decision")
    _common(p_dec)
    p_dec.add_argument("--phase", required=True,
                       choices=["planning", "implementation", "peer_review"])
    p_dec.add_argument("--decision", required=True)
    p_dec.add_argument("--rationale", required=True)
    p_dec.add_argument("--alternatives-considered", default="",
                       help="Comma-separated alternatives")
    p_dec.add_argument("--biomni-query-id", default=None)

    # log-biomni
    p_bio = sub.add_parser("log-biomni", help="Log a Biomni query for provenance")
    _common(p_bio)
    p_bio.add_argument("--query", required=True)
    p_bio.add_argument("--tool-used", required=True)
    p_bio.add_argument("--summary", required=True)
    p_bio.add_argument("--downstream-decision", required=True)

    # summarize
    p_sum = sub.add_parser("summarize", help="Print a run trace summary")
    _common(p_sum)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "init-run": cmd_init_run,
        "log-sequential": cmd_log_sequential,
        "log-decision": cmd_log_decision,
        "log-biomni": cmd_log_biomni,
        "summarize": cmd_summarize,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
