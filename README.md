# AI-EdVision - 智能教育视频分析系统

基于Flask和Vue的智能教育视频分析系统，提供视频处理、知识图谱构建、AI辅助教学等功能。

## 项目简介

AI-EdVision是一个智能教育视频分析系统，旨在通过AI技术提升教育视频的学习效果。系统能够自动处理教育视频，提取关键知识点，构建知识图谱，并提供个性化学习路径推荐。

### 主要功能

- 视频处理与分析：自动提取视频字幕、关键帧和重要内容
- 知识图谱构建：基于视频内容自动构建知识图谱
- 智能问答：基于大语言模型的智能问答系统
- 个性化学习：根据学习者特点推荐个性化学习路径
- 多模态分析：结合视频、音频和文本进行多模态分析

## 项目结构

```content
AI-EdVision/
├── backend/                # Flask后端
│   ├── app/
│   │   ├── __init__.py    # Flask应用初始化
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # API路由
│   │   ├── services/      # 业务逻辑
│   │   ├── tasks/         # 异步任务
│   │   └── utils/         # 工具函数
│   ├── config.py          # 配置文件
│   ├── requirements.txt   # Python依赖
│   └── run.py             # 启动脚本
│
├── frontend/              # Vue前端
│   ├── public/            # 静态资源
│   ├── src/
│   │   ├── assets/        # 资源文件
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   ├── store/         # Vuex状态管理
│   │   ├── api/           # API接口
│   │   └── utils/         # 工具函数
│   ├── package.json       # npm配置
│   └── vite.config.js     # Vite配置
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
git clone https://github.com/yourusername/AI-EdVision.git
cd AI-EdVision
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
conda create -n ai-edvision python=3.10 -y
conda activate ai-edvision

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

1. 启动Celery Worker（处理异步任务）：

   ```bash
   # 在backend目录下
   cd backend
   conda activate ai-edvision
   python -m celery -A app.celery_app worker --loglevel=info -P solo
   ```

2. 启动Flask后端服务：首次启动需要打开VPN

   ```bash
   # 在另一个终端，backend目录下
   conda activate ai-edvision
   python run.py
   ```

3. 启动前端开发服务器：

   ```bash
   # 在另一个终端，frontend目录下
   npm run dev
   # 或允许局域网访问
   npm run dev --host
   ```

4. 在浏览器中访问：
   - 本地访问：http://localhost:5173
   - 局域网访问：http://[您的IP地址]:5173 (使用`--host`选项时)