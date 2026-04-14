#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# WeChat Group Guard — install script (Linux / macOS / Git Bash)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "[*] Creating virtual environment…"
python3 -m venv .venv

echo "[*] Activating virtual environment…"
. .venv/bin/activate

echo "[*] Upgrading pip…"
pip install --upgrade pip --quiet

echo "[*] Installing dependencies…"
pip install -r requirements.txt --quiet

echo "[*] Copying config…"
if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "    → config.yaml created from config.example.yaml"
    echo "    → Edit config.yaml before first run"
else
    echo "    → config.yaml already exists, skipping"
fi

echo "[*] Creating data/log directories…"
mkdir -p data logs

echo ""
echo "[✓] Install complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml (especially dry_run setting)"
echo "  2. Run GUI:  ./scripts/run.sh"
echo "     Or console:  python main.py --mode console"
echo ""
