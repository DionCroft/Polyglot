#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d dist/LectureLive.app ]]; then
  echo "Build with Setup-Mac.command first, or install the ready-made Mac download."
  exit 1
fi
open dist/LectureLive.app
