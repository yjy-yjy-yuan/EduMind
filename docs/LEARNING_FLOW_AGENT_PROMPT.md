# EduMind 学习流智能体 — 完整提示词（哲学 + 技术）

**实现目标仓库（绝对路径）**：`/Users/yuan/final-work/EduMind`
**路径索引与可选参考仓库**：见同目录 [`PROJECT_PATHS.md`](./PROJECT_PATHS.md)。在其它文件夹/工作区开发时，请把上述路径写进任务描述，避免 AI 找错工程。

本文档供实现者或 AI 编码助手**一次性**遵循：前半为**设计哲学与原则**，后半为**可落地的搭建/重构说明**。二者冲突时，先对齐产品再改代码。

---

## 第一部分：设计哲学（建议通读后再实现）

### 1. 产品哲学：学习优先于「炫技」

- **学习是主语，Agent 是工具**。任何能力若不能缩短「从视频到可复习知识」的路径，就不值得优先做。
- **可预期胜过聪明**。用户宁可要稳定、可解释的笔记与时间戳，也不要偶尔惊艳、经常跑偏的「全自动」。
- **透明优先**：`plan` 与 `action_records` 不只是调试字段，而是用户对过程的信任基础——步骤要人话、可对照，避免黑箱「已完成」。
- **默认不替用户做重大决定**：删改、覆盖、批量操作需显式意图或二次确认（在 EduMind 现有交互约束内实现）。

### 2. 工程哲学：朴素、显式、可删

- **宁可用清晰的规则分支 + 可读函数名，也不要过早抽象**。抽象在第二次重复时再抽。
- **显式优于隐式**：意图从哪里来（规则 / LLM）、失败回退到哪一级，在代码路径上应一读就懂。
- **一个编排内核，多种场景配方**：扩展靠「多一个分支、多一组步骤」，不靠复制整套服务。
- **易维护 = 未来的自己能删代码**：每个开关（如 LLM 意图）都能整体关掉且系统仍可用。

### 3. Agent 哲学：编排优于自主，边界优于全能

- **本项目的 Agent 本质是「带上下文的业务流程编排」**，不是通用自主智能体。不追求多轮工具循环、长期记忆、开放式目标——那是另一类产品与成本结构。
- **强边界**：单次请求内完成明确任务；超出边界时诚实降级（模板回复、提示用户换说法），而不是幻觉补全。
- **人保留最终签字权**：写库、绑时间戳等副作用在架构上应集中、可审计；Agent 只负责提议与执行已授权类型的操作。

### 4. 成本与延迟哲学：省在刀刃上

- **规则与确定性逻辑是默认路径**；LLM 是可选加速器，不是地基。
- **每次用户操作默认 ≤1 次 LLM 调用**（除非配置显式放开）；多步若需多调用，必须写明理由与预算。
- **输入截断、超时、降级**不是优化项，是契约：无密钥、模型失败、超时，系统仍应给出可用结果或清晰错误。
- **缓存与复用**：同一视频、同一片段、短时间内重复请求，在实现简单的前提下复用摘要或中间结果。

### 5. 诚实哲学：限制是特性

- **明确写出 Agent「不会做什么」**（在文档与错误提示中一致），比夸大能力更能建立长期信任。
- **不把「不确定」包装成「事实」**：分类、意图置信度低时，用中性表述或请用户澄清。
- **日志哲学**：记录足够排障，不记录密钥与完整隐私文本；长度用计数或 hash 代替原文。

### 6. 演进哲学：渐进增强，而非大爆炸

- **先跑通、再聪明**：先保证规则路径与写库正确，再打开 LLM 意图或润色。
- **每个版本只引入一个「新风险面」**（例如本版只加意图分类，不改表结构），便于回滚与对比。
- **与 EduMind 架构对齐**：能力放在 `../edumind-backend`，前端薄；**不要**为 Agent 单独引入第二套运行时（如 Node/Bun CLI）。

### 7. 协作哲学：提示词与代码一样要可读

