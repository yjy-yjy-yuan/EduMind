# EduMind

EduMind 是一个 iOS-only 移动学习项目，工程链路如下：

1. `backend_fastapi/`：真实后端能力与 MySQL 数据写入
2. `mobile-frontend/`：移动端 H5 UI（由 iOS `WKWebView` 加载）
3. `ios-app/`：iOS `WKWebView` 容器与原生桥接层

不再维护桌面网页版、旧 Flask 后端或 Android 工程。

## 项目结构

```text
EduMind/
├── backend_fastapi/   # 唯一后端
├── mobile-frontend/   # 唯一前端（H5，由 WKWebView 加载）
├── ios-app/           # iOS WKWebView 容器与原生桥接
├── docs/              # iOS 链路相关文档
├── scripts/           # 本地验证、数据库管理、运维脚本
├── AGENTS.md          # 研发规范（AI 与人均遵守）
└── CHANGELOG.md
```

## 架构原则

- 前端只负责 UI、交互、请求发送；不实现业务规则或数据库逻辑
- 后端负责真实功能：上传、音视频提取、Whisper 转录、摘要生成、标签提取、数据库写入、QA、推荐
- 前后端通过 HTTP 端口联调；前端与 `ios-app/` 通过 `WKWebView` bridge 通信
- 数据库必须是 MySQL；尽量适配现有表，不随意改表或加表
- 交付目标是 iOS App，不是独立桌面网页

## 环境要求

- macOS（MacBook Pro）
- Python 3.10+
- Node.js 16+
- MySQL 8+
- FFmpeg
- 通义千问或 DeepSeek API Key

## 快速开始

### 1. 后端

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend_fastapi/requirements.txt
cp backend_fastapi/.env.example backend_fastapi/.env
# 编辑 .env：填写 DATABASE_URL、QWEN_API_KEY 或 DEEPSEEK_API_KEY
python backend_fastapi/run.py
```

默认监听 `0.0.0.0:2004`；健康检查 `http://127.0.0.1:2004/health`，API 文档 `http://127.0.0.1:2004/docs`。

### 2. 移动端前端（开发调试）

```bash
cd mobile-frontend
npm install
cp .env.example .env
npm run dev
```

浏览器仅用于开发调试；实际交付端是 iOS `WKWebView`，默认接口地址指向 `http://127.0.0.1:2004`。

### 3. 构建并同步到 iOS 容器

```bash
bash ios-app/sync_ios_web_assets.sh
```

该脚本执行三步：构建 `mobile-frontend` → 从 `backend_fastapi/.env` 读取端口并刷新 iOS 真机后端地址 → 将 `dist/` 同步到 `ios-app/EduMindIOS/EduMindIOS/WebAssets/`。

iOS 容器使用本地打包资源模式，不是 dev server 直连模式。前端任何改动后均须重新执行此脚本。

### 4. 本地验证

```bash
. .venv/bin/activate
python scripts/validate_backend_smoke.py   # 语法 + 路由导入 smoke 检查
bash ios-app/validate_ios_build.sh         # iOS 构建 + 屏幕方向配置校验
```

`validate_backend_smoke.py` 分两阶段运行：Stage 1 `compileall` 语法/字节码检查，Stage 2 逐进程导入各 router 和推荐 helper（已隔离 torch segfault）。

## 本地 Git Hooks

仓库使用 `pre-commit` 框架统一管理，覆盖三类 hook：

| Hook | 执行内容 |
|---|---|
| `pre-commit` | 基础文件/配置检查、Python `black` / `isort` / `flake8`、Shell 语法检查、前端调试语句守卫 |
| `commit-msg` | Conventional Commits 格式校验（`type(scope): description`） |
| `pre-push` | `scripts/validate_backend_smoke.py` + `npm run build:ios` |

一键安装：

