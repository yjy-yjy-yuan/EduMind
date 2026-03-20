#!/usr/bin/env bash
set -euo pipefail

if [ -n "${CI:-}" ]; then
  echo "CI detected, skipping hook installation."
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${REPO_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Creating virtual environment at ${VENV_DIR}"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Installing hook tooling into ${VENV_DIR}"
"$VENV_PYTHON" -m pip install --upgrade pip pre-commit mypy

echo "Installing Git hooks"
"$VENV_PYTHON" -m pre_commit install --install-hooks --hook-type pre-commit --hook-type pre-push --hook-type commit-msg

echo "Git hooks installed."
echo "Escape hatch: use --no-verify only when you intentionally need to bypass local hooks."
