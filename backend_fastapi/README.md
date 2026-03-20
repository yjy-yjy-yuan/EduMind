# EduMind Backend (FastAPI)

`backend_fastapi/` 是当前仓库的主后端。认证、视频、字幕、笔记、问答等新接口应优先落在这里。

## 技术栈

| 类别 | 技术 |
|------|------|
| Web | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| 数据校验 | Pydantic v2 |
| 后台任务 | ProcessPoolExecutor |
| AI | Whisper、Ollama / 外部模型服务 |

## 快速开始

```bash
cd backend_fastapi
pip install -r requirements.txt
cp .env.example .env
python run.py
```

默认监听：

- `http://127.0.0.1:2004/health`
- `http://127.0.0.1:2004/docs`

端口和主机由 `.env` 中的 `HOST`、`PORT` 控制，默认值定义在 `app/core/config.py`。
如果你调整了前端端口，也要同步更新 `.env` 的 `CORS_ORIGINS`。

## 目录结构

| 路径 | 说明 |
|------|------|
| `app/main.py` | FastAPI 应用入口 |
| `app/core/` | 配置、数据库、执行器 |
| `app/models/` | ORM 模型 |
| `app/routers/` | 路由定义 |
| `app/schemas/` | 请求/响应模型 |
| `app/services/` | 业务服务 |
| `app/tasks/` | 耗时任务 |
| `app/utils/` | 通用工具 |
| `scripts/` | 辅助脚本 |
| `tests/` | FastAPI 专属测试 |

## 依赖服务

按功能启用以下服务：

- MySQL
- Redis
- FFmpeg
- Ollama

部分接口不依赖全部服务，最小联调时可只启动当前链路所需组件。

## 用户认证约定

- 注册接口：邮箱或手机号至少一项必填，密码必须满足强密码规则。
- 登录接口：仅接受邮箱/手机号 + 密码。
- 数据落点：继续写入现有 `users` 表，不新增认证平行表。
- 资料更新接口现已支持登录后修改用户名，并直接写回 `users.username`。
- 头像上传接口会把文件保存到 `backend_fastapi/uploads/avatars/`，并将访问路径写入现有 `users.avatar` 字段，不新增附件表。
- 执行 `python scripts/init_db.py --create` 时，会自动为已有 `users` 表补齐手机号、密码重复检测指纹和登录次数字段。

## 测试

```bash
cd backend_fastapi
pytest tests/ -v
pytest -m smoke
pytest -m api
pytest --cov=app
```

## 端口约定

| 服务 | 默认端口 |
|------|---------|
| FastAPI 后端 | 2004 |
| 桌面端 Vite | 328 |
## 开发说明

- 修改接口时，同时检查根目录 README 和 `docs/` 中是否需要同步更新。
- 如果接口会被移动端调用，注意 `mobile-frontend/` 的字段兼容性。
- 旧版 `backend/` 中存在历史实现，迁移时优先保证 FastAPI 行为一致，而不是继续扩展 Flask 分支。
