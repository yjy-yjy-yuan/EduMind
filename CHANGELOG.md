# 变更日志

## 2026-03-16

### iOS 真机播放与视频处理链路修复
- 更新 [`backend_fastapi/app/core/executor.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/executor.py)：本地开发默认改用 `ThreadPoolExecutor` 执行后台任务，补充任务完成/异常日志与失败状态回写，修复视频处理任务长时间停留在“已提交，等待处理”的假死问题。
- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)：新增后台任务执行器类型与并发数配置项，便于后续按环境切换。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)：为 Whisper 转录阶段增加持续进度回写与耗时提示，避免长视频在 60% 附近长时间无变化。
- 更新 [`backend_fastapi/.env`](/Users/yuan/final-work/EduMind/backend_fastapi/.env)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)、[`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)：默认 Whisper 模型从 `turbo` 调整为 `base`，避免本地开发因损坏的 `turbo` 缓存触发 1.51GB 模型重下载而长时间卡住。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：处理中视频不再禁用播放按钮，改为允许进入播放器播放原始视频文件。
- 更新 [`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：播放器增加视频处理状态提示，明确当前是否在播放处理中原视频。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：最近上传列表新增自动刷新处理进度条与当前步骤显示，便于真机直接观察后台处理进度。

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

### 上传视频功能联调（按 VIDEO_UPLOAD_IMPLEMENTATION / DATABASE_SETUP / 主提示词）
- 更新 [`mobile-frontend/src/api/video.js`](mobile-frontend/src/api/video.js)：移除上传请求中显式 `Content-Type: multipart/form-data`，由 axios 对 FormData 自动设置 boundary，与后端 `File(...)` 兼容。
- 更新 [`mobile-frontend/.env.example`](mobile-frontend/.env.example)：补充真机=前端、端口连调说明及 `VITE_MOBILE_UI_ONLY` 注释（false 时走真实上传/登录）。
- 更新 [`backend_fastapi/.env.example`](backend_fastapi/.env.example)：补充真机连调说明（HOST=0.0.0.0、CORS 加入本机 IP:5173）。

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

### Xcode 控制台分级日志增强
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：新增基于 `OSLog.Logger` 的原生日志封装，将 `WKWebView` 生命周期、probe、watchdog 和错误输出映射为 `info / debug / notice / error / fault` 分级日志，便于在 Xcode 控制台筛选查看。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：前端通过 `window.webkit.messageHandlers.edumindLog` 回传的 `console.info()`、`console.warn()`、`console.error()` 现在会按级别写入原生控制台，不再全部混成同一种日志。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：补充 `console.info` 启动摘要和挂载成功信息，确保 Xcode 里能直接看到关键 `info` 日志节点。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：新增显式 `DEBUG` 前缀和 `console.debug()` 启动日志，便于在 Xcode 控制台直接搜索 `DEBUG` 查看调试链路。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：将原生与前端桥接日志统一为结构化格式，如 `[DEBUG][Bootstrap] ...`、`[INFO][WebView] ...`、`[ERROR][Router] ...`，降低控制台阅读成本。

### 笔记页交互简化
- 更新 [`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：移除“最近笔记堆叠”区域及其旋转/缩放卡片交互，改为仅保留稳定的普通笔记列表，提升真机点按与滚动操作的可用性。

### 全局背景视觉替换
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：将应用全局背景调整为参考示意图的柔雾渐变风格，以暖米色、淡紫和蜜桃色大面积模糊色块替换原有背景装饰，便于在真机上预览新氛围效果。

### 全局背景视觉调整（冷蓝渐变）
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：将应用背景由暖色柔雾切换为参考示意图的冷蓝抽象渐变风格，使用浅雾蓝底色、青蓝色大面积模糊光斑与右上深蓝主视觉区块，便于真机预览新的整体氛围。

### 全局背景视觉微调（冷蓝渐变二次优化）
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：进一步强化右上深蓝主视觉区、左侧白雾纵向光带和整体卡片透明度，使应用背景更贴近参考图的冷蓝抽象渐变效果。

### 品牌 Logo 接入
- 新增 [`mobile-frontend/src/assets/edumind-logo.svg`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/edumind-logo.svg)、[`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：新增 EduMind 品牌 logo 资源与可复用展示组件。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)：将首页与登录/注册页的品牌展示替换为新的 EduMind logo。

### iOS 原生 App 图标替换
- 更新 [`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json)：为 iOS 18 风格的 light/dark/tinted 三个通用图标位绑定实际文件名。
- 新增 [`AppIcon-1024.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png)、[`AppIcon-1024-dark.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024-dark.png)、[`AppIcon-1024-tinted.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024-tinted.png)：将新的 EduMind logo 写入原生 App 图标资源。

### 对 2026-03-14 App 图标记录的更正说明
- 更正 [`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json)：当前先收敛为单一 1024x1024 主图标 `AppIcon-1024.png`，未继续保留 dark/tinted 变体文件，优先保证原生 App 图标替换稳定生效。

### Logo 布局与渐变文字优化
- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：强化 logo 容器的固定比例与非压缩布局，避免在主页面顶部被按钮或窄屏挤压变形。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：新增全局 `gradient-text` 渐变文字样式。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)：将主标题改为渐变文字，并调整品牌区域布局，避免 logo 出现压缩、挤压。

