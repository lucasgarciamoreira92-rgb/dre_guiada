#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${DRE_PYTHON:-python3}"
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3,12), "Use Python 3.12 (DRE_PYTHON pode indicar o executável)."'
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if (!((a===22 && b>=12)||a===24)) {console.error("Use Node 22.12+ ou 24.");process.exit(1)}'
if [[ ! -d backend/.venv ]]; then "$PYTHON" -m venv backend/.venv; fi
backend/.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3,12), "O ambiente virtual existente não usa Python 3.12; preserve-o e recrie manualmente."'
backend/.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci && npx playwright install chromium)
(cd backend && .venv/bin/python -m alembic upgrade head)
backend/.venv/bin/python scripts/install_hooks.py
printf '%s\n' 'Ambiente preparado. Execute: backend/.venv/bin/python scripts/validate.py'
