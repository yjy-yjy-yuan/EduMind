# SentrySearch 集成记录

更新日期：2026-04-08

这个文件保留为“集成记录 + 当前边界”，不再继续使用早期的大段规划提示词。目的是让后续维护者快速知道：EduMind 语义搜索后端已经接入了哪些能力，哪些部分仍然没有完成。

## 已吸收进 EduMind 的能力

- 视频切片能力：
  `backend_fastapi/app/services/search/chunker.py`
- 向量嵌入工厂：
  `backend_fastapi/app/services/search/embedder.py`
- Gemini 视频/文本嵌入：
  `backend_fastapi/app/services/search/gemini_embedder.py`
- ChromaDB 持久化存储：
  `backend_fastapi/app/services/search/store.py`
- 搜索服务编排：
  `backend_fastapi/app/services/search/search.py`
- 搜索路由与状态接口：
  `backend_fastapi/app/routers/search.py`
- 后台索引任务：
  `backend_fastapi/app/tasks/vector_indexing.py`

## 当前实现方式

- EduMind 没有把 SentrySearch 作为外部服务挂进来，而是按现有 FastAPI 架构把必要模块吸收到 `backend_fastapi/app/services/search/`。
- 向量数据当前存储在本地 ChromaDB 持久化目录中。
- 每个视频单独建集合，集合名按 `user_{user_id}_video_{video_id}_chunks` 组织。
- 索引任务通过 EduMind 现有后台执行器提交，而不是新增 Celery 专用链路。

## 当前未完成或仅占位的部分

- `backend_fastapi/app/services/search/local_embedder.py`
  仍是占位实现，不应作为已完成的本地模型能力宣传。
- 搜索结果预览文本尚未回填字幕。
- 视频片段裁剪导出能力未在当前提交中完整落地。
- 前端和 iOS 搜索 UI 未包含在这次后端集成范围内。

## 当前文档入口

- 后端部署与当前状态：
  `backend_fastapi/SEMANTIC_SEARCH_DEPLOYMENT.md`
- 根目录产品说明：
  `README.md`
- 后端说明：
  `backend_fastapi/README.md`

## 后续继续扩展时的约束

- 不要把真实业务能力重新塞回 `mobile-frontend/`。
- 不要把这套搜索链路描述成“完整已验收”，除非本地嵌入、认证接入、字幕预览和前端/iOS 验证都补齐。
- 如果后续修改搜索接口、索引流程或部署步骤，需要同步更新上面三份文档和 `CHANGELOG.md`。
