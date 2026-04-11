# EduMind Video Recommendation Implementation Prompt

> 用途：给 Codex、Claude、Blitz 等编码助手直接使用，用于在当前 EduMind 仓库中推进视频推荐能力建设。
> 适用仓库：`/Users/yuan/final-work/EduMind`
> 当前产品边界：iOS-only，唯一有效链路为 `mobile-frontend/` + `backend_fastapi/` + `ios-app/`

## 一、当前项目现状

你面对的不是一个空白项目，而是一个已经收敛为 iOS-only 的移动学习系统：

1. `mobile-frontend/` 是唯一前端，负责 `WKWebView` 中的 H5 UI。
2. `backend_fastapi/` 是唯一真实后端，负责 MySQL、业务逻辑、视频处理、字幕、摘要、标签、问答和推荐能力。
3. `ios-app/` 是唯一 iOS 容器，负责 `WKWebView`、原生桥接、本地资源加载与真机验证。

必须严格遵守以下边界：

1. 前端只能做 UI、状态和 API 调用，不能把标签提取、聚类、排序、爬取、数据库逻辑或“假装真实推荐”的逻辑写在页面里。
2. 推荐系统的真实逻辑必须继续落在 `backend_fastapi/`。
3. 数据库必须继续使用 MySQL，并优先复用现有 `videos`、`users`、`subtitles` 等表，不要轻易新增平行表。
4. 产品目标是 iOS App，不是桌面网站；任何前端交互改动最终都要在 `WKWebView` 中验证。

## 二、当前推荐基础

仓库里已经有第一版站内推荐，不要推倒重来，应在现有实现上增量扩展：

### 后端现状

- `backend_fastapi/app/models/video.py`
  - `Video` 已有 `title`、`summary`、`tags`、`url`、`status`、`processing_origin` 等字段。
  - `tags` 当前以 JSON 字符串形式保存在 `videos.tags`。
- `backend_fastapi/app/services/video_recommendation_service.py`
  - 已实现基于标题、摘要、标签、状态和用户画像的轻量推荐。
  - 当前已按 `RECOMMENDATION_MAX_CANDIDATES_SCAN` 对站内候选做有上限扫描，不再默认全表加载。
  - 当前支持 `home / continue / review / related` 四个场景。
- `backend_fastapi/app/routers/recommendation.py`
  - 已提供 `/api/recommendations/scenes` 和 `/api/recommendations/videos`。
- `backend_fastapi/tests/api/test_recommendation_api.py`
  - 已覆盖推荐场景、首页推荐排序和相关推荐基础约束。
- `backend_fastapi/app/routers/video.py`
  - 已支持视频链接导入，并明确接受 B 站、YouTube、中国大学慕课链接。

### 前端现状

- `mobile-frontend/src/api/recommendation.js`
  - 已有推荐接口封装。
- `mobile-frontend/src/views/Home.vue`
  - 已有首页“推荐视频”区域，并接入当前推荐接口；是否默认带站外检索由 `VITE_RECOMMENDATION_INCLUDE_EXTERNAL` 控制。
- `mobile-frontend/src/views/Recommendations.vue`
  - 已有推荐页、相关推荐区域和“看同主题”交互。
  - “看同主题”应保持为完整闭环：可点击、可见 loading、可在当前页渲染结果，并在接口空结果或失败时允许前端基于当前已加载站内结果做兜底。
- `mobile-frontend/src/views/Upload.vue`
  - 已支持链接导入，且链接校验已覆盖 B 站 / YouTube / 中国大学慕课。

当前问题不是“完全没有推荐能力”，而是“只有站内轻量推荐，还没有围绕已上传视频标签聚类和外部候选源扩展的完整链路”。

## 三、这次要实现的目标

请围绕以下产品目标推进，而不是偏离到通用内容平台或桌面产品分支：

1. 优先对已经上传的视频做标签提取与标签归一化。
2. 将含有相同或高度相近标签的视频归为同一类，用于站内推荐与相关推荐。
3. 基于这些标签主题，从 B 站 / MOOC / YouTube 获取外部视频候选。
4. 外部候选只需要先获取元数据并做标签处理，不要在推荐阶段直接下载整段视频。
5. 推荐结果应能同时覆盖：
   - 站内已上传视频
   - 外部待导入视频候选
6. 外部候选在前端必须明确标识为“外部来源”，并通过现有链接导入链路进入学习系统，而不是伪装成已入库视频。