```bash
bash scripts/install_git_hooks.sh
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

说明：

- `ios-app/EduMindIOS/EduMindIOS/WebAssets/` 在 `pre-commit` 排除列表中，由 `sync_ios_web_assets.sh` 同步生成。
- `pre-push` 依赖 `.venv` 和 `mobile-frontend/node_modules` 已就绪。
- CI 环境（`CI` 变量存在时）自动跳过本地专用 hook。
- 如需临时跳过：`git commit --no-verify` / `git push --no-verify`，应作例外而非常态。

## GitHub Actions CI

最小后端 CI 工作流：[`.github/workflows/backend-ci.yml`](.github/workflows/backend-ci.yml)。

触发：`pull_request` + `workflow_dispatch`；path-filter 范围：`backend_fastapi/**`、`pyproject.toml`、`pytest.ini`。

检查项：`ruff check backend_fastapi/tests` + `pytest tests/smoke`（Python 3.10）。

CI 为云端回归门禁，不替代本地 smoke / iOS build 验证链路。本地改动验证默认使用 `validate_backend_smoke.py`，不直接运行 `pytest`。

## MySQL 数据库管理

当前后端显式管理的业务表（6 张）：`users`、`videos`、`notes`、`questions`、`subtitles`、`note_timestamps`。默认数据库名 `edumind`。

```bash
. .venv/bin/activate
python backend_fastapi/scripts/init_db.py --info        # 查看表结构
python backend_fastapi/scripts/init_db.py --create      # 补创建缺失表（不删已有数据）
python backend_fastapi/scripts/init_db.py --reset       # 删除并重建（危险）
python backend_fastapi/scripts/init_db.py --emit-sql backend_fastapi/scripts/mysql_managed_schema.sql
```

导出的 SQL 文件：[`backend_fastapi/scripts/mysql_managed_schema.sql`](backend_fastapi/scripts/mysql_managed_schema.sql)，可直接在 Navicat 执行。

## 用户认证

- 注册接受邮箱或手机号（至少一项），密码要求大小写字母 + 数字 + 特殊字符（≥8 位）。
- 登录只接受邮箱/手机号 + 密码；登录后支持修改用户名（写回 `users.username`）和上传头像（存于 `backend_fastapi/uploads/avatars/`）。
- 所有用户数据写入现有 `users` 表，不新建认证平行表。
- `init_db.py --create` 会补齐 `users` 表所需认证字段（手机号、登录次数等）。
- JWT Token 有效期由 `AUTH_TOKEN_TTL_SECONDS`（默认 604800 秒/7天）控制。

## 语义搜索

后端语义搜索（字幕向量检索）主要文件：

| 文件 | 说明 |
|---|---|
| `backend_fastapi/app/services/search/chunker.py` | 视频切片（按时长自动调整粒度） |
| `backend_fastapi/app/services/search/embedder.py` | 本地文本向量嵌入（`LocalEmbedder`） |
| `backend_fastapi/app/services/search/store.py` | ChromaDB 持久化 |
| `backend_fastapi/app/services/search/search.py` | 搜索编排 |
| `backend_fastapi/app/routers/search.py` | 搜索接口 |
| `backend_fastapi/app/tasks/vector_indexing.py` | 后台索引任务 |

当前能力：字幕语义搜索 + 相似度排序 + `preview_text` 回填；视频处理完成后按配置自动提交索引。

当前限制：搜索路由优先取 `X-User-ID` 请求头（未完全接入认证体系）；iOS / H5 搜索界面为轻量版本，结果摘要与完整认证联动尚未补齐。

部署与限制详情：[`backend_fastapi/SEMANTIC_SEARCH_DEPLOYMENT.md`](backend_fastapi/SEMANTIC_SEARCH_DEPLOYMENT.md)。

验证搜索链路：

```bash
./.venv/bin/python scripts/validate_search_integration.py
```

## AI Agent 开发工作流（Blitz / Codex CLI）

面向本地代码代理（Blitz、Codex CLI 等）的统一脚本：

```bash
bash scripts/blitz_prepare_edumind.sh      # 创建 .venv、安装依赖、同步 WebAssets
bash scripts/blitz_start_backend.sh        # 启动后端
bash scripts/blitz_backend_healthcheck.sh  # 检查 http://127.0.0.1:2004/health
bash scripts/blitz_build_ios.sh            # xcodebuild 构建 iOS 容器
```

更详细的 Agent 接管说明见 [`docs/BLITZ_EDUMIND_WORKFLOW.md`](docs/BLITZ_EDUMIND_WORKFLOW.md)。
## 视频处理与摘要生成

上传或链接导入视频后，后端依次执行：音频提取（FFmpeg）→ Whisper 转录 → 字幕写回（`subtitles` 表）→ 摘要生成（`videos.summary`）→ 标签提取（`videos.tags`）。

大模型不可用时自动降级到本地摘要与关键词提取逻辑，保证字段仍可写入。

可配置项（位于"我的"页处理设置）：

- 识别语言、Whisper 模型
- 摘要风格：`brief` / `study` / `detailed`
- 处理完成后是否自动生成摘要 / 提取标签

补充说明：

- iOS 本地离线转录使用 Apple `Speech` 端侧识别，同步后续写入同一套 `videos`、`subtitles` 表。
- 本地 GGUF / Ollama 模型只影响后端摘要/标签回退链路，不替代 iOS 端语音转文字。

手动补生成接口：

```bash
POST /api/videos/{video_id}/generate-summary
POST /api/videos/{video_id}/generate-tags
```


## 视频推荐

### 接口与场景

- `GET /api/recommendations/videos`：统一推荐接口，支持 `scene=home|continue|review|related`。
- `GET /api/recommendations/scenes`：返回可用场景列表。
- `GET /api/recommendations/ops/metrics`（需登录）：推荐运营聚合指标（`recommendation_import.success_rate`、`processing.completion_rate`）。

### 当前行为

1. **返回窗口**：请求条数规范化到 `6~8`，优先返回相似度 ≥ `RECOMMENDATION_SIMILARITY_MIN_SCORE`（默认 `0.55`）的条目；阈值筛选后不足下限时从同批候选按排序补齐（去重）。
2. **展示口径**：响应 `items[*]` 统一清空 `summary`、`reason_text`、`tags`，仅保留 `reason_label`/`reason_code`；前端不渲染切片描述与内容标签 chips。
3. **标题黑名单**：后端以 `RECOMMENDATION_EXCLUDED_TITLE_KEYWORDS`（默认含 `排列组合插空法详解`）在收口阶段剔除命中条目。
4. **站外候选自动入库**：登录态且 `include_external=true` 时，后端优先对可导入站外候选调用链接导入写入 `videos` 后返回站内视频；由 `RECOMMENDATION_AUTO_IMPORT_EXTERNAL`（默认 `true`）与 `RECOMMENDATION_AUTO_IMPORT_MAX_ITEMS`（默认 `2`）控制。
5. **首页**：`Home.vue` 仅展示标题 + 推荐卡片列表；移除了说明文案、首屏刷新按钮、统计卡片。
6. **推荐中枢页**（`/recommendations`）：Hero + 单列表 + 刷新入口，仅请求 `scene=home`。
7. **视频详情相关推荐**：`scene=related` + `seed_video_id`，排除种子，station 优先同来源 provider。

### API 契约

- `contract_version` 默认 `"2"`（对应 `RECOMMENDATION_CONTRACT_VERSION`）；v2 不再返回 `seed_video_title`，旧版可设为 `"1"`。
- 请求支持 `X-Trace-Id` / `X-Request-Id` 透传，响应头回传。
- 完整契约清单见 [`docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md`](docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md) 第九节。

### 视频详情双页布局

`/videos/:id` 为横向双页：**学习处理**（转录/摘要/笔记/操作）与 **相关推荐**（首次切换时懒加载）。

- 封面区固定在上方（`.video-detail__shared`），不随横向滑动。
- 页签 + `scroll-snap` 分页轨道仅作用于封面下方区域；分页面板不使用 `touch-action: pan-y`，避免吞掉外层横滑。
- 子页索引保存在 `sessionStorage`（`videoDetailSubPage:<id>`）。
- 相关文件：`VideoDetail.vue`、`VideoDetailRecommendPanel.vue`、`VideoDetailRecommendCard.vue`、`recommendationPresentation.js`、`videoDetailTelemetry.js`。
- 埋点通过 `CustomEvent('edumind:telemetry')`（`detail.scope === 'video_detail'`）抛出。

### iOS 已知行为清单

| # | 说明 |
|---|---|
| 1 | `WKWebView` 构建使用单文件 `iife + inlineDynamicImports`，路由懒加载不拆分 chunk |
| 2 | 推荐接口失败或无命中时显示"当前为兜底结果"轻提示 |
| 3 | 屏幕方向锁定为竖屏（`UIInterfaceOrientationPortrait`）；`validate_ios_build.sh` 构建前校验，检测到横屏方向立即报错 |


## 视频删除与运维脚本

- `DELETE /api/videos/{video_id}/delete` 级联删除关联 **问答**（`questions`）、**字幕**（`subtitles`）、**笔记时间戳**（`note_timestamps`）与 **笔记**（`notes`），避免外键约束失败。
- 按标题运维：`scripts/purge_video_recommendation_by_title.py`（需配置 `DATABASE_URL`；默认 dry-run，加 `--execute` 才写库）。`--delete-video` 删整条视频；`--reset-metadata` 仅清空摘要/标签与语义索引标记。

## 视频上下文问答

前端向 `POST /api/qa/ask` 提交 `video_id`、`question`、`chat_mode`；后端基于 `subtitles`、`videos.summary`、`videos.tags` 做轻量 RAG 召回，生成回答后写入 `questions` 表。

移动端自动携带最近几轮历史，支持连续追问。

### 对话模式（`chat_mode`）

| 模式 | 值 | 行为 |
|---|---|---|
| 直接回答 | `direct` | 优先通义千问；失败时切换 DeepSeek `deepseek-chat` 兜底 |
| 深度思考 | `deep_think` | 强制 `deepseek-reasoner`，不兜底；UI 展示可展开的推理过程 |

`/api/chat/modes` 接口返回可用模式列表。

### 流式进度事件（`stream=true`）

`accepted` → `retrieving` → `thinking`/`thinking_complete`（深度思考时）→ `reasoning`/`answering` → `organizing` → `completed`

### 引用片段

后端为字幕类引用附加 `time_order`（按 `start_time` 排序的时间位次），前端按 `time_order` 排序展示，保证多轮问答引用顺序稳定。

### 相关配置

```bash
QWEN_API_KEY=...
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_QA_MODEL=qwen-plus
DEEPSEEK_API_KEY=...
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_QA_MODEL=deepseek-chat
DEEPSEEK_REASONER_MODEL=deepseek-reasoner
QA_DEFAULT_PROVIDER=qwen
QA_MAX_HISTORY_MESSAGES=8
QA_MAX_HISTORY_CHARS=2200
```

## 设计助手（Sleek 代理）

`backend_fastapi/` 统一代理 Sleek API，前端与 iOS 容器不直接暴露 `SLEEK_API_KEY`。

后端接口（均以 `/api/design/` 为前缀）：`GET /status`、`GET/POST /projects`、`GET /projects/{id}/components`、`POST /projects/{id}/messages`、`GET /projects/{id}/runs/{run_id}`、`POST /projects/{id}/screenshots`。

启用：在 `backend_fastapi/.env` 中填写 `SLEEK_API_KEY`（scope 至少含 `projects:read/write`、`components:read`、`chats:read/write`、`screenshots`）。

## 后端测试目录

```
backend_fastapi/tests/
├── unit/        # 单元测试
├── api/         # 接口测试
├── smoke/       # 冒烟测试（CI 门禁）
└── integration/ # 集成测试
```

本地改动验证使用 `python scripts/validate_backend_smoke.py`，不直接使用 `pytest`。
GitHub Actions CI 在云端运行 `pytest tests/smoke` 作为回归门禁。

## 开发约束

1. 真实功能只写在 `backend_fastapi/`
2. `mobile-frontend/` 不直接实现业务规则或数据库逻辑
3. 前端任何改动后必须重新执行 `bash ios-app/sync_ios_web_assets.sh` 同步 WebAssets
4. 规范以 [`AGENTS.md`](AGENTS.md) 与 [`docs/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](docs/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md) 为准
5. 变更日志追加写入 [`CHANGELOG.md`](CHANGELOG.md)，不修改或删除历史记录

## 相关文档

- [`AGENTS.md`](AGENTS.md) — 研发规范（AI 与人均遵守）
- [`CHANGELOG.md`](CHANGELOG.md) — 变更日志
- [`docs/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](docs/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)
- [`docs/NOTE_SYSTEM_IMPLEMENTATION_PROMPT.md`](docs/NOTE_SYSTEM_IMPLEMENTATION_PROMPT.md)
- [`docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md`](docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md)
- [`docs/VIDEO_RECOMMENDATION_UI_IMPLEMENTATION_PROMPT.md`](docs/VIDEO_RECOMMENDATION_UI_IMPLEMENTATION_PROMPT.md)
- [`backend_fastapi/README.md`](backend_fastapi/README.md)
- [`backend_fastapi/README_RUN.md`](backend_fastapi/README_RUN.md)
- [`mobile-frontend/README.md`](mobile-frontend/README.md)
- [`ios-app/README.md`](ios-app/README.md)
