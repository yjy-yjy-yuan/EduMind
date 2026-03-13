# EduMind 移动端模块设计提示词（先提示词，后实现）

> 目标：为“移动端 H5 + iOS/WebView 容器”补齐模块划分与页面实现规范。  
> 约束：移动端工程独立于现有 `frontend/`；仅通过 `VITE_MOBILE_API_BASE_URL` 调用“移动应用后端”；不引入/不修改本仓库 `backend/`。

---

## 1) 总提示词（模块化 + 不遮挡 + 自适应）

你是资深移动端架构师 + 前端工程师。请在仓库根目录新增/完善独立移动端工程 `mobile-frontend/`，并为 iOS 等原生容器（如 `ios-app/`）预留 WebView 集成能力。要求：

1. 模块化：按“路由/页面、组件、API、状态、配置、工具、样式”分层；禁止把后端逻辑写进前端（只做调用与展示）。
2. 自适应与防遮挡：适配小屏、刘海屏、安全区、软键盘；底部 TabBar/输入框不能遮挡内容；避免 `100vh` 导致的 WebView 高度抖动。
3. 交互三态：每页至少包含 loading / empty / error，并提供重试与禁用态。
4. 端口解耦：`VITE_MOBILE_API_BASE_URL` 作为唯一后端入口；开发期可用 Vite proxy（可配置 `VITE_MOBILE_PROXY_TARGET`）。
5. 原生容器（如 iOS WebView）：启用 JS/本地存储能力，处理好返回行为（导航回退或关闭 WebView），开发期可指向本机/局域网 Vite dev server，发布期加载打包后的静态资源。

输出：模块清单、目录结构、各模块职责、以及落实到代码的新增/修改文件列表。

---

## 2) 模块清单提示词（建议的最终结构）

请将移动端工程按如下模块组织（目录可等价替换，但职责必须一致）：

- `mobile-frontend/src/config/`：环境变量与 baseUrl 拼接（处理末尾 `/`，支持相对 `/api`）。
- `mobile-frontend/src/utils/`：请求封装（axios instance）、错误归一化、格式化工具（时间/状态映射）。
- `mobile-frontend/src/api/`：按领域拆分（`auth`、`video`、`note`、`qa`），只定义接口函数，不写 UI。
- `mobile-frontend/src/store/`：轻量状态（认证信息、token/user 持久化）。
- `mobile-frontend/src/components/`：跨页组件（TabBar、通用 TopBar/Empty/Error 可选）。
- `mobile-frontend/src/views/`：页面（Home/Videos/VideoDetail/Player/Upload/Notes/NoteEdit/QA/Profile/Login/Register）。
- `mobile-frontend/src/styles.css`：全局变量 + 通用布局（safe-area、tabbar 高度、通用 page 容器）。

---

## 3) 防遮挡/自适应提示词（必须遵守）

1. **不要使用** 页面级 `height: 100vh`（WebView 软键盘会导致 100vh 不等于可视高度，出现遮挡/跳动）。
2. TabBar 固定在底部时：
   - 内容容器必须有 `padding-bottom: tabbarHeight + safe-area-bottom`
   - 列表最后一项与底部留白，确保不会被 TabBar 遮挡
3. 输入框页（例如 QA）：
   - 建议 `hideTabBar: true`，使用页面自己的 `position: sticky; bottom: 0` 输入栏
   - 输入栏下方加 `padding-bottom: env(safe-area-inset-bottom)`
4. 顶部区域：
   - 顶部栏建议 `position: sticky; top: 0`，并考虑 `env(safe-area-inset-top)` 以避免刘海遮挡

---

## 4) 原生容器提示词（以 iOS 为主）

请提供一个可直接被 Xcode 打开的 iOS 工程（推荐放在本仓库 `ios-app/` 目录下），满足：

- 使用 `WKWebView` 加载移动端 H5 页面；
- 开发期默认加载 `http://127.0.0.1:5173/`（或局域网地址）便于调试；
- 发布期默认加载打包到应用 Bundle 内的 `index.html`（用于离线）；
- 预留 API 基地址配置方式（如通过查询参数、本地配置文件等），与 `VITE_MOBILE_API_BASE_URL` 对齐。
