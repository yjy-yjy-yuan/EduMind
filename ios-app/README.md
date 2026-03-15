## EduMind iOS 容器（建议结构）

本目录推荐用于存放 iOS 原生工程（使用 Xcode 创建），通过 `WKWebView` 加载 `mobile-frontend` 构建出的 H5 页面。

### 1. 推荐目录结构

```text
ios-app/
├── sync_ios_web_assets.sh      # 一键构建并同步 H5 资源到 iOS 工程
├── EduMindIOS/                 # Xcode 工程目录（由 Xcode 创建）
│   ├── EduMindIOS.xcodeproj
│   ├── EduMindIOS/
│   │   ├── EduMindIOSApp.swift
│   │   ├── ContentView.swift   # 已改为 WKWebView 容器
│   │   ├── WebAssets/          # 打包后的 H5 静态资源
│   └── Assets.xcassets
└── README.md                   # 本说明
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

- 当前 UI-only 阶段：默认 `VITE_MOBILE_UI_ONLY=true`，页面走本地 mock 数据，不依赖后端；
- 后续接入真实接口时：推荐在构建前写入生产/测试 API 地址，或通过 URL 查询参数/本地配置文件传入。

### 4. 强制更新（无需卸载 App）

iOS 容器已支持“强制更新拦截”：

1. 启动时会读取 Info.plist 配置键 `EDUMIND_UPDATE_MANIFEST_URL`
2. 若该地址返回的清单命中强更条件，会展示全屏拦截层，只允许“立即更新”
3. 点击“立即更新”会跳转 `update_url`（如 App Store 链接或企业分发链接）

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

已提供脚本：

```bash
bash ios-app/sync_ios_web_assets.sh
```

该脚本会自动执行：

1. `mobile-frontend` 执行 `npm run build:ios`（生成相对路径资源，适配 `loadFileURL`）
2. 同步 `dist/` 到 `ios-app/EduMindIOS/EduMindIOS/WebAssets/`

### 6. 命令行编译（可选）

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
xcodebuild -project ios-app/EduMindIOS/EduMindIOS.xcodeproj \
  -scheme EduMindIOS \
  -destination 'generic/platform=iOS Simulator' \
  build
```

### 7. 视频上传权限说明

iOS 容器当前依赖 `WKWebView` 默认文件选择能力。由于 iPhone 上点击视频上传控件时，系统可能同时提供“拍摄视频 / 相册 / 文件”等入口，因此工程必须保留以下隐私说明，避免上传视频时触发系统权限崩溃：

- `NSCameraUsageDescription`
- `NSMicrophoneUsageDescription`
- `NSPhotoLibraryUsageDescription`

移动端 H5 侧也已将上传控件的 `accept` 从 `video/*` 收敛为明确的视频扩展名列表，以降低系统直接走相机分支的概率；如果后续恢复媒体通配类型或接入拍摄视频，不要删除这些键。
