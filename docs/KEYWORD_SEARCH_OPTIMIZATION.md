# 关键词搜索（标签相似度）优化技术文档

更新日期：2026-04-10
适用范围：`../edumind-backend/app/services/llm_similarity_service.py` 及其配套模块

## 1. 目标与边界

本次优化目标是提升“标签相似度”能力的可治理性和可回归性，不替代语义搜索主链路排序。

- 主链路（语义搜索）仍由 `app/services/search/` 负责。
- 本文关注 `LLMSimilarityService` 的提示词治理、解析稳健性、日志可观测与测试闭环。

## 2. 目录与职责

### 2.1 新增模块

- `app/services/tag_similarity_prompts.py`
  - 提示词模板与版本管理（v1/v2）
- `app/services/config_model_params.py`
  - 模型参数白名单、输入清洗、相似度默认配置
- `app/services/similarity_score_parser.py`
  - 统一分值解析与错误分型
- `app/services/similarity_analytics.py`
  - 审计日志结构体与统计聚合

### 2.2 变更模块

- `app/services/llm_similarity_service.py`
  - Provider 调用统一接入上述模块
  - 重试、降级与延迟拆分逻辑收敛
- `app/core/config.py`
  - 增加 `SIMILARITY_MAX_RETRIES`
  - 增加 `SIMILARITY_PROMPT_VERSION`

## 3. 关键实现

### 3.1 提示词版本化

- `TagSimilarityPromptFactory` 统一构建 `system/user/ollama` 提示词。
- 通过版本号切换模板，避免硬编码散落在服务代码中。

### 3.2 参数白名单与输入治理

- OpenAI 与 Ollama 分别维护可用模型和参数配置。
- 非白名单模型直接拒绝。
- 标签输入统一清洗、裁剪并做长度约束。

### 3.3 统一解析器

- 两条 provider 路径都走 `SimilarityScoreParser.parse()`。
- 支持常见输出形式（纯数字、`score: X`、代码块包裹数字）。
- 严格范围约束 `[0,1]`，并输出错误类型用于审计。

### 3.4 重试与降级

- 主流程从 `settings.SIMILARITY_MAX_RETRIES` 读取重试次数。
- 单次尝试顺序：Ollama（启用时）→ OpenAI（启用时）。
- 所有尝试失败后返回降级值：`SimilarityConfig.DEFAULT_FALLBACK_SCORE_ON_ERROR or 0.0`。

### 3.5 延迟测量修复

- 使用 `time.perf_counter()` 测总耗时。
- 记录 `parse_latency_ms` 为真实解析耗时。
- `provider_latency_ms = max(0.0, total_elapsed - parse_elapsed)`，避免浮点误差出现负值。

## 4. 测试策略

### 4.1 单元测试

- `test_tag_similarity_prompts.py`
  - 版本切换、模板输出一致性
- `test_config_model_params.py`
  - 白名单与输入治理边界
- `test_similarity_score_parser.py`
  - 多格式解析、越界值、错误分型
- `test_similarity_analytics.py`
  - 日志字段、统计结构与漂移检测
- `test_llm_similarity_service.py`
  - 重试链路、配置注入、返回值解包、延迟拆分

### 4.2 本次实测结果

```bash
cd ../edumind-backend
python -m pytest tests/unit/test_llm_similarity_service.py -q
python -m pytest tests/unit/test_similarity_score_parser.py tests/unit/test_similarity_analytics.py -q
python -m pytest tests/smoke -q
```

- `test_llm_similarity_service.py`: 7 passed
- `parser + analytics`: 64 passed
- `smoke`: 6 passed

## 5. 可观测字段（当前）

`SimilarityAuditLog` 当前关键字段：

- `trace_id`
- `prompt_version`
- `provider` / `model`
- `score` / `score_raw`
- `provider_latency_ms`
- `parse_latency_ms`
- `retry_count`
- `fallback_reason`

## 6. 已知限制（P1）

- `SimilarityMetrics` 目前是进程内聚合，重启后日志不保留。
- 尚未接入统一外部遥测系统（如 Prometheus / DataDog）。
- 运行轨迹尚未自动进入训练闭环。

## 7. 发布与回滚

- 发布建议：先灰度 `SIMILARITY_PROMPT_VERSION=v2`。
- 监控重点：解析失败率、超时率、分值漂移。
- 回滚方式：切回 `v1`，并保留故障窗口的审计样本。

## 8. 与语义搜索主链路关系

- 标签相似度服务是“子能力”，不是 `search.py` 主排序替代品。
- 若未来引入查询改写或重排 LLM，应单独模块化并纳入治理层，不直接塞入 router。
