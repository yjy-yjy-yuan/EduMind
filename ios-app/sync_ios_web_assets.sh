#!/usr/bin/env bash
#
# EduMind iOS Web Assets 同步脚本
#
# 用法:
#   bash ios-app/sync_ios_web_assets.sh              # Debug 模式（默认）: 联调本机 .local
#   bash ios-app/sync_ios_web_assets.sh --release     # Release/TestFlight 模式: 使用固定域名
#
# 环境变量:
#   FIXED_DOMAIN      固定后端域名，--release 模式必须设置（如 https://api.xxx.com）
#   BACKEND_PORT      后端端口（从后端 .env 读取，默认 2004）
#   EDUMIND_BACKEND_DIR  可选，显式指定后端目录（优先级最高）
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$REPO_DIR/mobile-frontend"
WEB_ASSETS_DIR="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS/WebAssets"
IOS_PROJECT_FILE="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj"
BACKEND_DIR=""
BACKEND_ENV_FILE=""

# Debug/Release 模式标志
IS_RELEASE=false

# 解析参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --release)
      IS_RELEASE=true
      shift
      ;;
    -h|--help)
      echo "用法: $0 [--release]"
      echo "  --release    Release/TestFlight 模式，使用固定域名（需设置 FIXED_DOMAIN 环境变量）"
      echo ""
      echo "环境变量:"
      echo "  FIXED_DOMAIN    固定后端域名，如 https://api.xxx.com"
      echo "  BACKEND_PORT    后端端口（默认 2004）"
      echo "  EDUMIND_BACKEND_DIR  后端目录（默认优先 ../edumind-backend）"
      exit 0
      ;;
    *)
      echo "[ios:sync][warn] 未知参数: $1，忽略"
      shift
      ;;
  esac
done

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

require_path "$MOBILE_DIR"
require_path "$MOBILE_DIR/package.json"
require_path "$IOS_PROJECT_FILE"
BACKEND_DIR="$(resolve_backend_dir || true)"
[ -n "$BACKEND_DIR" ] || fail "未找到后端目录。请确保存在 ../edumind-backend 或设置 EDUMIND_BACKEND_DIR"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"

command -v npm >/dev/null 2>&1 || fail "未找到 npm，请先安装 Node.js"
command -v rsync >/dev/null 2>&1 || fail "未找到 rsync，无法同步 WebAssets"

# ============================================================
# 1. 读取后端端口
# ============================================================
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
log "backend dir:  $BACKEND_DIR"

# ============================================================
# 2. 确定 API Base URL（双通道核心逻辑）
# ============================================================

# 检测 .local / 私网 IP / 占位符域名的风险模式（提取 URL host 部分后检测）
is_local_pattern() {
  local url="$1"
  # 提取 host:port 部分（去掉协议前缀）
  local host_port
  host_port="$(echo "$url" | sed -E 's|^https?://||' | sed -E 's|/.*$||')"
  # 检测 .local、127.0.0.1、localhost、私网 IP
  echo "$host_port" | grep -qE '(\.local$|\.local:|127\.0\.0\.1|localhost|^0\.0\.0\.0|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\.|^192\.168\.)'
}

# 检测占位符域名（Release 模式必须替换）
is_placeholder_domain() {
  local url="$1"
  # 提取 host 部分（去掉协议前缀和路径）
  local host
  host="$(echo "$url" | sed -E 's|^https?://||' | sed -E 's|:.*$||' | sed -E 's|/.*$||')"
  # 匹配占位符域名（精确尾缀匹配）
  echo "$host" | grep -qE '(^|\.)(xxx\.com|example\.com|test\.local)$'
}

if [ "$IS_RELEASE" = true ]; then
  # ---- Release / TestFlight 通道 ----
  if [ -z "${FIXED_DOMAIN:-}" ]; then
    fail "Release 模式必须设置 FIXED_DOMAIN 环境变量，如: FIXED_DOMAIN=https://api.xxx.com $0 --release"
  fi

  # 安全检查 1：禁止 .local / 私网 IP
  if is_local_pattern "$FIXED_DOMAIN"; then
    fail "Release 模式检测到非固定域名地址: $FIXED_DOMAIN\n  禁止在 TestFlight/Release 中使用 .local、127.0.0.1 或私网 IP。"
  fi

  # 安全检查 2：禁止占位符域名
  if is_placeholder_domain "$FIXED_DOMAIN"; then
    fail "Release 模式检测到占位符域名: $FIXED_DOMAIN\n  请将 FIXED_DOMAIN 替换为真实固定域名（如 https://api.yourdomain.com）。"
  fi

  IOS_API_BASE_URL="$FIXED_DOMAIN"
  BUILD_MODE="Release"
  PBXPROJ_TARGET_UUID="1C23BC322F62C3DC00D572F8"
  PBXPROJ_TARGET_NAME="Release"
  log "【Release 模式】iOS native API base URL: $IOS_API_BASE_URL (source: FIXED_DOMAIN env)"
