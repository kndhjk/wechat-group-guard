#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# Build Windows EXE with PyInstaller (run on Windows)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

# Must be run on Windows with Python installed
PYTHON=${PYTHON:-python}

echo "[*] Installing PyInstaller…"
pip install pyinstaller --quiet

echo "[*] Building EXE…"
$PYTHON -m PyInstaller scripts/build_spec.spec --noconfirm --clean 2>&1

echo ""
echo "[✓] Build complete."
echo "    Output: dist/WeChatGroupGuard/"
ls -la dist/WeChatGroupGuard/ 2>/dev/null || dir dist\\WeChatGroupGuard
echo ""
echo "To package as ZIP:"
echo "  powershell Compress-Archive -Path dist/WeChatGroupGuard -DestinationPath WeChatGroupGuard.zip"
