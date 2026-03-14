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

### iOS 白屏兼容补丁（补充）
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：构建阶段默认改为相对资源路径（`./`），仅 `web` 模式保留绝对路径，避免 `file://` 容器加载 `/assets/*` 失败白屏。
- 更新 [`mobile-frontend/package.json`](/Users/yuan/final-work/EduMind/mobile-frontend/package.json)：新增 `build:web`、`build:android` 脚本，明确 Web 与原生容器构建用途。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：加载 `index.html` 时自动把 `src="/..."`、`href="/..."` 归一化为相对路径，兼容旧构建产物，降低二次白屏概率。
- 更新 [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)、[`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：构建命令统一指向 `build:ios`（容器）与 `build:web`（网页部署），避免命令误用。

### 对 2026-03-13 记录的更正说明
- 更正 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：撤回“优先 `loadHTMLString` 注入修正路径”的策略，恢复 `loadFileURL` 主路径加载；当检测到旧版绝对资源路径（`/assets/...`）时改为给出明确重建提示，避免脚本模块在 WebView 中被拦截后继续白屏。
- 更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)、[`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：`file://` 场景从 `memory history` 改为 `hash history`，并在 `router.isReady()` 后再挂载应用，修复本地资源模式下可能出现的初始路由空渲染。

### iOS 强制更新能力（无需卸载）
- 更新 [`ios-app/EduMindIOS/EduMindIOS/EduMindIOSApp.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/EduMindIOSApp.swift)：新增启动期强制更新检查（远端清单 + 版本判定），命中后全屏拦截并仅允许跳转更新链接，避免通过“卸载重装”来升级。
- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：新增 `INFOPLIST_KEY_EDUMIND_UPDATE_MANIFEST_URL` 配置项，用于注入更新清单地址。
- 更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：补充强制更新配置说明、清单 JSON 示例与判定规则。

### 移动端 UI 重构（主流程页面）
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)、[`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：重建全局视觉变量、背景装饰与底部导航样式，统一为清晰高对比的新设计语言。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：在不改业务逻辑前提下重构主流程页的版式层级、卡片视觉、状态标签和操作按钮风格。
- 更新 [`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)、[`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)、[`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)、[`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)、[`mobile-frontend/src/views/Knowledge.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Knowledge.vue)、[`mobile-frontend/src/views/LearningPath.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LearningPath.vue)：补齐辅助页面视觉一致性，避免页面风格断层。

### iOS 白屏可观测性与路由回退修复
- 更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)：`file://` 场景回退到 `createMemoryHistory` 并显式 `replace('/')`，降低 WebView 对 hash/history 差异导致的空白首屏风险。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：为 `WKWebView` 增加导航失败处理、JS 错误桥接日志和加载超时兜底页，避免“纯白无报错”并提升定位效率。

### 移动端 UI-only 构建模式（仅界面，预留接口）
- 新增 [`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：提供认证、视频、笔记、问答的本地 mock 数据与占位响应，保持与真实接口兼容的返回结构。
- 更新 [`mobile-frontend/src/config/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/config/index.js)：新增 `UI_ONLY_MODE` 配置，支持环境变量 `VITE_MOBILE_UI_ONLY` 和 URL 参数 `uiOnly` 覆盖（默认开启）。
- 更新 [`mobile-frontend/src/api/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/auth.js)、[`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/api/note.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/note.js)、[`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)：统一接入 UI-only/真实后端双通道，当前阶段仅构建 UI 时可直接运行。
- 更新 [`mobile-frontend/.env.example`](/Users/yuan/final-work/EduMind/mobile-frontend/.env.example)、[`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)：补充 UI-only 默认配置与切换说明。

### iOS 预览链路与白屏诊断增强
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：新增 `WKWebView` 挂载看门狗与更详细的 `NSLog` 日志；当 `index.html` 已加载但前端根节点未挂载时，页面内直接显示诊断提示，不再只有纯白屏。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：将 `#Preview` 宏改为 `PreviewProvider`，规避当前 Xcode 预览插件链路异常对调试结果的干扰。

### 移动端 UI-only 边界收口
- 更新 [`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：`UI_ONLY_MODE` 下改为纯界面播放器占位，不再在页面层依赖真实视频流与字幕资源。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：移除真实预览图依赖，改为状态驱动的本地封面占位卡片，保持详情页完整 UI 流程。
- 更新 [`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)、[`mobile-frontend/src/views/Knowledge.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Knowledge.vue)、[`mobile-frontend/src/views/LearningPath.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LearningPath.vue)：统一文案为“当前仅实现 UI 与占位交互，后续通过预留接口接入真实能力”，避免页面描述与当前开发阶段不一致。

### iOS 本地资源启动兼容与启动日志增强
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：`ios` 构建改为单文件 IIFE 入口并在构建后把 `index.html` 重写为经典脚本标签，规避 `file://` 场景下 `type="module"` 在 `WKWebView` 中不执行的问题；样式文件名固定为 `index.css`。
- 更新 [`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)：移除 `workflow.svg` 资源依赖，改为纯 DOM/CSS 流程图，避免构建产物继续生成 `import.meta.url`。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：新增 `__edumindBootTrace` 启动轨迹、关键阶段 `console.log` 与全局异常 trace，便于定位前端启动卡点。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：增强 `WKWebView` 控制台桥接，新增原生 boot probe，输出 `readyState`、`#app` 子节点数、前端启动标记和最近 boot trace，便于在 Xcode 控制台精确定位启动失败位置。

### iOS UI-only 本地加载链路收口
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：iOS 产物的入口脚本改为 `defer` 经典脚本，避免 `index.js` 在 `#app` 还未解析完成时抢跑，修复真机 `file://` 场景下的空挂载。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：新增 `DOMContentLoaded`、`window.load`、挂载前后容器状态与 `requestAnimationFrame` 日志，并在真正完成首帧检查后再标记 `bootMounted`。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：移除 dev server 加载分支，iOS 容器固定只加载包内 `WebAssets/index.html`；同步修正 watchdog 提示文案与 probe 容错。
- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：移除 `INFOPLIST_KEY_EDUMIND_DEV_SERVER_URL` 预留项，避免后续误切到 `5173` 路径。
- 更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)、[`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)、[`docs/MOBILE_MODULE_PROMPTS.md`](/Users/yuan/final-work/EduMind/docs/MOBILE_MODULE_PROMPTS.md)：文档统一为“当前 iOS 仅加载本地静态 UI 资源”，消除旧版 `5173` 示例带来的误导。

### 移动端页面适配与字体优化
- 更新 [`mobile-frontend/index.html`](/Users/yuan/final-work/EduMind/mobile-frontend/index.html)：补充移动端 viewport 限制，关闭双击缩放与用户缩放，并禁用电话/邮箱自动识别，避免真机页面误放大与排版抖动。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：重建全局字体栈为 `SF Pro Text/Display + PingFang SC`，统一正文与标题字重、字距、行高；同时补充 `100% text-size-adjust`、流式边距、媒体元素自适应和小屏幕断点，修复页面贴边、挤压和横向溢出问题。
- 更新 [`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：外层壳布局改为 `100dvh` 移动端高度模型，并收紧内容区与背景装饰在小屏设备上的占位，提升 iPhone 真机上的首屏适配性与观感一致性。
