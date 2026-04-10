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
| `SearchEventLogger._log_event(dict)` | `emit_search_legacy_event(get_telemetry(), dict)` | 仍由 `SearchEventLogger` 内部调用；`dict["event"]` → `event_type`；缺省 `trace_id` 时自动生成 |
| `SearchEventLogger.log_*` 各静态方法 | 不变（仍调用 `_log_event`） | 对外签名未改 |
| `SimilarityAuditLogger.log_*` | 内部 `_emit_unified` → `emit_similarity_audit_event` | 不再向 `similarity_audit` logger 打 `[START]/[SUCCESS]` 前缀行；统一走管道 JSON |
| 直接读 `similarity_audit` logger 文本 | 改为解析 **`app.analytics.telemetry`** JSON 行或采集侧按 `module=similarity` 过滤 | **破坏性**仅对依赖旧字符串格式的日志采集；业务 API 无变 |
| 相似度漂移 / 失败率告警（手工） | `AnalyticsAlertEngine.evaluate_rates(module)`、`evaluate_drift_report(dict)` | 进程内滑动窗口；阈值见配置节 |

---

## 配置项（`app/core/config.py` / 环境变量）

| 变量 | 含义 | 默认 |
|------|------|------|
| `ANALYTICS_LOG_LEVEL` | `app.analytics.telemetry` 级别 | `INFO` |
| `ANALYTICS_ALERT_MAX_FAILURE_RATE` | 失败率（`status=error`）上限 | `0.15` |
| `ANALYTICS_ALERT_MAX_TIMEOUT_RATE` | 超时或超慢占比上限 | `0.10` |
| `ANALYTICS_ALERT_LATENCY_TIMEOUT_MS` | 「慢」判定毫秒阈值 | `30000` |
| `ANALYTICS_ALERT_DRIFT_REL_THRESHOLD` | 漂移告警文案中引用的相对阈值 | `0.10` |

---

## 迁移完成清单（本仓库）

- [x] `app/analytics`：`schema`、`pipeline`、`alerting`、`adapters/search`、`adapters/similarity`
- [x] `SearchEventLogger` 委托统一管道；异常时 DEBUG 降级，不阻断搜索
- [x] `SimilarityAuditLogger` 委托统一管道；异常时 DEBUG 降级，不阻断相似度计算
- [x] 配置项与默认告警阈值
- [x] 单元测试：`test_analytics_*.py`（schema / pipeline / alerting / adapters）
- [x] 回归：`test_similarity_analytics.py`、相似度与审计持久化相关测试通过

---

## 残留风险列表

1. **告警窗口为进程内内存**：重启清零；多实例各自统计，不适合作为唯一 SLO 数据源。
2. **高流量下 `emit` 附带 `evaluate_rates`**：窗口满后每次 emit 可能输出 WARNING 行；生产可调高阈值或后续拆「异步评估」。
3. **旧日志采集若解析 `[SUCCESS]` 前缀**：需切换为 JSON 解析；本仓库已不再输出该格式。
4. **`trace_id` 在搜索侧**：旧 dict 无 `trace_id` 时每条自动生成，跨服务关联需调用方传入 `trace_id` 字段（可选增强）。

---

## 测试命令（开发自验）

```bash
cd backend_fastapi
pytest tests/unit/test_analytics_schema.py tests/unit/test_analytics_pipeline.py \
  tests/unit/test_analytics_alerting.py tests/unit/test_analytics_adapters.py \
  tests/unit/test_similarity_analytics.py -q
```

---

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-04-10 | P1-2 首版交付 |
