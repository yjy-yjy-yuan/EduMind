# Compounding 闭环 MVP（P1-3）：轨迹导出与反馈管道

## 目标

为 **search** / **similarity** 运行轨迹建立可复用闭环：**结构化导出**、**脱敏**、**质检**、**反馈样本格式**，并支持**离线调度**。本阶段 **不包含** 重训练平台、特征存储集群、实时流处理。

---

## 已完成能力（本仓库可落地）

| 能力 | 说明 |
|------|------|
| 按日导出 | 从 `semantic_search_logs`、`similarity_audit_logs` 按 **UTC 日历日** 拉取（`created_at` / `date_key`） |
| 格式 | **JSONL**（`compounding_feedback_v1`）+ 搜索侧可选 **CSV**（脱敏列） |
| 脱敏 | `user_id` → **SHA256 截断哈希**（盐可配）；`query_text` / `tag` / `error_message` **裁剪** |
| 质检 | 缺字段、`schema` 不一致、`trace_id` 字段存在性、`meta.date_key` 一致性、**重复键**、**异常耗时/分值** |
| 质量报告 | 同目录 **`report_{date}_{batch_id}.json`**：样本量、**combined_error_rate**、相似度 batch **均值/标准差**、**drift_summary** 文本摘要（非生产级漂移模型） |
| 调度入口 | `backend_fastapi/scripts/export_compounding_trajectories.py`：**重试**（指数退避）、**幂等**（报告已存在则跳过，除非 `--force`） |
| 在线性能 | 导出仅在 **离线脚本/手动任务** 中执行，**不挂载** 到请求热路径 |

---

## 未完成 / 非目标（后续可扩展）

| 项 | 说明 |
|----|------|
| 重训练平台 | 不包含作业编排、GPU 集群、实验跟踪 |
| 流式 ingest | 无 Kafka/Pulsar；仅批量 DB 导出 |
| 强标签 | `labels` 多为占位；人工/评估标注需另管道 |
| 全局漂移检测 | 报告内为 **batch 内统计摘要**，非多版本模型漂移监控 |
| 分布式锁 | 幂等依赖本地文件存在性；多机并发写同一目录需外部协调 |

---

## 反馈记录格式（`compounding_feedback_v1`）

每行 JSON 含：`schema_version`、`source`（`search` \| `similarity`）、`record_id`、`trace_id`、`features`（脱敏后）、`labels`、`quality_flags`、`meta`。

- `search` 侧会带 `features.trace_id`、`features.trace_id_present`（若源表暂未落 `trace_id` 则为空，便于未来跨域关联扩展）。
- `meta.date_key` 为质检必填字段，用于后续 ETL 分区一致性校验。

详见：`app/compounding/formats.py`。

---

## 使用方式

在 **`backend_fastapi`** 目录下（已配置 `DATABASE_URL`）：

```bash
python scripts/export_compounding_trajectories.py --date 2026-04-10 --batch-id nightly
```

常用参数：

- `--output-dir`：默认 `exports/compounding`
- `--sources`：`search,similarity`（逗号分隔）
- `--formats`：`jsonl,csv`
- `--force`：覆盖已存在 `report_*.json`
- `--max-retries`：数据库失败重试次数（默认 3）

输出文件示例：

- `search_{date}_{batch_id}.jsonl`
- `similarity_{date}_{batch_id}.jsonl`
- `search_{date}_{batch_id}.csv`
- `report_{date}_{batch_id}.json`

---

## 配置与依赖

- 依赖现有 **MySQL** 表：`semantic_search_logs`、`similarity_audit_logs`（未建表则对应源导出为空）。
- 脱敏与裁剪参数已接 `Settings`（可环境变量覆盖）：
  - `COMPOUNDING_USER_ID_HASH_SALT`
  - `COMPOUNDING_QUERY_TEXT_MAX_CHARS`
  - `COMPOUNDING_TAG_MAX_CHARS`
  - `COMPOUNDING_ERROR_MESSAGE_MAX_CHARS`
- UTC 边界说明：导出查询按“UTC 语义的 naive 时间”计算日界，需与库表 `created_at` 写入口径保持一致。

---

## 测试

```bash
cd backend_fastapi
pytest tests/unit/test_compounding_export.py -q
```

---

## 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-04-10 | P1-3 MVP 首版 |
| 1.1 | 2026-04-10 | `trace_id/meta.date_key` 质检增强，脱敏配置接入 `Settings`，UTC 边界假设显式化 |
