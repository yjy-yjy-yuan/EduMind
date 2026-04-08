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
- 后端负责真实功能：上传、音视频提取、转录、摘要生成、标签提取、数据库写入、分析
- 前后端通过端口联调
- 数据库必须是 MySQL
- 尽量适配现有表结构，不随意改表或加表

## 环境要求

- MacBook Pro 开发环境
- Python 3.10+
- Node.js 16+
- MySQL
- FFmpeg
- 通义千问或 DeepSeek API Key

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
2. 读取 `backend_fastapi/.env` 中的 `PORT`，自动刷新 iOS 真机默认后端地址
3. 将最新 `dist/` 同步到 `ios-app/EduMindIOS/EduMindIOS/WebAssets/`

## 后端测试目录

后端测试已经统一放在 [backend_fastapi/tests](/Users/yuan/final-work/EduMind/backend_fastapi/tests)：

- `backend_fastapi/tests/unit/`：单元测试
- `backend_fastapi/tests/api/`：接口测试
- `backend_fastapi/tests/smoke/`：冒烟测试
- `backend_fastapi/tests/integration/`：集成测试

当前修改程序时，仓库要求不要用 `pytest` 做本次验证；优先执行：

```bash
. .venv/bin/activate
python scripts/validate_backend_smoke.py
```

`backend_fastapi/tests/` 仍保留历史回归用例与 pytest 风格目录结构；更具体的放置规则见 [backend_fastapi/tests/README.md](/Users/yuan/final-work/EduMind/backend_fastapi/tests/README.md)。

## Git Hooks 与本地质量门

当前仓库使用 `pre-commit` 框架，而不是 Husky。默认本地质量门如下：

1. `pre-commit`
   - 基础文本/配置检查
   - Python `black` / `isort` / `flake8`
   - `mobile-frontend/src/` 下调试语句守卫
2. `commit-msg`
   - Conventional Commits 校验
3. `pre-push`
   - `mypy`
   - `python -m compileall backend_fastapi/app backend_fastapi/scripts scripts/hooks scripts/validate_backend_smoke.py`
   - `python scripts/validate_backend_smoke.py`
   - `cd mobile-frontend && npm run build:ios`

如需本地安装 hooks：

```bash
bash scripts/install_git_hooks.sh
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

如需提前手动跑与 `pre-push` 一致的检查，优先执行：

```bash
MYPYPATH=backend_fastapi ./.venv/bin/python -m mypy --config-file pyproject.toml backend_fastapi/app/models backend_fastapi/app/schemas backend_fastapi/scripts/init_db.py scripts/hooks
mkdir -p .pycache-hook
PYTHONPYCACHEPREFIX="$PWD/.pycache-hook" ./.venv/bin/python -m compileall backend_fastapi/app backend_fastapi/scripts scripts/hooks scripts/validate_backend_smoke.py
./.venv/bin/python scripts/validate_backend_smoke.py
cd mobile-frontend && npm run build:ios
```

说明：

- `ios-app/EduMindIOS/EduMindIOS/WebAssets/` 已在 `pre-commit` 排除列表中，因为它们由 `bash ios-app/sync_ios_web_assets.sh` 同步生成。
- 如确需跳过 hook，使用 `--no-verify`，但默认不建议这样做。

## 语义搜索后端状态

当前仓库已经落下语义搜索后端的第一版骨架和主链路，范围集中在 `backend_fastapi/`：

1. 视频切片：`backend_fastapi/app/services/search/chunker.py`
2. 向量嵌入：`backend_fastapi/app/services/search/embedder.py`、`backend_fastapi/app/services/search/gemini_embedder.py`
3. 向量存储：`backend_fastapi/app/services/search/store.py`
4. 搜索编排：`backend_fastapi/app/services/search/search.py`
5. 搜索接口：`backend_fastapi/app/routers/search.py`
6. 后台索引：`backend_fastapi/app/tasks/vector_indexing.py`

当前已经支持：

- `mp4` / `mov` 切片
- ChromaDB 持久化
- 手动索引接口和索引状态接口
- 视频处理完成后按配置自动提交索引任务
- 多视频查询和按相似度排序返回

当前仍是“后端实验性能力”，还不能把整条链路视为完全闭环：

- `LocalEmbedder` 仍是占位实现
- 搜索结果 `preview_text` 还没有从字幕回填
- 搜索路由尚未接入完整认证体系，当前优先取 `X-User-ID` 请求头，否则回退默认用户
- iOS / H5 搜索界面不在这次提交范围内

部署与当前限制的详细说明见 [backend_fastapi/SEMANTIC_SEARCH_DEPLOYMENT.md](/Users/yuan/final-work/EduMind/backend_fastapi/SEMANTIC_SEARCH_DEPLOYMENT.md)。

## Blitz / Codex CLI 开发工作流

面向 Blitz、Codex CLI、Claude Code 等本地代码代理，当前仓库新增了 4 个统一脚本：

```bash
bash scripts/blitz_prepare_edumind.sh
bash scripts/blitz_start_backend.sh
bash scripts/blitz_backend_healthcheck.sh
bash scripts/blitz_build_ios.sh
```

推荐顺序：

1. `blitz_prepare_edumind.sh`
   创建或复用 `.venv`，安装后端依赖，必要时安装前端依赖，并执行 `bash ios-app/sync_ios_web_assets.sh`
2. `blitz_start_backend.sh`
   激活 `.venv` 并启动 `backend_fastapi/run.py`
3. `blitz_backend_healthcheck.sh`
   默认检查 `http://127.0.0.1:2004/health`
