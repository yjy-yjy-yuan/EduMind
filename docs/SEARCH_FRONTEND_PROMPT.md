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
      "chunk_id": "abc123",
      "start_time": 45.5,
      "end_time": 90.5,
      "similarity_score": 0.87,
      "preview_text": null
    }
  ],
  "total_time_ms": 234,
  "message": null
}
```

## 当前页面约定

- 搜索页路由已接入：`/search`
- 如果从视频详情页进入，会通过 `query.videoId` 和可选的 `query.videoTitle` 传递上下文
- 当前视频搜索依赖这个上下文；没有上下文时，应默认切到“所有视频”

## 前端实现要求

- 输入框、清空按钮、搜索按钮
- 搜索范围切换：
  - 当前视频
  - 所有视频
- 结果卡片展示：
  - 时间范围
  - 相似度百分比
  - 相似度颜色分级
  - `preview_text` 为空时显示“暂无文本预览”
- 点击结果后跳转播放器，并把 `start` 时间通过路由 query 带到 `/player/:id`

## 当前后端限制

- 返回的是平铺结果，不是按视频分组的嵌套结构
- 不返回 `video_title`
- `preview_text` 当前通常为 `null`

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
- 不要假设响应里有 `success`、`data.results`、`video_title`
- 不要把未来规划写成当前已接通能力
