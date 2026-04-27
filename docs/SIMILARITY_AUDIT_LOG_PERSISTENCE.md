# 相似度审计日志持久化实现 (P1-1)

## 概述

本文档描述相似度审计日志 (`SimilarityAuditLog`) 从纯内存转向持久化存储的架构和实现。

**目标**：在不破坏现有接口的前提下，实现服务重启后日志不丢失，并支持按天统计和按 trace_id 溯源。

---

## 架构设计

### 分层结构

```
┌─ API 路由层 (FastAPI)
│  └─ query logs, daily stats, trace lookup
│
├─ Service 层 (SimilarityAuditLogPersistenceService)
│  ├─ 内存缓冲管理（兼容原 SimilarityMetrics）
│  ├─ 同步持久化到 DB（失败不阻断主流程；由调用方持有短 `Session`）
│  ├─ 失败重试与降级策略；`persist_from_memory` 重试带指数退避（有上限）
│  └─ 查询接口（DB 优先）
│
├─ Repository 层 (SimilarityAuditLogRepository)
│  ├─ CRUD 操作
│  ├─ 批量保存
│  ├─ 按日期查询
│  └─ 按 trace_id 快速查找
│
└─ ORM 模型层 (SimilarityAuditLogModel)
   ├─ 数据库表定义
   ├─ 索引优化
   └─ 与内存对象的转换
```

### 可用性优先设计

- **内存+DB 双路**：DB 故障时自动降级到内存缓冲
- **失败重试**：单条 `record_log` 失败则保留在内存；`persist_from_memory` 对未落库条目按 `max_retries` 重试并指数退避
- **缓冲溢出管理**：内存缓冲区有大小限制，防止无限增长
- **服务重启恢复**：DB 中的日志可完整恢复（不依赖内存）

---

## 数据库设计

### 表结构：`similarity_audit_logs`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT | 主键 |
| `trace_id` | VARCHAR(50) | 追踪 ID，便于回溯单次计算 |
| `date_key` | VARCHAR(10) | 日期键 (YYYY-MM-DD)，用于按天查询 |
| `tag1`, `tag2` | VARCHAR(255) | 输入标签 |
| `event_type` | VARCHAR(50) | 事件类型 (call_start/success/failed/retry/fallback) |
| `provider` | VARCHAR(50) | 提供商 (openai/ollama/fallback) |
| `model` | VARCHAR(100) | 模型名称 |
| `prompt_version` | VARCHAR(50) | 提示词版本 |
| `success` | BOOLEAN | 是否成功 |
| `score` | FLOAT | 最终分值 (0-1) |
| `score_raw` | TEXT | 原始提取字符串 |
| `score_normalized` | FLOAT | 正规化后的分值 |
| `latency_ms` | FLOAT | 总耗时（毫秒） |
| `provider_latency_ms` | FLOAT | 提供商调用耗时 |
| `parse_latency_ms` | FLOAT | 解析耗时 |
| `parse_ok` | BOOLEAN | 是否解析成功 |
| `parse_error_type` | VARCHAR(50) | 解析错误类型 |
| `retry_count` | INT | 重试次数 |
| `retry_failed` | BOOLEAN | 是否经历重试失败 |
| `fallback_reason` | VARCHAR(255) | 降级原因 |
| `error_message` | TEXT | 错误信息详情 |
| `extra_metadata` | JSON | 扩展元数据 |
| `created_at` | DATETIME | 记录创建时间 |

### 索引策略

```sql
INDEX idx_trace_id (trace_id)          -- 快速按 trace_id 查找
INDEX idx_date_key (date_key)          -- 快速按日期筛选
INDEX idx_date_trace (date_key, trace_id)  -- 联合查询优化
INDEX idx_created_at (created_at)      -- 时间范围查询
```

---

## 部署说明

### 1. 执行数据库迁移

```bash
# 方式一：使用 MySQL CLI
mysql -h 127.0.0.1 -u root -p edumind < ../edumind-backend/migrations/add_similarity_audit_logs.sql

# 方式二：使用脚本（若有 ORM 自动创建功能）
python ../edumind-backend/scripts/init_db.py --create
```

### 2. 应用初始化

在 FastAPI `lifespan` 启动阶段调用 `init_persistence_service()`（本仓库已在 `app/main.py` 的 `lifespan` 中接入）。`scripts/init_db.py` 的 `MANAGED_TABLE_NAMES` 已包含 `similarity_audit_logs`，执行 `python scripts/init_db.py --create` 会与其他业务表一并创建缺失表。

### 3. 使用持久化服务

