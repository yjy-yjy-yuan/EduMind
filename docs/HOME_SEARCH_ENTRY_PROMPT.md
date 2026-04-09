# 首页搜索入口（跨视频语义搜索）— 可执行提示词

从「跨视频语义搜索」完整实现提示词（如 EduMind v2）中抽取的**仅首页入口与默认意图**切片，便于单独维护与修改。搜索页实现细节见 [`SEARCH_FRONTEND_PROMPT.md`](SEARCH_FRONTEND_PROMPT.md)。仓库级边界与分层见根目录 [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](../PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)。

---

## 任务目标

在 `mobile-frontend/src/views/Home.vue` 增加「跨视频语义搜索」入口，并打通到已有 `/search` 流程；**默认在「我的全部已索引视频」中搜索**。

## 项目边界（必须遵守）

1. 仅在 `mobile-frontend/`、`backend_fastapi/`、`ios-app/` 这条链路内改动（本切片通常只改 `mobile-frontend/` 与可选文案）。
2. 不在前端伪造搜索结果，不新增第二套搜索 API。
3. 不使用 `pytest` 验证改动；按仓库约定方式验证。
4. 若有用户可见行为变化，`CHANGELOG.md` 追加新条目（不改历史）。

## 现状基线（按此实现，不重造轮子）

1. 后端已存在：`POST /api/search/semantic/search`。
2. 前端已存在：`Search.vue`、`/search` 路由、`semanticSearch()` API 封装。
3. 搜索范围机制已存在：`current` / `all`；从视频详情进入时有 `videoId` 上下文。
4. 后端用户隔离依赖现有用户标识（如 `X-User-ID` / 认证上下文）。

## 实现要求（首页 + 默认意图）

### 1. 首页入口

- 在 `Home.vue` 增加明显入口（风格与 `ios-page` / `ios-card` 一致）。
- 点击后跳转 `/search`，并携带**默认全局搜索**意图（例如 query 参数 `scope=all`）。
- 若首页输入框已有关键词，应一并带上预填查询参数（例如 `q=...`），并让搜索页在落地后**自动触发一次搜索**，而不是要求用户二次点击。

### 2. 搜索页默认行为（与首页联动）

- 当来源是首页入口时，默认 `searchScope = 'all'`。
- 当来源同时携带首页关键词时，搜索页应在初始化后直接执行该次搜索，并在消费后移除一次性标记，避免返回页面时重复发请求。
- 页面文案明确：**「在我的全部视频中搜索」**（或等价表述，与产品一致）。
- 从视频详情进入时，保留「当前视频」能力，**不破坏现有行为**。

### 3. 请求与数据流

- 继续复用 `semanticSearch({ query, video_ids: null, limit, threshold })`。
- 不传或传空 `video_ids` 表示跨视频检索。
- 请求必须带现有用户标识，与 `Video.user_id` 语义一致。

### 4. 空态与失败态

- 当后端返回「无可搜索视频 / 索引未就绪」时，给出可读引导（去上传、等待索引完成、去视频页）。
- 与 `SEARCH_ENABLED`、索引构建流程现状保持一致，不新增虚假状态。

### 5. 维护性

- 默认值集中管理（如 `DEFAULT_SEARCH_SCOPE='all'`、`DEFAULT_LIMIT`、`DEFAULT_THRESHOLD`），避免散落硬编码。
- **不重复实现搜索逻辑**；`Home.vue` 只做入口与参数传递。
- 若需要首页直达搜索，优先通过路由 query 传递一次性意图标记，由 `Search.vue` 消费后清理，不要在首页直接复制搜索页的请求逻辑。
- 新增文案尽量集中，便于后续统一修改。

## 验收标准（本切片相关）

1. `cd mobile-frontend && npm run build:ios` 通过。
2. `bash ios-app/sync_ios_web_assets.sh` 完成资源同步。
3. `WKWebView` 验证：首页可进入搜索；默认全视频搜索；带关键词时进入搜索页后会立即发起检索；结果与跳转行为与 [`SEARCH_FRONTEND_PROMPT.md`](SEARCH_FRONTEND_PROMPT.md) 一致。
4. 如有用户可见变更：`. .venv/bin/activate && python scripts/validate_backend_smoke.py`（若未动后端可省略）；并更新 `CHANGELOG.md`。

## 非目标

1. 不新增独立搜索后端接口。
2. 不做仅桌面可用的交互。
3. 不引入与 iOS 链路无关的模块或目录。

---

**范围说明**：完整版（含全部验收步骤与非首页部分）以团队归档或对话中的 EduMind v2 为准；本文件仅覆盖「首页搜索窗口」与默认 `scope=all` 联动。
