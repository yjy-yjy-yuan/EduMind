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

手动补生成接口：

```bash
POST /api/videos/{video_id}/generate-summary
POST /api/videos/{video_id}/generate-tags
```

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
pytest backend_fastapi/tests/ -v
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
2. `pre-push`：对当前已清理干净的 Python 层执行 `mypy`（`backend_fastapi/app/models`、`backend_fastapi/app/schemas`、`backend_fastapi/scripts/init_db.py`、`scripts/hooks`），再跑后端快速测试集和 `mobile-frontend` 的 `npm run build:ios`
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
- [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)
- [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)
- [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)
- [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)