## 四、建议采用的实现边界

为了尽量贴合当前代码库和数据库约束，默认优先采用下面的实现思路：

1. 站内标签聚类：
   - 复用 `videos.tags`、`videos.summary`、`videos.title`。
   - 在后端新增标签归一化、主题聚合、相似标签分桶逻辑。
   - 优先不改表。
2. 外部候选采集：
   - 只抓取用于推荐所需的轻量元数据，例如 `title`、`description`、`link/url`、`author`、`published_at`、`cover`、`source`。
   - 优先使用 RSS / feed / 平台公开页面元数据；若某平台没有稳定 RSS，可做最小化的元数据抓取，但不要在第一版引入浏览器自动化、登录态或重量级抓取链路。
   - 推荐阶段不要下载完整视频文件。
3. 外部标签处理：
   - 以标题、简介、作者、分类等文本做标签提取与归一化。
   - 保持与站内视频相同或兼容的标签标准，方便统一排序。
4. 前端交互：
   - 站内视频继续走现有详情页。
   - 外部候选点击后应根据动作类型分流：
     - 可直接导入：进入现有“链接导入”流程，例如跳到上传页并预填 URL，或调用既有 URL 上传接口。
     - 暂不可直接导入：打开原始来源页。
   - UI 必须清晰区分“站内视频”和“外部推荐”。
5. 数据持久化：
   - 第一版默认不要新增外部推荐持久化表。
   - 优先按请求实时拉取并在内存中完成标签处理与排序。
   - 如果确实需要缓存或持久化，请先评估是否能扩展现有结构；若不能，请在代码里最小化引入，并同步更新 SQL、文档和测试。

## 五、推荐本轮目标

如果要正式开始建设视频推荐，默认优先实现“第一版真实可用闭环”，而不是一次性做成重型推荐平台。

本轮目标建议是：

1. 让站内视频先具备稳定的标签聚类和相关推荐能力。
2. 让后端能根据当前标签主题拉取外部候选源元数据。
3. 让外部候选也走统一标签提取和排序逻辑。
4. 让首页或推荐页能同时展示站内推荐与外部推荐，并清晰区分来源。
5. 让用户从外部推荐项一键进入现有导入链路，形成“推荐 -> 导入 -> 处理 -> 复盘”的主学习闭环。

本轮默认不优先做：

1. 脱离现有 `videos` 表另起一整套推荐数据库体系。
2. 重型实时爬虫调度系统。
3. 浏览器自动化登录抓取。
4. 与 iOS 主学习链路无关的桌面推荐页或后台运营系统。

## 六、可直接复制给编码助手的主提示词

复制下面整段内容给编码助手即可：

