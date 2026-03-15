# EduMind

EduMind 现已收敛为 iOS-only 移动学习项目。唯一有效工程链路如下：

1. `backend_fastapi/`：真实后端能力与 MySQL 数据写入
2. `mobile-frontend/`：移动端 H5 UI
3. `ios-app/`：iOS `WKWebView` 容器

不再维护桌面网页版、旧 Flask 后端或 Android 工程。

## 当前结构

```text
EduMind/
├── backend_fastapi/   # 唯一后端
├── mobile-frontend/   # 唯一前端
├── ios-app/           # iOS 容器
├── docs/              # iOS 链路相关文档
├── AGENTS.md
├── PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md
└── CHANGELOG.md
```

## 架构原则

- 前端只负责 UI、交互、请求发送
- 后端负责真实功能：上传、音视频提取、转录、数据库写入、分析
- 前后端通过端口联调
- 数据库必须是 MySQL
- 尽量适配现有表结构，不随意改表或加表

## 环境要求

- MacBook Pro 开发环境
- Python 3.10+
- Node.js 16+
- MySQL
- FFmpeg
- 按功能启用 Neo4j、Redis、Ollama

## 快速开始

### 1. 创建虚拟环境并启动后端

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend_fastapi/requirements.txt
cp backend_fastapi/.env.example backend_fastapi/.env
python backend_fastapi/run.py
```

默认地址：

- 健康检查：`http://127.0.0.1:2004/health`
- API 文档：`http://127.0.0.1:2004/docs`

### 2. 启动移动端前端

```bash
cd mobile-frontend
npm install
cp .env.example .env
npm run dev
```

说明：

- 浏览器仅用于开发调试
- 实际交付端是 iOS `WKWebView`
- 默认接口地址指向 `http://127.0.0.1:2004`

### 3. 构建并同步到 iOS 容器

```bash
bash ios-app/sync_ios_web_assets.sh
```

该脚本会：

1. 构建 `mobile-frontend`
2. 将最新 `dist/` 同步到 `ios-app/EduMindIOS/EduMindIOS/WebAssets/`

## 测试

```bash
. .venv/bin/activate
pytest backend_fastapi/tests/ -v
```

## 开发约束

1. 真实功能只写在 `backend_fastapi/`
2. `mobile-frontend/` 不直接实现业务规则或数据库逻辑
3. 前端改动后必须同步 iOS `WebAssets`
4. 文档规范以 `AGENTS.md` 与 `PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md` 为准

## 相关文档

- [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)
- [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)
- [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)
- [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)
- [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)
- [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)
