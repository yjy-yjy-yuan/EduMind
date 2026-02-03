# EduMind Mobile Frontend

独立移动端前端工程（H5 / WebView），不会改动或耦合本仓库现有 `frontend/` 与 `backend/`。

## 启动

```bash
cd mobile-frontend
npm install
npm run dev
```

## 配置后端地址（与本项目后端解耦）

在 `mobile-frontend/` 下创建 `.env`（参考 `.env.example`）：

- `VITE_MOBILE_API_BASE_URL`：移动应用后端基地址（例如 `http://127.0.0.1:5002` 或线上域名）
- `VITE_MOBILE_PROXY_TARGET`：本地开发可选代理目标（不填则默认使用 `VITE_MOBILE_API_BASE_URL`，再不填则 `http://127.0.0.1:5001`）

当 `VITE_MOBILE_API_BASE_URL` 为空时，前端会请求同源 `/api/...`，可通过 Vite 代理转发。

