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

### 环境区分

系统通过 `APP_ENV` 区分运行环境：

| APP_ENV 值 | 说明 | 配置文件 |
|------------|------|----------|
| local | 本地开发 | .env |
| development | 开发环境 | .env |
| production | 生产环境 | .env.production |

### 开发环境配置

```bash
# 直接使用 .env 文件 (已包含开发配置)
# APP_ENV=local 为默认值
```

### 生产环境配置

```bash
# 复制生产环境配置模板
cp .env.production .env

# 必须修改以下敏感配置:
# - SECRET_KEY: 改为随机强密钥
# - NEO4J_PASSWORD: 改为实际密码
# - OPENAI_API_KEY: 配置有效的通义千问 API 密钥
# - CORS_ORIGINS: 改为实际的前端域名
```


### 数据库配置 (MySQL)

**连接字符串格式**：
```
DATABASE_URL=mysql+pymysql://user:password@host:port/database
```

**MySQL 初始化步骤**：

```bash
# 1. 登录 MySQL
mysql -u root -p

# 2. 创建数据库
CREATE DATABASE ai_edvision CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 3. 初始化表结构 (两种方式)

# 方式一: 启动应用时自动创建
python run.py

# 方式二: 手动初始化
python scripts/init_db.py
```

**数据库表结构**：

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `videos` | 视频信息 | id, title, filename, filepath, status, duration, tags, summary |
| `users` | 用户信息 | id, username, email, password_hash, gender, education |
| `subtitles` | 字幕数据 | id, video_id, start_time, end_time, text, source, language |
| `notes` | 学习笔记 | id, title, content, video_id, tags, keywords |
| `note_timestamps` | 笔记时间戳 | id, note_id, time_seconds, subtitle_text |
| `questions` | 问答记录 | id, video_id, content, answer |

## 4. 启动依赖服务

```bash
# 启动 MySQL (macOS)
brew services start mysql

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
| http://localhost:2004/docs | Swagger UI 文档 (可交互测试 API) |

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

## 7. 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:328
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
| Vue 前端 | 328 |
| MySQL | 3306 |
| Neo4j Browser | 7474 |
| Neo4j Bolt | 7687 |
| Ollama | 11434 |
