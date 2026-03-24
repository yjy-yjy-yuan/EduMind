#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$REPO_DIR/mobile-frontend"
WEB_ASSETS_DIR="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS/WebAssets"
BACKEND_ENV_FILE="$REPO_DIR/backend_fastapi/.env"
IOS_PROJECT_FILE="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj"

log() {
  echo "[ios:sync] $*"
}

fail() {
  echo "[ios:sync][error] $*" >&2
  exit 1
}

require_path() {
  local path="$1"
  [ -e "$path" ] || fail "缺少必要文件或目录：$path"
}

require_path "$MOBILE_DIR"
require_path "$MOBILE_DIR/package.json"
require_path "$IOS_PROJECT_FILE"

command -v npm >/dev/null 2>&1 || fail "未找到 npm，请先安装 Node.js"
command -v rsync >/dev/null 2>&1 || fail "未找到 rsync，无法同步 WebAssets"

BACKEND_PORT="2004"
PORT_SOURCE="default(2004)"
if [ -f "$BACKEND_ENV_FILE" ]; then
  DETECTED_PORT="$(awk -F= '/^PORT=/{print $2; exit}' "$BACKEND_ENV_FILE" | tr -d '[:space:]')"
  if [ -n "${DETECTED_PORT:-}" ]; then
    BACKEND_PORT="$DETECTED_PORT"
    PORT_SOURCE="$BACKEND_ENV_FILE"
  fi
fi
log "backend port: $BACKEND_PORT (source: $PORT_SOURCE)"

LOCAL_HOSTNAME="$(scutil --get LocalHostName 2>/dev/null || true)"
if [ -z "${LOCAL_HOSTNAME:-}" ]; then
  LOCAL_HOSTNAME="$(hostname -s 2>/dev/null || true)"
fi
if [ -z "${LOCAL_HOSTNAME:-}" ]; then
  fail "无法读取当前机器的 LocalHostName。请先在 macOS 系统设置中确认主机名可用，或手动检查 scutil --get LocalHostName"
fi
log "LocalHostName: $LOCAL_HOSTNAME"

IOS_API_BASE_URL=""
if [ -n "${LOCAL_HOSTNAME:-}" ]; then
  IOS_API_BASE_URL="http://${LOCAL_HOSTNAME}.local:${BACKEND_PORT}"
fi
log "iOS native API base URL: ${IOS_API_BASE_URL:-<empty>}"

if [ -n "$IOS_API_BASE_URL" ]; then
  perl -0pi -e "s|INFOPLIST_KEY_EDUMIND_API_BASE_URL = \"[^\"]*\";|INFOPLIST_KEY_EDUMIND_API_BASE_URL = \"$IOS_API_BASE_URL\";|g" "$IOS_PROJECT_FILE"
else
  fail "未生成 iOS native API base URL，无法刷新 INFOPLIST_KEY_EDUMIND_API_BASE_URL"
fi

cd "$MOBILE_DIR"

if [ ! -d "node_modules" ]; then
  log "node_modules 缺失，执行 npm install"
  npm install
else
  log "复用已有 node_modules"
fi

# Some environments lose executable bits in node_modules/.bin.
if [ -f "node_modules/.bin/vite" ] && [ ! -x "node_modules/.bin/vite" ]; then
  chmod +x node_modules/.bin/vite || true
fi
if [ -f "node_modules/vite/bin/vite.js" ] && [ ! -x "node_modules/vite/bin/vite.js" ]; then
  chmod +x node_modules/vite/bin/vite.js || true
fi

log "执行 mobile-frontend iOS 构建"
npm run build:ios

mkdir -p "$WEB_ASSETS_DIR"
log "同步 dist/ -> $WEB_ASSETS_DIR"
rsync -a --delete "$MOBILE_DIR/dist/" "$WEB_ASSETS_DIR/"

for required_asset in index.html index.js index.css; do
  if [ ! -f "$WEB_ASSETS_DIR/$required_asset" ]; then
    fail "同步完成但缺少关键产物：$WEB_ASSETS_DIR/$required_asset。请检查 mobile-frontend/vite.config.js 的 iOS 构建输出是否仍为 index.html/index.js/index.css 布局。"
  fi
done

log "Web assets synced to: $WEB_ASSETS_DIR"
log "iOS native API base synced to: $IOS_API_BASE_URL"
