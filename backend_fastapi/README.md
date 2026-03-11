# EduMind Backend (FastAPI)

这是当前仓库的主后端工程，负责认证、视频处理、字幕、笔记、问答和知识图谱相关接口。新功能默认优先落在 `backend_fastapi/`，旧版 `backend/` 仅保留兼容。

## 技术栈

| 类别 | 技术 |
|------|------|
| Web | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| 数据校验 | Pydantic v2 |
| 后台任务 | ProcessPoolExecutor |
| 图谱 | Neo4j |
| AI | Whisper、Ollama / 第三方模型接口 |

## 快速开始

```bash
cd backend_fastapi
pip install -r requirements.txt
cp .env.example .env
python run.py
```

默认地址：

- `http://localhost:2004/health`
- `http://localhost:2004/docs`

## 目录说明

| 路径 | 说明 |
|------|------|
| `app/main.py` | FastAPI 应用入口 |
| `app/core/` | 配置、数据库、执行器 |
| `app/routers/` | 路由层 |
| `app/models/` | 数据模型 |
| `app/schemas/` | 请求与响应模型 |
| `app/services/` | 业务逻辑 |
| `app/tasks/` | 耗时任务 |
| `app/utils/` | 工具函数 |
| `tests/` | 后端测试 |

## 常用测试命令

```bash
cd backend_fastapi
pytest tests/ -v
pytest -m smoke
pytest -m api
pytest --cov=app
```

## 端口约定

| 服务 | 端口 |
|------|------|
| FastAPI 后端 | 2004 |
| 桌面端前端 | 328 |
| Neo4j Browser | 7474 |
| Neo4j Bolt | 7687 |

## 说明

- 如果你要改接口，优先同步更新根目录和 `docs/` 下的相关说明文档。
- 如果你要处理移动端接口，请同时关注 `mobile-frontend/` 的字段兼容性。
