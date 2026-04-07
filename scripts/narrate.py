#!/usr/bin/env python3
"""
narrate.py — fire-and-forget terminal narration for multi-step analyses.

Usage:
    python scripts/narrate.py \
      --phase  research|planning|execute|review \
      --event  <short_identifier>               \
      --message "<one sentence>"                \
      [--flag  warn|st|ok]                      \
      [--run-id <run_id>]                       \
      [--project-dir <path>]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Phase config ────────────────────────────────────────────────────────────

PHASES = {
    "research": {"label": "🔬  RESEARCH  ", "ansi": "\033[36m"},   # cyan
    "planning": {"label": "🧠  PLANNING  ", "ansi": "\033[35m"},   # magenta
    "execute":  {"label": "⚙️   EXECUTE   ", "ansi": "\033[32m"},   # green
    "review":   {"label": "🔍  REVIEW    ", "ansi": "\033[34m"},   # blue
}

FLAGS = {
    "st":   "🔀 ",
    "warn": "⚠  ",
    "ok":   "✓  ",
}

RESET = "\033[0m"


def use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def build_line(phase: str, flag: str | None, message: str) -> str:
    cfg = PHASES[phase]
    flag_prefix = FLAGS.get(flag, "") if flag else ""
    label = cfg["label"]
    body = f"{label}│ {flag_prefix}{message}"

    if use_color():
        return f"{cfg['ansi']}{label}{RESET}│ {flag_prefix}{message}"
    return body


def write_jsonl(run_id: str, project_dir: str, phase: str, event: str,
                message: str, flag: str | None) -> None:
    trace_dir = Path(project_dir) / "reasoning_traces" / run_id
    trace_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "event": event,
        "message": message,
        "flag": flag,
    }
    with open(trace_dir / "narration.jsonl", "a") as fh:
        fh.write(json.dumps(record) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Narrate an agent decision point.")
    parser.add_argument("--phase", required=True, choices=list(PHASES))
    parser.add_argument("--event", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--flag", choices=list(FLAGS), default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--project-dir", default=None)
    args = parser.parse_args()

    print(build_line(args.phase, args.flag, args.message), flush=True)

    # Write checkpoint so pre-bash hook can verify narration happened recently
    checkpoint = Path.home() / ".claude" / "narration_checkpoint"
    checkpoint.parent.mkdir(exist_ok=True)
    checkpoint.touch()

    if args.run_id and args.project_dir:
        write_jsonl(args.run_id, args.project_dir, args.phase,
                    args.event, args.message, args.flag)


if __name__ == "__main__":
    main()
