# EduMind 语义搜索实现说明

## 当前已落地

### 后端

- 语义搜索路由：
  - `POST /api/search/semantic/search`
  - `POST /api/search/videos/{video_id}/index`
  - `GET /api/search/videos/{video_id}/index/status`
- 自适应切片
- FFmpeg 视频切片
- Gemini / local embedder 工厂
- ChromaDB 持久化存储
- 多用户集合隔离
- 视频处理完成后可自动触发索引

### 前端

- 新增搜索页：`mobile-frontend/src/views/Search.vue`
- 新增搜索 API 封装：`mobile-frontend/src/api/search.js`
- 路由接入：`/search`
- 从视频详情页进入搜索时会携带 `videoId` / `videoTitle`
- 搜索结果点击后会跳到播放器，并带上 `start` 时间

## 本次文档同步

- 修正了搜索提示词中的旧字段名和旧接口名
- 修正了把未来监控规划误写成“已完成”的问题
- 删除了会误导交付的旧验证脚本与未接线日志模块

## 当前限制

- 搜索结果仍是平铺列表，前端按 `video_id` 自行分组
- 后端暂不返回 `video_title`
- `preview_text` 当前通常为 `null`
- 认证仍保留开发态默认用户回退

## 本次验证

```bash
pre-commit --all-files
bash scripts/hooks/pre_push.sh
```

如涉及 iOS 容器资源同步，再补：

```bash
bash ios-app/sync_ios_web_assets.sh
bash ios-app/validate_ios_build.sh
```
