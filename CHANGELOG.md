# 变更日志

## 2026-04-08

### 认证示例配置补全
- 更新 [`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：将 `AUTH_TOKEN_TTL_SECONDS` 与 `AUTH_TOKEN_CLOCK_SKEW_SECONDS` 从注释示例改为默认可见配置，避免开发者按示例复制环境文件时遗漏认证过期相关参数。

## 2026-04-04

### 推荐同主题来源偏好与推荐页收口
- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)、[`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)、[`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)：`related` 场景会从 seed 视频 URL 推断优先来源 provider，并把该来源写入站外抓取缓存键、provider 抓取顺序、候选排序和 `external_query` 响应，避免同主题扩展时被异来源结果抢前。
- 更新 [`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)：补充“同主题相关推荐优先同来源 provider” 的历史回归用例说明，固定当前推荐排序预期。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)：首页/上传页会展示推荐查询中的“优先来源”；推荐页移除冗余路线/来源说明区，收口为“场景 -> 当前推荐 -> 同主题扩展”主流程，并在相关推荐卡片上直接展示来源徽标。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步当前 `build:ios` 产物，供 iOS `WKWebView` 加载最新推荐页结构。
- 更新 [`docs/VIDEO_RECOMMENDATION_FEASIBILITY_AND_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_FEASIBILITY_AND_PROMPT.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：补充“相关推荐优先同来源 provider” 的当前行为说明，避免推荐文档仍停留在仅同主题、不含来源语境的旧描述。

### Hook 与验证文档纠错（修正过时 pytest 说明）
- 更新 [`scripts/hooks/pre_push.sh`](/Users/yuan/final-work/EduMind/scripts/hooks/pre_push.sh)、新增 [`scripts/validate_backend_smoke.py`](/Users/yuan/final-work/EduMind/scripts/validate_backend_smoke.py)：将推送前后端校验从 `pytest` 收敛为 `mypy + compileall + backend smoke validation + mobile build:ios`，与仓库“修改程序时禁止使用 pytest 验证”的现行规则保持一致。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)、[`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)、[`backend_fastapi/tests/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/README.md)、[`backend_fastapi/CLAUDE.md`](/Users/yuan/final-work/EduMind/backend_fastapi/CLAUDE.md)：修正文档中仍把 `pytest` 写成当前默认验证命令的过时内容，统一改为现行 smoke/build/static-check 流程。
- 对 2026-03-17 记录的更正说明：此前 `CHANGELOG.md` 与 `README.md` 中关于 `pre-push` 会运行 `pytest` 的描述已经过时；当前规则应以 `pre-push` 中实际执行的非-`pytest` 验证链路为准。

## 2026-04-01

### 新手使用指南与首页信息架构（Guide / Home / iOS WebAssets）
- 更新 [`mobile-frontend/src/views/Home.vue`](mobile-frontend/src/views/Home.vue)：移除「辅助入口」整卡及相关脚本与样式，避免首页冗余入口。
- 更新 [`mobile-frontend/src/views/Guide.vue`](mobile-frontend/src/views/Guide.vue)：
  - 「使用流程」仅保留有序说明，去掉流程 pill；
  - 「详细教程」中「偏好设置」补充 Whisper 模型档位与摘要风格（简洁/学习/详细）的可见说明；
  - 「详细教程」与「常见问题」内全部 `<details>` 共用单一展开状态，实现全局手风琴（同时仅一项展开），并加轻量过渡样式；
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步当前 `npm run build:ios` 产物，供 WKWebView 加载。
- 更新 [`AGENTS.md`](AGENTS.md)、新增根目录 [`index.md`](index.md)：约定 `CHANGELOG.md` 与变更日志工作流索引的关系。

### 分支提交日志（COMMIT_LOG）补全与纠错
- 更新 [`COMMIT_LOG.md`](COMMIT_LOG.md)：为 `0331-refactor/recommendation-flow` 追加 `2026-04-01` 提交条目（`a007418`、`67bc068`）；修正 `0329-feature/notes-video-enhancemen` 小节中误粘贴的重复「分支创建」段落，并将 `6c4fe40` 的补充说明改为嵌套列表。
- 更新 [`index.md`](index.md)：补充与 [`COMMIT_LOG.md`](COMMIT_LOG.md) 的分工说明。

### 视频推荐链路重构（性能/契约/站外）
- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)：新增 `RECOMMENDATION_MAX_CANDIDATES_SCAN`、`RECOMMENDATION_INCLUDE_EXTERNAL_DEFAULT`、`RECOMMENDATION_EXTERNAL_TIMEOUT_SECONDS`、`RECOMMENDATION_EXTERNAL_FETCH_PARALLEL`、`RECOMMENDATION_EXTERNAL_FETCH_RETRIES`。
- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)、[`backend_fastapi/app/routers/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/recommendation.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：站内推荐改为按配置上限加载候选，避免全表扫描；可选 `coach` 查询参数返回模板化 `coach_summary`。
- 更新 [`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)：站外抓取使用可配置超时、有限重试、可选并行抓取与总等待预算；补充缓存键说明文档。
- 更新 [`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)：响应增加可选 `coach_summary`。
- 更新 [`mobile-frontend/src/config/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/config/index.js)、[`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)：首页与推荐页默认 `include_external` 由 `VITE_RECOMMENDATION_INCLUDE_EXTERNAL` 控制；站外失败时展示可操作提示样式。
- 更新 [`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`mobile-frontend/.env.example`](/Users/yuan/final-work/EduMind/mobile-frontend/.env.example)：补充推荐相关环境变量说明。

### 根路径与页面标题统一为 EduMind
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)：根路由 `message` 与启动/关闭日志改为使用 `settings.APP_NAME`（EduMind），去除遗留的 AI-EdVision 文案。
- 更新 [`mobile-frontend/index.html`](/Users/yuan/final-work/EduMind/mobile-frontend/index.html)、[`mobile-frontend/dist/index.html`](/Users/yuan/final-work/EduMind/mobile-frontend/dist/index.html)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.html`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.html)：页面标题改为 EduMind Mobile。

### 认证配置补全（修复登录 500）
- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：补充 `AUTH_TOKEN_TTL_SECONDS` 与 `AUTH_TOKEN_CLOCK_SKEW_SECONDS`，与 [`app/utils/auth_token.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/auth_token.py) 对齐，避免 `POST /api/auth/login` 在签发 token 时因缺少配置字段报错。

### 笔记系统学习链路补全（对齐 NOTE_SYSTEM 提示词缺口）
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：本视频笔记区增加「新建笔记」；跳转问答时附带 `videoTitle` 查询参数。
- 更新 [`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：在视频上下文下增加「记笔记」入口，跳转 `/notes/new` 并传递 `videoId` / `videoTitle`。
- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：时间戳行「移除」、保存时与后端同步（删除已移除、新增无 id、变更先删后加）、「添加时间点」按钮。
- 更新 [`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：笔记列表顶栏与筛选区增加「问答 / 去问答」入口；在筛选了关联视频时跳转 `/qa` 并附带 `videoId`、`videoTitle`。

## 2026-03-30

### iOS WebView 强制切换最新前端资源
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：将 `WKWebView` 切换为无持久缓存数据仓库，并在启动时清理 Cookie，修复 `fix(note-edit): compact timestamp card layout`、`fix(mobile-frontend): align video detail action cards under whisper model` 等前端改动已经进入包内但容器仍可能显示旧版页面的问题。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.html`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.html)：重新同步当前 iOS 构建产物，确保容器实际加载的是包含紧凑时间点卡片、播放器时间戳记笔记和视频详情动作卡片调整后的版本。

### 播放器时间戳记笔记收口
- 更新 [`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：将播放器页收为唯一主入口，继续保留时间戳记笔记流程，但标题固定为分类 + 时间点，分类由系统自动判断，学习想法改为快捷标签输入。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)、[`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：移除视频详情、问答与笔记页里的学习流智能体入口，避免用户在多个页面间被分流。
- 更新 [`backend_fastapi/app/services/learning_flow_agent.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/learning_flow_agent.py)、[`backend_fastapi/app/schemas/agent.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/agent.py)、[`backend_fastapi/tests/api/test_agent_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_agent_api.py)：将后端 agent 收敛为时间戳笔记编排器，不再做问答回写，响应结构也同步去掉问答字段。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步最新 iOS WebView 资源。

### 播放器学习卡片头部压缩
- 更新 [`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：把标题/分类区压成更像学习卡片的头部信息，先展示系统分类和自动标题，再把短标题降级为可选输入，减少表单感和重复填写感。

## 2026-03-29

### 学习流智能体接入视频详情、问答与笔记页
- 新增 [`backend_fastapi/app/schemas/agent.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/agent.py)、[`backend_fastapi/app/services/learning_flow_agent.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/learning_flow_agent.py)、[`backend_fastapi/app/routers/agent.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/agent.py)：新增 `POST /api/agent/execute`，把“理解意图 -> 生成 plan -> 复用 QA / 笔记 / 时间戳 -> 写回现有表”的编排逻辑收口为独立后端服务，不新增业务表。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/tests/api/test_agent_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_agent_api.py)：挂载学习流智能体路由，并补充基础 API 测试骨架。
- 更新 [`mobile-frontend/src/api/agent.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/agent.js)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)、[`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)、[`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：在视频详情、问答、笔记与播放器页增加轻量学习助理入口，前端只负责收集上下文与展示结果，不承载真实业务逻辑。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步最新 iOS WebView 资源。

## 2026-03-28

### 新增分支提交日志文档
- 新增 [`COMMIT_LOG.md`](/Users/yuan/final-work/EduMind/COMMIT_LOG.md)：按“分支 -> 日期 -> 提交”整理自 `0319-feature/user-system` 起的开发记录，便于后续持续补写每个分支、每天的提交日志。

## 2026-03-23

### 离线补跑提示与链接幂等测试补强
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：最近上传卡片右侧标签改为区分“离线队列 / 补跑中 / 在线任务 / 重复”，避免把离线排队任务误读成已经在线成功。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充链接导入重复提交复用 existing video，以及历史 `FAILED` 链接允许重新提交的 API 测试，固化当前后端幂等行为。

## 2026-03-21

### Upload 页接入离线排队与自动补跑触发
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)、[`mobile-frontend/src/services/offlineQueue.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/offlineQueue.js)：上传页在本地文件/链接导入遇到后端不可达、超时或可重试 5xx 时，会将任务写入 IndexedDB 离线队列并立刻展示到最近上传；应用启动、Upload 页进入以及页面从后台回到前台时会自动触发离线补跑，补跑成功后再接回现有 `videoId + 状态轮询` 链路。
- 更新 [`mobile-frontend/src/services/videoStatus.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/videoStatus.js)：补充离线排队与自动补跑中的状态文案，便于最近上传列表区分在线处理和离线补跑阶段。
- 更新 [`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：将“是否可加入离线队列”的错误判定收口到视频 API 层，并在列表页/详情页增加离线补跑提示，明确无视频 ID 的任务仍在上传页等待自动补跑。

### 离线队列基础设施
- 新增 [`mobile-frontend/src/services/offlineQueue.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/offlineQueue.js)：补充基于 IndexedDB 的离线任务存取层，固定使用 `edumind_offline_queue / offline_tasks / taskId` 结构，并预置本地上传、链接导入、失败退避、状态更新等基础能力，供后续 Upload 页接入离线补跑。
- 新增 [`mobile-frontend/src/services/networkStatus.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/networkStatus.js)：统一识别“后端地址已配置但后端不可达”的网络错误、超时与可重试 5xx，作为上传失败进入离线队列的判定基础。

## 2026-03-20

### 用户资料支持修改用户名与头像
- 更新 [`backend_fastapi/app/routers/auth.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/auth.py)、[`backend_fastapi/app/schemas/auth.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/auth.py)：资料更新接口现已支持基于登录态修改用户名，并新增头像上传与头像文件读取接口；头像文件保存在后端 `uploads/avatars/` 目录，数据库继续只写回现有 `users.username` 与 `users.avatar` 字段，不新增表。
- 新增 [`backend_fastapi/tests/api/test_auth_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_auth_api.py)：补充当前用户鉴权、用户名更新落库、重复用户名拦截、头像上传后写回 `users.avatar` 并可读取文件的 API 回归测试。
- 更新 [`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)、[`mobile-frontend/src/api/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/auth.js)、[`mobile-frontend/src/store/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/store/auth.js)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：我的页面补充用户名编辑、头像选择与保存链路，前端状态和 UI-only mock 同步支持资料更新与头像预览。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：同步记录当前用户名修改与头像上传的后端落点约定。

### Git Hooks 可执行位修正
- 更新 [`backend_fastapi/scripts/init_db.py`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/init_db.py)：保留原有 shebang，并补齐可执行权限，消除 `check-shebang-scripts-are-executable` 对初始化脚本的失败告警。

## 2026-03-19

### AGENTS 提交提醒规则
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)：新增提交前提醒要求；后续每次涉及提交时，都会先提醒检查当前分支、暂存内容、验证状态，以及是否误带入敏感信息或机器本地配置。

### Whisper 模型目录文档同步
- 更新 [`docs/Mac Whisper 模型优化指南.md`](/Users/yuan/final-work/EduMind/docs/Mac%20Whisper%20模型优化指南.md)：将旧的桌面模型目录说明统一改为 `/Users/yuan/302_works/whisper_models`，同步修正文档中的默认下载路径、手动校验命令、复制示例与跨平台路径说明，避免继续把模型放到桌面旧目录。
- 更新 [`docs/Mac Whisper 模型优化指南.md`](/Users/yuan/final-work/EduMind/docs/Mac%20Whisper%20模型优化指南.md)：清理同页残留的旧 Celery Worker、旧桌面工程路径和过时配置位置说明，统一改为当前 `backend_fastapi` 后台执行器、Whisper 运行时与健康检查排查方式。

### 本地上传视频按摘要与关键词重命名
- 更新 [`backend_fastapi/app/services/video_content_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_content_service.py)：新增“主标题”提取逻辑，优先基于摘要与标签生成简短中文主题名，在线模型不可用时回退到本地规则提炼。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)：本地上传视频在处理完成后会按摘要/关键词提炼出的主内容重命名原始文件，并同步写回 `videos.title`、`videos.filename`、`videos.filepath`。
- 更新 [`backend_fastapi/tests/unit/test_video_processing_task.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_processing_task.py)：补充处理完成后重命名原始本地视频并同步数据库字段的回归测试。

## 2026-03-18

### Whisper 启动预热与运行时加载管理
- 新增 [`backend_fastapi/app/services/whisper_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/whisper_runtime.py)：集中管理 Whisper 设备选择、模型目录、模型文件存在性检查、已下载/首次下载两档加载超时、单模型缓存复用，以及启动后台预热状态。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)：视频转录阶段改为统一走 Whisper 运行时服务，避免每个任务各自散落模型加载逻辑，并保留现有 MPS 失败后自动回退 CPU 的处理链路。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：FastAPI 启动后会后台预热默认 Whisper 模型；新增 `WHISPER_PRELOAD_ON_STARTUP`、`WHISPER_LOAD_TIMEOUT_SECONDS`、`WHISPER_DOWNLOAD_TIMEOUT_SECONDS` 配置，`/health` 也会返回当前 Whisper 运行时状态，便于本机和 iOS 联调确认模型加载进度。
- 新增 [`backend_fastapi/tests/unit/test_whisper_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_whisper_runtime.py)，更新 [`backend_fastapi/tests/conftest.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/conftest.py)、[`backend_fastapi/tests/smoke/test_app_startup.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/smoke/test_app_startup.py)：补充 Whisper 运行时的缓存复用、超时策略、MPS 回退 CPU、启动预热测试，并在测试环境默认关闭启动预热，避免单测真实加载本机模型。
- 新增 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)，更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/services/processingSettings.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/processingSettings.js)：Whisper 模型选择改为页面内按键式选择；上传页和视频详情页可直接切换处理模型，点击后会同步保存到当前处理设置，并用于新上传、手动处理和失败重试；前端可选模型也补齐到 `large`。
- 更新 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：将模型按键从普通 pill 提升为卡片式选择器，补充模型定位文案、激活态高亮和移动端单列布局，提升在上传页与视频详情页中的可辨识度和点击反馈。

### DeepSeek 推理进度与问答页等待态修复
- 更新 [`backend_fastapi/app/routers/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/qa.py)、[`backend_fastapi/app/utils/qa_utils.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/qa_utils.py)：`POST /api/qa/ask` 在 `stream=true` 时改为返回可解析的 NDJSON 阶段事件流，覆盖 `accepted / retrieving / reasoning|answering / organizing / completed`，并在最终回答生成后继续写入现有 `questions` 表。
- 更新 [`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：问答页改为接入后端阶段进度流，新增顶部 AI 进度条与消息内进度条；DeepSeek `先思考再回答` 模式下，用户现在可以明确看到“已提交、检索中、推理中、整理中、已完成”的实时状态，不再只看到空白等待态。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：补充问答流式阶段进度的实现边界与当前行为说明。
- 更新 [`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：移除顶部独立进度卡片，仅保留消息内进度；问答输入区取消吸底布局，改为紧跟内容区，避免空页面时输入框被压到最底部；DeepSeek 的“先思考再回答”按钮文案同步改为“深度思考”。
- 更新 [`backend_fastapi/app/models/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/qa.py)、[`backend_fastapi/app/routers/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/qa.py)、[`backend_fastapi/app/schemas/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/qa.py)、[`backend_fastapi/scripts/mysql_managed_schema.sql`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/mysql_managed_schema.sql)：视频问答改为按 `user_id + provider + mode + video_id` 做同表隔离；`questions` 表新增 `user_id / provider / mode / model` 作用域字段，视频问答续聊改为优先使用数据库中同一作用域下的历史，避免通义千问与 DeepSeek 在同一视频下串历史；旧未标注记录不会自动混入新 provider 空间。
- 更新 [`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：前端视频问答页按 `user + provider + mode + videoId` 切分内存状态与本地缓存，切换通义千问 / DeepSeek 时会分别恢复各自历史，不再共用同一个 `messages` 数组。

## 2026-03-16

### 摘要生成与处理设置收口
- 新增 [`backend_fastapi/app/services/video_content_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_content_service.py)：新增真实视频内容分析服务，在字幕写回后生成摘要与标签；优先走在线大模型或 Ollama，失败时回退到本地摘要与关键词提取，避免功能停留在占位态。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)、[`backend_fastapi/app/tasks/video_download.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_download.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)：视频处理、链接导入、手动重处理三条链路统一支持 `language`、`model`、`summary_style`、`auto_generate_summary`、`auto_generate_tags` 参数，并将摘要写入 `videos.summary`、标签写入 `videos.tags`。
- 新增 [`backend_fastapi/tests/unit/test_video_content_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_content_service.py)，更新 [`backend_fastapi/tests/unit/test_video_processing_task.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_processing_task.py)：补充摘要回退、标签回退和处理完成后摘要/标签写回数据库的单测覆盖。
- 新增 [`mobile-frontend/src/services/processingSettings.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/processingSettings.js)，更新 [`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：新增“处理设置”入口，统一管理识别语言、Whisper 模型、摘要风格、自动摘要、自动标签，并将其用于新上传、链接导入、详情页重处理和失败任务重试；详情页新增摘要生成与标签提取入口。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：同步当前摘要链路、处理设置作用范围和后端职责边界。

### iOS 真机播放与视频处理链路修复
- 更新 [`backend_fastapi/app/core/executor.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/executor.py)：本地开发默认改用 `ThreadPoolExecutor` 执行后台任务，补充任务完成/异常日志与失败状态回写，修复视频处理任务长时间停留在“已提交，等待处理”的假死问题。
- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)：新增后台任务执行器类型与并发数配置项，便于后续按环境切换。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)：为 Whisper 转录阶段增加持续进度回写与耗时提示，避免长视频在 60% 附近长时间无变化。
- 更新 [`backend_fastapi/.env`](/Users/yuan/final-work/EduMind/backend_fastapi/.env)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)、[`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)：默认 Whisper 模型从 `turbo` 调整为 `base`，避免本地开发因损坏的 `turbo` 缓存触发 1.51GB 模型重下载而长时间卡住。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：处理中视频不再禁用播放按钮，改为允许进入播放器播放原始视频文件。
- 更新 [`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：播放器增加视频处理状态提示，明确当前是否在播放处理中原视频。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：最近上传列表新增自动刷新处理进度条与当前步骤显示，便于真机直接观察后台处理进度。

## 2026-03-11

### 文档对齐
- 重写 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：按当前仓库结构更新为 `backend_fastapi`、`mobile-frontend` 方案。
- 重写 [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：移除旧项目名与过时说明，统一为当前 FastAPI 主后端。
- 重写 [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)：统一运行步骤、环境名和启动命令。
- 重写 [`README_test.md`](/Users/yuan/final-work/EduMind/README_test.md)：修正测试入口与命令示例。

## 2026-03-12

### 移动端 iOS 风格首页改版
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：重设全局色板与视觉变量，改为自然活泼的绿色系风格，并补充 iOS 页面容器与卡片基础样式。
- 更新 [`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：增加背景装饰层与统一页面承载结构，优化移动端沉浸感。
- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：重做底部导航为磨砂悬浮样式，替换为统一 SVG 图标并强化激活态。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：按功能模块重新布局首页（欢迎区、快捷功能矩阵、最近学习内容），保留原有接口逻辑并升级视觉层级。

### 移除 Android、改为仅支持 iOS
- 删除 `android-app/` 目录下全部工程与配置文件（Gradle、Manifest、资源等），仓库不再包含 Android 构建。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：仓库结构改为 `ios-app/`，移除“构建 Android 容器”章节，改为可选 iOS 容器（Xcode + WKWebView）说明。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)：移除对 `android-app/` 与 Android 构建的说明；新增变更日志规范（仅追加 `CHANGELOG.md` 条目、不修改历史）。
- 更新 [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)：将“Android 配合方式”改为“以 iOS 为主的原生容器配合方式”。
- 更新 [`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)：去掉 Android 相关提示文案，改为通用/与 iOS 兼容表述。
- 更新 [`docs/MOBILE_MODULE_PROMPTS.md`](/Users/yuan/final-work/EduMind/docs/MOBILE_MODULE_PROMPTS.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：移除 `android-app` 与 Android 配置，统一为 iOS/`ios-app` 与 WKWebView 说明。
- 移除 `.gitignore`、`.gitignore.new` 中的 Android 相关忽略规则。
- 新增 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：iOS 容器目录说明与 WKWebView 加载 H5 的示例（开发期 dev server、发布期打包资源）。

### Xcode 与运行环境
- 使用 Xcode 连接虚拟机，便于在模拟器/真机上调试 iOS 应用。

## 2026-03-13

### 上传视频功能联调（按 VIDEO_UPLOAD_IMPLEMENTATION / DATABASE_SETUP / 主提示词）
- 更新 [`mobile-frontend/src/api/video.js`](mobile-frontend/src/api/video.js)：移除上传请求中显式 `Content-Type: multipart/form-data`，由 axios 对 FormData 自动设置 boundary，与后端 `File(...)` 兼容。
- 更新 [`mobile-frontend/.env.example`](mobile-frontend/.env.example)：补充真机=前端、端口连调说明及 `VITE_MOBILE_UI_ONLY` 注释（false 时走真实上传/登录）。
- 更新 [`backend_fastapi/.env.example`](backend_fastapi/.env.example)：补充真机连调说明（HOST=0.0.0.0、CORS 加入本机 IP:5173）。

### iOS 空白页修复
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：`ios` 模式增加 `build.assetsDir = ''`，避免 Xcode 复制资源平铺后导致 `index.html` 仍引用 `./assets/*` 而白屏。
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：`ios` 模式输出改为固定文件名（如 `index.js`、`index.css`），避免哈希文件名变化引发容器资源引用错位。
- 更新 [`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)、[`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)、[`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：移除 `filter/backdrop-filter` 相关样式，降低 iOS 26.x 模拟器 WebKit GPU 进程崩溃概率。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：`WKWebView` 资源查找新增“`WebAssets` 子目录 + 根目录”双路径兜底，提升加载成功率并在资源缺失时显示明确提示。
- 更新 [`mobile-frontend/src/utils/storage.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/utils/storage.js)（新增）并接入 [`mobile-frontend/src/store/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/store/auth.js)、[`mobile-frontend/src/utils/request.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/utils/request.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：为 `localStorage` 提供内存降级，避免 `file://` / WebView 安全限制导致启动即崩溃。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：增加全局启动异常捕获与页面内错误展示，避免“空白无提示”。
- 远程仓库调整：主仓将 `origin` 切换为 GitHub，保留 Gitee 为 `gitee` 备用远程。

### iOS 白屏兼容补丁（补充）
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：构建阶段默认改为相对资源路径（`./`），仅 `web` 模式保留绝对路径，避免 `file://` 容器加载 `/assets/*` 失败白屏。
- 更新 [`mobile-frontend/package.json`](/Users/yuan/final-work/EduMind/mobile-frontend/package.json)：新增 `build:web`、`build:android` 脚本，明确 Web 与原生容器构建用途。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：加载 `index.html` 时自动把 `src="/..."`、`href="/..."` 归一化为相对路径，兼容旧构建产物，降低二次白屏概率。
- 更新 [`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)、[`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：构建命令统一指向 `build:ios`（容器）与 `build:web`（网页部署），避免命令误用。

### 对 2026-03-13 记录的更正说明
- 更正 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：撤回“优先 `loadHTMLString` 注入修正路径”的策略，恢复 `loadFileURL` 主路径加载；当检测到旧版绝对资源路径（`/assets/...`）时改为给出明确重建提示，避免脚本模块在 WebView 中被拦截后继续白屏。
- 更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)、[`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：`file://` 场景从 `memory history` 改为 `hash history`，并在 `router.isReady()` 后再挂载应用，修复本地资源模式下可能出现的初始路由空渲染。

### iOS 强制更新能力（无需卸载）
- 更新 [`ios-app/EduMindIOS/EduMindIOS/EduMindIOSApp.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/EduMindIOSApp.swift)：新增启动期强制更新检查（远端清单 + 版本判定），命中后全屏拦截并仅允许跳转更新链接，避免通过“卸载重装”来升级。
- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：新增 `INFOPLIST_KEY_EDUMIND_UPDATE_MANIFEST_URL` 配置项，用于注入更新清单地址。
- 更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：补充强制更新配置说明、清单 JSON 示例与判定规则。

### 移动端 UI 重构（主流程页面）
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)、[`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：重建全局视觉变量、背景装饰与底部导航样式，统一为清晰高对比的新设计语言。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：在不改业务逻辑前提下重构主流程页的版式层级、卡片视觉、状态标签和操作按钮风格。
- 更新 [`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)、[`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)、[`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)、[`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)、[`mobile-frontend/src/views/Knowledge.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Knowledge.vue)、[`mobile-frontend/src/views/LearningPath.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LearningPath.vue)：补齐辅助页面视觉一致性，避免页面风格断层。

### iOS 白屏可观测性与路由回退修复
- 更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)：`file://` 场景回退到 `createMemoryHistory` 并显式 `replace('/')`，降低 WebView 对 hash/history 差异导致的空白首屏风险。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：为 `WKWebView` 增加导航失败处理、JS 错误桥接日志和加载超时兜底页，避免“纯白无报错”并提升定位效率。

### 移动端 UI-only 构建模式（仅界面，预留接口）
- 新增 [`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：提供认证、视频、笔记、问答的本地 mock 数据与占位响应，保持与真实接口兼容的返回结构。
- 更新 [`mobile-frontend/src/config/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/config/index.js)：新增 `UI_ONLY_MODE` 配置，支持环境变量 `VITE_MOBILE_UI_ONLY` 和 URL 参数 `uiOnly` 覆盖（默认开启）。
- 更新 [`mobile-frontend/src/api/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/auth.js)、[`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/api/note.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/note.js)、[`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)：统一接入 UI-only/真实后端双通道，当前阶段仅构建 UI 时可直接运行。
- 更新 [`mobile-frontend/.env.example`](/Users/yuan/final-work/EduMind/mobile-frontend/.env.example)、[`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)：补充 UI-only 默认配置与切换说明。

### iOS 预览链路与白屏诊断增强
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：新增 `WKWebView` 挂载看门狗与更详细的 `NSLog` 日志；当 `index.html` 已加载但前端根节点未挂载时，页面内直接显示诊断提示，不再只有纯白屏。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：将 `#Preview` 宏改为 `PreviewProvider`，规避当前 Xcode 预览插件链路异常对调试结果的干扰。

### 移动端 UI-only 边界收口
- 更新 [`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)：`UI_ONLY_MODE` 下改为纯界面播放器占位，不再在页面层依赖真实视频流与字幕资源。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：移除真实预览图依赖，改为状态驱动的本地封面占位卡片，保持详情页完整 UI 流程。
- 更新 [`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)、[`mobile-frontend/src/views/Knowledge.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Knowledge.vue)、[`mobile-frontend/src/views/LearningPath.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LearningPath.vue)：统一文案为“当前仅实现 UI 与占位交互，后续通过预留接口接入真实能力”，避免页面描述与当前开发阶段不一致。

### iOS 本地资源启动兼容与启动日志增强
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：`ios` 构建改为单文件 IIFE 入口并在构建后把 `index.html` 重写为经典脚本标签，规避 `file://` 场景下 `type="module"` 在 `WKWebView` 中不执行的问题；样式文件名固定为 `index.css`。
- 更新 [`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)：移除 `workflow.svg` 资源依赖，改为纯 DOM/CSS 流程图，避免构建产物继续生成 `import.meta.url`。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：新增 `__edumindBootTrace` 启动轨迹、关键阶段 `console.log` 与全局异常 trace，便于定位前端启动卡点。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：增强 `WKWebView` 控制台桥接，新增原生 boot probe，输出 `readyState`、`#app` 子节点数、前端启动标记和最近 boot trace，便于在 Xcode 控制台精确定位启动失败位置。

### iOS UI-only 本地加载链路收口
- 更新 [`mobile-frontend/vite.config.js`](/Users/yuan/final-work/EduMind/mobile-frontend/vite.config.js)：iOS 产物的入口脚本改为 `defer` 经典脚本，避免 `index.js` 在 `#app` 还未解析完成时抢跑，修复真机 `file://` 场景下的空挂载。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：新增 `DOMContentLoaded`、`window.load`、挂载前后容器状态与 `requestAnimationFrame` 日志，并在真正完成首帧检查后再标记 `bootMounted`。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：移除 dev server 加载分支，iOS 容器固定只加载包内 `WebAssets/index.html`；同步修正 watchdog 提示文案与 probe 容错。
- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：移除 `INFOPLIST_KEY_EDUMIND_DEV_SERVER_URL` 预留项，避免后续误切到 `5173` 路径。
- 更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)、[`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)、[`docs/MOBILE_MODULE_PROMPTS.md`](/Users/yuan/final-work/EduMind/docs/MOBILE_MODULE_PROMPTS.md)：文档统一为“当前 iOS 仅加载本地静态 UI 资源”，消除旧版 `5173` 示例带来的误导。

### 移动端页面适配与字体优化
- 更新 [`mobile-frontend/index.html`](/Users/yuan/final-work/EduMind/mobile-frontend/index.html)：补充移动端 viewport 限制，关闭双击缩放与用户缩放，并禁用电话/邮箱自动识别，避免真机页面误放大与排版抖动。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：重建全局字体栈为 `SF Pro Text/Display + PingFang SC`，统一正文与标题字重、字距、行高；同时补充 `100% text-size-adjust`、流式边距、媒体元素自适应和小屏幕断点，修复页面贴边、挤压和横向溢出问题。
- 更新 [`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：外层壳布局改为 `100dvh` 移动端高度模型，并收紧内容区与背景装饰在小屏设备上的占位，提升 iPhone 真机上的首屏适配性与观感一致性。

### Xcode 控制台分级日志增强
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：新增基于 `OSLog.Logger` 的原生日志封装，将 `WKWebView` 生命周期、probe、watchdog 和错误输出映射为 `info / debug / notice / error / fault` 分级日志，便于在 Xcode 控制台筛选查看。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：前端通过 `window.webkit.messageHandlers.edumindLog` 回传的 `console.info()`、`console.warn()`、`console.error()` 现在会按级别写入原生控制台，不再全部混成同一种日志。
- 更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：补充 `console.info` 启动摘要和挂载成功信息，确保 Xcode 里能直接看到关键 `info` 日志节点。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：新增显式 `DEBUG` 前缀和 `console.debug()` 启动日志，便于在 Xcode 控制台直接搜索 `DEBUG` 查看调试链路。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：将原生与前端桥接日志统一为结构化格式，如 `[DEBUG][Bootstrap] ...`、`[INFO][WebView] ...`、`[ERROR][Router] ...`，降低控制台阅读成本。

### 笔记页交互简化
- 更新 [`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：移除“最近笔记堆叠”区域及其旋转/缩放卡片交互，改为仅保留稳定的普通笔记列表，提升真机点按与滚动操作的可用性。

### 全局背景视觉替换
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：将应用全局背景调整为参考示意图的柔雾渐变风格，以暖米色、淡紫和蜜桃色大面积模糊色块替换原有背景装饰，便于在真机上预览新氛围效果。

### 全局背景视觉调整（冷蓝渐变）
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：将应用背景由暖色柔雾切换为参考示意图的冷蓝抽象渐变风格，使用浅雾蓝底色、青蓝色大面积模糊光斑与右上深蓝主视觉区块，便于真机预览新的整体氛围。

### 全局背景视觉微调（冷蓝渐变二次优化）
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)：进一步强化右上深蓝主视觉区、左侧白雾纵向光带和整体卡片透明度，使应用背景更贴近参考图的冷蓝抽象渐变效果。

### 品牌 Logo 接入
- 新增 [`mobile-frontend/src/assets/edumind-logo.svg`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/edumind-logo.svg)、[`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：新增 EduMind 品牌 logo 资源与可复用展示组件。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)：将首页与登录/注册页的品牌展示替换为新的 EduMind logo。

### iOS 原生 App 图标替换
- 更新 [`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json)：为 iOS 18 风格的 light/dark/tinted 三个通用图标位绑定实际文件名。
- 新增 [`AppIcon-1024.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png)、[`AppIcon-1024-dark.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024-dark.png)、[`AppIcon-1024-tinted.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024-tinted.png)：将新的 EduMind logo 写入原生 App 图标资源。

### 对 2026-03-14 App 图标记录的更正说明
- 更正 [`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/Contents.json)：当前先收敛为单一 1024x1024 主图标 `AppIcon-1024.png`，未继续保留 dark/tinted 变体文件，优先保证原生 App 图标替换稳定生效。

### Logo 布局与渐变文字优化
- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：强化 logo 容器的固定比例与非压缩布局，避免在主页面顶部被按钮或窄屏挤压变形。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：新增全局 `gradient-text` 渐变文字样式。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)：将主标题改为渐变文字，并调整品牌区域布局，避免 logo 出现压缩、挤压。

### 视频上传闭环收口
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/tasks/video_download.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_download.py)、[`backend_fastapi/app/models/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)：本地视频上传改为分块落盘并按 `MAX_CONTENT_LENGTH` 限制体积；链接上传改为立即返回 `downloading` 记录并交由后台任务下载；列表/状态接口补齐 `process_progress`、`current_step`、`error_message`。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/services/videoStatus.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/videoStatus.js)：移动端接入新的下载中状态，链接上传后会在下载完成时自动发起处理，最近上传卡片的状态归一和筛选逻辑同步调整。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`docs/VIDEO_UPLOAD_IMPLEMENTATION.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_UPLOAD_IMPLEMENTATION.md)：补充上传相关 API 测试，并在实现文档中追加本次收口说明。

### iOS 视频上传崩溃修复
- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：补充 `NSCameraUsageDescription`、`NSMicrophoneUsageDescription`、`NSPhotoLibraryUsageDescription`，修复 iOS 在点击视频上传控件时触发 `TCC_CRASHING_DUE_TO_PRIVACY_VIOLATION`。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：将上传控件的 `accept` 从 `video/*` 改为明确的视频扩展名列表，降低系统优先走“拍摄视频”分支的概率。
- 更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：补充 iOS 视频上传权限说明与排查要点。

## 2026-03-15

### 首页统计与视频页联动优化
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：首页“最近视频/已完成/进行中”改为基于全量视频统计，修复统计数与实际处理数不一致的问题；三个统计卡片支持点击跳转至视频页对应筛选视图。
- 更新 [`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)：新增最近视频/已完成/进行中三类筛选视图；对应页面展示视频名称卡片，点击卡片继续进入视频详情页查看具体信息。

### 首页统计卡点击跳转修正与 iOS 验收约束补充
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页统计卡改为 `button + router.push` 明确跳转；补充点击日志 `[INFO][Home] stat-card-click ...`；增强层级与触摸可达性（统计区 z-index 提升、装饰层 `pointer-events: none`），避免被视觉层遮挡导致点击无效。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：新增 iOS WebView 验收硬规则，要求交互改动必须在容器内验证路由跳转和目标页渲染，且每次改动后必须同步最新 `mobile-frontend/dist` 到 iOS 资源。

### iOS-only 项目结构收敛
- 新增仓库外备份目录 `../EduMind_backup_20260315_ios_only/`：在删除旧模块前完成整仓复制，便于回滚。
- 删除旧模块与旧脚本：移除 `frontend/`、`backend/`、`android-app/`、根目录 `tests/`、`test_src/` 以及旧启动脚本，仓库只保留 `backend_fastapi/`、`mobile-frontend/`、`ios-app/` 三段式 iOS 链路。
- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：统一为 MacBook Pro 开发、iOS `WKWebView` 容器、FastAPI 后端、MySQL 持久化的唯一实现方向。

### MySQL 视频处理与转录落库收口
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：本地视频上传成功后立即提交后台处理任务；手动处理接口改为统一走任务提交逻辑，并把状态、进度、错误信息写回当前 `videos` 记录。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)：移除对不存在字段 `processed` 的写入；处理完成后将预览图、视频信息、字幕文件路径写回 `videos`，并在现有 `subtitles` 表可用时写入 Whisper 分段结果；若数据库未启用该表则跳过，不自动建表、不让任务失败。
- 更新 [`backend_fastapi/app/tasks/video_download.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_download.py)：链接视频下载完成后在同一后台任务内继续执行转录处理，避免依赖前端页面停留才能继续推进。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：新增 `AUTO_CREATE_TABLES=false` 默认配置，关闭启动时自动建表，避免运行服务时擅自变更现有 MySQL 表结构。
- 更新 [`backend_fastapi/app/models/user.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/user.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：密码哈希显式固定为 `pbkdf2:sha256`，兼容当前 Python 运行时；删除视频时若进程池不可用则回退为同步清理，避免测试和受限环境直接报错。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`backend_fastapi/tests/unit/test_video_processing_task.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_processing_task.py)：补充自动提交处理任务与转录结果落库测试，覆盖 `videos/subtitles` 现有表的写回行为。
### 2026-03-15 真机视频播放链路修复

- `backend_fastapi` 视频流接口补充 `Range` 支持，适配 iOS `WKWebView` 的分段加载、拖动和断点请求。
- `mobile-frontend` 新增真实视频播放页状态展示与重载能力；只要配置了后端地址，视频相关接口会优先走 FastAPI，不再被 UI-only mock 固定拦截。
- `ios-app` 的 `WKWebView` 开启 inline media playback / AirPlay / PiP，并放开 Web 内容本地网络访问策略，保证真机可通过局域网地址访问 FastAPI 视频流。
- `ios-app` 新增 `EDUMIND_API_BASE_URL` 原生注入；H5 启动时会自动读取并保存默认后端地址，避免真机首次安装仍停留在 `UI ONLY` 页面。
- 修正本地真机联调配置：`backend_fastapi/.env` 改为监听 `0.0.0.0`、修复 MySQL `DATABASE_URL` 格式、允许 `Origin: null`；iOS 默认后端地址从易变的 IP 改为 `.local` 主机名。
- MySQL 认证补充 `cryptography` 依赖，兼容 `sha256_password` / `caching_sha2_password`；播放器页改为优先展示后端返回的明确错误，方便定位数据库或视频接口异常。

## 2026-03-16

### MySQL 受控重建脚本与 Navicat 导入 SQL

- 更新 [`backend_fastapi/scripts/init_db.py`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/init_db.py)：将数据库脚本改为只管理当前 FastAPI 实际使用的 6 张业务表（`users`、`videos`、`notes`、`questions`、`subtitles`、`note_timestamps`），新增 `--create`、`--reset`、`--emit-sql` 能力，支持受控删表重建与 SQL 导出。
- 新增 [`backend_fastapi/scripts/mysql_managed_schema.sql`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/mysql_managed_schema.sql)：生成可直接在 Navicat 执行的 MySQL 重建脚本，包含 `DROP TABLE IF EXISTS` 与完整 `CREATE TABLE` 语句。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：补充后端 MySQL 表管理命令、Navicat 导入入口和当前受控表清单。
- 更新 [`backend_fastapi/.env`](/Users/yuan/final-work/EduMind/backend_fastapi/.env)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`docs/DATABASE_SETUP.md`](/Users/yuan/final-work/EduMind/docs/DATABASE_SETUP.md)：将默认数据库名从 `ai_edvision` 统一调整为项目名 `edumind`，便于在 Navicat 中与项目名称保持一致。

### 真机地址与端口自动同步

- 更新 [`ios-app/sync_ios_web_assets.sh`](/Users/yuan/final-work/EduMind/ios-app/sync_ios_web_assets.sh)：构建 iOS 资源前自动读取 `backend_fastapi/.env` 中的 `PORT` 与当前 Mac `LocalHostName`，同步刷新 iOS 原生默认后端地址，避免端口变化后还要手工修改 Xcode Build Settings。

## 2026-03-18

### 模型按键进一步紧凑化
- 更新 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：将 Whisper 模型选择器进一步压缩为横向可滑动按钮条，当前模型与说明合并到单行头部展示，按钮保留激活高亮但显著减少垂直占位，适配上传页和视频详情页的小屏场景。
- 更新 [`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：开发设置页改为展示当前建议后端地址，不再写死 `2004` 和局域网 IP 示例。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：将真机默认地址说明统一为 `.local + backend_fastapi/.env PORT` 的单点配置链路。

### 数据库配置加载路径修复

- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)：将 `BaseSettings` 的 `env_file` 改为固定读取 `backend_fastapi/.env` 的绝对路径，避免从仓库根目录执行脚本时退回默认 `DATABASE_URL`（`root:password`）导致 MySQL `1045 Access denied`。

### 仓库忽略规则补强

- 更新 [`.gitignore`](/Users/yuan/final-work/EduMind/.gitignore)：补充 `*.sqlite`、`*.db-journal`、`*.sqlite-shm`、`*.sqlite-wal` 等本地数据库运行产物忽略规则，并新增 `**/.idea/` 与仓库根误生成目录 `~/` 的忽略，减少本地大文件或无关缓存被错误纳入版本控制的风险。

### 视频问答 RAG 联调打通

- 更新 [`backend_fastapi/app/routers/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/qa.py)、[`backend_fastapi/app/schemas/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/qa.py)、[`backend_fastapi/app/utils/qa_utils.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/qa_utils.py)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：视频问答改为真实后端 RAG，实现“字幕/摘要/标签检索 + 通义千问或 DeepSeek 在线回答”，新增 `QA_DEFAULT_PROVIDER`、`QWEN_QA_MODEL`、`DEEPSEEK_QA_MODEL`、`DEEPSEEK_REASONER_MODEL` 等配置；问答链路不再要求前端传 `api_key/use_ollama`，并移除 Ollama 作为上下文问答主路径。
- 更新 [`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：移动端问答页接入新的真实问答协议，新增通义千问 / DeepSeek provider 切换、后端错误透传和引用片段展示。
- 新增 [`backend_fastapi/tests/api/test_qa_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_qa_api.py)、[`backend_fastapi/tests/unit/test_qa_utils.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_qa_utils.py)：补充视频问答接口与 RAG 检索逻辑测试，覆盖问答落库、上下文不足校验和 DeepSeek reasoner 选择。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：同步视频上下文问答只允许通义千问 / DeepSeek、问答必须走后端真实 RAG、结果写入现有 `questions` 表的实现边界。

### 在线问答上下文记忆增强

- 更新 [`backend_fastapi/app/schemas/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/qa.py)、[`backend_fastapi/app/utils/qa_utils.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/qa_utils.py)、[`backend_fastapi/app/routers/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/qa.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：新增 `history` 问答历史入参和 `QA_MAX_HISTORY_MESSAGES` / `QA_MAX_HISTORY_CHARS` 配置，后端在做视频检索时会结合最近对话历史改写检索 query，并把历史轮次一并交给通义千问 / DeepSeek，提升连续追问时的上下文记忆稳定性。
- 更新 [`backend_fastapi/app/schemas/chat.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/chat.py)、[`backend_fastapi/app/utils/chat_system.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/chat_system.py)、[`backend_fastapi/app/routers/chat.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/chat.py)：聊天接口收敛为在线 provider-only，只保留通义千问 / DeepSeek 两类在线模型，不再暴露 `use_ollama`。
- 更新 [`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：前端问答页提交最近 8 条对话历史，支持后端在连续追问时保持更稳定的上下文记忆。

### DeepSeek 回答方式切换

- 更新 [`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)、[`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：当用户切换到 `DeepSeek` 时，问答页新增“直接回答 / 先思考再回答”选择按键；前端会把对应的 `deep_thinking` 参数随请求提交给后端，并在本地持久化用户选择。

## 2026-03-16

### 知识图谱可读性测试页

- 新增 [`mobile-frontend/src/tests/knowledgeGraphFixture.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/tests/knowledgeGraphFixture.js)、[`mobile-frontend/src/tests/KnowledgeGraphPreview.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/tests/KnowledgeGraphPreview.vue)：补充仅供测试使用的 mock 知识图谱页面，内置“宽松/标准/拥挤”密度、字号倍率、缩略图开关、自动避让与重排布局，用于观察移动端知识图谱是否出现节点遮挡、字号过小或缩略图堆叠遮蔽。
- 更新 [`mobile-frontend/src/views/Knowledge.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Knowledge.vue)：将现有知识页改为测试承载页，直接加载 `src/tests/` 下的知识图谱预览组件，便于从当前应用入口进入检查页面效果。

## 2026-03-16

### 删除知识图谱功能与测试页

- 删除 [`mobile-frontend/src/views/Knowledge.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Knowledge.vue)、[`mobile-frontend/src/tests/KnowledgeGraphPreview.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/tests/KnowledgeGraphPreview.vue)、[`mobile-frontend/src/tests/knowledgeGraphFixture.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/tests/knowledgeGraphFixture.js)：移除前端知识图谱页面及其测试用 mock 图谱预览文件。
- 更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)、[`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)：删除 `/knowledge` 路由、首页快捷入口和使用指南中的知识图谱入口与文案。
- 删除 [`backend_fastapi/app/routers/knowledge_graph.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/knowledge_graph.py)、[`backend_fastapi/app/routers/knowledge_graph_integration.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/knowledge_graph_integration.py)、[`backend_fastapi/app/schemas/knowledge_graph.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/knowledge_graph.py)、[`backend_fastapi/app/utils/knowledge_graph_utils.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/knowledge_graph_utils.py)：移除后端知识图谱 API、Schema 和 Neo4j 管理逻辑。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/requirements.txt`](/Users/yuan/final-work/EduMind/backend_fastapi/requirements.txt)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：移除知识图谱路由注册、Neo4j 配置项和 `neo4j` 依赖。

## 2026-03-19

### 用户系统注册/登录收口到现有 users 表

- 更新 [`backend_fastapi/app/models/user.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/user.py)、[`backend_fastapi/app/schemas/auth.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/auth.py)、[`backend_fastapi/app/routers/auth.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/auth.py)、新增 [`backend_fastapi/app/utils/auth_security.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/auth_security.py)、[`backend_fastapi/app/utils/auth_token.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/auth_token.py)：注册改为“邮箱或手机号至少一项 + 强密码”，登录改为“邮箱/手机号 + 密码”，并在现有 `users` 表内补充手机号、重复密码检测指纹、登录次数和轻量 token 读取链路，不新增数据库表。
- 更新 [`backend_fastapi/scripts/init_db.py`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/init_db.py)、[`backend_fastapi/scripts/mysql_managed_schema.sql`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/mysql_managed_schema.sql)：数据库初始化脚本现在会为已有 `users` 表补齐当前认证所需字段与索引，导出的 MySQL SQL 同步反映最新 `users` 表结构。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`backend_fastapi/tests/unit/test_models.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_models.py)、[`backend_fastapi/tests/conftest.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/conftest.py)：补充邮箱/手机号注册登录、重复密码拦截、token 获取当前用户等回归测试。
- 更新 [`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)、[`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Guide.vue)、[`mobile-frontend/src/api/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/auth.js)、[`mobile-frontend/src/store/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/store/auth.js)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：前端登录/注册 UI、UI-only mock、资料页展示与使用指南同步切换到邮箱/手机号认证约定，并展示登录次数。

### Git Hooks 收口到 pre-commit 多阶段方案

- 更新 [`.pre-commit-config.yaml`](/Users/yuan/final-work/EduMind/.pre-commit-config.yaml)、新增 [`scripts/install_git_hooks.sh`](/Users/yuan/final-work/EduMind/scripts/install_git_hooks.sh)、[`scripts/hooks/pre_push.sh`](/Users/yuan/final-work/EduMind/scripts/hooks/pre_push.sh)、[`scripts/hooks/commit_msg_check.py`](/Users/yuan/final-work/EduMind/scripts/hooks/commit_msg_check.py)、[`scripts/hooks/check_debug_statements.py`](/Users/yuan/final-work/EduMind/scripts/hooks/check_debug_statements.py)：保留并扩展现有 `pre-commit` 路线，补齐 `pre-commit`、`pre-push`、`commit-msg` 三类 hooks，覆盖 Python 格式化/静态检查、前端调试语句拦截、推送前 `mypy + pytest + build:ios` 以及 Conventional Commits 校验。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`.gitignore`](/Users/yuan/final-work/EduMind/.gitignore)：补充一键安装 hooks 的说明、`--no-verify` 逃生说明，并忽略 `pre-commit` 本地缓存目录。

## 2026-03-18

### 对 2026-03-18 视频问答隔离记录的更正说明

- 更正 [`backend_fastapi/app/routers/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/qa.py)、[`backend_fastapi/app/models/qa.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/qa.py)、[`backend_fastapi/scripts/mysql_managed_schema.sql`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/mysql_managed_schema.sql)：视频问答最终收口为“不改现有 `questions` 表结构”的实现；保留 `provider` 处理分流、前端内存隔离和本地缓存隔离，不再要求为 `questions` 表新增 `user_id / provider / mode / model` 字段。
- 更正 [`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)、[`mobile-frontend/src/api/qa.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/qa.js)：当前通义千问 / DeepSeek 的隔离主要落在前端空间分桶与请求参数上；当后端历史接口返回空结果时，前端会保留本地缓存，不再被空历史覆盖。
- 更正 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：视频问答当前不依赖数据库级 provider 隔离；在不改表前提下，服务端历史恢复默认安全禁用，以避免旧共享 `questions` 记录串入新的模型空间。

## 2026-03-18

### Whisper 模型改为滑动选择

- 更新 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：模型选择器改为横向滑动轨道，支持居中吸附和滑动停止后自动选中最近项；上传页与视频详情页现在使用真正的滑动选择模式，而不是静态按钮排布。

### Whisper 模型选择改为原生下拉

- 更新 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：根据 iOS 处理设置页样式，将模型选择器从横向滑动轨道收口为紧凑的原生 `select` 行；在 `WKWebView` 中点击后可直接唤起系统滑动选择器，且页面占位更接近处理设置页现有样式。
- 更新 [`mobile-frontend/src/services/processingSettings.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/processingSettings.js)、[`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：为每个 Whisper 模型补充“最突出的优点”说明；上传页、视频详情页和“我的-处理设置”页都会在当前选中模型下显示对应优势文案。

### Whisper 模型契约补全与回显修复

- 更新 [`backend_fastapi/app/services/whisper_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/whisper_runtime.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)、新增 [`backend_fastapi/app/services/video_processing_registry.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_processing_registry.py)：补充 Whisper 模型目录与校验能力，新增 `/api/videos/processing-options`，并让视频上传、链接导入、手动重处理、列表、详情、状态接口统一回显 `requested_model / effective_model / requested_language`，避免页面长期只看到默认 `base`。
- 更新 [`backend_fastapi/app/tasks/video_processing.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_processing.py)、[`backend_fastapi/app/tasks/video_download.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/tasks/video_download.py)：任务提交、下载过渡和处理完成/失败阶段的 `current_step` 现在会保留实际 Whisper 模型名，便于不改表结构也能从接口和数据库状态看出本次任务用的是哪个模型。
- 更新 [`mobile-frontend/src/services/processingSettings.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/processingSettings.js)、[`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：前端模型下拉现在优先对齐后端返回的模型目录，上传页/详情页/列表页会显示“本次任务实际模型”，UI-only mock 链路也同步返回模型信息，避免 mock 或回显缺失把所有任务都看成 `base`。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`backend_fastapi/tests/unit/test_video_processing_task.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_processing_task.py)：补充非 `base` 模型在本地上传、链接导入、手动重处理三条链路的传参与回显测试，并同步校验任务完成时的模型落点。
- 新增 [`ios-app/validate_ios_build.sh`](/Users/yuan/final-work/EduMind/ios-app/validate_ios_build.sh)、更新 [`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)：补充 iOS 容器一键验证脚本，串起 WebAssets 同步、`xcodebuild -allowProvisioningUpdates` 构建和常见签名 / CoreSimulator / `actool` 故障提示，方便本机持续验证 `WKWebView` 容器是否能加载最新前端资源。

### Whisper 大模型文件完整性诊断增强

- 更新 [`backend_fastapi/app/services/whisper_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/whisper_runtime.py)：为 Whisper 模型加载失败补充本地文件 SHA256 校验诊断；当 `large-v3.pt` 等已下载模型文件损坏时，运行时会优先返回“本地 Whisper 模型文件校验失败，请删除后重新下载”的明确错误，而不是把问题误判成通用下载失败或加载超时。
- 更新 [`backend_fastapi/tests/unit/test_whisper_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_whisper_runtime.py)：新增损坏模型文件回归测试，覆盖运行时在本地权重校验失败时的错误透传与状态记录。

### Whisper 模型优势文案移到标题行

- 更新 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：将当前选中模型的“优势”说明从下方独立区块移到 `Whisper 模型` 标题右侧，并保持随选择即时切换，减少纵向占位的同时让用户在打开下拉前就能看到当前模型的核心特点。

### 对 Whisper 模型优势位置的更正说明

- 更正 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：当前模型的“优势”说明最终收口到同一个下拉选择框内部，显示在模型名下方；选择框仍使用原生 `select` 承接 iOS 系统滚轮交互，但视觉上会在红框区域内同时展示“当前模型 + 对应优势”。

### Whisper 模型下拉选项显示核心优势

- 更新 [`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：原生下拉选项文本改为同时显示模型名和核心优势摘要，例如 `large · 效果最好`、`medium · 准确率更高`，让 iOS 系统滚轮选择时也能直接看到各模型最突出的特点。

### EduMind Logo 与 AppIcon 替换

- 更新 [`mobile-frontend/src/assets/edumind-logo.svg`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/edumind-logo.svg)：将共享品牌图替换为浅蓝底方形版本，保留脑图/书本主图形，并将底部品牌字样明确改为 `EduMind`；首页、登录页、注册页等所有使用 [`BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue) 的位置会统一显示新 logo。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png)：基于共享 logo 重新生成 iOS AppIcon，和主页品牌图保持同一视觉版本。

### EduMind AppIcon 适配 iOS 图标蒙版

- 新增 [`ios-app/branding/edumind-app-icon.svg`](/Users/yuan/final-work/EduMind/ios-app/branding/edumind-app-icon.svg)、更新 [`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png)：为 iOS AppIcon 单独提供适配版源文件，移除此前在系统图标蒙版里显得过小的内层圆角底板，让浅蓝底直接铺满整个图标画布，并放大主图形与 `EduMind` 字样，避免主屏幕上出现“小 logo 嵌在白块里”的效果。

## 2026-03-20

### 对 2026-03-20 用户资料编辑交互的更正说明

- 更正 [`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：头像不再通过独立按钮选择，而是改为点击当前头像后再触发更换；昵称默认只读，输入框右侧新增修改图标，点击后才进入可编辑状态，再通过“保存资料”写回后端。

### 对 2026-03-20 昵称编辑位置的更正说明

- 更正 [`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：昵称编辑条从“资料设置”区块上移到头像右侧的用户信息区，直接替换原先顶部静态昵称显示；同时缩小输入条和修改图标尺寸，使其更适配头像旁的横向布局。

### 认证接口从 UI mock 接回真实 users 表

- 更正 [`mobile-frontend/src/api/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/auth.js)、[`mobile-frontend/src/store/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/store/auth.js)：认证相关请求不再只要 `UI_ONLY_MODE` 打开就强制走 mock；现在与视频接口保持一致，仅在“没有配置后端地址时”才使用 UI-only 数据。已有的假 token / 假用户缓存也会在切回真实后端时自动清理，避免页面继续显示 `demo_user` 却不写入 MySQL `users` 表。
- 更正 [`mobile-frontend/src/config/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/config/index.js)、[`mobile-frontend/src/api/note.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/note.js)、[`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Login.vue)、[`mobile-frontend/src/views/Register.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)：前端默认不再静默开启 UI-only 模式；笔记接口也与认证/视频统一按“无后端地址时才 mock”处理，登录注册失败时会优先展示后端返回的真实错误，避免页面看似可用但 MySQL 一直没有新数据。

## 2026-03-23

### iOS 原生离线转录架构规则与桥接骨架

- 更新 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)：正式将 `ios-app/` 收口为“`WKWebView` 容器 + 原生离线执行层”，允许 iOS 本地文件访问、音频提取、原生桥接和端侧转录，并要求前端通过 `WKWebView` bridge 与原生层通信。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：新增 `edumindNative` 原生桥 handler，在 WebView 注入统一的请求/响应协议，首批支持 `ping` 和 `getCapabilities`，为后续本地视频选择、音频提取和端侧转录预留稳定入口。
- 新增 [`mobile-frontend/src/services/nativeBridge.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeBridge.js)、更新 [`mobile-frontend/src/main.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/main.js)：前端新增原生桥服务层并在启动时自动探测 iOS 原生桥能力，后续页面只通过该服务访问原生离线能力，不直接散落 `window.webkit.messageHandlers` 调用。

### iOS 本地视频离线转录最小闭环

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：新增 `startOfflineTranscription` 原生 action，接入 iOS 本地视频选择、音频提取、Apple Speech 端侧识别、进度事件和完成/失败回传，并补充语音识别权限文案。
- 更新 [`mobile-frontend/src/services/nativeBridge.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeBridge.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/services/videoStatus.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/videoStatus.js)：上传页新增 “iOS 本地离线转录” 入口和结果展示区，前端通过原生桥发起本地转录，并统一展示 `preparing / extracting / transcribing / completed / failed` 状态。

### 本地离线转录结果持久化与详情页

- 新增 [`mobile-frontend/src/services/nativeOfflineTranscripts.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeOfflineTranscripts.js)：使用 IndexedDB 持久化 iOS 本地离线转录结果，保存状态、文本、分段、语言和更新时间，并通过前端事件通知页面同步刷新。
- 新增 [`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)、更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)：增加本地离线转录详情路由 `/local-transcripts/:taskId`，支持查看完整文本、复制结果和删除本地记录。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：本地离线转录现在会在每次进度/完成/失败事件后自动写入 IndexedDB，并在上传页展示“本地转录历史”，支持从历史记录进入本地详情页。

### 本地离线转录增加全局入口

- 新增 [`mobile-frontend/src/views/LocalTranscripts.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscripts.vue)、更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)：新增本地离线转录列表页 `/local-transcripts`，支持按状态筛选、查看详情和删除结果。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)：首页和视频页增加本地离线转录入口，避免用户只能从上传页找到本地处理结果。

### iOS 本地离线转录语言映射修正

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：原生离线转录现在会优先读取 `locale`，并将 `Other / 中文 / 中文/其他 / English / 英文` 等前端语言值统一归一成可用的 Apple Speech locale，避免把 `other` 直接传给 `SFSpeechRecognizer` 导致识别器初始化失败；同时补充任务启动时的请求语言和归一化 locale 日志，便于真机排查。
- 更新 [`mobile-frontend/src/services/processingSettings.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/processingSettings.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：上传页发起 iOS 本地离线转录时，先将页面处理设置中的语言选项转换为原生侧可识别的 locale（例如 `zh-CN`、`en-US`），降低前后端枚举不一致造成的失败概率。

### iOS 本地离线转录切片识别与本地缓存忽略规则

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：原生离线转录不再只把整段音频一次性交给 Apple Speech，而是将较长音频切成多个小片段顺序识别，并在最终结果中合并文本与时间片段；单个片段若返回 `No speech detected` 会记日志后跳过，不再直接让整条任务失败，从而提高长视频或含静音片段视频的稳定性。
- 更新 [`.gitignore`](/Users/yuan/final-work/EduMind/.gitignore)：新增 `.swift-module-cache/`、`.xcode-derived*/`、`DerivedData/` 等本地 Xcode / Swift 构建缓存忽略规则，避免真机调试后的缓存文件误入 Git 暂存区并触发大文件 hook。

### iOS 本地离线转录增加 Xcode 进度日志

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：每次本地离线转录进度事件、失败事件和完成事件现在都会直接写入 Xcode 控制台日志，日志中包含 `taskId / phase / progress / locale / message`，便于真机排查当前卡在音频提取、分片识别还是结果合并阶段。

### iOS 本地离线转录日志增加文本进度条

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：Xcode 控制台中的原生离线转录日志现在会附带与在线处理风格接近的文本进度条，例如 `[██████░░░░░░░░] 45%`，便于快速判断当前任务推进到了哪个阶段。

### iOS 本地离线转录改为重叠分片与去重合并

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：本地离线转录的音频分片从较长整段切换为更短的重叠分片，并在合并结果时对相邻片段做文本重叠去重；同时在进度日志里带出当前片段的 `start/duration`，用于定位漏句、断句和跨片段识别不连续的问题。

### iOS 本地离线转录增加 16kHz 单声道预处理

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：每个待识别音频片段在送入 Apple Speech 前，会先转换为 `16kHz / 单声道 / PCM` 的识别友好格式；如果预处理失败则记录日志并回退到原始音频，优先提升长视频、远场收音和双声道视频的本地识别稳定性。

### iOS 本地离线转录增加单任务保护

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：原生侧现在会拒绝在已有离线转录任务执行时再次启动新任务；上传页的“iOS 本地离线转录”按钮也会在任务真正完成或失败前保持忙碌态，避免用户重复点击导致并发转录、内存压力上升甚至真机进程被系统终止。

### iOS 本地离线转录增加方言 / locale 明确选择

- 更新 [`mobile-frontend/src/services/processingSettings.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/processingSettings.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)：为 iOS 本地离线转录新增独立的“本地识别语言/方言”设置，可明确选择普通话、粤语、吴语、繁体中文或英语，并单独持久化，不影响后端在线 Whisper 的语言参数。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)、[`mobile-frontend/src/views/LocalTranscripts.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscripts.vue)：原生离线转录对 `yue-CN`、`wuu-CN` 等 locale 增加识别器 fallback，前端各处本地结果页面也统一显示对应方言/语言标签，便于用户确认当前任务是否按正确 locale 识别。

### 离线详情页对齐在线布局并增加本地视频播放器

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：iOS 容器新增 `edumind-local://offline-video/<taskId>` 本地视频自定义 scheme，并在离线任务创建时持久化任务到本地视频文件路径的映射，供 `WKWebView` 直接播放离线原始视频。
- 更新 [`mobile-frontend/src/services/nativeBridge.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeBridge.js)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)：本地离线转录详情页的布局对齐在线视频详情页，新增 hero 区、状态/进度展示和动作按钮，并内嵌本地视频播放器；在 iOS 原生容器中可直接播放对应离线任务的本地原始视频，不再只显示转录文本。

### 本地离线转录复用在线摘要生成

- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)：新增基于 `transcript_text` 直接生成摘要的后端接口，复用现有 `video_content_service.generate_video_summary()`，避免把摘要逻辑下沉到前端页面。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充“本地转录文本生成摘要成功”和“空转录文本被拒绝”的 API 测试，覆盖新增摘要接口的主路径和错误路径。
- 更新 [`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/services/nativeOfflineTranscripts.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeOfflineTranscripts.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)：本地离线转录结果新增 `summary / summaryStatus / summaryStyle` 持久化字段；上传页在本地转录完成后会按当前处理设置自动尝试提取摘要，本地详情页新增与在线视频详情页一致的摘要区，并支持手动重生成。

### 本地离线转录结果同步到 videos 表并生成主标题

- 更新 [`backend_fastapi/app/models/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/scripts/init_db.py`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/init_db.py)：在同一张 `videos` 表中新增 `processing_origin`，明确区分 `online_backend` 与 `ios_offline`；新增 `sync-offline-transcript` 接口，将 iOS 本地离线转录结果写回 `videos` 与 `subtitles`，并基于摘要提炼最关键内容作为视频标题。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充本地离线结果写入 `videos` 表、标记 `ios_offline`、写入字幕分段，以及同一 `task_id` 更新不重复插入的 API 测试。
- 更新 [`mobile-frontend/src/api/video.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/video.js)、[`mobile-frontend/src/services/nativeOfflineTranscripts.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeOfflineTranscripts.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：本地离线转录完成后会自动将结果同步进后端视频库；本地记录会保存 `syncedVideoId / syncStatus`；视频列表和首页识别 `ios_offline` 记录后优先跳转到本地详情页，避免误走在线播放器。

## 2026-03-24

### Agent 统一脚本与 iOS 构建入口

- 新增 [`scripts/blitz_prepare_edumind.sh`](/Users/yuan/final-work/EduMind/scripts/blitz_prepare_edumind.sh)、[`scripts/blitz_start_backend.sh`](/Users/yuan/final-work/EduMind/scripts/blitz_start_backend.sh)、[`scripts/blitz_backend_healthcheck.sh`](/Users/yuan/final-work/EduMind/scripts/blitz_backend_healthcheck.sh)、[`scripts/blitz_build_ios.sh`](/Users/yuan/final-work/EduMind/scripts/blitz_build_ios.sh)：补齐面向 Blitz / Codex / Claude Code 的统一入口脚本，分别覆盖环境准备、后端启动、`/health` 健康检查和 `xcodebuild` 构建；脚本统一采用仓库相对路径、明确失败提示和可复用日志前缀，便于 Agent 在本地连续执行 EduMind 的 iOS-only 开发链路。

### WebAssets 同步与前端 API 基地址诊断增强

- 更新 [`ios-app/sync_ios_web_assets.sh`](/Users/yuan/final-work/EduMind/ios-app/sync_ios_web_assets.sh)：同步脚本现在会明确打印读取到的后端端口、`LocalHostName` 和最终写入的 iOS native API base URL；同步完成后还会强校验 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.html`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.html)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css) 是否存在，缺失时直接以明确错误退出，方便 Agent 自动判断下一步是重建前端还是检查 Xcode 资源拷贝。
- 更新 [`mobile-frontend/src/config/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/config/index.js)：新增运行时 API base 解析器与 `getApiBaseSource()` 导出函数，在保持 `query -> storage -> native -> env -> empty` 既有优先级不变的前提下，补充 `console.info` 输出当前 API base 和来源，便于区分是 query 参数、localStorage、原生注入还是环境变量在生效。

### iOS WebView 容器结构化诊断

- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：在保留本地资源加载、`nativeConfig` 注入、console bridge、watchdog、probe 与本地离线转录能力不变的前提下，补充结构化错误页和错误码，包括 `ERR_WEB_ASSET_MISSING`、`ERR_LEGACY_ASSET_PATH`、`ERR_WEB_BUILD_LAYOUT`、`ERR_NAVIGATION_FAIL`、`ERR_NAVIGATION_INIT_FAIL`、`ERR_NAVIGATION_TIMEOUT`；同时新增 `edumindPageState` JS message handler 与 `window.__edumindReportPageState(...)` 上报入口，用于原生接收前端主动回传的 route、page、business id、mounted 状态并打印结构化日志。

### Agent 工作流文档同步

- 新增 [`docs/BLITZ_EDUMIND_WORKFLOW.md`](/Users/yuan/final-work/EduMind/docs/BLITZ_EDUMIND_WORKFLOW.md)：新增面向 AI agent 和开发者的中文工作流文档，明确当前 iOS-only 架构、正确启动顺序、前端修改后的必做同步操作、`WKWebView` 调试重点、白屏排查顺序、后端连通性排查顺序，以及给 Codex / Claude / Blitz 的操作建议。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：新增 “Blitz / Codex CLI 开发工作流” 小节，简要说明 4 个新脚本的用途、执行顺序、前端改动后必须重新同步 `WebAssets` 的约束，以及进一步查看 [`docs/BLITZ_EDUMIND_WORKFLOW.md`](/Users/yuan/final-work/EduMind/docs/BLITZ_EDUMIND_WORKFLOW.md) 的入口。

## 2026-03-24

### 笔记系统实施提示词落地

- 新增 [`docs/NOTE_SYSTEM_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/NOTE_SYSTEM_IMPLEMENTATION_PROMPT.md)：补充一份可直接交给 Codex / Claude / Blitz 的笔记系统专用提示词，收口当前 iOS-only 架构、现有 `notes` / `note_timestamps` 基线、第一版真实可用目标、实施边界、验收要求与禁止事项。
- 更新 [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：新增“笔记系统实现边界”小节，明确笔记系统必须继续复用现有表结构与后端链路，并指向新的专用提示词文档。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：在相关文档列表中新增笔记系统实施提示词入口，便于后续直接查找和复用。

## 2026-03-24

### 笔记后端接口与测试补强

- 更新 [`backend_fastapi/app/models/note.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/models/note.py)、[`backend_fastapi/app/schemas/note.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/note.py)、[`backend_fastapi/app/routers/note.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/note.py)：笔记返回结构补充 `video_title`，更新接口支持修改或清空 `video_id`，并统一规范化标签字符串，继续在不改表的前提下复用现有 `notes` / `note_timestamps` 链路。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充笔记创建携带标签与时间点、列表按 `video/tag/search` 筛选、时间点新增删除、视频关联更新与标签清空等 API 回归测试。

## 2026-03-24

### 笔记列表筛选与视频上下文入口

- 更新 [`mobile-frontend/src/api/note.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/note.js)、[`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：前端笔记 API 补齐标签聚合、时间点新增/删除接口，并同步扩展 UI-only mock 数据为“视频关联 + 标签 + 时间点”的真实结构。
- 更新 [`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：笔记列表新增关键词搜索、按视频筛选、标签筛选、时间点摘要展示，以及带当前视频上下文的新建入口。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：视频详情页新增“记笔记”入口，可携带 `videoId + videoTitle` 进入新建笔记流程。

## 2026-03-24

### 笔记编辑页接入时间点管理

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：新建/编辑页新增关联视频、标签推荐、重点时间点的新增/删除/保存能力，并支持从路由 query 预填视频上下文与初始时间点。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步最新移动端前端构建产物，确保 iOS `WKWebView` 加载的是当前笔记编辑页实现。

## 2026-03-24

### 视频笔记回显与记忆闭环修复

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：当用户从视频上下文记笔记但正文为空时，编辑页会基于关联视频和重点时间点自动生成可保存的记忆内容，避免“看起来已记笔记，实际没有落库”的情况；保存成功后还会带着 `noteId` 返回笔记页。
- 更新 [`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)：笔记页新增“刚保存/刚更新笔记”的回显提示、置顶与高亮逻辑，确保从视频详情页回来后能直接看到对应笔记。
- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：视频详情页新增“本视频笔记”预览区，直接展示当前视频最近的笔记、重点时间点摘要和进入全部笔记的入口，形成视频学习到笔记回看的记忆闭环。

## 2026-03-24

### 视频摘要一键导入笔记

- 更新 [`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)：视频详情页摘要区新增“一键导入到笔记”入口；在线模式下直接复用现有笔记创建/更新接口写入 `notes` 表，标题固定使用当前视频题目，内容写入当前摘要文本，并只更新同视频下的 `summary` 类型笔记，避免误覆盖普通学习笔记。
- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：从视频上下文进入新建笔记时，标题会优先预填当前视频题目，减少手工命名成本并统一视频笔记命名口径。

## 2026-03-24

### iOS 本地校验改为无签名构建

- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：移除工程中硬编码的 `Apple Development`、`DEVELOPMENT_TEAM = 669BK65A7K` 和自动签名设置，Debug / Release 默认改为无签名构建，避免仓库继续继承历史工程里的账号配置导致本机 `xcodebuild` 失败。
- 更新 [`ios-app/validate_ios_build.sh`](/Users/yuan/final-work/EduMind/ios-app/validate_ios_build.sh)、[`scripts/blitz_build_ios.sh`](/Users/yuan/final-work/EduMind/scripts/blitz_build_ios.sh)：本地 iOS 校验与 Agent 构建脚本统一改为无签名模式，默认走 `generic/platform=iOS`，用于验证当前容器工程与 `WebAssets` 是否可成功编译；真机安装仍需在 Xcode 中单独配置 Team / 描述文件。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`ios-app/README.md`](/Users/yuan/final-work/EduMind/ios-app/README.md)、[`docs/BLITZ_EDUMIND_WORKFLOW.md`](/Users/yuan/final-work/EduMind/docs/BLITZ_EDUMIND_WORKFLOW.md)：同步说明 `validate_ios_build.sh` 现在是“无签名本地校验”入口，避免继续把它误解为必须依赖 Apple ID 的签名构建。

## 2026-03-24

### 笔记重点时间点接入字幕自动回填与摘要片段选择

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：笔记编辑页新增“摘要关联片段”区，会基于当前视频摘要和语义合并字幕展示可选片段；点击片段后会同时把对应秒数写入重点时间点，并把片段正文追加到笔记内容。新增重点时间点时，输入秒数后也会自动补最近字幕，并把匹配到的主要内容写进笔记正文。
- 新增 [`mobile-frontend/src/api/subtitle.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/subtitle.js)，更新 [`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：前端新增视频字幕与语义分段接口封装，UI-only mock 同步补齐原始字幕和语义片段数据，保证笔记编辑页在 mock / live 两种模式下都能走通。
- 更新 [`backend_fastapi/app/routers/subtitle.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/subtitle.py)、[`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：字幕接口改为按开始时间排序返回；当数据库里缺少 `subtitles` 行但视频仍保留 `.srt` 文件时，会自动从字幕文件回退解析，确保旧视频也能支持按秒自动补字幕与片段选择。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步最新前端构建产物，确保 iOS `WKWebView` 加载的是当前笔记编辑页实现。

## 2026-03-24

### 对 2026-03-24 “iOS 本地校验改为无签名构建” 的更正说明

- 更新 [`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：工程默认配置恢复为可签名状态，继续使用 `Automatic` 与现有 `Apple Development` Team，解决真机安装时报 `No code signature found` 的问题。
- 保持 [`ios-app/validate_ios_build.sh`](/Users/yuan/final-work/EduMind/ios-app/validate_ios_build.sh) 与 [`scripts/blitz_build_ios.sh`](/Users/yuan/final-work/EduMind/scripts/blitz_build_ios.sh) 的无签名覆盖参数不变；无签名仅用于本地编译校验，不再等同于 Xcode 工程默认产物。

## 2026-03-24

### 对 2026-03-24 “笔记重点时间点接入字幕自动回填与摘要片段选择” 的更正说明

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：移除编辑页里重复展示的“当前摘要”正文和按时间节点展开的摘要片段卡片，避免与视频处理页已有摘要重复；重点时间点的秒数输入、自动补字幕、以及片段内容自动写入笔记正文的能力保留不变。

## 2026-03-24

### 对 2026-03-24 “笔记重点时间点接入字幕自动回填与摘要片段选择” 的再次更正说明

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：恢复编辑页中的“当前摘要”面板和摘要片段卡片列表，回到上一步版本；重点时间点、自动补字幕和片段内容联动能力继续保留。

## 2026-03-24

### 对 2026-03-24 笔记编辑页摘要展示的最新更正说明

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：删除笔记编辑页中的摘要正文展示和下方按时间节点展开的摘要卡片，避免与视频处理页已有摘要重复；重点时间点、自动补字幕和片段内容自动写入笔记正文继续保留。

## 2026-03-24

### 对 2026-03-24 笔记编辑页摘要展示的恢复说明

- 更新 [`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)：恢复笔记编辑页中的摘要正文展示和摘要片段卡片列表，撤销上一笔误删；时间点、自动补字幕和片段内容联动能力保持不变。

## 2026-03-25

### 视频推荐接口

- 新增 [`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)、[`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)、[`backend_fastapi/app/routers/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/recommendation.py)，并更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)：新增 `/api/recommendations/scenes` 与 `/api/recommendations/videos`，复用现有 `videos` 与 `users` 数据，先提供首页推荐、继续学习、复盘推荐和相关推荐四类接口契约。
- 新增 [`backend_fastapi/tests/api/test_recommendation_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_recommendation_api.py)：覆盖推荐场景枚举、首页推荐排序，以及 `related` 场景的 `seed_video_id` 约束，固定接口行为。

## 2026-03-25

### 首页推荐位接入

- 新增 [`mobile-frontend/src/api/recommendation.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/recommendation.js)，并更新 [`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：前端增加推荐接口封装与 UI-only mock 数据源，为首页推荐位和后续推荐页提供稳定调用入口。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：在保留原有首页骨架的前提下新增“推荐视频”区，并接入首页推荐接口，优先展示值得继续处理或复盘的视频。

## 2026-03-25

### 首页层级与视觉收束

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：首页改为“首要动作 / 继续学习 / 辅助入口 / 推荐视频”四段结构，收掉过重的面板堆叠，保留推荐链路的同时把主任务入口、继续学习和辅助入口分层展示。

## 2026-03-25

### Upload 页动线收束

- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：将上传页重排为“处理设置 -> 选择提交方式 -> 对应表单 -> 任务结果”四段，并把方式切换收成更轻的分段控件，减少表单堆叠和说明噪音。

## 2026-03-25

### Videos 页层级优化

- 更新 [`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)：列表页增加更清晰的概览、筛选计数、空状态和快捷动作，并把自动刷新与离线补跑提示集中展示，降低“后台控制台”感。

## 2026-03-25

### 对 2026-03-25 首页、上传页与视频库布局收束的更正说明

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)：撤回 2026-03-25 的首页、上传页和视频库层级重排，恢复为上一版页面布局，保留推荐、上传、视频状态与本地转录能力本身，不再继续使用收束后的新版界面结构。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：重新同步恢复后前端产物，确保 iOS `WKWebView` 容器加载到的是旧版页面布局而不是先前打包进 App 的新版资源。

## 2026-03-25

### 视频推荐实现提示词

- 新增 [`docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md)：补充面向 Codex / Claude / Blitz 的专用提示词，明确视频推荐要基于现有 `videos` 标签先做站内聚类，再扩展 B 站 / YouTube / 中国大学慕课外部候选元数据、标签处理和导入链路，并把“按可独立提交切片推进、每组改动超过 800 行必须继续拆分、CHANGELOG 只能追加”等硬约束写进主提示词。
- 更新 [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：在总控实现文档和仓库文档索引中补充视频推荐实现边界与专用提示词入口，保持 iOS-only 架构说明与推荐建设方向一致。

## 2026-03-25

### 首页推荐预览

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：在保留当前首页基础结构的前提下新增“推荐学习”入口和首页推荐预览区，接入现有推荐接口，并兼容站外候选跳转到上传页预填 URL。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页推荐预览切片对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 首页 Hero 刷新

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页顶部欢迎区调整为更聚焦的 hero 结构，补充上传新内容和查看视频库的主按钮，并同步刷新统计卡片的视觉层级。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页 hero 切片对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 首页继续学习总览

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：把首页中段从分散的快捷卡片和列表收成“继续学习”总览，新增聚焦视频卡、最近进入列表、离线转录与复盘概览，并补充辅助入口条带。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页继续学习总览切片对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 首页推荐区精修

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页推荐区改为更清晰的推荐面板，补充推荐理由、标签与时间信息展示，并增加直达推荐页的入口按钮。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页推荐区精修切片对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 推荐页上下文总览

- 更新 [`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)：新增“当前推荐上下文”面板，把当前场景、主题筛选、相关推荐种子和结果构成集中展示，并补充清除主题、清除相关推荐、导入新链接的快捷动作。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步推荐页上下文总览切片对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 首页推荐系统卡片

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：在首页顶部统计区补充“推荐系统”卡片，复用当前首页推荐数据展示入口状态，并直接接到推荐页。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页推荐系统卡片切片对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 首页统计卡统一尺寸

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：为首页顶部 4 张统计卡统一补齐底部提示文案，并调整卡片为一致的最小高度和内部布局，避免“推荐系统”卡片与其他卡片尺寸不一致。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页统计卡尺寸修正对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 对 2026-03-25 首页统计卡记录的更正说明

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页顶部 4 张统计卡改为单行横排展示，移除底部提示文案，统一为与原统计卡一致的紧凑卡片结构，避免“推荐系统”入口破坏横向排布。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页统计卡横排修正对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 对 2026-03-25 首页统计卡横排记录的补充更正

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：补上首页统计区容器的 `grid` 布局声明，并让 4 张统计卡在 iOS 首页顶部按单行四列真正横向铺开，修复卡片被块级堆叠成竖列的问题。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页统计区横排布局补充修正对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 对 2026-03-25 首页统计卡移动端尺寸的补充更正

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：修正移动端断点下 `.stats` 被错误降为单列的问题，并将首页顶部 4 张统计卡压回更接近原始尺寸的紧凑规格，确保一横排放下且卡片大小一致。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)：同步首页统计卡移动端横排与尺寸修正对应的 iOS `WKWebView` 静态资源。

## 2026-03-25

### 推荐后端科目归一与主题聚类

- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)：在现有推荐服务中新增科目识别、标签别名归一、主题主键提取和聚类桶排序逻辑，让已上传视频可以按“科目 + 主题”信号参与首页推荐、复盘推荐和相关推荐排序。
- 更新 [`backend_fastapi/tests/api/test_recommendation_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_recommendation_api.py)、[`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)：补充推荐接口和推荐服务测试，覆盖科目标签回填、标题/摘要推断科目以及相关推荐优先返回同科目内容的主路径。

## 2026-03-25

### 对 2026-03-25 推荐后端科目归一记录的补充更正

- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)：补充“排列组合 / 插空法 / 勾股定理 / 三角形”等数学主题关键词，修正真实已上传视频里部分数学内容未稳定归入“数学”科目的问题。
- 更新 [`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)：新增排列组合类视频归入数学科目的单测，避免后续回归。

## 2026-03-25

### 对 2026-03-25 重提标签科目未展示问题的修正

- 更新 [`backend_fastapi/app/services/video_content_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_content_service.py)：为真实标签生成链路补上科目识别与科目标签回写，让“提取标签 / 重提标签”在写回 `videos.tags` 时直接带上“数学”等科目标签，而不是只生成知识点标签。
- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)：改为复用视频内容服务里的共享科目归一规则，保证视频详情页标签与推荐聚类使用同一套科目判断逻辑。
- 更新 [`backend_fastapi/tests/unit/test_video_content_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_content_service.py)、[`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充“生成标签后返回并写回科目标签”的单测和 API 测试，覆盖 `generate-tags` 主路径。

## 2026-03-26

### 推荐后端接入站外候选元数据

- 新增 [`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)：抽象 B 站、YouTube、中国大学慕课 3 个站外候选 provider，统一抓取轻量元数据并补上科目、主题、标签归一，且单个 provider 失败不会阻断整体推荐接口。
- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)：为推荐链路新增 `include_external` 混合推荐能力，根据当前场景与站内主题推导站外检索词，并把站内视频与站外候选按统一的“科目 + 主题”信号合并排序。
- 更新 [`backend_fastapi/app/routers/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/recommendation.py)、[`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)：扩展推荐接口参数与返回结构，支持 `include_external`、`is_external`、`item_type`、`external_url`、`source_label`、`subject`、`cluster_key` 等字段，让移动端可以直接区分站内视频和站外候选。
- 更新 [`backend_fastapi/tests/unit/test_external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_external_candidate_service.py)、[`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)、[`backend_fastapi/tests/api/test_recommendation_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_recommendation_api.py)：补充 provider 解析、失败隔离和推荐接口混合返回测试，覆盖站外候选主路径。

## 2026-03-26

### 新增推荐系统 UI 优先实现提示词

- 新增 [`docs/VIDEO_RECOMMENDATION_UI_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_UI_IMPLEMENTATION_PROMPT.md)：补充“推荐系统 UI 优先”的专用提示词，明确本轮以首页推荐入口、独立推荐页、站外候选卡片、上传页导入承接和 iOS `WKWebView` 可用性为主，不优先扩展推荐后端算法。
- 更新 [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：补充 UI 优先推荐提示词入口，便于后续直接给 AI 编码助手下达“先改推荐界面”的任务。

## 2026-03-26

### 推荐系统 UI 第一轮页面修改

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页推荐区收成“推荐中枢预览”，补充站内/站外构成概览、下一步学习动作提示，并让首页预览直接混入真实推荐接口返回的站外候选。
- 更新 [`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)：强化推荐页的中枢感，新增推荐路线、来源总览、站外候选导入说明和当前场景的站外提示，让用户更容易区分站内视频与站外导入项。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：补充“从推荐导入”承接横幅，明确推荐链接会进入导入学习链路，并高亮链接导入卡片，减少从推荐页跳转到上传页后的理解成本。

## 2026-03-26

### 推荐系统 UI 视觉重构首轮

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页欢迎区替换为更克制的浅底白卡布局，新增“当前重心”聚焦卡，并把学习概览、辅助入口和推荐预览统一到更简洁的移动端卡片体系中。
- 更新 [`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)：将推荐页整体改为 clean minimal 风格，压低渐变和发光感，统一 hero、场景卡、标签卡、相关推荐卡和站外导入卡的版式与层级。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：将上传页的推荐导入承接区域改为同一套轻量视觉语言，统一顶部信息、导入横幅、按钮和最近任务列表的表现。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：将全局背景、卡片、阴影、主强调色和状态色从原来的高饱和青蓝玻璃感收回到中性浅底和深色按钮体系，避免局部页面重构后仍被全局视觉变量拖回旧风格。
- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：重做底部导航栏的外壳、激活态和上传入口表现，改为更贴近原生移动端的浮动导航条，减少旧版导航栏的生硬感和廉价发光感。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)、[`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：移除底部导航激活态上方的短横杠，并将整套推荐 UI 主色改为更柔和的莫兰迪黄紫系，让底部导航、首页、推荐页和导入页使用统一的柔和色板。
- 更新 [`mobile-frontend/src/views/Notes.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Notes.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)：清理笔记页和视频列表页中残留的蓝绿色筛选态、主按钮、标签与卡片高亮，补齐到同一套莫兰迪黄紫色板，避免这两页继续暴露旧主题。
- 更新 [`mobile-frontend/src/assets/morandi-surface.svg`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/morandi-surface.svg)、[`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：删除旧的冷调渐变背景，改用参考 Figma/Pencil 简约移动端模板氛围自制的莫兰迪黄紫背景图，并让全局页面统一使用该背景图作为底层氛围。
- 更新 [`mobile-frontend/src/views/Login.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Register.vue)、[`mobile-frontend/src/views/Guide.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/Player.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Player.vue)、[`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)、[`mobile-frontend/src/views/LocalTranscripts.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscripts.vue)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)、[`mobile-frontend/src/views/LearningPath.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LearningPath.vue)、[`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)：继续清扫其余页面残留的蓝色、青色和冷调阴影，把登录、详情、播放器、问答、笔记编辑、离线转录和学习路径等页面统一到黄紫莫兰迪色板。
- 对 2026-03-26 同日背景图记录的更正说明：将背景图承载方式改为独立全屏背景层，并增强背景图内黄紫图形的对比度与面积，避免在 iOS `WKWebView` 中被浅色底覆盖后看起来像“背景没有变化”。
- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)、[`mobile-frontend/src/assets/edumind-logo.png`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/edumind-logo.png)、[`ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png)：将前端品牌 logo 与 iOS App 图标统一替换为新的紫色 EduMind 品牌图，并移除前端 logo 的旧正方形约束，避免横版品牌图被压缩变形。
- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：将品牌图展示方式改为带留白和圆角承载框的品牌卡片，补充暖紫阴影与边框高光，让首页和登录/注册页里的 logo 不再像生硬贴图。
- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：继续优化首页左上角品牌区，将 logo 收成更完整的品牌牌匾样式，补充独立承载面、品牌标识和更稳定的留白比例，让首页 logo 看起来更像主品牌入口而不是普通小图片。

## 2026-03-26

### 接入 agent-skills 对应的 Sleek 设计助手链路

- 新增 [`backend_fastapi/app/services/sleek_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/sleek_service.py)、[`backend_fastapi/app/schemas/design.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/design.py)、[`backend_fastapi/app/routers/design.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/design.py)：将 `agent-skills` 仓库里的 Sleek API 能力收敛为 EduMind 后端代理，支持项目列表、项目创建、聊天生成、运行状态查询、组件 HTML 拉取与截图预览，并要求沿用现有 EduMind 登录态访问。
- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：新增 `SLEEK_API_KEY` 等配置项，把设计助手路由挂进 FastAPI，并补充 Sleek key 所需 scope 与启用说明。
- 新增 [`backend_fastapi/tests/api/test_design_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_design_api.py)：补充设计助手接口测试，覆盖鉴权、项目列表、项目创建、设计生成截图回显与组件 HTML 拉取主路径。
- 新增 [`mobile-frontend/src/api/design.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/design.js)、[`mobile-frontend/src/views/DesignAssistant.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/DesignAssistant.vue)：为移动端新增“设计助手”页面，支持选择或创建 Sleek 项目、提交自然语言设计描述、查看生成截图和读取组件 HTML 原型。
- 更新 [`mobile-frontend/src/router/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/router/index.js)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)、[`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：新增移动端路由与“我的”页入口，并把 `agent-skills` 的接入方式、后端代理原则和使用步骤写入文档。

## 2026-03-27

### 降低推荐路由与视频路由的耦合

- 新增 [`backend_fastapi/app/services/video_api_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_api_service.py)：集中承载视频接口共享的处理参数构建、处理元数据补充和视频序列化逻辑，避免这些 API 辅助函数继续散落在 router 层。
- 更新 [`backend_fastapi/app/routers/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/recommendation.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：推荐路由不再直接依赖视频路由中的函数，视频路由也改为复用共享 service，收紧 router 间耦合，为后续继续拆分推荐链路做准备。

## 2026-03-27

### 收紧上传后推荐链路并增加站外抓取缓存

- 更新 [`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)：为站外候选抓取增加短 TTL 内存缓存，避免首页、推荐页和上传回流在短时间内重复打 B 站、YouTube、中国大学慕课等外部源；同时保持返回对象复制，避免缓存对象被调用方改写。
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：将上传成功响应中的自动推荐收紧为“先返回站内推荐”，不再在上传主链路里同步触发站外抓取，降低外部源波动对上传接口延迟的影响。
- 更新 [`backend_fastapi/tests/unit/test_external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_external_candidate_service.py)、[`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充站外抓取缓存命中测试，并调整上传接口测试，确保上传后自动返回的是轻量站内推荐结果。

## 2026-03-27

### 首页接入推荐增强摘要

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：首页推荐预览开始消费后端返回的 `external_query`、`external_providers`、`action_target`、`can_import`、`import_hint` 等增强字段，直接展示站外检索主题、provider 抓取状态和可导入提示，并按后端动作元数据决定首页推荐卡片的跳转目标。
- 更新 [`CHANGELOG.md`](/Users/yuan/final-work/EduMind/CHANGELOG.md)：追加记录首页推荐摘要接入，不改历史。

## 2026-03-27

### 接通推荐增强字段与上传后推荐回流

- 更新 [`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)、[`mobile-frontend/src/api/recommendation.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/recommendation.js)：推荐页开始消费后端返回的 `external_providers`、`external_query`、`action_target`、`can_import`、`import_hint` 等增强字段，直接在页面里展示站外 provider 状态、检索上下文和可导入/不可导入提示，并按后端动作元数据决定跳转目标。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：上传成功后不再默认立刻跳出当前页，而是优先展示后端回流的 `recommendations`，让用户在上传完成后立即看到“下一步学什么”的推荐结果，并保留查看刚上传视频的快捷入口。
- 更新 [`mobile-frontend/src/api/mockGateway.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/api/mockGateway.js)：为 UI-only 模式补齐推荐增强字段、站外 provider 摘要和上传后推荐返回，保证 mock 流程与真实后端接口保持一致。

## 2026-03-27

### 强化推荐接口编排信息

- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)：为站内视频和站外候选统一补充 `provider`、`action_type`、`action_label`、`action_target` 等动作字段，并在推荐结果中新增站内/站外数量统计、来源分布汇总和站外检索上下文摘要，方便前端按“打开详情 / 导入学习”两类动作直接消费。
- 更新 [`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)：扩展推荐返回 schema，增加来源统计和站外检索摘要结构，保持现有推荐接口向后兼容。
- 更新 [`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)、[`backend_fastapi/tests/api/test_recommendation_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_recommendation_api.py)：补充推荐动作目标、来源统计和站外检索摘要测试，确保新字段在 service 与 API 两层都稳定返回。

## 2026-03-28

### 收紧首页品牌头视觉层级

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页左上角品牌区从厚重的套娃卡片改成更轻的横向品牌条，缩小 logo 展示面积，补充简洁说明文字，并同步收紧指南按钮的底色与阴影，减少首页头部的装饰感。
- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：为品牌组件增加无边框 `plain` 展示变体，方便首页等位置直接使用干净贴图，避免每处都强制带厚边框品牌卡。

## 2026-03-27

### 增强站外 provider 可观测性与失败摘要

- 更新 [`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)：为 B 站、YouTube、中国大学慕课等站外 provider 增加抓取报告结构，记录每个 provider 的状态、候选数量、失败摘要和耗时，并在抓取失败时输出 DEBUG 级别日志到后端运行终端。
- 更新 [`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)、[`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)：将 provider 级抓取摘要接入推荐接口返回，新增 `external_providers`、`external_failed_provider_count`、`external_fetch_failed`，让前端或调试面板可以直接看到本次站外抓取成功/失败情况。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)：根据 `settings.DEBUG` 自动设置日志级别，确保本地开发运行时可以直接看到站外 provider 抓取失败的 DEBUG 输出。
- 更新 [`backend_fastapi/tests/unit/test_external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_external_candidate_service.py)、[`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)、[`backend_fastapi/tests/api/test_recommendation_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_recommendation_api.py)：补充 provider 报告、失败摘要和推荐接口可观测性字段测试，覆盖抓取失败不阻断主路径的场景。

## 2026-03-27

### 补全推荐候选直连下载入库链路

- 新增 [`backend_fastapi/app/services/video_url_import_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_url_import_service.py)：抽出远程视频链接导入共享服务，统一处理外部 URL 来源识别、重复提交去重、下载中记录创建、预填摘要/标签写回以及后台下载任务提交，避免推荐导入和普通 URL 上传各自维护一套逻辑。
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)：让原有 `/api/videos/upload-url` 支持接收推荐候选的 `title`、`summary`、`tags` 预填元数据，下载前先写入 `videos` 记录，保证入库后立刻保留推荐侧的上下文信息。
- 更新 [`backend_fastapi/app/routers/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/recommendation.py)、[`backend_fastapi/app/schemas/recommendation.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/recommendation.py)、[`backend_fastapi/app/services/video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_recommendation_service.py)、[`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)：新增 `/api/recommendations/import-external` 直连入库接口，并在推荐条目中显式返回 `can_import`、`import_hint`、`action_api`、`action_method`，同时把中国大学慕课搜索页候选标记为“暂不可直接导入”，避免前端继续把不可下载的搜索页当成可入库视频。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)、[`backend_fastapi/tests/api/test_recommendation_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_recommendation_api.py)、[`backend_fastapi/tests/unit/test_external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_external_candidate_service.py)、[`backend_fastapi/tests/unit/test_video_recommendation_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_video_recommendation_service.py)：补充推荐候选直连入库、推荐元数据预填持久化和慕课候选不可导入标记测试，覆盖推荐到视频入库的主路径。

## 2026-03-27

### 强化慕课课程页解析与上传后自动推荐触发

- 更新 [`backend_fastapi/app/services/external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/external_candidate_service.py)：为中国大学慕课 provider 增加“搜索词 -> 具体课程页”解析链路，优先通过公开搜索结果定位 `icourse163.org/learn/...` 课程页，再把课程详情页作为可导入候选返回；仅在无法解析课程页时才回退为不可直接导入的搜索页候选。
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)：在本地上传和 URL 上传成功响应里自动附带一份实时推荐结果，上传后立即触发推荐获取，不再要求用户额外点击按钮才能拿到下一步推荐内容。
- 更新 [`backend_fastapi/tests/unit/test_external_candidate_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_external_candidate_service.py)、[`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：补充慕课课程页解析与上传后自动返回推荐结果的回归测试，覆盖“上传即得推荐”和“慕课候选真正可导入”两条主路径。

## 2026-03-27

### 明确后端测试目录结构

- 新增 [`backend_fastapi/tests/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/README.md)：明确 `unit/`、`api/`、`smoke/`、`integration/` 的职责边界和测试文件命名规则，统一后端测试入口，避免测试继续散落到业务目录。
- 更新 [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：补充后端测试目录说明和常用运行命令，强调新增后端测试应统一放在 `backend_fastapi/tests/` 下。

## 2026-03-28

### 进一步压缩首页品牌头装饰感

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：移除首页品牌头中的长段说明文案和厚重品牌展示卡，改成更轻的横向品牌头，只保留小尺寸 logo、品牌名和简短标题，让首页开头更接近原生应用导航头而不是宣传海报。

### 切换紫色莫兰迪背景与全局主题

- 新增 [`mobile-frontend/src/assets/morandi-purple-surface.png`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/morandi-purple-surface.png)：将你提供的紫色背景图压平生成前端背景资源，替换回这一轮指定的紫色莫兰迪背景方案。
- 更新 [`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)、[`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)、[`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：将全局背景、底部导航、首页、推荐页和上传页重新切回紫色莫兰迪主色，并压掉暖黄/米色硬编码。

### 继续收紧首页顶部品牌头

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页顶部品牌头进一步收成更轻的导航式布局，缩小 logo 承载块、压低字标尺寸，并把“使用指南”按钮调整得更细，减少和下方主标题的视觉重复。

### 将首页 logo 承载块调整为正方形

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：将首页顶部 logo 承载面改成更突出的正方形卡片，同时收小右侧字标，让品牌视觉重点更明确落在 logo 本身。

### 将首页顶部品牌头改为大 logo 面板

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：移除顶部品牌头里的小字标组合，改成更接近参考图的大 logo 品牌面板，让首页开头直接突出你的品牌图形本身。

### 更正首页 logo 头部布局

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：撤回大 logo 面板样式，恢复为更轻的横向 logo 结构，继续使用当前新 logo 图片，只调整承载格式，不再使用整块大面板。

### 将底部导航恢复为贴底样式

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：移除悬浮外壳和底部悬空留白，将底部导航改成真正贴着屏幕底部的导航条，保留顶部圆角但不再做漂浮胶囊效果。

### 收紧 logo 图源留白并居中显示

- 更新 [`mobile-frontend/src/assets/edumind-logo.png`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/edumind-logo.png)：基于当前使用的 logo 图裁掉外围大面积留白，保留中间品牌主体，让小尺寸位置也能看清图形。
- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)：将 logo 组件改成严格居中显示，确保首页和其他位置都以居中的方式承载新的 logo 资源。

### 为首页小尺寸 logo 单独切换 mark 图

- 新增 [`mobile-frontend/src/assets/edumind-logo-mark.png`](/Users/yuan/final-work/EduMind/mobile-frontend/src/assets/edumind-logo-mark.png)，并更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)、[`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：让首页顶部的小尺寸 logo 改用去留白的方形 mark 图，其它大 logo 位置继续保留完整字标图。

### 恢复 Ollama 运行时状态可见性

- 新增 [`backend_fastapi/app/services/ollama_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/ollama_runtime.py)：统一探测 `Ollama` 配置、可用性、当前目标模型和已加载模型列表，避免程序层面对本地 Ollama 再次“失明”。
- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)、[`backend_fastapi/tests/smoke/test_app_startup.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/smoke/test_app_startup.py)、[`backend_fastapi/tests/unit/test_ollama_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_ollama_runtime.py)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：健康检查现在会返回 `ollama` 运行时状态，并补充对应测试与说明，在不恢复旧本地问答分支的前提下恢复对 Ollama 的可观测性。

### 记录 iOS 离线模型现状并切换本地 GGUF 默认模型

- 新增 [`docs/iOS离线模型评估与切换说明.md`](/Users/yuan/final-work/EduMind/docs/iOS离线模型评估与切换说明.md)：记录当前 iOS 离线视频处理实际使用的 Apple `Speech` 端侧识别、目标 `Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF` 模型信息、两者差异，以及“是否需要 Ollama”的结论，明确 GGUF 适合本地推理而不适合作为 ASR 替身。
- 新增 [`backend_fastapi/scripts/import_qwen35_gguf_to_ollama.sh`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/import_qwen35_gguf_to_ollama.sh)，并更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/.env`](/Users/yuan/final-work/EduMind/backend_fastapi/.env)：将当前项目本地 LLM 默认模型别名切到 `qwen35-9b-opus-distilled`，方便用 Ollama 导入并接管摘要、标题、语义整理等本地回退能力。
- 更新 [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)：把后端运行说明统一回 `.venv`，补充 GGUF 导入命令，并明确 iOS 端本地离线转录仍然走 Apple `Speech`。

### 优化首页 logo 与字标衔接

- 更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)：给首页顶部的 `logo + 字标` 增加更轻的共同承载层，收小 logo 卡的边框和阴影，并压细字标层级，让图标与文字的过渡更自然。

### 对当日 logo 衔接调整的更正说明

- 更正上条首页 logo 衔接调整：移除新增的共同外层承载框，恢复为原有横向结构，只通过间距、对齐和 logo 卡本身的轻量样式来让 `logo + 字标` 衔接更自然。

### 收紧底部导航圆角样式

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：保持底部导航贴底，不恢复悬浮效果，只通过收窄左右边距、补边框和增大顶部圆角，让底栏本体的圆角更明确。

### 继续收窄底部导航宽度

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：在保留当前圆角贴底样式的前提下，继续增大左右留白，让底部导航在手机里不再铺得过宽。

### 再次压缩底部导航占宽

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：进一步收小底栏最大宽度并继续加大左右留白，让贴底圆角导航看起来更紧凑，不再显得发胀。

### 压低底部导航底边留白

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：减少底栏内部的底部安全区额外留白，并同步收小最小高度，让导航视觉上更贴近屏幕底边。

### 继续压低底部导航贴底距离

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)：继续减少底栏底部安全区上的额外 padding，并再次收小最小高度，让贴底感更明显。

### 统一残留暖黄卡面为浅紫色

- 更新 [`mobile-frontend/src/components/BrandLogo.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/BrandLogo.vue)、[`mobile-frontend/src/views/NoteEdit.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/NoteEdit.vue)、[`mobile-frontend/src/views/VideoDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/VideoDetail.vue)、[`mobile-frontend/src/views/LearningPath.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LearningPath.vue)、[`mobile-frontend/src/views/Profile.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Profile.vue)、[`mobile-frontend/src/views/Videos.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Videos.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/components/WhisperModelPicker.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/WhisperModelPicker.vue)、[`mobile-frontend/src/views/QA.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/QA.vue)：将前端里残留的暖黄/米杏卡片面统一替换为首页同系浅紫色卡面，避免页面间继续串色。

### 更正底部导航为圆角卡片样式

- 更新 [`mobile-frontend/src/components/TabBar.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/components/TabBar.vue)、[`mobile-frontend/src/App.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/App.vue)、[`mobile-frontend/src/styles.css`](/Users/yuan/final-work/EduMind/mobile-frontend/src/styles.css)：将底部导航从透明贴底条恢复为不透明的圆角卡片样式，并统一页面底部预留高度，确保导航适应屏幕宽度但不遮挡主页面卡片内容。

### 美化本地视频文件选择控件

- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：隐藏原生文件选择框，改为自定义的“选择本地视频”按钮和文件状态展示卡，避免 iOS `WKWebView` 中出现缺字方块和默认系统样式破坏页面观感。

### 补强 Ollama 模型在位探测与远程导入

- 更新 [`backend_fastapi/app/services/ollama_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/ollama_runtime.py)、[`backend_fastapi/tests/unit/test_ollama_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_ollama_runtime.py)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：在现有 `ollama` 运行时状态基础上补充 `model_present`，让健康检查可以直接看出当前配置模型是否已真正导入。
- 更新 [`backend_fastapi/scripts/import_qwen35_gguf_to_ollama.sh`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/import_qwen35_gguf_to_ollama.sh)、[`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)、[`docs/iOS离线模型评估与切换说明.md`](/Users/yuan/final-work/EduMind/docs/iOS离线模型评估与切换说明.md)：导入脚本现在同时支持本地 `.gguf` 和 `hf.co/...` 直接拉取，便于在不恢复旧 Ollama 问答分支的前提下恢复本地模型加载能力。

### 兼容推理模型的思维标签输出

- 新增 [`backend_fastapi/app/utils/ollama_compat.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/ollama_compat.py)、[`backend_fastapi/tests/unit/test_ollama_compat.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_ollama_compat.py)，并更新 [`backend_fastapi/app/services/video_content_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/video_content_service.py)、[`backend_fastapi/app/utils/semantic_utils.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/semantic_utils.py)、[`backend_fastapi/app/services/llm_similarity_service.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/llm_similarity_service.py)：为本地 Ollama 调用统一加上 stop tokens，并清理 `<think>`、`<analysis>`、`<|endoftext|>` 等推理模型残留标记，避免新模型污染现有摘要、标题、语义分段和相似度链路的输出格式。

### 离线转录同步继续写入数据库标签

- 更新 [`backend_fastapi/app/schemas/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/schemas/video.py)、[`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：`/api/videos/sync-offline-transcript` 现在在继续写入现有 `videos` / `subtitles` 的同时，也支持把离线结果的 `tags` 与 `auto_generate_tags` 一起落到 `videos.tags`。
- 更新 [`mobile-frontend/src/services/nativeOfflineTranscripts.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/nativeOfflineTranscripts.js)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)、[`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)、[`docs/iOS离线模型评估与切换说明.md`](/Users/yuan/final-work/EduMind/docs/iOS离线模型评估与切换说明.md)：前端本地离线记录会继续携带标签与自动标签配置，相关文档也补充说明了 iOS 离线结果仍然回写同一套 MySQL 主库。

### 对齐本地 Qwen 3.5 9B 模型别名

- 更新 [`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env`](/Users/yuan/final-work/EduMind/backend_fastapi/.env)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)、[`backend_fastapi/tests/unit/test_ollama_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_ollama_runtime.py)、[`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：将后端本地 Ollama 默认模型别名从 `qwen35-9b-opus-distilled` 对齐为 `qwen-3.5:9b`，方便按你当前的测试口径直接确认运行时模型名称。

## 2026-03-28 22:35 (Asia/Shanghai) 对齐导入脚本默认模型别名

- 更新 [`backend_fastapi/scripts/import_qwen35_gguf_to_ollama.sh`](/Users/yuan/final-work/EduMind/backend_fastapi/scripts/import_qwen35_gguf_to_ollama.sh)：将 `OLLAMA_MODEL_NAME` 默认值从 `qwen35-9b-opus-distilled` 对齐为 `qwen-3.5:9b`，避免后续重新导入 GGUF 时又回到旧别名。

## 2026-03-28 22:55 (Asia/Shanghai) 强化方言与儿化音转录链路

- 更新 [`backend_fastapi/app/services/whisper_runtime.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/services/whisper_runtime.py)：将产品可选 Whisper 模型扩展到 `large-v3` / `large-v3-turbo`，并为中文转录补充更严格的提示词与解码参数，提升方言、儿化音和课堂口语场景下的准确率。
- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)、[`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：新增音频直传到后端 Whisper 的转录接口，保证 iPhone 原生链路可以在 Apple Speech 不可靠时继续走统一的高质量转录入口。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/LocalTranscripts.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscripts.vue)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)：iPhone 端现在对中文/方言场景优先切换到 `large-v3` Whisper，高精度转录失败时也会在日志和页面里明确显示当前使用的引擎，不再把 Apple Speech 当成唯一主识别器。

## 2026-03-28 23:10 (Asia/Shanghai) 落地 iPhone 本机 Whisper 离线转录

- 更新 [`ios-app/EduMindIOS/EduMindIOS/OnDeviceWhisperRuntime.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/OnDeviceWhisperRuntime.swift)、[`ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS.xcodeproj/project.pbxproj)：为 iOS 工程接入本机 `whisper.spm` 依赖，并新增本地 Whisper 运行时，支持模型缓存、首次下载、多语种参数映射和本机分段转录。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：将原生离线主链路改为“本机 Whisper 优先，Apple Speech 兜底”，并在 Xcode 日志与桥接事件里持续输出当前引擎和处理进度，避免再因为后端未启动而阻断本地转录。
- 更新 [`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)、[`mobile-frontend/src/views/LocalTranscripts.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscripts.vue)、[`mobile-frontend/src/views/LocalTranscriptDetail.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/LocalTranscriptDetail.vue)：新增 `Whisper 本机离线转录` 引擎展示，方便区分本机 Whisper、Apple Speech 与旧的后端 Whisper。

