# AI-EdVision Backend (FastAPI)

基于 FastAPI 的视频智能伴学系统后端，从 Flask 迁移而来。

## 迁移收益

| 收益 | 说明 |
|------|------|
| 异步非阻塞 | 原生 async/await，上传/下载/流式回答不卡主线程 |
| 自动 API 文档 | Swagger UI (`/docs`) + ReDoc (`/redoc`) |
| 类型安全 | Pydantic 自动验证请求/响应 |
| 简化部署 | 无需 Redis/Celery，后台任务用 ProcessPoolExecutor |
| 易于测试 | 依赖注入可替换 `get_db`，测试更方便 |

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 + Alembic |
| 验证 | Pydantic v2 |
| 后台任务 | ProcessPoolExecutor |
| AI | Whisper + Ollama/Qwen API |
| 知识图谱 | Neo4j |

## 快速开始

1. **安装依赖**: `conda activate ai-edvision && pip install -r requirements.txt`
2. **配置环境**: `cp .env.example .env` 并编辑配置
3. **启动服务**: `python run.py`
4. **访问文档**: http://localhost:2004/docs

## 目录结构

| 目录/文件 | 说明 |
|-----------|------|
| `app/main.py` | FastAPI 应用入口 |
| `app/core/` | 配置 (config.py)、数据库 (database.py)、执行器 (executor.py) |
| `app/routers/` | API 路由：video, subtitle, note, qa, chat, auth, knowledge_graph |
| `app/models/` | SQLAlchemy 模型 |
| `app/schemas/` | Pydantic 请求/响应模型 |
| `app/services/` | 业务逻辑层 |
| `app/tasks/` | 后台任务 (视频处理等) |
| `app/utils/` | 工具函数 |
| `tests/` | 测试：smoke/, unit/, api/ |
| `alembic/` | 数据库迁移 |

## API 端点

| 路由 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /docs` | Swagger UI 文档 |
| `/api/videos/*` | 视频上传、处理、列表、流式传输 |
| `/api/subtitles/*` | 字幕提取、语义合并、编辑 |
| `/api/notes/*` | 笔记 CRUD、时间戳管理 |
| `/api/qa/*` | AI 问答 (流式响应) |
| `/api/chat/*` | 聊天系统 (流式响应) |
| `/api/auth/*` | 用户注册、登录、信息更新 |
| `/api/knowledge-graph/*` | 知识图谱构建、查询 |

## 测试

| 命令 | 说明 |
|------|------|
| `pytest tests/ -v` | 运行所有测试 |
| `pytest -m smoke` | 冒烟测试 |
| `pytest -m unit` | 单元测试 |
| `pytest -m api` | API 测试 |
| `pytest --cov=app` | 覆盖率报告 |

## 端口配置

| 服务 | 端口 |
|------|------|
| FastAPI Backend | 2004 |
| Vue Frontend | 328 |
| Neo4j Browser | 7474 |
| Neo4j Bolt | 7687 |

## 与 Flask 版本对比

| 特性 | Flask | FastAPI |
|------|-------|---------|
| 启动命令 | 4 条 (Flask + Celery + Redis + 前端) | 2 条 (FastAPI + 前端) |
| 请求处理 | 同步阻塞 | 异步非阻塞 |
| API 文档 | 无 | 自动生成 |
| 参数验证 | 手动 | Pydantic 自动 |
| 后台任务 | Celery + Redis | ProcessPoolExecutor |
| 类型安全 | 无 | 完整类型注解 |
