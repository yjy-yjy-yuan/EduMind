## EduMind iOS 容器（建议结构）

本目录推荐用于存放 iOS 原生工程（使用 Xcode 创建），通过 `WKWebView` 加载 `mobile-frontend` 构建出的 H5 页面。

### 1. 推荐目录结构

```text
ios-app/
├── sync_ios_web_assets.sh      # 一键构建并同步 H5 资源到 iOS 工程（支持 Debug/Release 双通道）
├── EduMindIOS/                 # Xcode 工程目录（由 Xcode 创建）
│   ├── EduMindIOS.xcodeproj
│   ├── EduMindIOS/
│   │   ├── EduMindIOSApp.swift
│   │   ├── ContentView.swift   # 已改为 WKWebView 容器
│   │   ├── WebAssets/          # 打包后的 H5 静态资源
│   │   └── Assets.xcassets
│   └── README.md               # 本说明
```

### 2. WebView 加载策略

当前 iOS 容器固定加载打包到应用内的静态资源，不再依赖 dev server。这样可以避免 `WKWebView` 因网络、代理或局域网地址漂移导致的白屏。

#### 本地资源加载示例

先在仓库根目录构建移动端 H5：

```bash
cd mobile-frontend
npm install
npm run build:ios
```

然后将 `mobile-frontend/dist/` 目录内容拷贝到 Xcode 工程中，勾选「Copy items if needed」并加入应用 Bundle，例如放到 `WebAssets/` 目录。

Swift 端加载本地 `index.html` 的示例：

```swift
if let indexURL = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "WebAssets") {
    webView.loadFileURL(indexURL, allowingReadAccessTo: indexURL.deletingLastPathComponent())
}
```

### 3. API 基地址配置

`mobile-frontend` 默认通过环境变量（如 `VITE_MOBILE_API_BASE_URL`）访问 FastAPI 后端。
在 iOS WebView 中：

- H5 启动时会优先读取原生注入的 `window.__edumindNativeConfig.apiBaseUrl`；
- 原生注入值来自 Info.plist / Build Settings 中的 `EDUMIND_API_BASE_URL`；
- 若 H5 本地还没有保存过后端地址，会自动把该值落到 `localStorage`，首次安装也能直接连到 FastAPI；
- 若换了 Wi‑Fi 或 Mac 局域网 IP 变化，仍可在"我的"页面手动覆盖。

**【重要】双通道配置说明**

| 通道 | 用途 | API 地址来源 |
|------|------|-------------|
| Debug | 本地开发联调 | `sync_ios_web_assets.sh` 动态注入本机 `LocalHostName.local` |
| Release / TestFlight | App Store / TestFlight 分发 | `project.pbxproj` Release 配置（已预置固定域名） |

`project.pbxproj` 配置现状：

```
Debug 配置（UUID: 1C23BC312F62C3DC00D572F8）:
  INFOPLIST_KEY_EDUMIND_API_BASE_URL = "__DEBUG_DYNAMIC__"
  （由 sync_ios_web_assets.sh 动态注入）

Release 配置（UUID: 1C23BC322F62C3DC00D572F8）:
  INFOPLIST_KEY_EDUMIND_API_BASE_URL = "https://api.xxx.com"
  （已预置固定域名，脚本不覆盖）
```

**使用方式：**

- **本地 Debug 开发**：`bash ios-app/sync_ios_web_assets.sh`（默认 Debug 模式，自动注入本机 LocalHostName）
- **Release / TestFlight 打包**：`FIXED_DOMAIN=https://api.xxx.com bash ios-app/sync_ios_web_assets.sh --release`

详细配置说明见 [`docs/BACKEND_FIXED_DOMAIN.md`](docs/BACKEND_FIXED_DOMAIN.md)。

### 4. 强制更新（无需卸载 App）

iOS 容器已支持"强制更新拦截"：

1. 启动时会读取 Info.plist 配置键 `EDUMIND_UPDATE_MANIFEST_URL`
2. 若该地址返回的清单命中强更条件，会展示全屏拦截层，只允许"立即更新"
3. 点击"立即更新"会跳转 `update_url`（如 App Store 链接或企业分发链接）

