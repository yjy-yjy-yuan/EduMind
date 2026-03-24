#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_PATH="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj"
SCHEME_NAME="EduMindIOS"
CONFIGURATION="${BLITZ_IOS_CONFIGURATION:-Debug}"
DESTINATION="${BLITZ_IOS_DESTINATION:-generic/platform=iOS Simulator}"
DERIVED_DATA_PATH="${BLITZ_IOS_DERIVED_DATA:-$REPO_DIR/.xcode-derived}"
BUILD_LOG_PATH="$DERIVED_DATA_PATH/blitz-ios-build.log"

log() {
  echo "[blitz:ios-build] $*"
}

fail() {
  echo "[blitz:ios-build][error] $*" >&2
  exit 1
}

command -v xcodebuild >/dev/null 2>&1 || fail "未找到 xcodebuild，请先安装 Xcode 并完成首次启动。"
[ -d "$PROJECT_PATH" ] || fail "未找到 iOS 工程：$PROJECT_PATH"

mkdir -p "$DERIVED_DATA_PATH"

log "开始构建 iOS 工程"
log "project=$PROJECT_PATH"
log "scheme=$SCHEME_NAME"
log "destination=$DESTINATION"
log "derivedData=$DERIVED_DATA_PATH"

set +e
xcodebuild \
  -project "$PROJECT_PATH" \
  -scheme "$SCHEME_NAME" \
  -configuration "$CONFIGURATION" \
  -destination "$DESTINATION" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  build 2>&1 | tee "$BUILD_LOG_PATH"
BUILD_EXIT_CODE=${PIPESTATUS[0]}
set -e

if [ "$BUILD_EXIT_CODE" -ne 0 ]; then
  fail "iOS 构建失败。请查看日志：$BUILD_LOG_PATH"
fi

log "iOS 构建成功。日志：$BUILD_LOG_PATH"
