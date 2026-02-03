# CLAUDE.md

EduMind：基于深度学习的视频智能伴学系统。FastAPI + Vue 3 架构，支持视频字幕提取、知识图谱构建、AI 问答。

## Tech Stack
- **Backend**: FastAPI + SQLAlchemy 2.0 + Neo4j + Whisper + Ollama (已从 Flask 迁移)
- **Frontend**: Vue 3 + Element Plus + D3.js
- **Environment**: Python 3.10, conda env: `edumind`

## Ports
| Service  | Port |
|----------|------|
| Frontend | 328 |
| Backend (FastAPI) | 2004 |
| Neo4j    | 7474 |

## Quick Start (FastAPI - 推荐)
```bash
# 启动依赖服务
brew services start neo4j

# 后端 (Terminal 1)
cd backend_fastapi && conda activate edumind && python run.py

# 前端 (Terminal 2)
cd frontend && npm run dev

# 访问
# 前端: http://localhost:328
# API 文档: http://localhost:2004/docs
```

## Quick Start (Flask - 旧版本)
```bash
# 启动依赖服务
brew services start redis neo4j

# 后端 (Terminal 1)
cd backend && conda activate edumind && python run.py

# Celery (Terminal 2)
cd backend && conda activate edumind
python -m celery -A app.celery_app worker --loglevel=info -P solo

# 前端 (Terminal 3)
cd frontend && npm run dev
```

## Code Style
- **Line width**: 120 characters max
- **Formatting**: black + isort (profile: black)
- **Linting**: flake8, pylint (non-blocking)
- **Style guide**: Google Python Style Guide

```bash
# 代码格式化检查
pre-commit run --all-files
```

## Claude Code 注意事项

### IMPORTANT: 语言和修改规范
- **YOU MUST** 始终使用中文回复
- **YOU MUST** 仅修改用户明确提出的需求，不得擅自修改其他代码
- **YOU MUST** 修改代码后检查缩进和格式一致性
- 不要重复已撤销的改动
- 不要重复执行 `git diff --stat`

### 中文文件处理
中文写入乱码时使用 heredoc：
```bash
cat > file.md << 'EOF'
中文内容
EOF
```
