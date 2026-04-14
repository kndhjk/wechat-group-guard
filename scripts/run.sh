#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# WeChat Group Guard — run script (Linux / macOS / Git Bash)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Activate venv if it exists, otherwise run directly
if [ -f .venv/bin/activate ]; then
    . .venv/bin/activate
fi

# Default to GUI mode
MODE="${1:-gui}"

python main.py --mode "$MODE"
