# 集中式遥测管道（P1-2）迁移说明

## 目标

将 **SearchEventLogger**、**SimilarityAuditLogger** 等结构化日志收敛到 **`app.analytics`** 统一管道：固定 **event schema**、单一写入入口、可配置日志级别、最小告警规则，并保持 **对外 API 不变**（向后兼容）。

---

## 统一事件 Schema（外层）

所有经管道落日志的行均为 **单行 JSON**，包含：

| 字段 | 说明 |
|------|------|
| `timestamp` | UTC ISO8601（Z） |
| `schema_version` | 当前为 `1` |
| `event_type` | 业务事件名（如 `search_completed`、`similarity_call_success`） |
| `trace_id` | 追踪 ID |
| `module` | `search` \| `similarity` \| … |
| `latency_ms` | 可选，毫秒 |
| `status` | `ok` \| `error` \| `timeout` \| `degraded` \| `started` |
| `metadata` | 领域字段（原扁平 dict 中除 `event`/`timestamp`/`trace_id`/`duration_ms` 外的键） |

Logger 名：**`app.analytics.telemetry`**。级别由配置 **`ANALYTICS_LOG_LEVEL`**（默认 `INFO`）与事件 `status` 共同决定（`error` → ERROR，`timeout`/`degraded` → WARNING，其余 INFO）。

---

## 旧入口 → 新入口映射

| 旧入口 / 行为 | 新入口 | 说明 |
|----------------|--------|------|
| `SearchEventLogger._log_event(dict)` | `emit_search_legacy_event(get_telemetry(), dict)` | `dict["event"]` → `event_type`；`duration_ms` 容错解析，失败时 `latency_ms=None` 且 `metadata.parse_error` 记录原因；缺省 `trace_id` 时使用 **`ANALYTICS_TRACE_ID_PLACEHOLDER`**（默认 `unset`），并设 `metadata.trace_id_source=missing` |
| `SearchEventLogger.log_*`（搜索主链路） | 可选参数 **`trace_id`** | `/api/search/semantic/search` 从 **`X-Trace-Id`** 或 **`X-Request-Id`** 透传至 `semantic_search_videos` → 各日志事件，便于端到端关联 |
| `SimilarityAuditLogger.log_*` | 内部 `_emit_unified` → `emit_similarity_audit_event` | 不再向 `similarity_audit` logger 打 `[START]/[SUCCESS]` 前缀行；统一走管道 JSON |
| 直接读 `similarity_audit` logger 文本 | 改为解析 **`app.analytics.telemetry`** JSON 行或采集侧按 `module=similarity` 过滤 | **破坏性**仅对依赖旧字符串格式的日志采集；业务 API 无变 |
| 相似度漂移 / 失败率告警（手工） | `AnalyticsAlertEngine.evaluate_rates(module)`、`evaluate_drift_report(dict)` | 进程内滑动窗口；阈值见配置节；**同键节流**（`failure_rate:<module>`、`timeout_or_slow:<module>`）由 `ANALYTICS_ALERT_MIN_INTERVAL_SEC` 控制重复 WARNING |

---

## 搜索 `status` 推断（事件名关键字）

顺序：**timeout** → **degraded** → **error** → **started** → **ok**。

| 命中子串（`event` 小写） | `status` |
|--------------------------|----------|
| `timeout`、`timed_out`、`time_out` | `timeout` |
| `degraded`、`partial_success`、`fallback` | `degraded` |
| `failed`、`_fail`、`fault`、`_error` | `error` |
| `search_request_received` 或以 `_request_received` 结尾 | `started` |
| 其他 | `ok` |

---

## 配置项（`app/core/config.py` / 环境变量）

| 变量 | 含义 | 默认 |
|------|------|------|
| `ANALYTICS_LOG_LEVEL` | `app.analytics.telemetry` 级别 | `INFO` |
| `ANALYTICS_ALERT_MAX_FAILURE_RATE` | 失败率（`status=error`）上限 | `0.15` |
| `ANALYTICS_ALERT_MAX_TIMEOUT_RATE` | 超时或超慢占比上限 | `0.10` |
| `ANALYTICS_ALERT_LATENCY_TIMEOUT_MS` | 「慢」判定毫秒阈值 | `30000` |
| `ANALYTICS_ALERT_DRIFT_REL_THRESHOLD` | 漂移告警文案中引用的相对阈值 | `0.10` |
| `ANALYTICS_ALERT_MIN_INTERVAL_SEC` | 同一告警键重复输出的最小间隔（秒） | `60` |
| `ANALYTICS_TRACE_ID_PLACEHOLDER` | 未提供 `trace_id` 时的占位符 | `unset` |

---

## 迁移完成清单（本仓库）

- [x] `app/analytics`：`schema`、`pipeline`、`alerting`、`adapters/search`、`adapters/similarity`
- [x] `SearchEventLogger` 委托统一管道；异常时 DEBUG 降级，不阻断搜索
- [x] `SimilarityAuditLogger` 委托统一管道；异常时 DEBUG 降级，不阻断相似度计算
- [x] 配置项与默认告警阈值
- [x] 单元测试：`test_analytics_*.py`（schema / pipeline / alerting / adapters）
- [x] 回归：`test_similarity_analytics.py`、相似度与审计持久化相关测试通过

### 测试计数口径（避免与汇报/审计不一致）

以下命令**仅统计** `test_analytics_*.py` 四文件（不含 `test_similarity_analytics.py` 等回归）：

```bash
cd ../edumind-backend
pytest tests/unit/test_analytics_schema.py tests/unit/test_analytics_pipeline.py \
  tests/unit/test_analytics_alerting.py tests/unit/test_analytics_adapters.py -q
```

**等价写法**：`pytest tests/unit/test_analytics_*.py -q`。
**计数口径**：以 `pytest` 实际 **collected** 为唯一准绳；文档中的数字仅作历史样例，不作为长期固定事实。

与 `test_similarity_analytics.py` 一并跑时，合计条数 =
`collected(test_analytics_*.py) + collected(test_similarity_analytics.py)`，请以命令行输出为准。

---

## 残留风险列表

1. **告警窗口为进程内内存**：重启清零；多实例各自统计，不适合作为唯一 SLO 数据源。
2. **高流量下 `emit` 附带 `evaluate_rates`**：已用告警键节流降低重复 WARNING；仍可调高阈值或后续拆「异步评估」。
3. **旧日志采集若解析 `[SUCCESS]` 前缀**：需切换为 JSON 解析；本仓库已不再输出该格式。
4. **端到端追踪**：客户端/网关应传 **`X-Trace-Id`**；未传时 `trace_id` 为占位符 + `metadata.trace_id_source=missing`，便于监控侧过滤。

---

## 测试命令（开发自验）

```bash
cd ../edumind-backend
pytest tests/unit/test_analytics_schema.py tests/unit/test_analytics_pipeline.py \
  tests/unit/test_analytics_alerting.py tests/unit/test_analytics_adapters.py \
  tests/unit/test_similarity_analytics.py -q
```

---

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-04-10 | P1-2 首版交付 |
| 1.1 | 2026-04-10 | 搜索 duration 容错、`status` 关键字扩展、告警节流、`X-Trace-Id` 透传 |
| 1.2 | 2026-04-10 | 明确 `test_analytics_*.py` 测试计数口径；补充 `duration_ms > 1e12` 降级用例 |
| 1.3 | 2026-04-10 | 测试计数改为“动态口径优先”，弱化固定数字维护成本 |
