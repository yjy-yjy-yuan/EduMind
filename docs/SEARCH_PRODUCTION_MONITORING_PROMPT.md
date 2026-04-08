# 语义搜索生产监控提示词

## 目标

为 EduMind 当前语义搜索后端规划一套可渐进落地的生产监控方案。

## 当前真实状态

已存在：

- 搜索路由
  - `POST /api/search/semantic/search`
  - `POST /api/search/videos/{video_id}/index`
  - `GET /api/search/videos/{video_id}/index/status`
- 标准 Python 日志
- 自适应切片、FFmpeg 切片、Gemini / local embedder、ChromaDB 存储

尚未完成：

- Prometheus exporter
- Grafana dashboard
- ELK 日志链路
- Sentry
- request id / trace id

## 监控建设顺序

### Phase 1

先补关键日志点：

- 搜索请求入口
- 自适应切片参数选择
- 索引开始 / 完成 / 失败
- 搜索完成 / 失败
- Gemini 调用失败
- ChromaDB 搜索失败

### Phase 2

如果部署环境允许，再补 Prometheus 指标：

- `search_api_requests_total`
- `search_api_duration_seconds`
- `search_index_runs_total`
- `search_index_failures_total`
- `search_query_results_count`

### Phase 3

再考虑：

- Sentry
- 告警规则
- runbook
- trace id

## 当前真实字段

请求字段：

- `query`
- `video_ids`
- `limit`
- `threshold`

响应字段：

- `query`
- `results`
- `total_time_ms`
- `message`

## 不要写错

- 不要把端点写成 `/api/search/index`
- 不要把字段写成 `query_text`
- 不要把阈值写成 `similarity_threshold`
- 不要把未来规划写成“当前已经完成”
