# 基于深度学习的视频智能伴学系统设计与实现

基于Flask和Vue的视频智能伴学系统，采用深度学习技术实现视频处理、知识图谱构建、AI辅助教学等功能。

## 项目简介

本系统是一个基于深度学习的视频智能伴学系统，旨在通过AI技术提升教育视频的学习效果。系统能够自动处理教育视频，提取关键知识点，构建知识图谱，并提供个性化学习路径推荐。

### 主要功能

- 视频处理与分析：自动提取视频字幕、关键帧和重要内容
- 知识图谱构建：基于视频内容自动构建知识图谱
- 智能问答：基于大语言模型的智能问答系统
- 个性化学习：根据学习者特点推荐个性化学习路径
- 多模态分析：结合视频、音频和文本进行多模态分析

## 后端架构迁移

本项目已完成从 Flask 到 FastAPI 的后端架构迁移。

### 为什么迁移到 FastAPI？

| 对比项 | Flask (旧) | FastAPI (新) |
|--------|-----------|--------------|
| 请求处理 | 同步阻塞 | 异步非阻塞 (async/await) |
| API 文档 | 无自动生成 | Swagger UI + ReDoc 自动生成 |
| 参数验证 | 手动验证 | Pydantic 自动验证 |
| 后台任务 | Celery + Redis (4 条启动命令) | ProcessPoolExecutor (2 条启动命令) |
| 类型安全 | 无 | 完整类型注解 |
| 测试 | 手动配置 | 依赖注入，易于 Mock |

### 迁移详情

- **框架**: Flask → FastAPI + Uvicorn
- **ORM**: Flask-SQLAlchemy → SQLAlchemy 2.0 (Mapped[] 类型注解)
- **配置**: python-dotenv → Pydantic Settings
- **后台任务**: Celery + Redis → ProcessPoolExecutor
- **验证**: 手动 → Pydantic v2

## 项目结构

```
EduMind/
├── backend/                # Flask 后端 (旧版本，保留兼容)
│   ├── app/
│   │   ├── __init__.py    # Flask 应用初始化
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # API 路由
│   │   ├── services/      # 业务逻辑
│   │   ├── tasks/         # Celery 异步任务
│   │   └── utils/         # 工具函数
│   ├── config.py          # 配置文件
│   ├── requirements.txt   # Python 依赖
│   └── run.py             # 启动脚本
│
├── backend_fastapi/        # FastAPI 后端 (推荐使用)
│   ├── app/
│   │   ├── main.py        # FastAPI 应用入口
│   │   ├── core/          # 核心配置 (config, database, executor)
│   │   ├── routers/       # API 路由 (APIRouter)
│   │   ├── models/        # SQLAlchemy 2.0 模型
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── services/      # 业务逻辑层
│   │   ├── tasks/         # 后台任务 (ProcessPoolExecutor)
│   │   └── utils/         # 工具函数
│   ├── tests/             # pytest 测试框架
│   ├── requirements.txt   # Python 依赖
│   └── run.py             # 启动脚本
│
├── frontend/              # Vue 前端
│   ├── public/            # 静态资源
│   ├── src/
│   │   ├── assets/        # 资源文件
│   │   ├── components/    # Vue 组件
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   ├── store/         # Vuex 状态管理
│   │   ├── api/           # API 接口
│   │   └── utils/         # 工具函数
│   ├── package.json       # npm 配置
│   └── vite.config.js     # Vite 配置
```

## 系统要求

### 硬件要求

- CPU: 推荐Intel Core i5/i7或AMD Ryzen 5/7以上处理器
- 内存: 至少8GB RAM，推荐16GB或更高
- 存储空间: 至少20GB可用空间
- GPU: 推荐NVIDIA GPU（用于加速视频处理和AI模型）

### 软件要求

- 操作系统: Windows 10/11 64位
- Python 3.10
- Node.js 16+
- Neo4j数据库
- Redis内存数据库
- FFmpeg视频处理工具
- Ollama本地大语言模型部署工具

## 环境配置

### 1. 安装Python 3.10

