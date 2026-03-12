# EduMind Frontend

`frontend/` 是桌面端 Vue 3 + Vite 工程。

## 启动

```bash
cd frontend
npm install
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

## 当前联调状态

- Vite 已配置 `/api` 代理到 `http://127.0.0.1:2004`
- `src/config/index.js` 默认也会把 `VITE_API_BASE_URL` 回退到 `http://localhost:2004`
- 但 `src/main.js` 仍保留了一个历史的 `axios.defaults.baseURL = 'http://localhost:5001'`

这意味着桌面端正在从 Flask 向 FastAPI 迁移中。多数页面可直接配合 `backend_fastapi/` 联调，但如果遇到认证或个别旧页面请求异常，需要优先检查是否命中了旧的 `5001` 配置。

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
- 不建议继续扩散直接写死 `5001` 的调用方式
- 如果修改了接口契约，记得同步检查移动端是否共用该接口
