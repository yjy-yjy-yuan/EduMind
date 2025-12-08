# CLAUDE.md

## 项目概述
AI-EdVision：基于深度学习的视频智能伴学系统。Flask + Vue 3 架构，支持视频字幕提取、知识图谱构建、AI 问答。

## 技术栈
- **后端**：Flask + Celery + Redis + Neo4j + Whisper + Ollama
- **前端**：Vue 3 + Element Plus + D3.js
- **环境**：Python 3.10, conda env: `ai-edvision`

## 常用命令
```bash
# 后端
cd backend && conda activate ai-edvision
python run.py                                              # 启动 Flask
python -m celery -A app.celery_app worker --loglevel=info -P solo  # 启动 Celery

# 前端
cd frontend && npm run dev

# 测试
PYTHONPATH=backend python -m pytest tests/ -v

# 依赖服务
brew services start redis neo4j
```

## 项目结构
```
backend/
├── app/routes/      # API 蓝图 (video, subtitle, note, qa, auth, knowledge_graph)
├── app/models/      # 数据模型 (Video, Subtitle, Note, User, Question)
├── app/tasks/       # Celery 异步任务
├── app/services/    # 业务逻辑 (摘要、标签生成)
└── config.py        # 配置文件

frontend/src/
├── views/           # 页面组件
├── components/      # 通用组件
├── api/             # API 调用层
└── store/           # Vuex 状态管理
```

## 代码规范
| 后端 | 前端 |
|------|------|
| PEP 8 风格 | Vue 3 Composition API |
| Blueprint 路由组织 | Scoped 样式 |
| Celery 处理耗时任务 | API 层与组件分离 |

## 开发端口
- Frontend: `localhost:5173`
- Backend: `localhost:5001`
- Neo4j: `localhost:7474`

## Claude Code 注意事项
中文文件写入乱码时，改用 Bash heredoc：
```bash
cat > file.md << 'EOF'
中文内容
EOF
```

## 整体开发规范

- **语言要求**：始终使用中文回复和解释
- **精准修改**：仅针对用户明确提出的需求进行修改，不得擅自修改其他未提及的功能或代码
- **代码质量**：修改代码后必须检查并确保缩进的正确性和代码格式的一致性
- **代码格式化**：使用 `uv run pre-commit run --files $(git ls-files -mo --exclude-standard)` 对未暂存的文件执行代码格式化检查
- **文档完整性**：新实现的功能（已验证可运行）或修复完成的bug必须提供实用的文档说明和使用示例
- **风格规范**：最大行宽是 120 个字符
- 其它情况下，要尽量遵循 Google 开源项目风格指南
- 不需要为单个组件创建使用文档

## Python 开发规范

- **支持的 Python 版本**：>= 3.10
- **Import 规范**：
  - 只导入包和模块，而不单独导入函数或者类
  - 使用 `from src.dir import module` 替代 `import src.dir.module`，避免出现导入带 `.` 的包名
- **命名规范**：不需要在名称前加单下划线 (`_`) 来保护模块变量和函数
- **代码检查**：实现的代码尽量遵守 pylint 开发规范，避免 pylint 报错

## AI 开发规范

- **不要重复改动**：如果 AI 发现某一个已经做过改动不见了，并不是因为改动没有生效，而是因为用户认为这个改动是不合理的，或者手动用其它方式实现了，不要重复改动
- **精准修改**：每次改动仅修改与当前命令相关的内容，不要额外修改。不要把之前对话的内容放到本次修改中
- **避免重复命令**：不要重复执行 `git diff --stat` 命令