`record_log` 需要可提交的 `Session`（与依赖注入的 `get_db()` 生成器不同，需在业务代码中显式 `SessionLocal()` 并 `close`）。`LLMSimilarityService` 已通过 `_record_similarity_audit_log` 使用全局持久化单例写入 DB。

```python
from app.core.database import SessionLocal
from app.services.similarity_service_container import get_persistence_service

service = get_persistence_service()
db = SessionLocal()
try:
    service.record_log(audit_log, db)
finally:
    db.close()

# 查询每日统计（同样需要会话）
db = SessionLocal()
try:
    stats = service.get_daily_stats("2026-04-10", db)
    log = service.get_log_by_trace_id("trace_001", db)
    logs = service.get_logs_in_date_range("2026-04-01", "2026-04-10", db)
finally:
    db.close()
```

---

## 测试覆盖

### 单元测试（17 个）

所有测试位于 `../edumind-backend/tests/unit/test_similarity_audit_log_persistence.py`

#### Repository 层（6 个测试）
- ✅ 单条日志保存
- ✅ 日志真实持久化验证
- ✅ 按日期查询（空结果）
- ✅ 按日期查询（有结果）
- ✅ 按 trace_id 查询
- ✅ 批量保存

#### Service 层（6 个测试）
- ✅ 服务初始化
- ✅ 内存+DB 并行记录
- ✅ DB 故障自动降级到内存
- ✅ 从 DB 查询统计（支持重启恢复）
- ✅ 按 trace_id 溯源
- ✅ 无数据时统计 `date` 与查询日一致

#### 降级与重试（3 个测试）
- ✅ DB 错误时自动降级
- ✅ 初始失败后重试
- ✅ 内存缓冲大小限制

#### 集成测试（2 个测试）
- ✅ 端到端保存和查询
- ✅ 重启恢复验证

### 测试结果

```
======================== 17 passed in 0.08s =========================
```

### 回归测试（已验证）

- ✅ 原有 64 个相似度测试仍全部通过（与上表合计 **81/81**）
- ✅ 烟雾测试通过
- ✅ 编译检查通过
- ✅ Pre-commit 钩子通过

---

## 配置项

可在 `app/core/config.py` 中配置：

```python
# 相似度持久化配置
SIMILARITY_AUDIT_LOG_PERSISTENCE_ENABLED: bool = True
SIMILARITY_AUDIT_LOG_MAX_MEMORY_BUFFER: int = 1000  # 内存缓冲区大小
SIMILARITY_AUDIT_LOG_MAX_RETRIES: int = 3  # 持久化重试次数
```

---

## 运维指南

### 数据查询

#### 查询今天的统计信息

```python
from app.core.database import SessionLocal
from app.services.similarity_service_container import get_persistence_service

service = get_persistence_service()
db = SessionLocal()
try:
    today_stats = service.get_daily_stats(None, db)  # None 表示今天
    print(f"Total calls: {today_stats['total_calls']}")
    print(f"Success rate: {today_stats['success_rate']:.2%}")
    print(f"Avg latency: {today_stats['avg_latency_ms']:.1f}ms")
finally:
    db.close()
```

#### 按 trace_id 回溯单次计算

```python
db = SessionLocal()
try:
    log = service.get_log_by_trace_id("trace_001", db)
finally:
    db.close()
if log:
    print(f"Tag1: {log.tag1}, Tag2: {log.tag2}")
    print(f"Score: {log.score}")
    print(f"Latency: {log.latency_ms}ms")
    print(f"Provider: {log.provider}, Model: {log.model}")
```

### 数据清理

#### 删除 30 天前的日志

```python
from datetime import datetime, timedelta

cutoff_date = (datetime.utcnow() - timedelta(days=30)).date().isoformat()
deleted_count = repo.delete_logs_before_date(cutoff_date, db)
print(f"Deleted {deleted_count} logs before {cutoff_date}")
```

### 监控告警

#### 检测相似度分布漂移

推荐使用 `LLMSimilarityService.check_score_drift`（已对接持久化统计）；若仅做进程内调试也可用 `SimilarityMetrics.check_drift`。

```python
from app.services.llm_similarity_service import llm_similarity_service

drift_report = llm_similarity_service.check_score_drift(
    date="2026-04-10",
    baseline=0.5,
    threshold=0.1,
)

if drift_report["drift_detected"]:
    print(f"⚠️ Drift detected! Mean: {drift_report['actual_mean']:.3f}")
```

---

## 故障排除

### 问题 1：DB 连接失败时日志不记录

**症状**：DB 连接异常时，日志完全丢失

**解决**：写入失败时 `record_log` 会捕获异常并保留内存缓冲；若暂时无法持有会话，可传 `db=None` 仅写内存。

