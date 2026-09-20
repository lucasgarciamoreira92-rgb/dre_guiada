#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Match .nvmrc on the official Apple Silicon Mac when Homebrew Node 22 exists.
if [[ -x /opt/homebrew/opt/node@22/bin/node ]]; then
  export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
fi
exec backend/.venv/bin/python scripts/validate_visual.py
