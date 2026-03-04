"""
Session harvester for retrospective analysis.

Takes a Claude Code session JSONL file from ~/.claude/projects/<project>/
and extracts tool call sequences, bash commands, and sequential thinking blocks
into a structured session_summary.json.

Usage
-----
    python scripts/harvest_session.py \
        --session-file ~/.claude/projects/<project>/<session_id>.jsonl \
        --output-dir reasoning_traces/retro/

Output
------
    <output-dir>/session_summary.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def load_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def extract_events(entries: list[dict]) -> dict:
    bash_commands: list[dict] = []
    tool_calls: list[dict] = []
    sequential_thinking_blocks: list[dict] = []
    file_ops: list[dict] = []

    for entry in entries:
        # Claude Code session format varies; handle both message-level and event-level
        msg_type = entry.get("type", "")
        role = entry.get("role", "")

        # Tool use blocks from assistant messages
        content = entry.get("content", [])
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})
                    record = {
                        "tool": tool_name,
                        "input_summary": _summarize_input(tool_name, tool_input),
                    }
                    tool_calls.append(record)

                    if tool_name == "Bash":
                        bash_commands.append({
                            "command": tool_input.get("command", "")[:2000],
                            "description": tool_input.get("description", ""),
                        })
                    elif tool_name in ("Read", "Write", "Edit", "Glob", "Grep"):
                        file_ops.append({
                            "tool": tool_name,
                            "path": tool_input.get("file_path", tool_input.get("pattern", "")),
                        })
                    elif tool_name == "mcp__sequential-thinking__sequentialthinking":
                        sequential_thinking_blocks.append({
                            "thought_number": tool_input.get("thoughtNumber"),
                            "total_thoughts": tool_input.get("totalThoughts"),
                            "thought": (tool_input.get("thought") or "")[:300],
                            "next_thought_needed": tool_input.get("nextThoughtNeeded"),
                            "is_revision": tool_input.get("isRevision", False),
                        })

    return {
        "total_tool_calls": len(tool_calls),
        "bash_commands": bash_commands,
        "file_operations": file_ops,
        "sequential_thinking_blocks": sequential_thinking_blocks,
        "tool_call_counts": _count_tools(tool_calls),
    }


def _summarize_input(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return (tool_input.get("command") or "")[:120]
    if tool_name in ("Read", "Write", "Edit"):
        return tool_input.get("file_path", "")
    if tool_name == "mcp__sequential-thinking__sequentialthinking":
        return f"thought {tool_input.get('thoughtNumber')}/{tool_input.get('totalThoughts')}"
    return str(tool_input)[:120]


def _count_tools(tool_calls: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tc in tool_calls:
        t = tc["tool"]
        counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Harvest Claude Code session for retrospective analysis")
    parser.add_argument("--session-file", required=True,
                        help="Path to .jsonl session file from ~/.claude/projects/")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to write session_summary.json")
    args = parser.parse_args()

    session_path = Path(args.session_file).expanduser()
    if not session_path.exists():
        print(f"ERROR: session file not found: {session_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = load_jsonl(session_path)
    events = extract_events(entries)

    summary = {
        "harvested_at": datetime.now(timezone.utc).isoformat(),
        "source_session": str(session_path),
        "total_messages": len(entries),
        **events,
    }

    out_path = output_dir / "session_summary.json"
    with out_path.open("w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"[harvest_session] Wrote {out_path}")
    print(f"  Total messages:          {summary['total_messages']}")
    print(f"  Total tool calls:        {summary['total_tool_calls']}")
    print(f"  Bash commands:           {len(summary['bash_commands'])}")
    print(f"  Sequential thinking:     {len(summary['sequential_thinking_blocks'])}")
    print(f"  File operations:         {len(summary['file_operations'])}")
    if summary["tool_call_counts"]:
        print("  Top tools:")
        for tool, count in list(summary["tool_call_counts"].items())[:5]:
            print(f"    {count:4d}  {tool}")


if __name__ == "__main__":
    main()