### 视频上传闭环收口
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/tasks/video_download.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_download.py)、[`backend_fastapi/app/models/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)：本地视频上传改为分块落盘并按 `MAX_CONTENT_LENGTH` 限制体积；链接上传改为立即返回 `downloading` 记录并交由后台任务下载；列表/状态接口补齐 `process_progress`、`current_step`、`error_message`。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/services/videoStatus.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/videoStatus.js)：移动端接入新的下载中状态，链接上传后会在下载完成时自动发起处理，最近上传卡片的状态归一和筛选逻辑同步调整。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`docs/VIDEO_UPLOAD_IMPLEMENTATION.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_UPLOAD_IMPLEMENTATION.md)：补充上传相关 API 测试，并在实现文档中追加本次收口说明。

### iOS 视频上传崩溃修复
- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：补充 `NSCameraUsageDescription`、`NSMicrophoneUsageDescription`、`NSPhotoLibraryUsageDescription`，修复 iOS 在点击视频上传控件时触发 `TCC_CRASHING_DUE_TO_PRIVACY_VIOLATION`。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：将上传控件的 `accept` 从 `video/*` 改为明确的视频扩展名列表，降低系统优先走“拍摄视频”分支的概率。
- 更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：补充 iOS 视频上传权限说明与排查要点。

## 2026-03-15

### 首页统计与视频页联动优化
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：首页“最近视频/已完成/进行中”改为基于全量视频统计，修复统计数与实际处理数不一致的问题；三个统计卡片支持点击跳转至视频页对应筛选视图。
- 更新 [`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)：新增最近视频/已完成/进行中三类筛选视图；对应页面展示视频名称卡片，点击卡片继续进入视频详情页查看具体信息。

### 首页统计卡点击跳转修正与 iOS 验收约束补充
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页统计卡改为 `button + router.push` 明确跳转；补充点击日志 `[INFO][Home] stat-card-click ...`；增强层级与触摸可达性（统计区 z-index 提升、装饰层 `pointer-events: none`），避免被视觉层遮挡导致点击无效。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：新增 iOS WebView 验收硬规则，要求交互改动必须在容器内验证路由跳转和目标页渲染，且每次改动后必须同步最新 `mobile-frontend/dist` 到 iOS 资源。

### iOS-only 项目结构收敛
- 新增仓库外备份目录 `../EduMind_backup_20260315_ios_only/`：在删除旧模块前完成整仓复制，便于回滚。
- 删除旧模块与旧脚本：移除 `frontend/`、`backend/`、`android-app/`、根目录 `tests/`、`test_src/` 以及旧启动脚本，仓库只保留 `backend_fastapi/`、`mobile-frontend/`、`ios-app/` 三段式 iOS 链路。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：统一为 MacBook Pro 开发、iOS `WKWebView` 容器、FastAPI 后端、MySQL 持久化的唯一实现方向。

### MySQL 视频处理与转录落库收口
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：本地视频上传成功后立即提交后台处理任务；手动处理接口改为统一走任务提交逻辑，并把状态、进度、错误信息写回当前 `videos` 记录。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)：移除对不存在字段 `processed` 的写入；处理完成后将预览图、视频信息、字幕文件路径写回 `videos`，并在现有 `subtitles` 表可用时写入 Whisper 分段结果；若数据库未启用该表则跳过，不自动建表、不让任务失败。
- 更新 [`backend_fastapi/app/tasks/video_download.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_download.py)：链接视频下载完成后在同一后台任务内继续执行转录处理，避免依赖前端页面停留才能继续推进。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：新增 `AUTO_CREATE_TABLES=false` 默认配置，关闭启动时自动建表，避免运行服务时擅自变更现有 MySQL 表结构。
- 更新 [`backend_fastapi/app/models/user.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/user.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：密码哈希显式固定为 `pbkdf2:sha256`，兼容当前 Python 运行时；删除视频时若进程池不可用则回退为同步清理，避免测试和受限环境直接报错。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`backend_fastapi/tests/unit/test_video_processing_task.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_processing_task.py)：补充自动提交处理任务与转录结果落库测试，覆盖 `videos/subtitles` 现有表的写回行为。
### 2026-03-15 真机视频播放链路修复