- **给下一位维护者留「为什么」**：在 `pipeline` 或配置旁用简短注释写非显而易见的权衡（为何截断、为何回退到规则）。
- **行为变化写进根目录 `CHANGELOG.md`**：遵守 EduMind 变更日志规范。

### 8. 反模式清单（明确禁止）

- 为演示效果而默认开启高成本模型或长上下文。
- 把业务 SQL 和 prompt 字符串散落在多处，导致无法单测、无法关 LLM。
- 用「再套一层 Agent」解决所有问题，而不是先收敛产品需求。
- 在移动端暴露密钥或把调试信息当作用户可见文案。

---

## 第二部分：技术实现提示词

### 角色与目标

在仓库 **`/Users/yuan/final-work/EduMind`**（主工程根目录，勿与其它仓库混淆）内，对**学习流智能体**进行模块化搭建与重构。目标：

1. **保持产品形态**：仍是 FastAPI 暴露的 `POST /api/agent/execute`，移动端 H5 经同一后端；**不**引入外部 TS/CLI 项目作为运行时依赖。
2. **借鉴架构思想（非拷贝外部代码）**：拆成「上下文组装 → 意图路由 → 分步工具（纯函数/小类）→ 持久化 → 结构化 `action_records`」，便于测试与迭代。
3. **遵守仓库约束**：以根目录 **`AGENTS.md`** 为准——仅 `../edumind-backend` + `mobile-frontend` + `ios-app`；**数据库保持 MySQL**；不随意改表；新能力优先适配现有表（`Note`、`NoteTimestamp`、`Video` 等）。
4. **测试约束**：仓库 **AGENTS.md** 规定「禁止使用 pytest 测试修改的程序」——本次任务以**手工验收清单** + **`/docs` 手工调用**为主，不要用 `../edumind-backend/tests/` 里的 pytest 作为本次改动的自动化验证手段。

### 现状基线（实现前必读）

| 项目 | 路径 |
|------|------|
| 路由 | `../edumind-backend/app/routers/agent.py` |
| 核心逻辑 | `../edumind-backend/app/services/learning_flow_agent.py` |
| 契约 | `../edumind-backend/app/schemas/agent.py` |
| 前端封装 | `mobile-frontend/src/api/agent.js` |
| 配置 | `../edumind-backend/app/core/config.py` |

### 目标目录结构（建议）

在 **`../edumind-backend/app/services/learning_flow_agent/`** 下建包：

| 模块 | 职责 |
|------|------|
| `context.py` | 从 `AgentExecuteRequest` + `Session` 构建 `LearningContext`（dataclass）：`video`、字幕片段、QA  digest、`page_context`、`user_input`、安全截断上限等。 |
| `intents.py` | `infer_intent`：默认规则/关键词；可选配置项开启短 JSON 的 LLM 意图分类，失败回退规则。 |
| `tools/` | 分模块：`subtitles.py`、`summary.py`、`note_writer.py`、`tags.py` 等；路由层不写业务分支。 |
| `pipeline.py` | `run_learning_flow(ctx) -> dict`：按意图调用工具链，合并 `action_records`，返回与 `AgentPlanResponse` 兼容的 dict。 |
| `__init__.py` | 导出 `execute_learning_flow_agent(db, *, request) -> dict[str, Any]`，供 router 导入。 |

**旧文件**：原单文件 `learning_flow_agent.py` 改为 re-export 或删除，并全仓库更新 import。

### 上下文组装（`build_context`）

1. **视频校验**：`video_id` 存在时，不存在则 `ValueError("视频不存在")`（与现有一致）。
2. **字幕**：迁移并保留「按当前时间取片段」逻辑；设最大字符数（如 4000），超出截断并记 `action_record`：`context_truncated`。
3. **QA**：`recent_qa_messages` 规范为最近 N 条、每条限长，**禁止**无限制 JSON 拼进 prompt。
4. **`page_context`**：参与意图与步骤（如 `qa` 与 `video_detail` 区分对待）。

