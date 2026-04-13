#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
chmod +x scripts/run.sh scripts/uninstall.sh
printf '\nInstall complete. Run with: ./scripts/run.sh\n'
