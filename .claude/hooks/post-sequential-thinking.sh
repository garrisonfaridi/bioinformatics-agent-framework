#!/usr/bin/env bash
# Post sequential-thinking hook: record that ST was invoked (filesystem-level audit)

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE=".claude/st_invocations.log"

mkdir -p .claude
echo "$TIMESTAMP sequential_thinking_invoked" >> "$LOG_FILE"

exit 0
