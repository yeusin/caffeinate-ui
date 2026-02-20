#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

rm -rf build dist

uv run pyinstaller caffeinate_ui.spec --noconfirm