## 2026-03-31 12:55 (Asia/Shanghai) 安全与架构基线加固迁移

- 更新 [`backend_fastapi/app/main.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/main.py)：新增 `SecurityHeadersMiddleware`，统一附加 `X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy` 等安全响应头，并在 `production` 环境附加 `Strict-Transport-Security`，降低 MIME 嗅探、点击劫持与跨站上下文泄露风险。
- 更新 [`mobile-frontend/src/config/index.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/config/index.js)：将 mock 开关改为“生产默认不可开启”，仅在显式设置 `VITE_ALLOW_UI_ONLY_IN_PROD=true` 时允许生产环境走 `UI_ONLY_MODE`，避免线上误入 UI-only 假链路造成功能假成功与数据不一致。
- 审计说明：目标参考仓库 `yjy-yjy-yuan/claude-code` 当前为 `size=0` 空仓库，未发现可迁移代码结构；本次迁移按现有 EduMind iOS-only 架构完成安全基线强化。

### 深度安全迁移第一步：认证 token 增加过期控制

- 更新 [`backend_fastapi/app/utils/auth_token.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/utils/auth_token.py)、[`backend_fastapi/app/core/config.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/core/config.py)、[`backend_fastapi/.env.example`](/Users/yuan/final-work/EduMind/backend_fastapi/.env.example)：登录签发 token 升级为 `userId.expiresAt.signature`，新增 `AUTH_TOKEN_TTL_SECONDS`（默认 7 天）和 `AUTH_TOKEN_CLOCK_SKEW_SECONDS` 配置，服务端校验时强制检查过期时间；同时保持旧格式 `userId.signature` 的兼容解析，避免升级期间现有会话瞬时失效。
- 更新 [`mobile-frontend/src/store/auth.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/store/auth.js)：前端本地 token 格式识别同步兼容新旧两种签名结构，防止升级后误清理合法登录态。
- 新增 [`backend_fastapi/tests/unit/test_auth_token.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/unit/test_auth_token.py)：覆盖新 token 生成/解析、过期拒绝、旧 token 兼容三类关键路径。