### 意图与计划

1. **`infer_intent`**：阶段 A 必做——关键词 + 规则，至少区分若干类（如时间戳笔记 / 仅摘要不写库 / 需澄清）。阶段 B 可选——`LEARNING_AGENT_INTENT_LLM_ENABLED` 为真且密钥可用时，一次短 LLM 调用输出 JSON：`intent`、`confidence`、`reason_short`；失败回退阶段 A。
2. **`build_plan(intent, ctx) -> list[str]`**：步骤对用户可读，并与 `action_records` 大致一致。

### 工具函数约定

每个工具建议返回：

```text
{ "ok": bool, "data": dict, "message": str, "record": Optional[{type, message, data}] }
```

`pipeline` 合并 `record`；失败时短路，`result` 含明确错误信息；HTTP 映射保持与 `routers/agent.py` 现有一致。

### 与 `video_content_service` 集成

- 摘要：继续优先 `fallback_summary`、`normalize_summary_style`；新增 LLM 片段摘要放在 `tools/summary.py`，复用现有 Qwen/DeepSeek 配置模式。
- 标签与分类：迁移 `_infer_note_category`、`_build_thought_tags`、`fallback_tags`，**默认行为不变**。

### API 与 Schema 兼容性

- 默认不破坏 `AgentExecuteRequest` / `AgentPlanResponse`；新字段须 `Optional` + 默认值。
- 若扩展（如 `dry_run`），须同步 `mobile-frontend/src/api/agent.js` 的 mock 结构。
- `routers/agent.py` 保持 `response_model=AgentPlanResponse`。

### 建议新增配置（`config.py`）

- `LEARNING_AGENT_MAX_SUBTITLE_CHARS`
- `LEARNING_AGENT_MAX_QA_MESSAGES` / `LEARNING_AGENT_MAX_QA_CHARS`
- `LEARNING_AGENT_INTENT_LLM_ENABLED: bool = False`
- `LEARNING_AGENT_INTENT_MODEL: str`（默认可与 `QWEN_QA_MODEL` 对齐）
- Base URL / Key 优先复用现有变量，避免重复密钥。

### 前端最小接入（若尚未接通）

在 `VideoDetail.vue` 或播放器页增加输入与提交，调用 `executeLearningFlowAgent`，传入 `video_id`、`current_time_seconds`、`subtitle_text`、`page_context`、`user_input`；展示 `plan`、`actions`、`action_records`、`result`。Mock 模式字段与后端一致。

### 日志

结构化 `debug` 日志：`intent`、`video_id`、`actions`；禁止打印密钥与完整长字幕。

### 验收标准（手工）

1. 无 `video_id`：行为与现有一致（含 preview），不 500。
2. 合法 `video_id`：可创建笔记；带 `current_time_seconds` 时有 `NoteTimestamp`。
3. 错误 `video_id`：404，`detail` 与现有一致。
4. iOS WKWebView 或文档写明路径下走通一次。
5. 全仓库无错误 import。

### 非目标

- 不引入子进程跑 Node/Bun CLI；不把外部泄漏源码项目编进 EduMind。
- 不新增 MySQL 表，除非产品单独批准。
- 不使用 pytest 作为本次任务的自动化验证手段。

### 交付物

1. 新包与更新的 router/schema/前端（若需要）。
2. 可选：简短 `docs/LEARNING_AGENT_PIPELINE.md`（≤80 行）说明意图枚举与配置。
3. 根目录 **`CHANGELOG.md`** 追加一条。

---

## 第三部分：范围说明

- 本文档针对**现有学习流 Agent**（`POST /api/agent/execute`）的**重构与增强**，不是默认再建一个完全独立的「第二套超级 Agent」产品；若未来拆分多场景，仍建议共用同一编排内核，通过 `scenario`/`mode` 或服务端推断扩展。

---

*文档版本：与 EduMind `AGENTS.md` 及后端目录结构对齐；若目录变更请同步更新本节路径。*
