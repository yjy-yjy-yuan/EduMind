# SentrySearch 集成现状说明

更新日期：2026-04-10

## 1. 文档目的

本文件用于说明 EduMind 当前“语义搜索能力”的集成边界与真实状态，避免将历史阶段性描述误当作现状。

## 2. 当前真实状态

EduMind 没有作为独立外部服务接入 SentrySearch，而是将相关能力吸收进 `../edumind-backend/app/services/search/`：

- 切片：`chunker.py`
- 嵌入工厂与后端：`embedder.py`、`gemini_embedder.py`、`local_embedder.py`
- 向量存储：`store.py`
- 搜索编排：`search.py`
- 路由：`app/routers/search.py`
- 索引任务：`app/tasks/vector_indexing.py`

## 3. 与历史描述的更正

以下历史说法已不准确，现统一更正：

- “`local_embedder.py` 仍为占位实现” → 已不成立。
- “搜索结果预览文本尚未回填字幕” → 已不成立，当前链路支持 `preview_text`。
- “前端和 iOS 搜索 UI 未落地” → 已不成立，已存在基础搜索页与 iOS WebView 验证链路。

## 4. 当前仍需持续完善的项

- 认证与权限链路仍需按产品要求持续收敛。
- 搜索相关监控指标与审计日志仍在迭代中。
- 结果质量（召回、重排、阈值）仍需基于真实样本持续调参。

## 5. 权威入口文档

- 搜索部署与状态：`../edumind-backend/SEMANTIC_SEARCH_DEPLOYMENT.md`
- 项目总览：`README.md`
- 变更留痕：`CHANGELOG.md`
