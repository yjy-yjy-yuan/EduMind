# AI-EdVision 后端运行指南

从零开始运行 FastAPI 后端的完整流程。

## 1. 创建并激活虚拟环境

```bash
# 创建 conda 环境 (Python 3.10)
conda create -n ai-edvision python=3.10 -y

# 激活环境
conda activate ai-edvision
```

## 2. 安装依赖

```bash
cd backend_fastapi
pip install -r requirements.txt
```

## 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置 (可选，默认配置可直接运行)
# vim .env
```

**主要配置项**：

| 配置 | 默认值 | 说明 |
|------|--------|------|
| PORT | 2004 | 后端端口 |
| DATABASE_URL | sqlite:///./app.db | 数据库连接 |
| NEO4J_URI | bolt://localhost:7687 | Neo4j 地址 |
| WHISPER_MODEL | turbo | 语音识别模型 |
| OLLAMA_MODEL | qwen3:8b | AI 对话模型 |

## 4. 启动依赖服务

```bash
# 启动 Neo4j (macOS)
brew services start neo4j

# 启动 Ollama (可选，用于 AI 问答)
ollama serve
```

## 5. 启动后端服务

```bash
cd backend_fastapi
conda activate ai-edvision
python run.py
```

**启动成功输出**：
```
INFO:     启动 AI-EdVision API...
INFO:     数据库表创建成功
INFO:     上传目录已就绪: .../uploads
INFO:     Uvicorn running on http://127.0.0.1:2004
```

## 6. 验证服务

| 地址 | 说明 |
|------|------|
| http://localhost:2004/health | 健康检查 |
| http://localhost:2004/docs | Swagger UI 文档 |
| http://localhost:2004/redoc | ReDoc 文档 |

**健康检查成功响应**：
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "neo4j": "connected"
  }
}
```

## 7. 启动前端 (可选)

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:5173
```

## 快速启动脚本

创建 `start.sh` 一键启动：

```bash
#!/bin/bash
cd "$(dirname "$0")"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ai-edvision
python run.py
```

## 常见问题

### 端口被占用

```bash
# 查看占用进程
lsof -i :2004
# 终止进程
kill -9 <PID>
```

### Neo4j 连接失败

```bash
# 检查 Neo4j 状态
brew services list | grep neo4j
# 重启服务
brew services restart neo4j
```

### 依赖安装失败

```bash
# 升级 pip
pip install --upgrade pip
# 重新安装
pip install -r requirements.txt --force-reinstall
```

## 运行测试

```bash
# 确保在 backend_fastapi 目录
cd backend_fastapi
conda activate ai-edvision

# 运行所有测试
pytest tests/ -v

# 仅运行冒烟测试
pytest -m smoke
```

## 端口一览

| 服务 | 端口 |
|------|------|
| FastAPI 后端 | 2004 |
| Vue 前端 | 5173 |
| Neo4j Browser | 7474 |
| Neo4j Bolt | 7687 |
| Ollama | 11434 |
