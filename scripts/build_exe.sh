#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. .venv/bin/activate
pyinstaller --noconfirm --windowed --name WeChatGroupGuard gui/app.py
printf '\nBuild complete. Output: dist/WeChatGroupGuard/ or dist/WeChatGroupGuard.exe\n'