4. `blitz_build_ios.sh`
   用 `xcodebuild` 构建 `ios-app/EduMindIOS/EduMindIOS.xcodeproj`

补充说明：

1. `mobile-frontend/` 任何改动后，都必须重新执行 `bash ios-app/sync_ios_web_assets.sh`
2. iOS 容器是本地打包资源模式，不是 dev server 直连模式
3. 若要做更完整的 iOS 校验，执行 `bash ios-app/validate_ios_build.sh`；该脚本默认执行无签名构建，用于验证本地代码和 `WebAssets` 能否成功编译
4. 更详细的 Agent 接管说明见 [`docs/BLITZ_EDUMIND_WORKFLOW.md`](/Users/yuan/final-work/EduMind/docs/BLITZ_EDUMIND_WORKFLOW.md)

## 摘要生成与处理设置

当前视频处理链路已经包含真实摘要生成，不再停留在 UI-only 占位：

1. 上传或链接导入视频
2. 后端完成音频提取与 Whisper 转录
3. 后端写回字幕文件和 `subtitles` 表
4. 后端继续生成课程摘要并写回 `videos.summary`
5. 后端继续提取学习标签并写回 `videos.tags`

处理设置入口在 iOS 端“我的”页面，当前会影响：

1. 新上传视频
2. 链接导入视频
3. 视频详情页重新处理
4. 失败任务重试

当前可配置项：

1. 识别语言
2. Whisper 模型
3. 摘要风格：`brief` / `study` / `detailed`
4. 是否在处理完成后自动生成摘要
5. 是否在处理完成后自动提取标签

如果在线大模型不可用，后端会自动回退到本地摘要与关键词提取逻辑，保证 `videos.summary` 与 `videos.tags` 仍可生成。

补充说明：

- iOS 本地离线转录当前仍然使用 Apple `Speech` 端侧识别
- 本地 GGUF / Ollama 模型只影响后端本地摘要、标题、标签与语义整理回退链路，不直接替代 iOS 端语音转文字
- iOS 本地离线转录在同步到后端后，仍然继续写入同一套 MySQL `videos`、`subtitles`，并可按配置补写 `videos.tags`

手动补生成接口：

```bash
POST /api/videos/{video_id}/generate-summary
POST /api/videos/{video_id}/generate-tags
```

## 视频推荐当前行为

当前推荐链路已经不是“只按最近时间排序”的早期占位态，默认行为如下：

1. 后端按受限候选集扫描站内视频，不再无上限全表加载。
2. 推荐接口支持 `home / continue / review / related` 四种场景。
3. 首页与推荐页默认通过 `VITE_RECOMMENDATION_INCLUDE_EXTERNAL` 控制是否带站外候选，避免弱网下首屏被站外抓取拖慢。
4. 站外候选会明确区分两类动作：
   - 可直接导入：进入现有 URL 导入链路
   - 暂不可直接导入：打开原始来源页，而不是伪装成已入库视频
5. 推荐页里的“看同主题”会围绕当前站内视频加载 `related` 推荐；若接口暂无结果或请求失败，前端会用当前页已加载的站内内容做同主题兜底，并在当前页“相关推荐”区域内展示结果。
6. `related` 场景在扩站外候选时，会优先继承 seed 视频的原始来源平台语境；例如当前视频来自 YouTube 时，同主题站外候选会优先同来源 provider。

## 视频上下文问答

当前视频问答已经接入真实后端 RAG，不再依赖前端占位回复：

