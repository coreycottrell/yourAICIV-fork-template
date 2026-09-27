#!/usr/bin/env bash
# model_boot.sh — the wired consumer of the model switch.
#
# Spec: .claude/skills/multi-model-inference-mastery/SKILL.md §3.1.
# Reads config/model_mode.json + sources config/model_mode.env, then execs the
# session runtime so the parent process AND every agent() sub-call underneath
# inherit the switched substrate (the load-bearing env var is
# CLAUDE_CODE_SUBAGENT_MODEL — without it, sub-agents stay on the parent's
# default model even when the base URL is redirected).
#
# HONEST STAMP: NET-NEW implementation for the aiciv-fork-template against the
# PROVEN-in-origin mechanism. UNVALIDATED against a real router in any fork.
#
#   ./tools/model_boot.sh --show-env          # print the env the mode would export
#   ./tools/model_boot.sh -p "prompt..."      # run claude with the mode's env
#   ./tools/model_boot.sh <any claude args>   # pass-through

set -euo pipefail

ROOT="${CIV_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE="$ROOT/config/model_mode.json"
ENVFRAG="$ROOT/config/model_mode.env"

if [ -f "$ENVFRAG" ]; then
    # shellcheck disable=SC1090
    source "$ENVFRAG"
fi

if [ "${1:-}" = "--show-env" ]; then
    echo "mode file: $(cat "$STATE" 2>/dev/null || echo '(none — default)')"
    echo "ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL:-'(unset)'}"
    echo "ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-'(unset)'}"
    echo "CLAUDE_CODE_SUBAGENT_MODEL=${CLAUDE_CODE_SUBAGENT_MODEL:-'(unset)'}"
    if [ -n "${ANTHROPIC_API_KEY:-}" ]; then echo "ANTHROPIC_API_KEY=(set, redacted)"; else echo "ANTHROPIC_API_KEY=(unset)"; fi
    exit 0
fi

exec claude "$@"
