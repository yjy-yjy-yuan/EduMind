# 变更日志

## 2026-03-11

### 文档对齐
- 重写 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：按当前仓库结构更新为 `backend_fastapi`、`mobile-frontend` 方案。
- 重写 [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：移除旧项目名与过时说明，统一为当前 FastAPI 主后端。
- 重写 [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)：统一运行步骤、环境名和启动命令。
- 重写 [`README_test.md`](/Users/yuan/final-work/EduMind/README_test.md)：修正测试入口与命令示例。

## 2026-03-12

### 移动端 iOS 风格首页改版
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：重设全局色板与视觉变量，改为自然活泼的绿色系风格，并补充 iOS 页面容器与卡片基础样式。
- 更新 [`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：增加背景装饰层与统一页面承载结构，优化移动端沉浸感。
- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：重做底部导航为磨砂悬浮样式，替换为统一 SVG 图标并强化激活态。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：按功能模块重新布局首页（欢迎区、快捷功能矩阵、最近学习内容），保留原有接口逻辑并升级视觉层级。

### 移除 Android、改为仅支持 iOS
- 删除 `android-app/` 目录下全部工程与配置文件（Gradle、Manifest、资源等），仓库不再包含 Android 构建。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：仓库结构改为 `ios-app/`，移除“构建 Android 容器”章节，改为可选 iOS 容器（Xcode + WKWebView）说明。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)：移除对 `android-app/` 与 Android 构建的说明；新增变更日志规范（仅追加 `CHANGELOG.md` 条目、不修改历史）。
- 更新 [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)：将“Android 配合方式”改为“以 iOS 为主的原生容器配合方式”。
- 更新 [`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)：去掉 Android 相关提示文案，改为通用/与 iOS 兼容表述。
- 更新 [`docs/MOBILE_MODULE_PROMPTS.md`](/Users/yuan/final-work/EduMind/docs/MOBILE_MODULE_PROMPTS.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：移除 `android-app` 与 Android 配置，统一为 iOS/`ios-app` 与 WKWebView 说明。
- 移除 `.gitignore`、`.gitignore.new` 中的 Android 相关忽略规则。
- 新增 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：iOS 容器目录说明与 WKWebView 加载 H5 的示例（开发期 dev server、发布期打包资源）。

### Xcode 与运行环境
- 使用 Xcode 连接虚拟机，便于在模拟器/真机上调试 iOS 应用。

## 2026-03-13

### iOS 空白页修复
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：`ios` 模式增加 `build.assetsDir = ''`，避免 Xcode 复制资源平铺后导致 `index.html` 仍引用 `./assets/*` 而白屏。
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：`ios` 模式输出改为固定文件名（如 `index.js`、`index.css`），避免哈希文件名变化引发容器资源引用错位。
- 更新 [`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)、[`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)、[`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：移除 `filter/backdrop-filter` 相关样式，降低 iOS 26.x 模拟器 WebKit GPU 进程崩溃概率。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：`WKWebView` 资源查找新增“`WebAssets` 子目录 + 根目录”双路径兜底，提升加载成功率并在资源缺失时显示明确提示。
- 更新 [`mobile-frontend/src/utils/storage.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/utils/storage.js)（新增）并接入 [`mobile-frontend/src/store/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/store/auth.js)、[`mobile-frontend/src/utils/request.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/utils/request.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：为 `localStorage` 提供内存降级，避免 `file://` / WebView 安全限制导致启动即崩溃。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：增加全局启动异常捕获与页面内错误展示，避免“空白无提示”。
- 远程仓库调整：主仓将 `origin` 切换为 GitHub，保留 Gitee 为 `gitee` 备用远程。
