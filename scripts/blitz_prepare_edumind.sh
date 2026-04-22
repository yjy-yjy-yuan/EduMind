#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
BACKEND_DIR=""
BACKEND_REQUIREMENTS=""
MOBILE_DIR="$REPO_DIR/mobile-frontend"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
  echo "[blitz:prepare] $*"
}

fail() {
  echo "[blitz:prepare][error] $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [ -e "$path" ] || fail "缺少必要文件或目录：$path"
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

BACKEND_DIR="$(resolve_backend_dir || true)"
[ -n "$BACKEND_DIR" ] || fail "未找到后端目录。请确保存在 ../edumind-backend 或设置 EDUMIND_BACKEND_DIR"
BACKEND_REQUIREMENTS="$BACKEND_DIR/requirements.txt"
require_file "$BACKEND_REQUIREMENTS"
require_file "$MOBILE_DIR/package.json"
require_file "$REPO_DIR/ios-app/sync_ios_web_assets.sh"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "未找到 Python：$PYTHON_BIN"
command -v npm >/dev/null 2>&1 || fail "未找到 npm，请先安装 Node.js"

if [ ! -x "$VENV_PYTHON" ]; then
  log "创建虚拟环境：$VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  log "复用已有虚拟环境：$VENV_DIR"
fi

log "安装后端依赖：$BACKEND_REQUIREMENTS"
"$VENV_PYTHON" -m pip install -r "$BACKEND_REQUIREMENTS"

if [ ! -d "$MOBILE_DIR/node_modules" ]; then
  log "安装前端依赖：mobile-frontend/node_modules"
  (
    cd "$MOBILE_DIR"
    npm install
  )
else
  log "复用已有前端依赖：$MOBILE_DIR/node_modules"
fi

log "同步 iOS WebAssets"
bash "$REPO_DIR/ios-app/sync_ios_web_assets.sh"

log "准备完成。建议下一步："
echo "  1. bash scripts/blitz_start_backend.sh"
echo "  2. bash scripts/blitz_backend_healthcheck.sh"
echo "  3. bash scripts/blitz_build_ios.sh"
