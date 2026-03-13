# EduMind

EduMind 是一个面向教育视频学习场景的智能分析系统，当前仓库同时维护 FastAPI 主后端、Flask 旧后端、桌面端和移动端 H5 前端（可由 iOS WebView 等容器加载）。

## 仓库现状

```text
EduMind/
├── backend_fastapi/   # 当前主后端，新接口优先放这里
├── backend/           # 旧版 Flask 后端，保留兼容
├── frontend/          # 桌面端 Vue 3 + Vite
├── mobile-frontend/   # 移动端 H5 / WebView 前端
├── ios-app/           # iOS WebView 容器（建议使用 Xcode 创建与维护）
├── docs/              # 文档、方案、提示词
├── tests/             # 根目录测试
└── dev_start.py       # 一键启动旧版 backend + frontend 的开发脚本
```

当前默认开发组合是：

- 后端：`backend_fastapi/`，默认端口 `2004`
- 桌面端：`frontend/`，Vite 默认端口 `328`（可在 `frontend/.env` 调整）
- 移动端：`mobile-frontend/`，Vite 默认端口由 Vite 自动分配，接口默认指向 `2004`

需要注意：

- `dev_start.py` 目前仍面向 `backend/` + `frontend/` 的旧联调流程，不是 FastAPI 的统一启动脚本。
- `frontend/` 和 `mobile-frontend/` 都支持通过 `.env` 调整后端代理目标；换电脑后如果端口不同，优先改 `.env`。

## 主要能力

- 视频上传、转码与处理状态跟踪
- Whisper 转录与字幕管理
- 视频摘要、标签、知识点分析
- 视频问答与历史记录
- 学习笔记与时间点跳转
- 知识图谱生成与查询
- 移动端学习流程与 iOS/移动端 H5 集成

## 环境要求

- Python `3.10+`
- Node.js `16+`
- npm
- 按功能启用的外部依赖：MySQL、Neo4j、Redis、FFmpeg、Ollama

## 快速开始

### 1. 启动主后端

```bash
cd backend_fastapi
pip install -r requirements.txt
cp .env.example .env
python run.py
```

默认地址：

- 健康检查：`http://127.0.0.1:2004/health`
- API 文档：`http://127.0.0.1:2004/docs`

### 2. 启动桌面端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认访问地址：`http://127.0.0.1:328`

如需调整端口/代理，编辑 `frontend/.env`：

- `VITE_FRONTEND_PORT=328`
- `VITE_API_PROXY_TARGET=http://127.0.0.1:2004`

### 3. 启动移动端 H5

```bash
cd mobile-frontend
npm install
npm run dev
```

推荐先复制环境变量模板：

```bash
cd mobile-frontend
cp .env.example .env
```

默认配置项：

- `VITE_MOBILE_API_BASE_URL=http://127.0.0.1:2004`
- `VITE_MOBILE_PROXY_TARGET=http://127.0.0.1:2004`

- （可选）iOS 原生容器：推荐在 `ios-app/` 目录下使用 Xcode 创建 iOS 工程，通过 `WKWebView` 加载 `mobile-frontend` 的 H5 页面（开发期指向 Vite dev server，发布期加载打包后的静态资源）。
## 测试

根目录 `pytest` 主要覆盖共享后端测试：

```bash
pytest
pytest -m smoke
pytest -m unit
pytest -m api
pytest -m integration
```

FastAPI 子项目也可以单独执行：

```bash
cd backend_fastapi
pytest tests/ -v
```

## 开发建议

1. 新后端接口优先开发在 `backend_fastapi/`
2. 桌面端页面改动放在 `frontend/`
3. 移动端业务放在 `mobile-frontend/`
5. `backend/` 仅做兼容维护，不再作为首选实现

## 相关文档

- [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)
- [`CHANGELOG.md`](/Users/yuan/final-work/EduMind/CHANGELOG.md)
- [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)
- [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)
- [`frontend/README.md`](/Users/yuan/final-work/EduMind/frontend/README.md)
- [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)
- （可选）`ios-app/`：建议在该目录下创建 Xcode 工程并编写 iOS 容器说明。