1. 前端向 `POST /api/qa/ask` 提交 `video_id`、`question`、`provider`
2. 后端基于现有 `subtitles`、`videos.summary`、`videos.tags` 组装检索上下文
3. 后端对字幕片段做轻量召回，再调用通义千问或 DeepSeek 生成回答
4. 问答记录写入现有 `questions` 表，不新增平行问答表

为保证连续追问时的上下文记忆，移动端会把最近几轮问答一并提交给后端，后端再结合视频字幕检索结果组织最终提示词；因此“它 / 这个 / 上一题提到的第二点”这类追问不再只靠当前一句话硬猜。

当前移动端问答页支持以下模型交互：

1. 选择 `通义千问` 进行标准在线问答
2. 选择 `DeepSeek` 进行在线问答
3. 当选择 `DeepSeek` 时，可进一步切换：
4. `直接回答`：优先返回速度
5. `深度思考`：优先多步推理质量，通常更慢

当前 `DeepSeek` 的两种模式分别对应：

1. `直接回答` -> `deepseek-chat`
2. `深度思考` -> `deepseek-reasoner`

当前问答页在真实后端模式下还会显示阶段进度，便于区分“还在推理中”还是“已经完成回答”。`POST /api/qa/ask` 在传入 `stream=true` 时会按顺序返回可解析的进度事件，当前至少包含：

1. `accepted`：问题已提交
2. `retrieving`：正在检索视频字幕、摘要与标签
3. `reasoning` / `answering`：正在调用 DeepSeek 或通义千问
4. `organizing`：正在整理回答与引用片段
5. `completed`：最终回答已生成

当前视频问答将 `通义千问` 与 `DeepSeek` 作为两个独立聊天空间处理，但当前隔离范围收敛为“前端状态 + 本地缓存 + 请求处理分流”：

1. 切到 `通义千问` 时，只显示并续写通义千问自己的本地问答空间
2. 切到 `DeepSeek` 时，只显示并续写 DeepSeek 自己的本地问答空间
3. 同一 `videoId` 下，两种 provider 的前端内存状态与本地缓存不会再混用
4. 后端仍会按 `provider` 做处理分流，但在不改现有 `questions` 表结构的前提下，服务端历史恢复默认安全禁用，避免把旧共享记录错误混入新的模型空间

当前问答提供方只支持：

1. `qwen`
2. `deepseek`

相关配置位于 `backend_fastapi/.env`：

```bash
OPENAI_API_KEY=your-qwen-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_API_KEY=your-qwen-api-key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
QA_DEFAULT_PROVIDER=qwen
QWEN_QA_MODEL=qwen-plus
DEEPSEEK_QA_MODEL=deepseek-chat
DEEPSEEK_REASONER_MODEL=deepseek-reasoner
QA_MAX_HISTORY_MESSAGES=8
QA_MAX_HISTORY_CHARS=2200
```

说明：

1. 当前通义千问链路已经可用，`OPENAI_*` 与 `QWEN_*` 都是为 Qwen 的 OpenAI 兼容接口准备的兼容变量。
2. 若要使用 DeepSeek，至少需要补齐 `DEEPSEEK_API_KEY`。
3. 若希望默认问答走 DeepSeek，可将 `QA_DEFAULT_PROVIDER` 改为 `deepseek`。
4. 当前版本不要求修改现有 MySQL `questions` 表；数据库继续只保存基础问答记录，视频问答空间隔离以前端本地缓存与请求参数为准。

## 设计助手（接入 agent-skills / Sleek）

你提供的 `agent-skills` 仓库本质上是 Sleek API 的技能说明，而不是可直接放进 `mobile-frontend/` 的组件包。当前仓库已经按 EduMind 的 iOS-only 架构，将它收敛为一条新的后端代理链路：

1. `backend_fastapi/` 负责保存 `SLEEK_API_KEY`，统一代理 `projects`、`components`、`chat runs`、`screenshots`
2. `mobile-frontend/` 新增“设计助手”页面，只调用 EduMind 自己的 `/api/design/*`
3. `ios-app/` 无需直连 Sleek，也不会暴露第三方 API Key

启用步骤：

```bash
cp backend_fastapi/.env.example backend_fastapi/.env
# 在 backend_fastapi/.env 中补齐：
# SLEEK_API_KEY=...
python backend_fastapi/run.py
```

需要的 Sleek scope 至少包括：

1. `projects:read`
2. `projects:write`
3. `components:read`
4. `chats:read`
5. `chats:write`
6. `screenshots`

当前新增的 EduMind 后端接口：

1. `GET /api/design/status`
2. `GET /api/design/projects`
3. `POST /api/design/projects`
4. `GET /api/design/projects/{project_id}/components`
5. `GET /api/design/projects/{project_id}/components/{component_id}`
6. `POST /api/design/projects/{project_id}/messages`
7. `GET /api/design/projects/{project_id}/runs/{run_id}`
8. `POST /api/design/projects/{project_id}/screenshots`