### 深度安全迁移第二步：上传文件类型双重校验

- 更新 [`backend_fastapi/app/routers/video.py`](/Users/yuan/final-work/EduMind/backend_fastapi/app/routers/video.py)：在本地视频上传接口中新增 MIME 校验，形成“扩展名 + `content-type`”双重防护；仅允许 `video/*` 或兼容 `application/octet-stream`，拦截伪装为 `.mp4` 的文本/脚本类上传。
- 更新 [`backend_fastapi/tests/api/test_video_api.py`](/Users/yuan/final-work/EduMind/backend_fastapi/tests/api/test_video_api.py)：新增“伪装 MIME 拒绝”和“octet-stream 兼容通过”测试用例，确保 iOS/WebView 上传链路兼容且安全边界明确。

## 2026-04-02 20:58 (Asia/Shanghai) 推荐交互与文档同步

- 新增 [`mobile-frontend/src/services/recommendationActions.js`](/Users/yuan/final-work/EduMind/mobile-frontend/src/services/recommendationActions.js)，并更新 [`mobile-frontend/src/views/Home.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Home.vue)、[`mobile-frontend/src/views/Upload.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Upload.vue)：统一推荐卡片动作解析，修复站外候选 `can_import=false` 时仍被误判为“不可导入”或错误跳到上传页的问题；现在可导入候选继续走现有 URL 导入链路，不可直接导入的候选会按后端动作打开原始来源页。
- 更新 [`mobile-frontend/src/views/Recommendations.vue`](/Users/yuan/final-work/EduMind/mobile-frontend/src/views/Recommendations.vue)：修复“看同主题”按钮不可点击的问题，并补全完整交互闭环。按钮现在只对站内视频开放，点击后会进入 loading、自动滚动到“相关推荐”区域、优先请求 `scene=related`，并在接口空结果或失败时使用当前页已加载的站内推荐做同主题兜底渲染。
- 更新 [`README.md`](/Users/yuan/final-work/EduMind/README.md)、[`mobile-frontend/README.md`](/Users/yuan/final-work/EduMind/mobile-frontend/README.md)、[`docs/VIDEO_RECOMMENDATION_FEASIBILITY_AND_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_FEASIBILITY_AND_PROMPT.md)、[`docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md)：同步当前推荐链路现状，修正“全表加载视频”等过时说明，并补充站外动作分流、环境变量控制与“看同主题”当前行为。
- 更新 [`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.js)、[`ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/WebAssets/index.css)：同步最新前端构建产物到 iOS `WKWebView` 资源目录。
- 验证与 hooked checks：
  - `cd /Users/yuan/final-work/EduMind/mobile-frontend && npm run build:ios`
  - `cd /Users/yuan/final-work/EduMind && bash ios-app/sync_ios_web_assets.sh`
  - `cd /Users/yuan/final-work/EduMind && pre-commit run --files README.md mobile-frontend/README.md docs/VIDEO_RECOMMENDATION_FEASIBILITY_AND_PROMPT.md docs/VIDEO_RECOMMENDATION_IMPLEMENTATION_PROMPT.md mobile-frontend/src/services/recommendationActions.js mobile-frontend/src/views/Home.vue mobile-frontend/src/views/Recommendations.vue mobile-frontend/src/views/Upload.vue`
  - `cd /Users/yuan/final-work/EduMind && MYPYPATH=backend_fastapi ./.venv/bin/python -m mypy --config-file pyproject.toml backend_fastapi/app/models backend_fastapi/app/schemas backend_fastapi/scripts/init_db.py scripts/hooks`
  - `cd /Users/yuan/final-work/EduMind && ./.venv/bin/python -m pytest backend_fastapi/tests/unit backend_fastapi/tests/api backend_fastapi/tests/smoke -q`
