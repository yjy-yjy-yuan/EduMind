# Backend CLAUDE.md

Flask + Celery + Redis + Neo4j 后端服务

## Bash Commands
```bash
# 启动服务
python run.py                                              # Flask 服务 (端口 5001)
python -m celery -A app.celery_app worker --loglevel=info -P solo  # Celery 工作进程

# 测试
PYTHONPATH=backend python -m pytest tests/ -v             # 所有测试
PYTHONPATH=backend python -m pytest tests/unit/ -v        # 单元测试
PYTHONPATH=backend python -m pytest tests/api/ -v         # API 测试
PYTHONPATH=backend python -m pytest tests/smoke/ -v -m smoke  # 冒烟测试
PYTHONPATH=backend python -m pytest tests/ -v --cov=backend/app  # 覆盖率
```

## Core Files
```
app/
├── __init__.py        # Flask 应用工厂 (create_app)
├── extensions.py      # SQLAlchemy, Celery, CORS 初始化
├── config.py          # 配置类
├── routes/            # API 蓝图
│   ├── video.py       # /api/videos
│   ├── subtitle.py    # /api/subtitles
│   ├── note.py        # /api/notes
│   ├── qa.py          # /api/qa
│   ├── auth.py        # /api/auth
│   └── knowledge_graph.py  # /api/knowledge-graph
├── models/            # SQLAlchemy 数据模型
├── tasks/             # Celery 异步任务
│   ├── video_processing.py      # 通用版本
│   └── video_processing_mac.py  # Mac MPS 加速版本
└── utils/             # 工具函数
    ├── knowledge_graph_utils.py  # Neo4j 操作
    ├── qa_utils.py               # AI 问答
    └── subtitle_utils.py         # 字幕处理
```

## Code Style
- Python >= 3.10
- Import 只导入模块，不导入函数或类: `from app.routes import video`
- 行宽: 120 字符
- 格式化: black + isort

## Testing
测试标记: `@pytest.mark.smoke`, `@pytest.mark.unit`, `@pytest.mark.api`, `@pytest.mark.integration`, `@pytest.mark.slow`

```
tests/
├── conftest.py        # 共享 fixtures
├── smoke/             # 冒烟测试 - 快速验证
├── unit/              # 单元测试 - 模型、服务、任务
├── api/               # API 测试 - HTTP 接口
└── integration/       # 集成测试 - 组件交互
```

## Async Tasks
- Celery 处理视频转码、字幕提取等耗时任务
- Mac 系统自动使用 MPS 加速 (`video_processing_mac.py`)
- 任务状态通过 Redis 存储
