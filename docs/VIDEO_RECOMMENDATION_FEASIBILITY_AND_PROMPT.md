# 视频推荐 × Agent 可行性分析 + 重构/增强完整提示词

**实现目标仓库（绝对路径）**：`/Users/yuan/final-work/EduMind`
**路径索引与可选参考仓库**：见 [`PROJECT_PATHS.md`](./PROJECT_PATHS.md)。跨目录实现时请在任务中显式写明该路径。

> **阅读顺序**：先读「第一部分」可行性结论；再读「第二部分」实现提示词（含哲学与范围）。
> 涉及模块：`backend_fastapi` 推荐服务、`external_candidate_service`、首页与推荐页 `mobile-frontend`。

---

## 第一部分：可行性分析（仅分析，不含实现承诺）

### 1. 「两个项目」指什么

| 维度 | 说明 |
|------|------|
| **A. EduMind 内：推荐子系统** | 路由 `GET /api/recommendations/videos`、核心 `video_recommendation_service.py`、站外 `external_candidate_service.py`、前端 `Home.vue` / `Recommendations.vue`。 |
| **B. EduMind 内：学习流 Agent** | `POST /api/agent/execute` 与 `learning_flow_agent`（笔记/时间戳编排）。 |
| **（可选对照）外部 CLI 参考** | 若曾参考 Claude Code 类仓库，仅借鉴「编排/可观测」思想，**不**作为运行时依赖。 |

**结论**：可行性分析聚焦 **A 与 B 同属 EduMind**，是否要在推荐链路上「加一层 Agent」。

### 2. 当前推荐链路在做什么（基线）

- **站内**：从数据库按更新时间倒序加载**受限候选集**（由 `RECOMMENDATION_MAX_CANDIDATES_SCAN` 控制），为每条构建 `RecommendationProfile`（科目、标签、token、聚类），按场景 `home/continue/review/related` 打分排序，合并 `exclude_ids`、seed 相关推荐。
- **站外（`include_external=true`）**：根据 `build_external_query_context` 生成查询文本，调用 `fetch_external_candidates_report`（多 provider HTML/搜索抓取，支持缓存、超时预算与失败摘要），再与站内混合 `select_combined_items`。
- **同主题来源一致性**：`related` 场景除了主题/科目匹配，还应尽量继承 seed 视频的原始来源平台语境；若当前视频来自 B站/YouTube/慕课，站外候选排序与抓取顺序应优先同来源 provider，避免只“同主题”但链接风格失真。
- **前端交互**：首页与推荐页默认可通过 `VITE_RECOMMENDATION_INCLUDE_EXTERNAL` 控制是否首屏带站外抓取；推荐页“看同主题”会请求 `scene=related`，并在接口空结果或失败时用**各场景已加载列表合并去重**后的候选池做本地兜底，**排除**种子视频 ID 与**当前场景主列表**已出现的视频 ID，避免「相关推荐」与主网格重复。
- **动作分流**：站外候选根据 `can_import` / `action_type` 区分为“进入上传导入链路”或“打开原始来源页”，不会再把不可直接导入的候选伪装成已入库视频。
- **兜底**：若无任何结果，按最近更新时间回退若干条并标记 `fallback_used`。

### 3. 「推荐出问题」的常见根因（需在重构前实测确认）

| 现象 | 可能原因 | 与 Agent 无关 / 有关 |
|------|----------|----------------------|
| 首页加载慢或超时 | `include_external: true` 触发站外抓取，多 provider 串行/超时（如 8s）、网络或反爬 | **先修工程与配置** |
| 站外一直失败 | B 站/YouTube/DuckDuckGo 页面结构变化、风控、缓存键命中旧失败 | **先修 external_candidate** |
| 结果为空或离谱 | 库内视频极少、标签/摘要空导致 token 弱；`related` 未传 `seed_video_id`（422） | **规则与参数** |
| 首页与推荐页不一致 | 参数不同（`scene/limit/include_external`）、是否带 token 用户画像 | **前端与 API 契约** |
| 受限候选集仍不够稳 | `RECOMMENDATION_MAX_CANDIDATES_SCAN` 过小导致相关推荐弱，或过大导致排序开销抬高 | **查询与配置** |

**Agent 不能自动修复上述「抓取失败、全表扫描、422」**；必须先做 **服务层与前端契约** 修复。Agent 只适合在**稳定排序之后**增加「解释、下一步建议、诊断文案」等**薄层能力**。

### 4. 是否适合构建「推荐 Agent」？

**适合（低成本、易维护）的形态**：

- **解释型 / 教练型**：在已有 `items[]` + `reason_text` 之上，可选 **一次** LLM 调用生成「本轮推荐一句话说明」或「站外失败时用户可执行步骤」（也可用模板替代 LLM）。
- **编排型**：不新增「第二个超级 Agent」，而是 **`POST /api/recommendations/explain` 或 `?explain=1`** 返回 `coach_summary` 字段，**不**参与排序、不改数据库。

**不适合（成本高、难维护）的形态**：

- 用 LLM 替代现有打分排序（贵、慢、难测）。
- 用多轮工具循环实时抓取站外（与现有 `external_candidate_service` 重复且更脆弱）。

