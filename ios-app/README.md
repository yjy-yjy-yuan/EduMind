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

开发阶段可以直接访问本机或局域网的 Vite dev server，发布阶段则加载打包到应用内的静态资源。

#### 开发阶段示例（指向 dev server）

```swift
let webView = WKWebView(frame: view.bounds)
webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
view.addSubview(webView)

if let url = URL(string: "http://127.0.0.1:5173") {
    webView.load(URLRequest(url: url))
}
```

#### 发布阶段示例（加载打包资源）

先在仓库根目录构建移动端 H5：

```bash
cd mobile-frontend
npm install
npm run build
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

- 开发阶段：直接复用 dev server 环境配置；
- 发布阶段：推荐在构建前写入生产环境的 API 地址，或通过 URL 查询参数/本地配置文件传入。

### 4. 一键同步命令

已提供脚本：

```bash
bash ios-app/sync_ios_web_assets.sh
```

该脚本会自动执行：

1. `mobile-frontend` 执行 `npm run build:ios`（使用 `./assets` 相对路径，适配 `loadFileURL`）
2. 同步 `dist/` 到 `ios-app/EduMindIOS/EduMindIOS/WebAssets/`

### 5. 命令行编译（可选）

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
xcodebuild -project ios-app/EduMindIOS/EduMindIOS.xcodeproj \
  -scheme EduMindIOS \
  -destination 'generic/platform=iOS Simulator' \
  build
```
