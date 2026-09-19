#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -x backend/.venv/bin/python ]]; then
  printf '%s\n' 'Ambiente Python ausente. Execute bash scripts/setup.sh primeiro.' >&2
  exit 1
fi
exec backend/.venv/bin/python scripts/validate.py
