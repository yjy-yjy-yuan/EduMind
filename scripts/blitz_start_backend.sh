#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_ACTIVATE="$REPO_DIR/.venv/bin/activate"
BACKEND_DIR=""
BACKEND_ENTRY=""
BACKEND_ENV=""

log() {
  echo "[blitz:backend] $*"
}

fail() {
  echo "[blitz:backend][error] $*" >&2
  exit 1
}

resolve_backend_dir() {
  local candidates=()
  if [ -n "${EDUMIND_BACKEND_DIR:-}" ]; then
    candidates+=("${EDUMIND_BACKEND_DIR}")
  fi
  candidates+=(
    "$REPO_DIR/../edumind-backend"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate/run.py" ] && [ -d "$candidate/app" ]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

[ -f "$VENV_ACTIVATE" ] || fail "未找到虚拟环境：$VENV_ACTIVATE。请先执行 bash scripts/blitz_prepare_edumind.sh"
BACKEND_DIR="$(resolve_backend_dir || true)"
[ -n "$BACKEND_DIR" ] || fail "未找到后端目录。请确保存在 ../edumind-backend 或设置 EDUMIND_BACKEND_DIR"
BACKEND_ENTRY="$BACKEND_DIR/run.py"
BACKEND_ENV="$BACKEND_DIR/.env"
[ -f "$BACKEND_ENTRY" ] || fail "未找到后端入口：$BACKEND_ENTRY"

BACKEND_HOST="127.0.0.1"
BACKEND_PORT="2004"
if [ -f "$BACKEND_ENV" ]; then
  DETECTED_HOST="$(awk -F= '/^HOST=/{print $2; exit}' "$BACKEND_ENV" | tr -d '[:space:]' || true)"
  DETECTED_PORT="$(awk -F= '/^PORT=/{print $2; exit}' "$BACKEND_ENV" | tr -d '[:space:]' || true)"
  if [ -n "${DETECTED_HOST:-}" ]; then
    BACKEND_HOST="$DETECTED_HOST"
  fi
  if [ -n "${DETECTED_PORT:-}" ]; then
    BACKEND_PORT="$DETECTED_PORT"
  fi
fi

log "激活虚拟环境：$VENV_ACTIVATE"
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

cd "$REPO_DIR"
log "启动后端：python $BACKEND_ENTRY"
log "预期监听地址：http://$BACKEND_HOST:$BACKEND_PORT"
exec python "$BACKEND_ENTRY"
