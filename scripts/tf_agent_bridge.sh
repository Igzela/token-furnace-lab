#!/usr/bin/env bash
# Token Furnace Agent Bridge
# Executes orchestrator-generated prompts via Claude Code CLI.
#
# Usage:
#   ./scripts/tf_agent_bridge.sh <prompt_file> <artifact_path> [options]
#
# Options:
#   --model <model>      Override model (default: inherit from Claude Code config)
#   --timeout <seconds>  Timeout for claude CLI (default: 300)
#   --subagent-type <type>  Subagent type (default: Plan)
#   --write-mode         Enable write tools (Write, Edit, mkdir, cp) in addition to read-only
#   --dry-run            Print the command without executing
#
# Environment:
#   CLAUDE_MODEL         Override model
#   CLAUDE_EXTRA_ARGS    Additional args for claude CLI

set -euo pipefail

PROMPT_FILE="${1:?Usage: $0 <prompt_file> <artifact_path>}"
ARTIFACT_PATH="${2:?Usage: $0 <prompt_file> <artifact_path>}"
shift 2

# Parse options
TIMEOUT=300
DRY_RUN=false
WRITE_MODE=false
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model) EXTRA_ARGS+=("--model" "$2"); shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        --subagent-type) EXTRA_ARGS+=("--agent" "$2"); shift 2 ;;
        --write-mode) WRITE_MODE=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) EXTRA_ARGS+=("$1"); shift ;;
    esac
done

# Validate
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "ERROR: Prompt file not found: $PROMPT_FILE" >&2
    exit 1
fi

# Build command
CMD=(claude -p --output-format json)
CMD+=("${EXTRA_ARGS[@]}")

# Add model from env if set
if [[ -n "${CLAUDE_MODEL:-}" ]]; then
    CMD+=("--model" "$CLAUDE_MODEL")
fi

# Add allowed tools (read-only by default, write-mode adds write tools)
if $WRITE_MODE; then
    CMD+=("--allowedTools" "Read" "Write" "Edit" "Grep" "Glob" "Bash(git *)" "Bash(mkdir *)" "Bash(cp *)")
else
    CMD+=("--allowedTools" "Read" "Grep" "Glob" "Bash(git *)")
fi

if $DRY_RUN; then
    echo "DRY RUN: ${CMD[*]}" >&2
    echo "  Prompt: $PROMPT_FILE" >&2
    echo "  Output: $ARTIFACT_PATH" >&2
    exit 0
fi

# Execute with timeout
echo "[$(date -Iseconds)] Starting agent bridge..." >&2
echo "  Prompt: $PROMPT_FILE" >&2
echo "  Output: $ARTIFACT_PATH" >&2

mkdir -p "$(dirname "$ARTIFACT_PATH")"

# Run claude CLI with timeout
if timeout "$TIMEOUT" "${CMD[@]}" < "$PROMPT_FILE" > "$ARTIFACT_PATH.tmp" 2>/dev/null; then
    # Extract text from JSON response
    if command -v jq &>/dev/null; then
        jq -r '.result // .content // .text // empty' "$ARTIFACT_PATH.tmp" > "$ARTIFACT_PATH" 2>/dev/null || \
            cp "$ARTIFACT_PATH.tmp" "$ARTIFACT_PATH"
    else
        cp "$ARTIFACT_PATH.tmp" "$ARTIFACT_PATH"
    fi
    rm -f "$ARTIFACT_PATH.tmp"
    echo "[$(date -Iseconds)] Agent bridge complete: $ARTIFACT_PATH" >&2
else
    EXIT_CODE=$?
    rm -f "$ARTIFACT_PATH.tmp"
    echo "[$(date -Iseconds)] Agent bridge failed (exit=$EXIT_CODE)" >&2
    echo "# Agent bridge failed (timeout=${TIMEOUT}s, exit=$EXIT_CODE)" > "$ARTIFACT_PATH"
    exit 1
fi