移动端入口位于“我的”页中的“设计助手”。当前流程支持：

1. 创建或选择 Sleek 项目
2. 直接输入自然语言描述生成页面
3. 自动回显生成结果截图
4. 查看生成组件的 HTML 原型

## MySQL 表管理

当前后端显式管理的业务表只有 6 张：

1. `users`
2. `videos`
3. `notes`
4. `questions`
5. `subtitles`
6. `note_timestamps`

查看当前脚本管理的表结构：

```bash
. .venv/bin/activate
python backend_fastapi/scripts/init_db.py --info
```

只补创建缺失表，不删除现有数据：

```bash
. .venv/bin/activate
python backend_fastapi/scripts/init_db.py --create
```

删除并重建当前后端管理的表：

```bash
. .venv/bin/activate
python backend_fastapi/scripts/init_db.py --reset
```

导出可直接在 Navicat 执行的 MySQL SQL：

```bash
. .venv/bin/activate
python backend_fastapi/scripts/init_db.py --emit-sql backend_fastapi/scripts/mysql_managed_schema.sql
```

默认导出的 SQL 文件位置：

- [`backend_fastapi/scripts/mysql_managed_schema.sql`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/mysql_managed_schema.sql)

当前默认数据库名已统一为 `edumind`。

## 用户认证当前约定

- 注册只接受“邮箱或手机号”至少一项，密码必须至少 8 位，且同时包含大小写字母、数字和特殊字符。
- 登录只接受邮箱/手机号 + 密码。
- 用户数据继续写入现有 `users` 表；不会新建认证平行表。
- 登录后支持在“我的”页修改用户名，并将新值写回 `users.username`。
- 登录后支持上传头像照片；文件保存在 `backend_fastapi/uploads/avatars/`，数据库继续只在现有 `users.avatar` 字段内记录可访问路径。
- `python backend_fastapi/scripts/init_db.py --create` 现在会补齐 `users` 表的认证字段（手机号、重复密码指纹、登录次数）并同步必要索引。

## 测试

```bash
. .venv/bin/activate
python scripts/validate_backend_smoke.py
```

## Git Hooks

仓库当前统一使用 `pre-commit` 管理本地 Git hooks，覆盖：

1. `pre-commit`
2. `pre-push`
3. `commit-msg`

一键安装：

```bash
bash scripts/install_git_hooks.sh
```

该命令会：

1. 复用或创建根目录 `.venv`
2. 安装 `pre-commit` 与 `mypy`
3. 安装 `pre-commit`、`pre-push`、`commit-msg` 三类 hook

当前 hook 规则：

1. `pre-commit`：基础文件检查、Python `black` / `isort` / `flake8`、Shell 语法检查、前端 `console.log` / `debugger` 拦截
2. `pre-push`：对当前已清理干净的 Python 层执行 `mypy`（`backend_fastapi/app/models`、`backend_fastapi/app/schemas`、`backend_fastapi/scripts/init_db.py`、`scripts/hooks`），再跑 `compileall + scripts/validate_backend_smoke.py`，最后执行 `mobile-frontend` 的 `npm run build:ios`
3. `commit-msg`：强制 Conventional Commits，格式为 `type(scope): description`

约定说明：

1. Hook 默认只在本地开发环境执行；脚本检测到 `CI` 时会自动跳过本地专用逻辑
2. `pre-commit` 只检查暂存文件，保持提交前反馈尽量快
3. 如需临时跳过，可使用 `git commit --no-verify` 或 `git push --no-verify`，但这应是明确的例外而不是常态
4. 首次执行 hook 时，`pre-commit` 会拉取并缓存自身依赖，后续会复用缓存
5. `pre-push` 依赖 `.venv` 和 `mobile-frontend/node_modules` 已就绪

## 开发约束

1. 真实功能只写在 `backend_fastapi/`
2. `mobile-frontend/` 不直接实现业务规则或数据库逻辑
3. 前端改动后必须同步 iOS `WebAssets`
4. 文档规范以 `AGENTS.md` 与 `PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md` 为准

## 相关文档

- [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)
- [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)
- [`docs/NOTE_SYSTEM_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/NOTE_SYSTEM_IMPLEMENTATION_PROMPT.md)
- [`docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md)
- [`docs/VIDEO_RECOMMENDATION_UI_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_UI_IMPLEMENTATION_PROMPT.md)
- [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)
- [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)
- [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)
- [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)
