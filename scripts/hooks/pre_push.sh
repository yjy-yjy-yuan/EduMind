#!/usr/bin/env bash
set -euo pipefail

if [ -n "${CI:-}" ]; then
  echo "CI detected, skipping local pre-push hooks."
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="${REPO_DIR}/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Missing ${VENV_PYTHON}. Create the project virtualenv before pushing." >&2
  echo "Expected: python3 -m venv .venv && . .venv/bin/activate && pip install -r backend_fastapi/requirements.txt" >&2
  exit 1
fi

if [ ! -d "${REPO_DIR}/mobile-frontend/node_modules" ]; then
  echo "Missing mobile-frontend/node_modules. Run 'cd mobile-frontend && npm install' before pushing." >&2
  exit 1
fi

echo "Running backend smoke validation..."
"$VENV_PYTHON" scripts/validate_backend_smoke.py

echo "Running mobile iOS build..."
(
  cd "${REPO_DIR}/mobile-frontend"
  npm run build:ios
)