```md
你正在 `/Users/yuan/final-work/EduMind` 仓库中继续构建 EduMind 的视频推荐功能。请直接在代码库里实施，不要只停留在方案描述。

必须严格遵守以下项目事实：

1. 本项目已经收敛为 iOS-only，唯一有效链路是 `mobile-frontend/` + `backend_fastapi/` + `ios-app/`。
2. `mobile-frontend/` 只负责 UI、路由、状态和 API 调用，不能在页面里实现标签提取、聚类、爬虫、RSS 解析、排序、数据库逻辑或伪造“真实推荐”。
3. `backend_fastapi/` 是唯一真实业务层；视频标签标准化、聚类、外部候选源采集、标签处理、排序和推荐接口必须继续落在后端。
4. 数据库必须继续使用 MySQL，并优先复用现有 `videos`、`users`、`subtitles` 等表。不要轻易新增平行表。
5. 任何前端交互改动完成后，都要考虑 iOS `WKWebView` 的可点击、可滚动、可跳转和安全区适配；不能只按桌面浏览器验证。

先理解当前现状：

- 后端当前已有推荐骨架：
  - `backend_fastapi/app/services/video_recommendation_service.py`
  - `backend_fastapi/app/routers/recommendation.py`
  - `backend_fastapi/app/schemas/recommendation.py`
  - `backend_fastapi/tests/api/test_recommendation_api.py`
- 当前 `Video` 模型已有推荐相关数据：
  - `backend_fastapi/app/models/video.py`
  - 其中已包含 `title`、`summary`、`tags`、`url`、`status`
- 当前前端已有推荐入口：
  - `mobile-frontend/src/api/recommendation.js`
  - `mobile-frontend/src/views/Home.vue`
- 当前链接导入链路已支持：
  - B 站
  - YouTube
  - 中国大学慕课
  - 参考 `backend_fastapi/app/routers/video.py` 与 `mobile-frontend/src/views/Upload.vue`

当前问题不是“没有推荐模块”，而是“推荐模块还停留在站内轻量排序，尚未形成基于标签聚类和外部候选源的真实推荐闭环”。

请在现有实现基础上，把推荐功能推进到“第一版真实可用”的状态。默认优先级如下：

1. 先强化站内视频标签聚类：
   - 复用已有 `videos.tags`、`videos.summary`、`videos.title`
   - 做标签归一化、去噪、同义主题归并或近似主题聚合
   - 让相同标签的视频能稳定分到一起
   - 推荐结果要真正使用这些聚类结果，而不是只按最近时间排序
2. 再引入外部候选源：
   - 目标来源是 B 站 / YouTube / 中国大学慕课
   - 优先获取轻量元数据，不要在推荐阶段下载完整视频
   - 优先使用 RSS / feed / 公开元数据；若某平台没有稳定 RSS，再做最小化元数据抓取
   - 外部候选也必须走标签提取和归一化
   - 各平台失败要彼此隔离，某一个源不可用时不能拖垮整体推荐接口
3. 再做统一排序与接口返回：
   - 推荐结果应能返回“站内视频”和“外部候选”两类项
   - 返回结构里要明确来源、跳转方式、推荐理由、标签、原始链接等必要字段
   - 兼容现有推荐接口时优先保持已有字段不破坏；如需扩展 schema，请保持向后兼容
4. 最后接前端：
   - 首页推荐区或新增推荐页要能展示站内和外部推荐
   - 外部项必须明确展示来源平台与“导入学习链路”动作
   - 不要把外部候选伪装成已经导入成功的视频
   - 如果选择跳到上传页，优先复用现有链接导入能力并传递 URL
   - “看同主题”按钮必须形成完整闭环：能点、点击后有 loading、能在当前页看到同主题推荐、失败时有明确 fallback 或错误提示

实现时必须遵守这些硬约束：

1. 不要把所有代码一次性改完后才总结。
   你必须每完成一个“可独立提交”的切片，就汇报本切片实际修改了什么、验证了什么、下一步准备做什么。
2. 必须按“可独立提交”的粒度推进。
   每个切片都必须是独立可审阅、可测试、可回滚的，不要把多个大功能糊成一个提交。
3. 如果某一组改动超过 800 行，必须继续拆分。
   不能把超过 800 行的大块功能混成同一组改动。
4. 如果某项文档更新只是为了配合某个功能改动，应跟该功能相邻提交，而不是全部堆到最后。
5. `CHANGELOG.md` 只能追加，绝不能修改或删除历史记录。
   如需更正历史说明，只能在最新条目里写“对某某日期记录的更正说明”。
6. 不要只给计划，不要只给 TODO。
   在确认上下文后直接改代码、补测试、补文档、跑验证。

实现时还必须遵守这些开发规范：

1. 不要恢复桌面 Web、旧 Flask、Android 或与 iOS 主链路无关的分支。
2. 不要把 mock 逻辑包装成真实能力；如果某路径暂时还是占位态，必须明确标识。
3. 不要随意改表；如确实需要改动 schema，必须优先考虑是否可以不改表，或扩展现有结构，并同步更新：
   - SQL 或 schema 管理文件
   - 后端测试
   - `README.md`
   - `docs/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`
   - `CHANGELOG.md`
4. 新增后端能力必须补测试，至少覆盖：
   - 标签聚类核心逻辑
   - 外部候选源适配或解析逻辑
   - 推荐接口主路径
   - 关键失败路径
5. 前端改动完成后，至少要跑：
   - `npm run build:ios`
   - `bash ios-app/sync_ios_web_assets.sh`
   - 如涉及 iOS 容器或桥接，补 `bash ios-app/validate_ios_build.sh`

建议你按下面的切片推进，每个切片完成后先汇报，再继续下一个切片：

1. 切片一：站内标签聚类与排序增强
   - 只聚焦后端
   - 在现有推荐 service 基础上引入标签标准化、主题分桶、排序增强
   - 补对应单测/API 测试
   - 文档和 `CHANGELOG.md` 只做与本切片直接相关的追加更新
2. 切片二：外部候选源抽象与元数据标签处理
   - 设计统一的外部候选结构
   - 以适配器模式接入 B 站 / YouTube / 中国大学慕课
   - 优先实现轻量元数据拉取和标签提取，不下载完整视频
   - 补适配器与失败回退测试
3. 切片三：统一推荐接口与前端接入
   - 扩展推荐接口返回结构
   - 首页或推荐页展示混合推荐
   - 外部项接到既有 URL 导入链路
   - 完成 iOS WebAssets 同步和必要验证

如果你发现某个平台在当前环境下无法稳定做真实采集，请遵守以下原则：

1. 先保持其它来源正常工作，不要因为一个源卡死整体功能。
2. 明确在代码和说明里标出该平台的限制，而不是伪造结果。
3. 优先保留可扩展的 adapter 接口和失败隔离，而不是为了“看起来全支持”写死假数据。

完成每个切片后请输出：

1. 本切片实际修改了什么
2. 涉及哪些文件
3. 运行了哪些测试/构建/同步命令
4. 当前剩余风险和下一切片计划

如果用户要求你创建 commit，在提交前必须提醒用户检查：

1. 当前分支
2. `git status`
3. `git diff --staged`
4. `git log --oneline -5`
5. 测试/验证状态
6. 是否误包含 secrets 或 machine-local 配置
```