else
  # ---- Debug 本地联调通道 ----
  LOCAL_HOSTNAME="$(scutil --get LocalHostName 2>/dev/null || true)"
  if [ -z "${LOCAL_HOSTNAME:-}" ]; then
    LOCAL_HOSTNAME="$(hostname -s 2>/dev/null || true)"
  fi
  if [ -z "${LOCAL_HOSTNAME:-}" ]; then
    fail "无法读取当前机器的 LocalHostName。请先在 macOS 系统设置中确认主机名可用，或手动检查 scutil --get LocalHostName"
  fi
  log "LocalHostName: $LOCAL_HOSTNAME"

  IOS_API_BASE_URL="http://${LOCAL_HOSTNAME}.local:${BACKEND_PORT}"
  BUILD_MODE="Debug"
  PBXPROJ_TARGET_UUID="1C23BC312F62C3DC00D572F8"
  PBXPROJ_TARGET_NAME="Debug"
  log "【Debug 模式】iOS native API base URL: $IOS_API_BASE_URL (source: scutil LocalHostName)"
fi

# ============================================================
# 3. 刷新 project.pbxproj 中的 API 配置（按模式精确更新对应块）
# ============================================================

# pbxproj 配置块 UUID：
#   Debug  : 1C23BC312F62C3DC00D572F8
#   Release: 1C23BC322F62C3DC00D572F8
#
# 策略：
#   Debug  模式：只更新 Debug  块（1C23BC312F62C3DC00D572F8）
#   Release 模式：只更新 Release 块（1C23BC322F62C3DC00D572F8）
#
# 使用 Python 精确替换，避免误伤其他配置块

if command -v python3 >/dev/null 2>&1; then
  python3 - "$IOS_PROJECT_FILE" "$IOS_API_BASE_URL" "$PBXPROJ_TARGET_UUID" "$PBXPROJ_TARGET_NAME" <<'PYEOF'
import sys
import re

filepath = sys.argv[1]
new_url = sys.argv[2]
target_uuid = sys.argv[3]
target_name = sys.argv[4]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到目标配置块（通过 UUID + name 定位）
# 块结构: UUID /* Name */ = { ... name = Name; }
block_pattern = re.compile(
    r'(' + re.escape(target_uuid) + r' /\* ' + target_name + r' \*/ = \{.*?name = ' + target_name + r';\s*\};)',
    re.DOTALL
)
block_match = block_pattern.search(content)

if block_match:
    block = block_match.group(1)
    # 只替换目标块中的 INFOPLIST_KEY_EDUMIND_API_BASE_URL
    # Support both quoted values and legacy placeholders like __DEBUG_DYNAMIC__ (unquoted).
    new_block = re.sub(
        r'(INFOPLIST_KEY_EDUMIND_API_BASE_URL = )(?:"[^"]*"|[^;]+)',
        r'\1"' + new_url + '"',
        block
    )
    content = content[:block_match.start()] + new_block + content[block_match.end():]
    print(f"[ios:sync] 已更新 {target_name} 配置块（UUID {target_uuid}）中的 API_BASE_URL -> {new_url}")
else:
    print(f"[ios:sync][warn] 未找到 {target_name} 配置块（UUID {target_uuid}），跳过 pbxproj 更新")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"[ios:sync] pbxproj 已更新（模式: {target_name}）")
PYEOF
else
  fail "python3 未找到，无法精确更新 pbxproj。请安装 Python 3。"
fi

# ============================================================
# 4. 构建前端 H5
# ============================================================
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

log "执行 mobile-frontend iOS 构建（mode=ios）"
npm run build:ios

# ============================================================
# 5. 同步构建产物到 iOS WebAssets
# ============================================================
mkdir -p "$WEB_ASSETS_DIR"
log "同步 dist/ -> $WEB_ASSETS_DIR"
rsync -a --delete "$MOBILE_DIR/dist/" "$WEB_ASSETS_DIR/"

for required_asset in index.html index.js index.css; do
  if [ ! -f "$WEB_ASSETS_DIR/$required_asset" ]; then
    fail "同步完成但缺少关键产物：$WEB_ASSETS_DIR/$required_asset。请检查 mobile-frontend/vite.config.js 的 iOS 构建输出。"
  fi
done

log "=============================================="
log "同步完成"
log "  模式:        $BUILD_MODE"
log "  API Base:   $IOS_API_BASE_URL"
log "  WebAssets:  $WEB_ASSETS_DIR"
log "=============================================="
if [ "$IS_RELEASE" = true ]; then
  log "【重要】project.pbxproj Release 配置已更新为: $IOS_API_BASE_URL"
  log "【重要】若需回滚 Debug 模式，运行: $0（不带 --release）"
fi