- 访问[Python官网](https://www.python.org/downloads/release/python-3100/)下载Python 3.10
- 安装时勾选"Add Python to PATH"选项
- 验证安装：打开命令提示符，输入`python --version`确认版本为3.10.x

### 2. 安装Node.js

- 访问[Node.js官网](https://nodejs.org/)下载Node.js 16+版本
- 按照默认选项完成安装
- 验证安装：打开命令提示符，输入`node --version`和`npm --version`确认版本

### 3. 安装Redis

#### 3.1 Windows系统
- 访问[Redis for Windows](https://github.com/microsoftarchive/redis/releases)下载最新的Redis-x64-xxx.msi安装包
- 双击安装包进行安装
- 安装时选择"Add the Redis installation folder to the PATH environment variable"
- 验证安装：打开命令提示符，输入`redis-cli --version`确认安装成功

#### 3.2 Mac 系统
-  安装 Redis
brew install redis

-  启动 Redis 服务（后台运行）
brew services start redis

- 或手动启动（前台运行）
redis-server

-  配置文件位置
cat /opt/homebrew/etc/redis.conf

- 启动服务
brew services start redis

- 停止服务
brew services stop redis

- 查看日志
tail -f /opt/homebrew/var/log/redis.log

- 测试连接
redis-cli ping  # 应该返回：PONG

- 进入 Redis 命令行
redis-cli

### 4. 安装FFmpeg

#### 4.1 Windows系统
- 访问[FFmpeg官网](https://ffmpeg.org/download.html)下载FFmpeg
- 解压下载的文件到指定目录（如C:\ffmpeg）
- 将FFmpeg的bin目录添加到系统环境变量PATH中
- 验证安装：打开命令提示符，输入`ffmpeg -version`确认安装成功

#### 4.2 Mac系统

- 安装 FFmpeg
brew install ffmpeg

- 检查版本
ffmpeg -version

- 测试是否正常工作
ffmpeg -version | head -n 1

### 5. 安装Neo4j

#### 5.1 Windows系统
- 访问[Neo4j官网](https://neo4j.com/download/)下载Neo4j Desktop
- 按照安装向导完成安装
- 创建一个新的数据库，设置用户名和密码（默认用户名为neo4j）
- 启动数据库并记录连接信息（URI、用户名和密码）

#### 5.2 Mac系统

- 安装neo4j
brew install neo4j

- 方法1：后台服务（开机自启）
brew services start neo4j

- 方法2：前台运行（关闭终端会停止）
/opt/homebrew/opt/neo4j/bin/neo4j console

- 访问 Web 界面
open http://localhost:7474


### 6. 安装Ollama并下载模型

- 访问[Ollama官网](https://ollama.com/)下载并安装Ollama
- 打开命令提示符，运行以下命令下载所需模型：
  ```bash
  ollama pull deepseek-r1:8b
  ollama pull qwen3:8b
  ```

## 安装与部署指南

### 第一步：克隆项目

```bash
git clone https://github.com/yourusername/EduMind.git
cd EduMind
```

### 第二步：配置数据库连接

1. 修改Neo4j数据库连接信息：
   - 打开`backend/app/utils/knowledge_graph_utils.py`文件
   - 找到`KnowledgeGraphManager`类的`__init__`方法
   - 修改数据库连接信息为您自己的配置：

   ```python
   def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="your_password", similarity_service=None):
   ```

2. 同样修改`backend/app/routes/knowledge_graph.py`文件中的数据库连接信息：

   ```python
   # 创建知识图谱管理器实例
   kg_manager = KnowledgeGraphManager(
       uri="bolt://localhost:7687",
       user="neo4j",
       password="your_password"
   )
   ```

### 第三步：配置环境变量

1. 在`backend`目录下创建`.env`文件（如果不存在）
2. 添加以下配置：

   ```python
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///app.db
   ```

### 第四步：启动Redis服务

```bash
# 在命令提示符或PowerShell中运行
redis-server

# 在另一个终端中验证Redis是否正常运行
redis-cli ping  # 应返回PONG
```

### 第五步：安装后端依赖

```bash
# 创建并激活虚拟环境
cd backend
conda create -n edumind python=3.10 -y
conda activate edumind

# 安装基本依赖
pip install -r requirements.txt

# 安装PyTorch（根据您的环境选择）
# GPU环境（CUDA 11.8）
conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.8 -c pytorch -c nvidia
# 或CPU环境
pip install torch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu

# Mac上使用 MPS 加速
# 安装 PyTorch 2.0.0（支持 MPS 加速）
pip install torch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0
- 安装 PyTorch（conda 会自动选择合适的版本）
conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 -c pytorch

# 安装FAISS（根据您的环境选择）
# Windows/Linux GPU环境（NVIDIA CUDA）
conda install -c conda-forge faiss-gpu=1.8.0 -y

# Mac 系统（包括 M1/M2/M3/M4 芯片）- 使用 CPU 版本的环境(包含其他系统)
# 注意：虽然 FAISS 使用 CPU，但 PyTorch 向量计算仍会使用 MPS 加速
conda install -c conda-forge faiss-cpu=1.8.0 -y

# 初始化数据库（首次安装时按顺序执行）
python init_db.py          # 创建所有数据库表
python run_migration.py    # 运行数据库迁移，添加额外字段

# 如果只是更新表结构（已有数据库时使用）
python update_tables.py    # 更新表结构，不删除数据
```

### 第六步：安装前端依赖

```bash
cd ../frontend
npm install
```

### 第七步：启动系统

#### 方式一：FastAPI 后端 (推荐)

只需 2 条命令，无需 Redis/Celery：

```bash
# 终端 1：启动 FastAPI 后端
cd backend_fastapi
conda activate edumind
python run.py
# 或: uvicorn app.main:app --reload --port 2004

# 终端 2：启动前端
cd frontend
npm run dev
```

访问地址：
- 前端：http://localhost:328
- API 文档：http://localhost:2004/docs
- ReDoc：http://localhost:2004/redoc

#### 方式二：Flask 后端 (旧版本)

需要 4 条命令，依赖 Redis：

1. 启动 Celery Worker（处理异步任务）：

   ```bash
   cd backend
   conda activate edumind
   python -m celery -A app.celery_app worker --loglevel=info -P solo
   ```

2. 启动 Flask 后端服务：

   ```bash
   # 在另一个终端
   conda activate edumind
   python run.py
   ```

3. 启动前端开发服务器：

   ```bash
   cd frontend
   npm run dev
   # 或允许局域网访问
   npm run dev --host
   ```

4. 在浏览器中访问：
   - 本地访问：http://localhost:328
   - 局域网访问：http://[您的IP地址]:328

## 开发者指南

### 配置 Pre-commit 代码检查

本项目使用 pre-commit 进行代码质量检查，包含以下检查项：

- **black**: Python 代码格式化
- **isort**: Python import 排序
- **flake8**: Python 代码风格检查
- **pylint**: Python 代码质量检查
- **mypy**: Python 类型检查
- **通用检查**: BOM、空白、大文件、YAML/JSON 格式等

#### 安装步骤

```bash
# 1. 激活虚拟环境
conda activate edumind

# 2. 安装开发依赖
pip install black isort flake8 pylint mypy pre-commit

# 3. 安装 pre-commit 钩子
pre-commit install

# 4. 验证安装
pre-commit --version
```

#### 使用方法

```bash
# 手动运行所有检查（针对所有文件）
pre-commit run --all-files

# 手动运行所有检查（仅针对暂存文件）
pre-commit run

# 检查未暂存的修改文件
pre-commit run --files $(git ls-files -mo --exclude-standard)

# 跳过 pre-commit 检查提交（不推荐）
git commit --no-verify -m "commit message"
```

#### 配置文件说明

| 文件 | 说明 |
|------|------|
| `.pre-commit-config.yaml` | Pre-commit 钩子配置 |
| `pyproject.toml` | Python 工具配置（black、isort、pylint、mypy） |

### 运行测试

```bash
# 激活环境
conda activate edumind

# 运行所有测试
PYTHONPATH=backend python -m pytest tests/ -v

# 运行特定测试文件
PYTHONPATH=backend python -m pytest tests/unit/test_models.py -v

# 运行带覆盖率的测试
PYTHONPATH=backend python -m pytest tests/ -v --cov=backend/app
```