当前工程已在 Build Settings 中预留：

- `INFOPLIST_KEY_EDUMIND_UPDATE_MANIFEST_URL = ""`

你只需要在 Xcode 的 Target Build Settings 里把它改成实际清单 URL（建议 HTTPS）。

清单示例（JSON）：

```json
{
  "force_update": true,
  "latest_version": "1.2.0",
  "latest_build": 12,
  "min_supported_build": 10,
  "update_url": "itms-apps://itunes.apple.com/app/id1234567890",
  "title": "发现新版本",
  "message": "当前版本已停止支持，请立即更新后继续使用。",
  "button_text": "立即更新"
}
```

判定规则：

- 当前 `build < min_supported_build` 时，强制更新
- 或 `force_update=true` 且存在更高版本（`latest_build`/`latest_version`）时，强制更新
- 未配置 `EDUMIND_UPDATE_MANIFEST_URL` 时，不会阻塞启动

### 5. 一键同步命令

已提供脚本（支持 Debug/Release 双通道）：

```bash
# Debug 模式（默认）：联调本机后端
bash ios-app/sync_ios_web_assets.sh

# Release/TestFlight 模式：使用固定域名
FIXED_DOMAIN=https://api.xxx.com bash ios-app/sync_ios_web_assets.sh --release
```

Debug 模式脚本会自动执行：

1. 读取 `../edumind-backend/.env` 里的 `PORT`
2. 读取当前 Mac 的 `LocalHostName`
3. 将 `EDUMIND_API_BASE_URL` 刷新成 `http://<LocalHostName>.local:<PORT>`
4. 再同步最新 `mobile-frontend/dist` 到 `WebAssets`

Release 模式脚本会：

1. 验证 FIXED_DOMAIN 不含 `.local` / `127.0.0.1` / 私网 IP / 占位符域名（安全检查）
2. 将 `EDUMIND_API_BASE_URL` 刷新成 `FIXED_DOMAIN`（仅 Release 块，不影响 Debug 配置）
3. 执行前端构建
4. 同步产物到 WebAssets

### 6. 命令行编译（可选）

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
xcodebuild -project ios-app/EduMindIOS/EduMindIOS.xcodeproj \
  -scheme EduMindIOS \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  build
```

如果你要连同前端资源同步和构建日志一起做一遍本地校验，可直接执行：

```bash
# Debug 验证（本地联调）
bash ios-app/validate_ios_build.sh

# Release 验证（TestFlight 准备）
# validate_ios_build.sh --release 会：
#   a. 调用 sync_ios_web_assets.sh --release（真正更新 Release UUID）
#   b. 执行 xcodebuild -configuration Release
#   c. 若 FIXED_DOMAIN 含占位符域名，自动失败
FIXED_DOMAIN=https://api.xxx.com bash ios-app/validate_ios_build.sh --release
```

说明：

- `validate_ios_build.sh` 的目标是验证当前仓库代码和 `WKWebView` 资源能否成功编译，不要求本机已登录 Apple ID
- 如果你要做真机安装或归档，再在 Xcode 里单独配置 Team / 描述文件并执行签名构建

### 7. 视频上传权限说明

iOS 容器当前依赖 `WKWebView` 默认文件选择能力。由于 iPhone 上点击视频上传控件时，系统可能同时提供"拍摄视频 / 相册 / 文件"等入口，因此工程必须保留以下隐私说明，避免上传视频时触发系统权限崩溃：

- `NSCameraUsageDescription`
- `NSLocalNetworkUsageDescription`
- `NSMicrophoneUsageDescription`
- `NSPhotoLibraryUsageDescription`

移动端 H5 侧也已将上传控件的 `accept` 从 `video/*` 收敛为明确的视频扩展名列表，以降低系统直接走相机分支的概率；如果后续恢复媒体通配类型或接入拍摄视频，不要删除这些键。
