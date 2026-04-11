# 关键词搜索（标签相似度）优化交付总结

更新日期：2026-04-10
分支：`0410-feature/keyword-search-optimization`

## 1. 本次已交付内容

### 代码模块（后端）
- `backend_fastapi/app/services/tag_similarity_prompts.py`
- `backend_fastapi/app/services/config_model_params.py`
- `backend_fastapi/app/services/similarity_score_parser.py`
- `backend_fastapi/app/services/similarity_analytics.py`
- `backend_fastapi/app/services/llm_similarity_service.py`
- `backend_fastapi/app/core/config.py`

### 单元测试
- `backend_fastapi/tests/unit/test_tag_similarity_prompts.py`
- `backend_fastapi/tests/unit/test_config_model_params.py`
- `backend_fastapi/tests/unit/test_similarity_score_parser.py`
- `backend_fastapi/tests/unit/test_similarity_analytics.py`
- `backend_fastapi/tests/unit/test_llm_similarity_service.py`

### 文档与脚本
- `docs/KEYWORD_SEARCH_OPTIMIZATION.md`
- `scripts/demo_keyword_search.py`
- `scripts/verify_keyword_search_submission.sh`

## 2. P0 收敛结果（已完成）

- 提示词治理：标签相似度提示词从服务代码中拆出，支持版本化（v1/v2）与回滚。
- OpenAI/Ollama 一致性：统一走提示词工厂与统一解析器，避免双实现分叉。
- 安全治理：模型参数白名单、输入清洗、防注入约束。
- 解析稳健性：支持多格式解析，覆盖越界、无数字、多数字等错误分类。
- 审计与监控：结构化日志记录（trace_id、provider、prompt_version、parse/latency 等）。
- 重试链路：`SIMILARITY_MAX_RETRIES` 配置化，重试与降级逻辑可追踪。
- 延迟拆分：记录真实 `parse_latency_ms`，`provider_latency_ms` 使用 `perf_counter` + 下限保护。

## 3. 本次验证（实测）

在当前工作区执行并通过：

```bash
cd backend_fastapi
python -m pytest tests/unit/test_llm_similarity_service.py -q
python -m pytest tests/unit/test_similarity_score_parser.py tests/unit/test_similarity_analytics.py -q
python -m pytest tests/smoke -q
```

结果：
- `test_llm_similarity_service.py`: 7 passed
- `parser + analytics`: 64 passed
- `smoke`: 6 passed

补充：
- 服务层测试已加严，去除恒真断言，补齐配置注入链路验证。

## 4. 仍属 P1 的事项（未宣称完成）

- 轨迹持久化：`SimilarityMetrics` 目前为进程内存聚合，未接入持久化存储。
- 集中式遥测平台：尚未接入统一外部遥测管道（如 Prometheus / DataDog）。
- 反馈闭环自动化：尚未把运行轨迹自动导入训练/评估闭环。

## 5. 发布建议

- 灰度：先按小流量启用 `SIMILARITY_PROMPT_VERSION=v2`。
- 监控：重点关注解析失败率、超时率、分值分布漂移。
- 回滚：异常时切回 `v1` 并保留审计样本用于复盘。
