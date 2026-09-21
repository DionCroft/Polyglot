#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo "Use this setup on an Apple Silicon Mac, without Rosetta."
  exit 1
fi
if ! command -v python3.11 >/dev/null 2>&1; then
  echo "Install Python 3.11 for macOS from python.org, then run this file again."
  echo "For an easier installation, use the ready-made LectureLive.app. See docs/MACOS.md."
  exit 1
fi
python3.11 -m venv .venv-macos
.venv-macos/bin/python -m pip install --only-binary=:all: --require-hashes -r requirements-macos-lock.txt
.venv-macos/bin/python -m scripts.setup_macos
.venv-macos/bin/python -m scripts.build_macos
echo "Ready: open dist/LectureLive.app. Read docs/MACOS.md for microphone permissions."
read -r -p "Press Return to close. "
