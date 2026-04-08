# EduMind 语义搜索后端落地说明

更新日期：2026-04-08

本文档记录 `backend_fastapi/` 中已经落地的语义搜索后端能力、当前限制和最小部署步骤。它描述的是当前仓库状态，不再把计划项写成“已完成”。

## 当前已落地

### 代码入口

- 路由：`app/routers/search.py`
- Schema：`app/schemas/search.py`
- 搜索服务：`app/services/search/search.py`
- 分片：`app/services/search/chunker.py`
- 向量工厂：`app/services/search/embedder.py`
- Gemini 嵌入：`app/services/search/gemini_embedder.py`
- 本地嵌入占位：`app/services/search/local_embedder.py`
- ChromaDB 存储：`app/services/search/store.py`
- 后台索引任务：`app/tasks/vector_indexing.py`
- 数据模型：`app/models/vector_index.py`
- 迁移脚本：`scripts/migrations_semantic_search.py`

### 已实现能力

- 支持 `mp4` / `mov` 视频切片。
- 支持可配置的切片时长、切片重叠、分辨率和 FPS 预处理。
- 支持将视频片段写入 ChromaDB 持久化目录。
- 支持 Gemini 文本查询嵌入与视频分片嵌入。
- 支持按 `user_{user_id}_video_{video_id}_chunks` 规则隔离集合。
- 支持搜索接口、手动触发索引接口、索引状态接口。
- 支持后台索引任务状态流转：`pending -> processing -> completed/failed`。
- 支持在视频处理完成后按配置自动提交索引任务。

## 当前限制

下面这些点已经在代码或文档中明确为限制，不应再按“已完成”验收：

- `LocalEmbedder` 仍是占位实现，不能视为可用的生产级本地嵌入方案。
- 搜索结果中的 `preview_text` 仍未从字幕回填，当前返回 `null`。
- 认证尚未完全接入搜索路由；当前用户解析优先取请求头 `X-User-ID`，否则回退到默认用户 `1`。
- 本文档不把“视频片段裁剪导出”列为已完成能力，仓库当前没有完整落地 `trimmer.py`。
- 本文档不把前端搜索 UI 或 iOS 搜索交互列为已完成能力；当前提交范围主要是后端链路。

## 需要的配置

在 `backend_fastapi/.env` 中补齐语义搜索配置：

```bash
SEARCH_ENABLED=true
SEARCH_BACKEND=gemini
SEARCH_GEMINI_API_KEY=
SEARCH_CHROMA_DB_DIR=./data/chroma
SEARCH_ADAPTIVE_CHUNKING=true
SEARCH_CHUNK_DURATION=30
SEARCH_CHUNK_OVERLAP=5
SEARCH_PREPROCESS=true
SEARCH_PREPROCESS_RESOLUTION=480
SEARCH_PREPROCESS_FPS=5
SEARCH_AUTO_INDEX_NEW_VIDEOS=true
```

说明：

- 启用 `SEARCH_ADAPTIVE_CHUNKING=true` 后，索引会按视频总时长自动选择切片参数，短视频切得更细，长视频切得更粗。
- 当前默认规则是：`<3min -> 12s/2s`、`<10min -> 20s/4s`、`<30min -> 45s/8s`、`<60min -> 60s/10s`、`>=60min -> 75s/12s`。
- `SEARCH_GEMINI_API_KEY` 为空时，代码会继续尝试走 Gemini SDK 的默认环境变量。
- 开发环境的后台执行器默认是线程池；生产环境可通过 `BACKGROUND_TASK_EXECUTOR=process` 切到进程池。

## 最小部署步骤

### 1. 安装依赖

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend_fastapi/requirements.txt
```

### 2. 创建数据库字段

当前仓库提供的是 SQL 脚本而不是完整 Alembic revision。至少需要落下：

- `vector_indexes` 表
- `videos.has_semantic_index`
- `videos.vector_index_id`
- 若现有 `videos` 表尚无 `user_id`，还需要执行 `backend_fastapi/migrations/add_user_id_to_videos.sql`

### 3. 准备 ChromaDB 目录

```bash
mkdir -p backend_fastapi/data/chroma
```

### 4. 启动后端

```bash
python backend_fastapi/run.py
```

### 5. 验证

```bash
. .venv/bin/activate
python scripts/validate_backend_smoke.py
python -m compileall backend_fastapi/app backend_fastapi/scripts scripts/hooks scripts/validate_backend_smoke.py
```

## 当前接口

### 语义搜索

`POST /api/search/semantic/search`

请求体示例：

```json
{
  "query": "讲了牛顿第二定律的部分",
  "video_ids": [1, 2],
  "limit": 10,
  "threshold": 0.5
}
```

### 手动触发索引

`POST /api/search/videos/{video_id}/index`

### 查看索引状态

`GET /api/search/videos/{video_id}/index/status`

## 验收建议

若要确认这条链路不是“只有骨架”，建议至少验证：

1. 视频处理完成后，`Video.has_semantic_index` 能被更新。
2. ChromaDB 数据目录里能看到对应集合数据。
3. 同一查询对多个视频搜索时能返回按相似度排序的片段。
4. 索引失败时，`vector_indexes.status` 和 `error_message` 会落库。