## 七、使用建议

如果你准备把这份提示词交给编码助手，推荐这样使用：

1. 先附上本文件。
2. 再附上 `AGENTS.md`。
3. 如果你只想推进某一个子任务，再补一句明确范围，例如：
   - “这一轮先只做站内标签聚类和相关推荐增强，不接前端。”
   - “这一轮只做外部候选源适配器和接口，不改 UI。”
   - “这一轮前端只负责把外部推荐项接到上传页预填 URL，不新增独立推荐页。”

## 七点五、用户动线（产品视角，与实现同步）

1. **首页与推荐页**共用 `GET /api/recommendations/videos`；首页默认 `include_external=true`（`VITE_RECOMMENDATION_HOME_INCLUDE_EXTERNAL`，默认开启），以便与推荐中枢一致的「站外候选 → 入库 → 可打开详情」闭环。
2. **已登录**：后端在 `RECOMMENDATION_AUTO_IMPORT_EXTERNAL`、`include_external` 为真时，对可导入站外候选自动 `import_remote_video_from_url`，响应中条目为 `item_type=video`、`action_type=open_video_detail`，用户进入的是真实 `videos.id` 详情页，可继续处理链路。
3. **未登录**：仍返回站外候选（链接类），用户需手动导入或登录后刷新以看到已入库视频。
4. **首屏加载顺序**：首页应先拉齐视频列表再拉推荐，避免「推荐为空、兜底仍为空」的竞态。
5. **兜底可见性**：当推荐接口失败或返回空集合但首页有视频库兜底时，前端应明确提示“当前为兜底结果”，避免用户误解为实时推荐。
6. **iOS 打包约束**：`WKWebView` 构建采用单文件 `iife + inlineDynamicImports`，路由懒加载在 iOS 包内不产生独立 chunk；相关体积告警策略应结合该约束解释。

## 八、验收底线

视频推荐这一轮完成后，至少应满足以下底线：

1. 不是只有前端卡片，而是接入真实后端推荐逻辑。
2. 不是只按最近时间排序，而是真正使用标签聚类或主题信号。
3. 不是只推站内视频，而是能返回外部候选源结果，且来源清晰可辨。
4. 不是把外部结果停留在浏览，而是能接回现有“链接导入 -> 处理 -> 学习”的主链路。
5. 不是只在浏览器里看起来正常，而是在 iOS `WKWebView` 中也可正常使用。

## 九、Recommendation Contract v1（冻结，基线：2026-04-11）

本节为推荐子系统的**单一事实源（SSOT）**：工单拆分、测试用例与渐进升级应与本节对齐；与 `AGENTS.md` 冲突时以仓库规范为准，并在此节追加「更正说明」。

### 架构与交付角色（执行提示词摘要）

以高级系统架构师 / 技术负责人身份推进「相似性视频推荐」重构：需求澄清 → 方案 → 实现 → 测试 → `WKWebView` 验证 → 演示交付。UI 须与现有 `mobile-frontend/` 一致、简洁可信；业务与排序**仅在后端**；遵守增量 TDD、可回滚提交、`CHANGELOG.md` 仅追加等仓库规则。

### 契约分级说明

- **P0**：上线与互操作性底线，未满足不得标为完成。
- **P1**：可观测、对账、渐进升级与治理增强。
- **P2**：实验、解释接口、弱网/A-B 等增强项。

