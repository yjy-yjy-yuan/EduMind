#!/bin/bash
set -e

# 检查是否指定了固定域名
if [ -z "$FIXED_DOMAIN" ]; then
  echo "错误: 必须指定 FIXED_DOMAIN 环境变量"
  echo "用法: FIXED_DOMAIN=https://api.xxx.com bash ios-app/build_release_ipa.sh"
  exit 1
fi

echo "🔨 开始构建 EduMind iOS Release 版本..."

# 1. 同步前端资源（Release 模式）
echo "📦 构建前端资源..."
cd "$(dirname "$0")/.."
FIXED_DOMAIN="$FIXED_DOMAIN" bash ios-app/sync_ios_web_assets.sh --release

# 2. 构建并归档
echo "🔧 使用 Xcode 构建并归档..."
cd ios-app/EduMindIOS

# 清理旧构建
xcodebuild clean \
  -project EduMindIOS.xcodeproj \
  -scheme EduMindIOS \
  -configuration Release

# 构建并归档
ARCHIVE_PATH="$PWD/build/EduMindIOS.xcarchive"
xcodebuild archive \
  -project EduMindIOS.xcodeproj \
  -scheme EduMindIOS \
  -configuration Release \
  -archivePath "$ARCHIVE_PATH" \
  -destination 'generic/platform=iOS'

# 3. 创建 export.plist（使用 ad-hoc 签名）
echo "📱 创建导出配置..."
EXPORT_PLIST="$PWD/build/export_options.plist"

cat > "$EXPORT_PLIST" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>development</string>
    <key>compileBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <false/>
    <key>signingStyle</key>
    <string>automatic</string>
</dict>
</plist>
EOF

# 4. 导出 IPA
IPA_PATH="$PWD/build/EduMindIOS.ipa"
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$PWD/build" \
  -exportOptionsPlist "$EXPORT_PLIST"

echo "✅ 构建完成！IPA 文件位置: $IPA_PATH"
echo ""
echo "📌 接下来的步骤："
echo "   1. 上传 IPA 到 GitHub Release 或其他文件托管"
echo "   2. 用户通过 AltStore 安装: https://altstore.io/"
echo "   3. 安装教程见: https://altstore.io/faq/"
