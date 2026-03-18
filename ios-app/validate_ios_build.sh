#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_PATH="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj"
SCHEME_NAME="EduMindIOS"
DERIVED_DATA_PATH="$REPO_DIR/.xcode-derived"
BUILD_LOG_PATH="$DERIVED_DATA_PATH/ios-build.log"

mkdir -p "$DERIVED_DATA_PATH"

if ! command -v xcodebuild >/dev/null 2>&1; then
  echo "xcodebuild 不可用，请先安装 Xcode 并完成首次启动。"
  exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
  echo "未找到 iOS 工程：$PROJECT_PATH"
  exit 1
fi

echo "==> Sync latest WebAssets"
bash "$REPO_DIR/ios-app/sync_ios_web_assets.sh"

echo "==> Build iOS project"
set +e
xcodebuild \
  -project "$PROJECT_PATH" \
  -scheme "$SCHEME_NAME" \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  -allowProvisioningUpdates \
  build 2>&1 | tee "$BUILD_LOG_PATH"
BUILD_EXIT_CODE=${PIPESTATUS[0]}
set -e

if [ "$BUILD_EXIT_CODE" -eq 0 ]; then
  echo
  echo "iOS 构建成功。产物目录：$DERIVED_DATA_PATH/Build/Products/Debug-iphoneos"
  exit 0
fi

echo
echo "iOS 构建失败。常见原因："

if rg -q "No profiles for|requires a provisioning profile|signing" "$BUILD_LOG_PATH"; then
  echo "- 签名或描述文件未就绪：请在 Xcode 中打开工程，确认已登录 Apple ID，并为 target 选择可用 Team。"
fi

if rg -q "No available simulator runtimes|CoreSimulatorService connection became invalid|simdiskimaged" "$BUILD_LOG_PATH"; then
  echo "- CoreSimulator/运行时异常：请先手动启动一次 Xcode 和 Simulator，确认 Xcode 完成组件安装。"
fi

if rg -q "actool" "$BUILD_LOG_PATH"; then
  echo "- 资源编译异常：优先检查 Xcode 是否首次启动未完成初始化，或系统组件权限受限。"
fi

echo "- 完整日志：$BUILD_LOG_PATH"
exit "$BUILD_EXIT_CODE"