- `backend_fastapi` 视频流接口补充 `Range` 支持，适配 iOS `WKWebView` 的分段加载、拖动和断点请求。
- `mobile-frontend` 新增真实视频播放页状态展示与重载能力；只要配置了后端地址，视频相关接口会优先走 FastAPI，不再被 UI-only mock 固定拦截。
- `ios-app` 的 `WKWebView` 开启 inline media playback / AirPlay / PiP，并放开 Web 内容本地网络访问策略，保证真机可通过局域网地址访问 FastAPI 视频流。
- `ios-app` 新增 `EDUMIND_API_BASE_URL` 原生注入；H5 启动时会自动读取并保存默认后端地址，避免真机首次安装仍停留在 `UI ONLY` 页面。
- 修正本地真机联调配置：`backend_fastapi/.env` 改为监听 `0.0.0.0`、修复 MySQL `DATABASE_URL` 格式、允许 `Origin: null`；iOS 默认后端地址从易变的 IP 改为 `.local` 主机名。
- MySQL 认证补充 `cryptography` 依赖，兼容 `sha256_password` / `caching_sha2_password`；播放器页改为优先展示后端返回的明确错误，方便定位数据库或视频接口异常。

## 2026-03-16

### MySQL 受控重建脚本与 Navicat 导入 SQL

- 更新 [`backend_fastapi/scripts/init_db.py`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/init_db.py)：将数据库脚本改为只管理当前 FastAPI 实际使用的 6 张业务表（`users`、`videos`、`notes`、`questions`、`subtitles`、`note_timestamps`），新增 `--create`、`--reset`、`--emit-sql` 能力，支持受控删表重建与 SQL 导出。
- 新增 [`backend_fastapi/scripts/mysql_managed_schema.sql`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/mysql_managed_schema.sql)：生成可直接在 Navicat 执行的 MySQL 重建脚本，包含 `DROP TABLE IF EXISTS` 与完整 `CREATE TABLE` 语句。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：补充后端 MySQL 表管理命令、Navicat 导入入口和当前受控表清单。
- 更新 [`backend_fastapi/.env`](/Users/yuan/final-work/EduMind/backend_fastapi/.env)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`docs/DATABASE_SETUP.md`](/Users/yuan/final-work/EduMind/docs/DATABASE_SETUP.md)：将默认数据库名从 `ai_edvision` 统一调整为项目名 `edumind`，便于在 Navicat 中与项目名称保持一致。

### 真机地址与端口自动同步

- 更新 [`ios-app/sync_ios_web_assets.sh`](/Users/yuan/final-work/EduMind/ios-app/sync_ios_web_assets.sh)：构建 iOS 资源前自动读取 `backend_fastapi/.env` 中的 `PORT` 与当前 Mac `LocalHostName`，同步刷新 iOS 原生默认后端地址，避免端口变化后还要手工修改 Xcode Build Settings。
- 更新 [`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：开发设置页改为展示当前建议后端地址，不再写死 `2004` 和局域网 IP 示例。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：将真机默认地址说明统一为 `.local + backend_fastapi/.env PORT` 的单点配置链路。

### 数据库配置加载路径修复

- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)：将 `BaseSettings` 的 `env_file` 改为固定读取 `backend_fastapi/.env` 的绝对路径，避免从仓库根目录执行脚本时退回默认 `DATABASE_URL`（`root:password`）导致 MySQL `1045 Access denied`。

### 仓库忽略规则补强

- 更新 [`.gitignore`](/Users/yuan/final-work/EduMind/.gitignore)：补充 `*.sqlite`、`*.db-journal`、`*.sqlite-shm`、`*.sqlite-wal` 等本地数据库运行产物忽略规则，并新增 `**/.idea/` 与仓库根误生成目录 `~/` 的忽略，减少本地大文件或无关缓存被错误纳入版本控制的风险。