### A. API 契约（后端对外）

| ID | 要求 |
|----|------|
| P0-C001 | `GET /api/recommendations/scenes` 必须返回 200，响应体包含 `message` 与 `scenes[]`。 |
| P0-C002 | `scenes[].value` 只允许 `home\|continue\|review\|related`。 |
| P0-C003 | `scenes[].requires_seed=true` 仅允许出现在 `related`。 |
| P0-C004 | `GET /api/recommendations/videos` 支持参数：`scene`、`limit`(1..12)、`include_external`、`coach`、`seed_video_id`、`exclude_video_ids`、`user_id`(legacy)。 |
| P0-C005 | `scene=related` 且缺少 `seed_video_id` 必须返回 422，`detail="scene=related 时必须传入 seed_video_id"`。 |
| P0-C006 | `seed_video_id` 不存在必须返回 404，`detail="seed 视频不存在"`。 |
| P0-C007 | `scene` 非法值必须自动归一到 `home`，不得 500。 |
| P0-C008 | `exclude_video_ids` 必须支持逗号分隔整数，非法片段忽略，不得 500。 |
| P0-C009 | `Authorization: Bearer <token>` 有效时，`personalized=true/false` 按真实兴趣信号计算。 |
| P0-C010 | 无 token 时接口仍可用，降级为非个性化推荐，不返回 401。 |
| P0-C011 | `message` 固定为「获取推荐视频成功」。 |
| P0-C012 | `strategy` 必须可追踪：`video_status_interest_v1`（无站外）或 `video_status_interest_external_v2`（含站外）。 |
| P0-C013 | `POST /api/recommendations/import-external` 入参沿用 `VideoUploadURL` 契约，至少包含 `url`。 |
| P0-C014 | `import-external` 成功返回 `VideoUploadResponse`，且 `status` 为 `downloading\|pending\|processing` 之一。 |
| P0-C015 | 重复导入须走现有去重语义（`duplicate=true`），不得重复造脏数据。 |
| P1-C016 | 新增 `request_id`/`trace_id` 回传头（如 `X-Trace-Id`），便于前后端对账。 |
| P1-C017 | `videos` 接口增加 `contract_version` 字段，便于渐进升级。 |
| P1-C096 | 新增 `GET /api/recommendations/ops/metrics` 聚合接口（窗口天数可配），返回推荐导入成功率与导入后处理完成率，供运营看板直接消费。 |
| P2-C018 | 可选 `POST /api/recommendations/explain`，默认模板，不依赖强制 LLM。 |

### B. 响应字段契约（`/api/recommendations/videos`）

| ID | 要求 |
|----|------|
| P0-C019 | 顶层字段稳定：`scene`、`strategy`、`personalized`、`fallback_used`、`seed_video_id`、`seed_video_title`、`internal_item_count`、`external_item_count`、`external_failed_provider_count`、`external_fetch_failed`、`sources`、`external_query`、`external_providers`、`items`、`coach_summary`；以及 **`contract_version`**（P1-C017）。 |
| P1-C095 | **闭环 v2（追加）**：`flow_version`（`recommendation_flow_v1` \| `recommendation_flow_v2`）、`auto_materialized_external_count`、`auto_materialization_failed_count`；`items[]` 可含 `materialized_from_external`、`materialization_status`（站外候选经自动入库后转为站内视频项时）。`include_external=false` 时仍为 v1 语义，自动入库计数为 0。 |
| P0-C020～C030 | `items` 永不为 `null`；计数一致；`sources` / `external_query` / `external_providers` / 单条 `item` 字段与站内外动作语义见原冻结清单（`reason_code`、`action_type`、可导入与不可导入分支等）。 |
| P1-C031 | `reason_code` 枚举白名单文档化（见 D 段）。 |
| P1-C032 | `recommendation_score` 保留 2 位小数，禁止字符串化。 |
| P2-C033 | 可选 `rank_index` 字段，便于 A/B 与回放。 |

### C. 请求参数与输入校验

P0-C034～C038：limit 边界、`RECOMMENDATION_INCLUDE_EXTERNAL_DEFAULT`、`RECOMMENDATION_MAX_CANDIDATES_SCAN`、`related` 排除 seed、`exclude_video_ids` 对站内与 fallback 同时生效。P1：scene 大小写兼容、`user_id` 仅 legacy。P2：locale/lang 预留。

