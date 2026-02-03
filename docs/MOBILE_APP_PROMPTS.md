# EduMind 移动端页面生成提示词（先写提示词，再落地实现）

> 目标：在不改动本仓库现有 `frontend/` 架构、且不依赖 `backend/` 的前提下，为 EduMind 新增一个**独立的移动端前端工程**（H5 / WebView，可用于封装 App）。
> 约束：移动端只通过可配置的 `VITE_MOBILE_API_BASE_URL` 调用“移动应用后端”（端口/域名可变），不要把后端代码或逻辑耦合进本项目；移动端工程放在单独目录（例如 `mobile-frontend/`）。

---

## 0) 总提示词（给生成器/代码助手）

你是资深移动端产品 + 前端工程师。请基于现有项目（Vue 3 + Vite，当前已有桌面端页面与 API 模块），新增一套移动端页面，路由统一挂在 `/m` 下。要求：

1. 在仓库根目录新增独立工程 `mobile-frontend/`（允许新增 `docs/` 文档），不改现有 `frontend/`，严禁改动 `backend/` 或引用后端代码。
2. 所有接口请求必须通过移动端工程内的请求实例发出，基地址读取 `import.meta.env.VITE_MOBILE_API_BASE_URL`（可为空，空则走同源 `/api`）。
3. UI 移动优先：顶部标题栏 + 内容区 + 底部 TabBar（首页/视频/上传/笔记/我的）。
4. 关键页面：登录/注册、首页、视频列表、视频详情、视频播放、上传、笔记列表、笔记编辑、AI 问答、个人中心。
5. 每个页面必须包含：加载态、空态、错误态；接口异常给出可理解提示；按钮禁用状态合理。
6. 代码风格：Composition API（`<script setup>`），尽量少依赖新增第三方 UI 库（沿用现有 Element Plus 的 Toast 可接受，但页面组件以原生结构+CSS 为主）。

输出内容：新增/修改的文件列表 + 关键代码（按文件划分），保证可直接运行。

---

## 1) 接口层提示词（移动端与后端解耦）

请在移动端工程中新增专用请求实例 `mobile-frontend/src/utils/request.js`：

- `baseURL = VITE_MOBILE_API_BASE_URL || VITE_API_BASE_URL || ''`（去掉末尾 `/`）
- 默认超时 10 分钟
- `FormData` 上传时删除 `Content-Type`
- 可选：从 `localStorage.mobile_token` 读取 token，自动加 `Authorization: Bearer <token>`
- 统一返回 `{ data, status, headers }`

并新增移动端 API 模块目录 `mobile-frontend/src/api/`：

- `video.js`：list/get/status/upload/process/delete
- `note.js`：list/get/create/update/delete
- `qa.js`：ask（非流式）
- `auth.js`：login/register/me/logout（字段尽量兼容 `success/user/token/message` 的多种返回格式）

---

## 2) 路由与壳子提示词（独立移动端工程）

请在 `mobile-frontend/src/router/index.js` 定义移动端路由：

- `/login`、`/register`（不显示 TabBar）
- `/`（Shell，内含 `<router-view/>` + TabBar）
  - `/`：移动端首页
  - `/videos`：视频列表
  - `/videos/:id`：视频详情
  - `/player/:id`：视频播放（隐藏 TabBar）
  - `/upload`：上传
  - `/notes`：笔记列表
  - `/notes/new`、`/notes/:id`：笔记编辑（隐藏 TabBar）
  - `/qa`：AI 问答
  - `/profile`：个人中心

---

## 3) 页面生成提示词（逐页）

### 3.1 移动端首页（/）

页面元素：
- 顶部：标题“视频智能伴学（移动端）”
- 功能入口卡片：视频、上传、笔记、问答、个人中心
- 最近视频（可选）：调用 `GET /api/videos/list?page=1&per_page=3`，展示标题+状态

状态要求：加载 skeleton、无数据空态、错误提示+重试。

### 3.2 视频列表（/videos）

列表项展示：预览图（如果可拼 URL）、标题、状态徽标、进度条（processing/pending）。
交互：点击进入详情；下拉/按钮刷新；分页“加载更多”（page +1）。

### 3.3 视频详情（/videos/:id）

展示：标题、状态、进度、当前步骤、摘要（如果有）、操作按钮：
- 处理：POST `/api/videos/{id}/process`
- 播放：进入 `/player/:id`（完成状态可用）
- 问答：进入 `/qa?videoId=:id`（可选）

若 status 为 processing/pending，间隔轮询 `GET /api/videos/{id}/status`。

### 3.4 视频播放（/player/:id）

使用 `<video controls>` 播放：
- 视频 URL：`{base}/api/videos/{id}/stream`
- 字幕 track（可选）：`{base}/api/videos/{id}/subtitle?format=vtt`

### 3.5 上传（/upload）

两种上传：
- 本地文件：`POST /api/videos/upload`（FormData: file）
- 链接：`POST /api/videos/upload-url`

显示上传进度、成功后跳转到详情或列表。

### 3.6 笔记列表/编辑（/notes、/notes/:id）

列表：标题、更新时间；空态。
编辑：标题 input + 内容 textarea；保存（create/update）、删除（可选）。

### 3.7 AI 问答（/qa）

简化：非流式问答 `POST /api/qa/ask`，展示对话列表（用户/AI）。
支持 query：`videoId`（存在则按视频问答模式传参）。

### 3.8 登录/注册/个人中心（/login、/register、/profile）

登录注册按后端返回兼容：
- 可能返回 `{success, user}` 或 `{token, user}` 或 `{data:{...}}`
- token 写入 `localStorage.mobile_token`，user 写入 `localStorage.mobile_user`
个人中心：展示用户信息与退出登录。

---

## 4) 验收清单（对齐需求）

- `mobile-frontend/` 可独立安装/构建运行，且不影响原 `frontend/`。
- `VITE_MOBILE_API_BASE_URL` 可切换不同“移动后端”端口/域名；不引入后端代码。
- 核心流程：登录 → 上传/列表 → 详情轮询 → 播放 → 问答/笔记 可操作。
