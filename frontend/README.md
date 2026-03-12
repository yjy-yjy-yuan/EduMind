# EduMind Frontend

`frontend/` 是桌面端 Vue 3 + Vite 工程。

## 启动

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认端口为 `328`，配置见 `vite.config.js`。

## 常用命令

```bash
npm run dev
npm run build
npm run preview
npm run test:unit
npm run lint
```

## 端口与代理配置

- `VITE_FRONTEND_PORT`：本地 Vite 开发端口（默认 `328`）
- `VITE_API_PROXY_TARGET`：Vite `/api` 代理目标（默认 `http://127.0.0.1:2004`）
- `VITE_API_BASE_URL`：可选，浏览器直接请求后端地址；留空时优先走 `/api` 代理

换电脑后如果后端端口变化，优先改 `.env` 里的 `VITE_API_PROXY_TARGET`。

## 目录说明

| 路径 | 说明 |
|------|------|
| `src/api/` | 接口封装 |
| `src/components/` | 通用组件 |
| `src/config/` | 全局配置 |
| `src/router/` | 路由定义 |
| `src/store/` | 状态管理 |
| `src/utils/` | 工具函数 |
| `src/views/` | 页面视图 |

## 建议

- 新页面和新接口调用优先使用 `/api` 代理或 `VITE_API_BASE_URL`
- 如果修改了接口契约，记得同步检查移动端是否共用该接口
