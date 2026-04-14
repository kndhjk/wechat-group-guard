#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[*] Removing virtual environment…"
rm -rf .venv
echo "[*] Virtual environment removed."
echo ""
echo "Note: data/, logs/, config.yaml, and .gitignore-controlled files remain."
echo "To remove everything: rm -rf wechat-group-guard"
