#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf .venv
printf 'Virtual environment removed. Project files kept.\n'
printf 'If you also want to remove runtime data, delete: data/ logs/\n'
