# 前端语义搜索实现提示词

## 目标

为 `mobile-frontend/` 提供一个能直接对接当前后端的语义搜索页面，并确保在 iOS `WKWebView` 里可用。

## 当前真实接口

搜索端点：

`POST /api/search/semantic/search`

请求体：

```json
{
  "query": "机器学习基础",
  "video_ids": [1],
  "limit": 20,
  "threshold": 0.5
}
```

响应体：

```json
{
  "query": "机器学习基础",
  "results": [
    {
      "video_id": 1,
      "video_title": "机器学习导论",
      "chunk_id": "abc123",
      "start_time": 45.5,
      "end_time": 90.5,
      "similarity_score": 0.87,
      "preview_text": "这一段主要介绍监督学习与无监督学习的差异..."
    }
  ],
  "total_time_ms": 234,
  "message": null
}
```

## 当前页面约定

- 搜索页路由已接入：`/search`
- 首页可通过 `query.scope=all` + 可选 `query.q=...` 进入跨视频搜索；若带有首页关键词，搜索页应自动执行一次搜索
- 如果从视频详情页进入，会通过 `query.videoId` 和可选的 `query.videoTitle` 传递上下文
- 当前视频搜索依赖这个上下文；没有上下文时，应默认切到“所有视频”
- 搜索页返回后会恢复上次的关键词、范围和结果；首页来源的一次性自动搜索标记应在首次消费后清理，避免重复请求

## 前端实现要求

- 输入框、清空按钮、搜索按钮
- 搜索范围切换：
  - 当前视频
  - 所有视频
- 结果卡片展示：
  - 视频标题
  - 时间范围
  - 相似度百分比
  - 相似度颜色分级
  - `preview_text` 为空时显示“暂无文本预览”
- 跨视频搜索时允许前端按 `video_id` / `video_title` 分组展示
- 点击结果后跳转播放器，并把 `start` 时间通过路由 query 带到 `/player/:id`

## 当前后端限制

- 返回的是平铺结果，不是按视频分组的嵌套结构
- 搜索结果仍是片段级列表，因此前端若要按视频分组，需要自行聚合
- 搜索质量目前依赖字幕与本地语义链路，`preview_text` 虽已回填，但仍可能受字幕质量影响

如果需要按视频分组，前端自己按 `video_id` 分组。

## iOS 适配要求

- 触摸区域不少于 `44x44`
- 不依赖 hover
- 在 `WKWebView` 中输入、滚动、点击都要稳定

涉及页面交互改动时，至少执行：

```bash
cd mobile-frontend && npm run build:ios
bash ios-app/sync_ios_web_assets.sh
bash ios-app/validate_ios_build.sh
```

## 禁止事项

- 不要把请求字段写成 `query_text`
- 不要把阈值字段写成 `similarity_threshold`
- 不要假设响应里有 `success`
- 不要把 `data.results`、`video_title`、`preview_text` 写回过时的占位说明；应以当前真实接口返回为准
- 不要把未来规划写成当前已接通能力
