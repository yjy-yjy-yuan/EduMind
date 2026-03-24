#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_PATH="$REPO_DIR/ios-app/EduMindIOS/EduMindIOS.xcodeproj"
SCHEME_NAME="EduMindIOS"
DERIVED_DATA_PATH="$REPO_DIR/.xcode-derived"
BUILD_LOG_PATH="$DERIVED_DATA_PATH/ios-build.log"
DESTINATION="${EDUMIND_IOS_VALIDATE_DESTINATION:-generic/platform=iOS}"

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
  -destination "$DESTINATION" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGN_IDENTITY="" \
  build 2>&1 | tee "$BUILD_LOG_PATH"
BUILD_EXIT_CODE=${PIPESTATUS[0]}
set -e

if [ "$BUILD_EXIT_CODE" -eq 0 ]; then
  echo
  echo "iOS 构建成功。产物目录：$DERIVED_DATA_PATH/Build/Products/Debug-iphoneos"
  echo "本次为无签名校验构建；如需真机安装，请在 Xcode 中配置 Team / 描述文件后再执行签名构建。"
  exit 0
fi

echo
echo "iOS 构建失败。常见原因："

if rg -q "No profiles for|requires a provisioning profile|No Accounts|signing" "$BUILD_LOG_PATH"; then
  echo "- 若这里仍出现签名错误，说明工程被外部参数强制走了签名链路；默认校验脚本已禁用签名，仅用于验证本地可编译性。"
fi

if rg -q "No available simulator runtimes|CoreSimulatorService connection became invalid|simdiskimaged" "$BUILD_LOG_PATH"; then
  echo "- CoreSimulator/运行时异常：请先手动启动一次 Xcode 和 Simulator，确认 Xcode 完成组件安装。"
fi

if rg -q "actool" "$BUILD_LOG_PATH"; then
  echo "- 资源编译异常：优先检查 Xcode 是否首次启动未完成初始化，或系统组件权限受限。"
fi

echo "- 完整日志：$BUILD_LOG_PATH"
exit "$BUILD_EXIT_CODE"