**结论**：**可以**在推荐功能稳定后，**叠加**薄层 Agent（解释/教练）；**不可以**指望 Agent 替代推荐核心算法与站外抓取修复。

### 5. 与「学习流 Agent」的关系

- **共享**：同一套哲学（规则优先、单次 LLM 可选、可观测 `action_records` 或等价字段）。
- **不共享**：默认 **不同路由**；推荐侧不要与学习流笔记写库混在一个巨型 handler 里，避免改一处坏两处。

---

## 第二部分：完整实现提示词（重构推荐 + 可选薄层解释）

以下整段可直接复制给实现者或 AI 编码助手。

---

### 2.1 哲学（约束）

1. **先正确、再聪明**：推荐列表必须先稳定、可解释、可回退；LLM 仅作可选润色。
2. **站外是增强**：默认首页应 **可配置** 为「仅站内」或「站内+站外」，避免每次首屏强制拉站外。
3. **诚实**：`external_fetch_failed` 与 provider 失败要对用户可读，**禁止**静默失败。
4. **不引入新运行时**：不引入 Node/Bun CLI；Python 内完成。

### 2.2 目标

1. **修复/重构** `video_recommendation_service` 与 `recommendation` 路由，解决 **性能、可观测性、参数一致性**；按 AGENTS.md **不随意改表**。
2. **加固** `external_candidate_service`：超时、重试策略、失败降级、缓存键文档化（**不**假设 pytest 为本次验证手段，遵守仓库对 pytest 的约束）。
3. **前端** `Home.vue` / `Recommendations.vue`：与后端参数对齐；首屏是否 `include_external` 由配置或显式用户开关决定。
4. **可选**：新增 `coach_summary` 或独立 `explain` 接口，**单次 LLM 或模板**，默认关闭。

### 2.3 现状必读文件

- `backend_fastapi/app/routers/recommendation.py`
- `backend_fastapi/app/services/video_recommendation_service.py`
- `backend_fastapi/app/services/external_candidate_service.py`
- `backend_fastapi/app/schemas/recommendation.py`
- `mobile-frontend/src/api/recommendation.js`
- `mobile-frontend/src/views/Home.vue`（`reloadRecommendations`）
- `mobile-frontend/src/views/Recommendations.vue`

### 2.4 后端重构要点

1. **查询**：避免无条件 `query(Video).all()`；改为按场景 **限制候选集**（例如最近更新 N 条 + 状态过滤 + 可选 subject 预筛），或分页/游标；保留 `related` seed 逻辑正确性。
2. **站外**：`include_external` 为 true 时，**并行或超时预算**明确；失败时站内结果仍返回；`external_providers` 必含可诊断信息。
3. **同来源偏好**：`related` 场景若 seed 视频带外部 URL，应把来源平台纳入站外检索上下文与排序依据；至少保证同来源 provider 不会因固定顺序被提前截断。
4. **配置**：在 `config.py` 增加例如 `RECOMMENDATION_MAX_CANDIDATES_SCAN`、`RECOMMENDATION_INCLUDE_EXTERNAL_DEFAULT`、`RECOMMENDATION_EXTERNAL_TIMEOUT_SECONDS`（命名可调整）。
5. **契约**：`VideoRecommendationResponse` 与前端 `normalizeRecommendationItems` 字段一致（`items`、`external_query`、`external_providers`）；若已有来源偏好，还应把 `preferred_provider` 与 `preferred_provider_label` 一并返回给前端摘要区。

### 2.5 可选「推荐解释 Agent」

- 若实现：新增 `GET /api/recommendations/videos` 的 `coach: bool = False` **或** `POST /api/recommendations/explain` body `{ scene, items_snapshot }`，返回 `{ coach_summary, provider_hints: [] }`。
- **单次 LLM**，输入仅摘要级元数据（标题、标签、失败原因），**禁止**把完整用户库写入 prompt。
- 若未配置密钥，返回 `coach_summary` 为 **模板** 文案。

### 2.6 前端要点

1. 首屏 **默认 `include_external: false`** 或环境变量控制，避免白屏等待。
2. 推荐页「刷新」与首页参数一致；`related` 场景必须传 `seed_video_id`。
3. “看同主题”按钮必须有明确反馈：点击即进入 loading、固定当前 seed，并在当前页“相关推荐”区域渲染结果。
4. 若 `related` 接口暂无结果或失败，前端可使用内存中各场景已加载的站内推荐（合并去重后的候选池）做同主题兜底，**排除**种子与当前场景主列表已出现 ID，并在 UI 标明本地兜底；不得伪造后端成功。
5. 展示 `external_fetch_failed` 与 provider 失败时，给用户明确可操作提示（去推荐页、关闭站外、检查网络）。

### 2.7 验收（手工）

1. 空库 / 单视频 / 多视频下推荐均有结果或明确 fallback。
2. `include_external=true` 时，站外全失败仍能返回站内列表且 UI 不报错。
3. 首页在弱网下首屏可接受（或仅站内）。
4. 更新 `CHANGELOG.md`。

### 2.8 非目标

- 不引入协同过滤深度学习模型。
- 不复制外部泄漏源码进仓库。

---

*文档结束。若需将「第二部分」单独拆成工单，可只复制第二部分。*
