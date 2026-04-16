#!/usr/bin/env bash
#
# EduMind iOS 构建验证脚本
#
# 用法:
#   bash ios-app/validate_ios_build.sh              # Debug 模式（默认）
#   bash ios-app/validate_ios_build.sh --release     # Release/TestFlight 模式
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_PATH="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj"
SCHEME_NAME="EduMindIOS"
DERIVED_DATA_PATH="$REPO_DIR/.xcode-derived"
BUILD_LOG_PATH="$DERIVED_DATA_PATH/ios-build.log"

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
      echo "  --release    Release/TestFlight 模式，使用 Release 配置和固定域名"
      echo ""
      echo "环境变量:"
      echo "  FIXED_DOMAIN       固定后端域名（--release 模式必须设置，如 https://api.xxx.com）"
      echo "  EDUMIND_IOS_VALIDATE_DESTINATION    xcodebuild -destination 参数（默认 generic/platform=iOS）"
      exit 0
      ;;
    *)
      echo "[ios:validate][warn] 未知参数: $1，忽略"
      shift
      ;;
  esac
done

DESTINATION="${EDUMIND_IOS_VALIDATE_DESTINATION:-generic/platform=iOS}"

info() {
  echo "[ios:validate] $*"
}

fail() {
  echo "[ios:validate][error] $*" >&2
  exit 1
}

if ! command -v xcodebuild >/dev/null 2>&1; then
  fail "xcodebuild 不可用，请先安装 Xcode 并完成首次启动。"
fi

if [ ! -d "$PROJECT_PATH" ]; then
  fail "未找到 iOS 工程：$PROJECT_PATH"
fi

# ============================================================
# 1. 同步 WebAssets（调用 sync 脚本，同步 Debug/Release 模式）
# ============================================================
info "==> 同步 WebAssets（模式: $([ "$IS_RELEASE" = true ] && echo "Release" || echo "Debug")）"

if [ "$IS_RELEASE" = true ]; then
  if [ -z "${FIXED_DOMAIN:-}" ]; then
    fail "Release 模式必须设置 FIXED_DOMAIN 环境变量，如: FIXED_DOMAIN=https://api.xxx.com $0 --release"
  fi
  info "Release 模式: FIXED_DOMAIN=$FIXED_DOMAIN"
  bash "$REPO_DIR/ios-app/sync_ios_web_assets.sh" --release
else
  bash "$REPO_DIR/ios-app/sync_ios_web_assets.sh"
fi

# ============================================================
# 2. 验证屏幕方向配置
# ============================================================
info "==> 验证屏幕方向配置"
ORIENTATION_CONFIG=$(rg -o 'UISupportedInterfaceOrientations[^;]*;' "$PROJECT_PATH/project.pbxproj" | head -2)
if echo "$ORIENTATION_CONFIG" | rg -q "LandscapeLeft|LandscapeRight"; then
  info "警告: 检测到 UISupportedInterfaceOrientations 包含横屏方向，当前应仅支持竖屏"
  info "配置内容: $ORIENTATION_CONFIG"
  exit 1
else
  info "屏幕方向配置正确: 仅支持竖屏 (Portrait)"
fi

# ============================================================
# 3. 构建 iOS 工程
# ============================================================
BUILD_CONFIGURATION=$([ "$IS_RELEASE" = true ] && echo "Release" || echo "Debug")
info "==> 构建 iOS 工程 (configuration: $BUILD_CONFIGURATION)"

mkdir -p "$DERIVED_DATA_PATH"

set +e
xcodebuild \
  -project "$PROJECT_PATH" \
  -scheme "$SCHEME_NAME" \
  -configuration "$BUILD_CONFIGURATION" \
  -destination "$DESTINATION" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGN_IDENTITY="" \
  build 2>&1 | tee "$BUILD_LOG_PATH"
BUILD_EXIT_CODE=${PIPESTATUS[0]}
set -e

if [ "$BUILD_EXIT_CODE" -eq 0 ]; then
  info ""
  info "iOS 构建成功！"
  info "  配置:       $BUILD_CONFIGURATION"
  info "  产物目录:  $DERIVED_DATA_PATH/Build/Products/$BUILD_CONFIGURATION-iphoneos"
  if [ "$IS_RELEASE" = true ]; then
    info "  API Base:   $FIXED_DOMAIN"
    info "  【重要】此为无签名校验构建；如需上传 TestFlight，请在 Xcode 中配置签名后重新构建。"
  else
    info "  API Base:   Debug 本机联调模式"
    info "  【重要】此为无签名 Debug 校验构建；如需真机安装，请在 Xcode 中配置 Team / 描述文件。"
  fi
  exit 0
fi

# ============================================================
# 4. 构建失败诊断
# ============================================================
info ""
info "iOS 构建失败（exit $BUILD_EXIT_CODE）。常见原因："

if rg -q "No profiles for|requires a provisioning profile|No Accounts|signing" "$BUILD_LOG_PATH" 2>/dev/null; then
  info "- 签名错误：默认已禁用签名，仅用于验证本地可编译性。若需签名，构建时请配置 Team。"
fi

if rg -q "No available simulator runtimes|CoreSimulatorService connection became invalid|simdiskimaged" "$BUILD_LOG_PATH" 2>/dev/null; then
  info "- CoreSimulator/运行时异常：请先手动启动一次 Xcode 和 Simulator，确认 Xcode 完成组件安装。"
fi

if rg -q "actool" "$BUILD_LOG_PATH" 2>/dev/null; then
  info "- 资源编译异常：优先检查 Xcode 是否首次启动未完成初始化，或系统组件权限受限。"
fi

if rg -q "cannot open file.*\.swift" "$BUILD_LOG_PATH" 2>/dev/null; then
  info "- Swift 源文件无法打开：确认 ContentView.swift 等文件存在且路径正确。"
fi

info "- 完整日志：$BUILD_LOG_PATH"
exit "$BUILD_EXIT_CODE"
