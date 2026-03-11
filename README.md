# EduMind

EduMind 是一个面向教育视频学习场景的智能分析系统，当前仓库包含桌面端、移动端、Android 容器工程，以及以 FastAPI 为主的后端实现。系统围绕视频上传、转录分析、笔记、问答、知识图谱和学习推荐展开。

## 当前仓库结构

```text
EduMind/
├── backend_fastapi/   # 主后端，推荐开发与部署入口
├── backend/           # 旧版 Flask 后端，保留兼容
├── frontend/          # 桌面端 Vue 应用
├── mobile-frontend/   # 移动端 H5 / WebView 前端
├── android-app/       # Android 容器工程
├── docs/              # 方案、提示词与专题说明
├── tests/             # 根目录测试集
├── AGENTS.md          # 仓库协作规范
└── CHANGELOG.md       # 中文变更日志
```

## 主要能力

- 视频上传与处理状态跟踪
- 音视频转录与字幕管理
- 视频摘要、关键词、知识点分析
- 学习笔记与时间点回跳
- 基于视频内容的智能问答
- 知识图谱构建与查询
- 移动端学习流程与 Android 封装

## 技术现状

- 主后端：FastAPI + SQLAlchemy 2.0 + Pydantic
- 旧后端：Flask，保留兼容，不作为新功能首选入口
- 桌面端：Vue 3 + Vite
- 移动端：Vue 3 + Vite，独立目录 `mobile-frontend/`
- Android：`android-app/` WebView 容器工程
- 数据与依赖：MySQL、Neo4j、FFmpeg、Ollama（按功能启用）

## 快速开始

### 1. 启动 FastAPI 后端

```bash
cd backend_fastapi
pip install -r requirements.txt
cp .env.example .env
python run.py
```

默认接口地址：

- 健康检查：[http://localhost:2004/health](http://localhost:2004/health)
- API 文档：[http://localhost:2004/docs](http://localhost:2004/docs)

### 2. 启动桌面端

```bash
cd frontend
npm install
npm run dev
```

### 3. 启动移动端 H5

```bash
cd mobile-frontend
npm install
npm run dev
```

可在 `mobile-frontend/.env` 中配置：

- `VITE_MOBILE_API_BASE_URL`
- `VITE_MOBILE_PROXY_TARGET`

### 4. 构建 Android 容器

```bash
cd android-app
./gradlew assembleDebug
```

如果要加载离线页面，请先构建移动端并把 `mobile-frontend/dist/` 同步到 `android-app/app/src/main/assets/`。

## 运行测试

推荐从仓库根目录执行：

```bash
pytest
```

常用命令：

```bash
pytest -m smoke
pytest -m unit
pytest -m api
pytest -m integration
```

## 推荐开发顺序

1. 先开发 `backend_fastapi/` 新接口与服务
2. 桌面端改动放在 `frontend/`
3. 移动端主业务放在 `mobile-frontend/`
4. Android 容器能力放在 `android-app/`
5. 旧版 `backend/` 仅在兼容场景下维护

## 相关文档

- [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)
- [`CHANGELOG.md`](/Users/yuan/final-work/EduMind/CHANGELOG.md)
- [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)
- [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)
- [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)
