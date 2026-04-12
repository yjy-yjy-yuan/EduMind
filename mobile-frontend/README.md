# EduMind Mobile Frontend

`mobile-frontend/` 是独立的移动端 H5 / WebView 工程，当前默认与 `backend_fastapi/` 联调。

## 启动

```bash
cd mobile-frontend
npm install
cp .env.example .env
npm run dev
```

## 常用命令

```bash
npm run dev
npm run build
npm run build:web
npm run build:ios
npm run preview
```

## 环境变量

`.env.example` 当前默认配置如下：

- `VITE_MOBILE_API_BASE_URL=http://127.0.0.1:2004`
- `VITE_MOBILE_UI_ONLY=true`
- `VITE_MOBILE_PROXY_TARGET=http://127.0.0.1:2004`

说明：

- `VITE_MOBILE_API_BASE_URL` 用于浏览器直接请求完整后端地址
- `VITE_MOBILE_UI_ONLY` 为 `true` 时启用纯 UI 模式，`src/api/*` 会走本地 mock 网关（保留真实接口函数签名，后续可无痛切回后端）
- `VITE_MOBILE_PROXY_TARGET` 用于本地 Vite `/api` 代理
- `VITE_RECOMMENDATION_INCLUDE_EXTERNAL` 控制首页与推荐页是否默认附带站外推荐抓取
- UI-only 模式下即使后端不可用也不会影响页面渲染；可通过 URL 参数 `?uiOnly=0` 临时关闭
- 两者都不填且关闭 UI-only 时，代码会退回同源 `/api/...`，而 `vite.config.js` 会继续默认代理到 `http://127.0.0.1:2004`

推荐链路建议：

- 弱网或真机联调时，优先让 `VITE_RECOMMENDATION_INCLUDE_EXTERNAL=false`
- 这样首页首屏会先展示站内推荐，把站外增强留给推荐页按需触发

旧文档里出现过 `5001/5002` 的示例，那是旧后端阶段的端口，不再是当前默认值。

## 目录说明

| 路径 | 说明 |
|------|------|
| `src/api/` | 移动端接口封装 |
| `src/components/` | 通用组件 |
| `src/config/` | API 基地址与运行时配置 |
| `src/router/` | 移动端路由 |
| `src/store/` | 状态管理 |
| `src/views/` | 页面视图 |

## 设计助手入口

当前移动端已新增“设计助手”页，入口位于“我的”页面中。它不会直接请求 Sleek，而是统一走 EduMind 后端的 `/api/design/*` 代理接口：

- 先在 `backend_fastapi/.env` 中配置 `SLEEK_API_KEY`
- 登录 EduMind 后进入“我的” -> “设计助手”
- 可创建 Sleek 项目、提交自然语言设计描述、查看截图预览和组件 HTML 原型

## 原生容器配合方式（以 iOS 为主）

如果用于 iOS / 原生容器离线资源打包，优先使用 iOS 构建命令：

```bash
cd mobile-frontend
npm run build:ios
```

在 iOS 工程中（例如放在本仓库的 `ios-app/` 目录下，用 Xcode 创建的工程），将 `dist/` 内容拷贝到应用 Bundle 中（如 `Assets` 或自定义资源目录），并在 `WKWebView` 中通过 `Bundle.main.url(forResource:)` 等方式加载本地 `index.html`。当前仓库的 iOS 容器已经固定为本地静态资源加载路径，不再依赖 `5173` dev server。

## 推荐页交互说明

当前推荐前端已经固定支持以下行为：

1. 推荐卡片会明确区分站内视频与站外候选。
2. 站外候选若 `can_import=true`，主动作会进入上传页并预填 URL。
3. 站外候选若 `can_import=false`，主动作会打开原始来源页，而不是错误地跳回上传页。
4. **「推荐学习中枢」页**（`/recommendations`）为 **单列表**：请求 `scene=home` 的推荐结果，提供 Hero 与「刷新推荐 / 刷新列表」；**不再**提供多场景切换、主列表「看同主题」或页内「同主题」区块。
5. **`scene=related` 的相关推荐**主要在 **视频详情页**「相关推荐」子页使用（需 `seed_video_id`），与独立推荐页解耦。
6. 若当前种子视频本身来自 B 站、YouTube 或中国大学慕课，首页、上传页和推荐页的查询摘要会显示“优先来源”，帮助用户看清本轮相关推荐继承的是哪个来源平台语境。

如果要部署到常规 Web 服务器根路径，可使用：

```bash
npm run build:web
```

## 固定域名构建（后端使用固定域名，换 Wi‑Fi/换地点不失效）

后端使用固定域名（如 `https://api.yourdomain.com`）时，构建前设置该地址，请求会始终发往该域名：

```bash
cp .env.production.example .env.production
# 编辑 .env.production，将 https://api.yourdomain.com 改为实际后端固定域名
npm run build
# iOS 打包（会读 .env.ios）：cp .env.production.example .env.ios && 编辑域名 && npm run build:ios
```

详见仓库根目录 `docs/BACKEND_FIXED_DOMAIN.md`。
