# EduMind Backend (Legacy Flask)

`backend/` 是旧版 Flask 后端，目前保留兼容，不再作为新功能首选入口。

## 当前定位

- 历史桌面端和辅助脚本仍可能依赖这里
- `dev_start.py` 当前启动的就是这个后端
- 默认端口为 `5001`

如果你在开发新接口，请优先使用 [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md) 对应的 FastAPI 实现。

## 启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

## 目录说明

| 路径 | 说明 |
|------|------|
| `app/api/` | 一部分旧接口实现 |
| `app/routes/` | Flask 路由 |
| `app/core/` | 核心配置 |
| `app/models/` | 数据模型 |
| `app/schemas/` | 序列化模型 |
| `app/tasks/` | Celery/后台任务 |
| `app/utils/` | 工具函数 |
| `app/static/` | 静态资源 |

## 说明

- 这里仍保留一些历史默认值和本地依赖配置，不建议继续扩展
- 若只是为了兼容旧页面或核对历史行为，可以运行本目录
- 文档中的架构与推荐开发路径以根目录 README 和 `backend_fastapi/` 为准
