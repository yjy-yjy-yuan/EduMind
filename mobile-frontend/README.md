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
npm run preview
npm run build -- --mode android
```

## 环境变量

`.env.example` 当前默认配置如下：

- `VITE_MOBILE_API_BASE_URL=http://127.0.0.1:2004`
- `VITE_MOBILE_PROXY_TARGET=http://127.0.0.1:2004`

说明：

- `VITE_MOBILE_API_BASE_URL` 用于浏览器直接请求完整后端地址
- `VITE_MOBILE_PROXY_TARGET` 用于本地 Vite `/api` 代理
- 两者都不填时，代码会退回同源 `/api/...`，而 `vite.config.js` 会继续默认代理到 `http://127.0.0.1:2004`

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

## Android 配合方式

如果用于 Android 离线资源打包：

```bash
cd mobile-frontend
npm run build -- --mode android
```

然后将 `dist/` 内容同步到 `android-app/app/src/main/assets/`。