```python
# ✅ 正常：传入会话尝试落库
service.record_log(audit_log, db)

# ✅ 仅内存（例如无 DB 或脚本环境）
service.record_log(audit_log, None)
```

### 问题 2：内存缓冲满了会怎样

**症状**：长期 DB 不可用，内存缓冲达到上限

**解决**：FIFO 队列会自动丢弃最旧的日志，保留最新的。可调整 `max_memory_buffer` 配置。

```python
init_persistence_service(max_memory_buffer=2000)  # 增大缓冲区
```

### 问题 3：如何强制从内存重新持久化

**症状**：一段时间内 DB 恢复了，想从内存缓冲中恢复日志

**解决**：

```python
service.persist_from_memory(db)  # 将内存中所有日志重新提交到 DB
```

---

## 性能指标

### 单条日志操作

| 操作 | 耗时 | 备注 |
|------|------|------|
| 内存缓冲记录 | <1ms | O(1) |
| DB 单条插入 | 1-5ms | 取决于 MySQL 配置 |
| 按 date_key 查询 | 1-10ms | 有索引 |
| 按 trace_id 查询 | 1-3ms | 单行查询，主索引 |
| 批量插入 100 条 | 10-50ms | 取决于 batchsize |

### 内存占用

- 单条日志（ORM 模型）：~2KB
- 缓冲 1000 条：~2MB
- 缓冲 10000 条：~20MB

### DB 存储

- 单条日志：~1.5KB（含索引）
- 1 个月数据（1M 条日志）：~1.5GB

---

## 配置优化建议

### 生产环境推荐

```python
# app/core/config.py

# 启用持久化
SIMILARITY_AUDIT_LOG_PERSISTENCE_ENABLED: bool = True

# 合理缓冲区大小（10 min 数据量，假设 100 QPS）
SIMILARITY_AUDIT_LOG_MAX_MEMORY_BUFFER: int = 60000

# 重试次数
SIMILARITY_AUDIT_LOG_MAX_RETRIES: int = 3

# 定期清理策略（可选）
SIMILARITY_AUDIT_LOG_RETENTION_DAYS: int = 30
SIMILARITY_AUDIT_LOG_CLEANUP_HOUR: int = 2  # 凌晨 2 点
```

---

## 检查清单

分两类：**代码与仓库侧**（本分支已交付，下列为「已完成」状态）与 **目标环境侧**（各 MySQL/集群上线前自行勾选）。

### 代码与仓库侧（本仓库已满足）

- [x] **应用启动**：`app/main.py` 的 `lifespan` 中已调用 `init_persistence_service()`
- [x] **审计写入路径**：`LLMSimilarityService` → `_record_similarity_audit_log` → `SessionLocal` + `SimilarityAuditLogPersistenceService.record_log`
- [x] **自动化测试**：持久化专项 **17** 项 + 相似度域 **64** 项，合计 **81/81**（维护发布前在 `../edumind-backend` 下跑通即视为满足）
- [x] **烟雾脚本**：`python scripts/validate_backend_smoke.py`（仓库级回归已覆盖）

### 目标环境侧（部署到具体库/集群时自验）

- [ ] 数据库表已创建（`similarity_audit_logs`）
- [ ] 表索引已生效（`SHOW INDEX FROM similarity_audit_logs;`，预期含主键及 4 个二级索引）
- [ ] 监控 DB 连接错误率与日志缓冲量（按运维策略接入）

---

## 后续改进

### 可选项（低优先级）

1. **异步持久化**：使用后台任务队列（Celery/RQ）
   - 优点：完全非阻塞
   - 缺点：增加复杂度

2. **日志分片**：按日期创建分片表
   - 优点：大数据量下查询快
   - 缺点：需要复杂的迁移策略

3. **实时告警**：集成 Prometheus/DataDog
   - 优点：及时发现问题
   - 缺点：需要额外基础设施

4. **导出功能**：JSON/CSV 批量导出
   - 优点：便于分析
   - 缺点：I/O 压力

---

## 参考链接

- ORM 模型：[similarity_audit_log.py](../app/models/similarity_audit_log.py)
- Repository：[similarity_audit_log_repository.py](../app/repositories/similarity_audit_log_repository.py)
- Service：[similarity_audit_log_service.py](../app/services/similarity_audit_log_service.py)
- 测试：[test_similarity_audit_log_persistence.py](../tests/unit/test_similarity_audit_log_persistence.py)
- Migration：[add_similarity_audit_logs.sql](../migrations/add_similarity_audit_logs.sql)

---

## 版本历史

| 版本 | 日期 | 描述 |
|------|------|------|
| 1.0 | 2026-04-10 | 初始实现；持久化专项 17 项；与相似度 64 项合计 81/81 |