**闭环 v2 配置（后端 Settings）**：`RECOMMENDATION_AUTO_IMPORT_EXTERNAL`（默认 `true`）控制登录态下是否对可导入站外候选自动写入 `videos`；`RECOMMENDATION_AUTO_IMPORT_MAX_ITEMS`（默认 `2`）限制单次 `/videos` 响应前最多尝试自动入库的站外条数。为 `false` 或 `max_items=0` 时退化为仅返回候选、不自动写库。

### D. 排序、理由、降级

P0-C042～C048：主题信号优先、四场景差异化、`related` 同主题优先、站外同 provider 语境、`fallback_used` 触发条件唯一、站外失败不拖垮主接口、空结果合法。P1-C049：`reason_code` 白名单。P1-C050：`coach_summary` 不阻塞主链路。P2-C051：冷启动策略版本号。

### E. 外部来源与合规（治理）

P0-C052～C057：轻量元数据、域名白名单集中配置、超时/重试/并行可开关、失败可见、缓存键维度。P1-C058～C059：import 前 URL 校验、治理执行入口不可绕过。P2-C060：版权与外链分地区配置。

### F. 可观测性与复利

P0-C061～C063：接入 `app.analytics.telemetry`；事件含 `event_type`、`trace_id`、`module`、`status`、`latency_ms`、`metadata`；建议事件集：`recommendation_request_received`、`recommendation_ranking_completed`、`recommendation_external_fetch_completed`、`recommendation_external_fetch_failed`、`recommendation_fallback_used`、`recommendation_import_external_*`；闭环 v2 另含 `recommendation_external_materialization_completed`、`recommendation_external_materialization_failed`（自动入库成功/失败摘要）与 `recommendation_ops_metrics_served`（运营聚合接口访问）。P1-C064～C066：Trace 透传、告警阈值、轨迹导出。P2-C067：效果指标沉淀。

### G. 前端与 iOS

P0-C068～C073：四态 UI、related loading 与 seed 固定、站内外区分、动作跟随后端 `action_type`、`WKWebView` 验证。P1-C074 / P2-C075：可访问性与弱网。

### H. 兼容、发布、回滚

P0-C076～C078：不破坏现有解析；新增字段向后兼容；可回退站内-only + recent fallback。P1-C079～C080：特性开关与版本化灰度。P2-C081：A/B 归档。

### I. 测试契约

P0-C082～C087：API/排序/站外隔离/fallback/import/本地验证链（`validate_backend_smoke`、`compileall`、`build:ios`、`sync_ios_web_assets`、`validate_ios_build`）。P1-C088～C089：遥测与轨迹导出。P2-C090：离线策略对比。

### J. 文档与变更记录

P0-C091～C092：API/行为变化同步 `README.md` 与 `docs/*recommendation*`；`CHANGELOG.md` 仅追加。P1-C093：以**本节**为 SSOT，避免 prompt 分叉。P2-C094：运行手册。

### 实现状态速查（维护时请更新）

| 条目 | 说明 |
|------|------|
| P1-C016 / P1-C064 | `GET/POST /api/recommendations/*` 回传 `X-Trace-Id` 与 `X-Request-Id`（与上游透传一致时可对账）。 |
| P1-C017 | 响应体含 `contract_version`，默认与 `settings.RECOMMENDATION_CONTRACT_VERSION` 一致。 |
| P0-C061～C063 | `RECOMMENDATION_TELEMETRY_ENABLED` 为真时写入推荐域 telemetry 事件（见路由层）。 |
| P1-C096 | `GET /api/recommendations/ops/metrics`：聚合返回 `recommendation_import.success_rate` 与 `processing.completion_rate`，并附 `auto_materialization.success_rate`；数据源字段 `data_source` 便于识别 `database` / `memory_fallback`。 |
| 用户闭环增强 | 登录态下，`/api/recommendations/videos` 可将站外可导入候选自动入库后再返回（`flow_version=recommendation_flow_v2`、`auto_materialized_external_count`），用户可直接打开详情继续处理链路。 |
| 安全回归补充 | `POST /api/recommendations/import-external` 在 `AUTH_ALLOW_LEGACY_USER_ID_ONLY=True` 且 Bearer 无效时返回 401，不回退 legacy `user_id`（见 `tests/api/test_recommendation_api.py`）。 |
| 其余 P0 | 以现有 `recommendation` 路由、`video_recommendation_service`、`Recommendations.vue` 为准持续对齐；缺口在 issue/下一迭代关闭。 |
