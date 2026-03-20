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

if ! "$VENV_PYTHON" -m mypy --version >/dev/null 2>&1; then
  echo "mypy is not installed in .venv. Run 'bash scripts/install_git_hooks.sh' to bootstrap hook tooling." >&2
  exit 1
fi

echo "Running mypy..."
(
  cd "$REPO_DIR"
  MYPYPATH=backend_fastapi "$VENV_PYTHON" -m mypy \
    --config-file pyproject.toml \
    backend_fastapi/app/models \
    backend_fastapi/app/schemas \
    backend_fastapi/scripts/init_db.py \
    scripts/hooks
)

echo "Running backend fast test suite..."
(
  cd "$REPO_DIR"
  "$VENV_PYTHON" -m pytest backend_fastapi/tests/unit backend_fastapi/tests/api backend_fastapi/tests/smoke -q
)

echo "Running mobile iOS build..."
(
  cd "${REPO_DIR}/mobile-frontend"
  npm run build:ios
)
