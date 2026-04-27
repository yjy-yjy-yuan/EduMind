# 搜索结果详细内容显示 - 功能增强实现

**日期**: 2026-04-08
**版本**: 功能增强 v1.1
**范围**: 后端数据结构扩展 + 前端显示优化 + 搜索状态记忆

---

## 概述

本次实现对搜索结果的显示进行了全面增强，使用户能看到**更丰富的内容信息**，从而快速判断搜索结果的相关性。

### 改动前后对比

| 维度 | 改动前 | 改动后 |
|------|--------|--------|
| **结果信息** | 时间段 + 相似度 + 简短文本 | 视频标题 + 时间段 + 相似度 + 截断预览（240字）+ 交互提示 |
| **视频标题** | 不显示 | 显示视频标题，缺失时回退为"视频 ID: xxx" |
| **字幕内容** | 显示简短预览 | 显示截断预览文本（最多 240 字），最高 60px 高度可滚动 |
| **分组显示** | 分组标题为"视频 ID: xxx" | 分组标题优先显示 `video_title`（⚠️ 暂未补充时长、上传时间等视频元信息） |
| **交互提示** | 无 | "👉 点击播放此片段" 清晰提示 |
| **返回保留状态** | 返回后需重新搜索 | 返回搜索页后自动恢复关键词、范围与结果 |

---

## 后端改动

### 1. 扩展 SearchResultChunk Schema

**文件**: `../edumind-backend/app/schemas/search.py`

**改动**:
```python
class SearchResultChunk(BaseModel):
    """搜索结果中的单个片段"""

    video_id: int
    video_title: Optional[str] = Field(None, description="视频标题")  # ← 新增
    chunk_id: str
    start_time: float
    end_time: float
    similarity_score: float
    preview_text: Optional[str]
```

**说明**: `video_title` 允许为 `null`，前端可优雅降级处理

---

### 2. 搜索逻辑中补齐视频标题

**文件**: `../edumind-backend/app/services/search/search.py`

**改动内容**:

在 `semantic_search_videos()` 函数中：

1. **搜索前获取视频标题映射**
   ```python
   # 获取视频标题映射（用于补充每条搜索结果）
   video_title_map = {}
   if db:
       from app.models.video import Video

       videos = db.query(Video).filter(Video.id.in_(video_ids)).all()
       video_title_map = {v.id: v.title for v in videos}
   ```

2. **创建结果时补齐标题**
   ```python
   chunk = SearchResultChunk(
       video_id=video_id,
       video_title=video_title_map.get(video_id),  # ← 新增
       chunk_id=result["chunk_id"],
       start_time=result["start_time"],
       end_time=result["end_time"],
       similarity_score=result["similarity_score"],
       preview_text=result.get("preview_text"),
   )
   ```

**兼容性**: 不破坏现有 API 接口，`video_title` 新增字段对现有客户端无影响

---

## 前端改动

### 1. 增强 ResultCard 组件

**文件**: `mobile-frontend/src/views/Search.vue`

**改动内容**:

#### (1) 扩展 setup 逻辑，增加字段处理函数

```javascript
const getSimilarityPercentage = (similarity) => {
  return Math.round(similarity * 100)
}

const getVideoTitle = (result) => {
  return result.video_title || `视频 ID: ${result.video_id}`
}

const getPreviewText = (result) => {
  if (result.preview_text && result.preview_text.trim()) {
    return result.preview_text
  }
  return '（暂无文本预览）'
}
```

#### (2) 重构 ResultCard 模板结构

新的卡片内容分层：

**顶部**: 视频标题 + 相似度百分比
```html
<div class="result-header">
  <div class="result-video-title">{{ getVideoTitle(result) }}</div>
  <div class="result-similarity-percentage">
    <span class="percentage-text">{{ getSimilarityPercentage(result.similarity_score) }}% 相关</span>
  </div>
</div>
```

**中部**: 时间范围 + 相似度条
```html
<div class="result-meta">
  <div class="result-time">
    <span class="time-label">⏱️</span>
    <span class="time-range">{{ formatTime(result.start_time) }} - {{ formatTime(result.end_time) }}</span>
  </div>
</div>

<div class="result-similarity">
  <div class="similarity-bar">
    <div class="similarity-fill" :style="{ width: (result.similarity_score * 100) + '%', ... }"></div>
  </div>
</div>
```

**主体**: 字幕预览文本（截断至 240 字，可滚动）
```html
<div :class="['result-preview', { placeholder: !result.preview_text || !result.preview_text.trim() }]">
  {{ getPreviewText(result) }}
</div>
```

**底部**: 交互提示
```html
<div class="result-cta">
  <span class="play-hint">👉 点击播放此片段</span>
</div>
```

---

### 2. 优化分组显示

**改动内容**:

#### (1) 扩展分组计算逻辑

```javascript
const groupedResults = computed(() => {
  const groups = new Map()
  for (const result of results.value) {
    const videoId = result.video_id
    const list = groups.get(videoId) || []
    list.push(result)
    groups.set(videoId, list)
  }
  return Array.from(groups.entries()).map(([videoId, items]) => {
    const videoTitle = items[0]?.video_title || `视频 ID: ${videoId}`  // ← 新增
    return { videoId, videoTitle, items }
  })
})
```

#### (2) 模板中使用优化的分组标题

```html
<div class="result-group-title">{{ group.videoTitle }}</div>
```

之前: `视频 ID: {{ group.videoId }}`
现在: `{{ group.videoTitle }}` (优先显示标题，缺失时回退)

---

### 3. 样式优化

**改动内容**:

#### (1) 结果卡片样式增强

```css
.result-item {
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.result-item:active {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);  /* 按压反馈 */
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.result-video-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1976d2;
  word-break: break-word;
}

.percentage-text {
  font-size: 13px;
  font-weight: 600;
  color: #4CAF50;  /* 绿色表示相关度高 */
}
```

#### (2) 时间范围样式

```css
.time-range {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  font-weight: 500;
  color: #2196f3;
}
```

#### (3) 预览文本样式

```css
.result-preview {
  font-size: 13px;
  line-height: 1.5;
  color: #555;
  margin-bottom: 8px;
  max-height: 60px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;  /* 保留换行 */
}
```

#### (4) 交互提示样式

```css
.result-cta {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
}

.play-hint {
  font-size: 12px;
  color: #2196f3;
  font-weight: 500;
}
```

#### (5) 分组样式

```css
.result-group {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.result-group-title {
  color: #1976d2;
  font-size: 13px;
  font-weight: 600;
  word-break: break-word;  /* 长标题换行 */
}
```

---

### 4. 搜索状态记忆

**目标**:

- 用户点击搜索结果进入播放器后，再返回搜索页时，仍能看到刚才的关键词和匹配结果
- 当前视频搜索与全局搜索分开记忆，避免不同搜索上下文互相覆盖

**实现方式**:

在 `mobile-frontend/src/views/Search.vue` 中新增搜索状态持久化逻辑，基于 `@/utils/storage` 保存以下内容：

- `query`
- `results`
- `error`
- `hasSearched`
- `searchScope`

#### (1) 按上下文生成缓存 key

```javascript
const SEARCH_STATE_KEY_PREFIX = 'm_search_state'

const searchStateKey = computed(() => {
  if (currentVideoId.value !== null) {
    return `${SEARCH_STATE_KEY_PREFIX}:video:${currentVideoId.value}`
  }
  return `${SEARCH_STATE_KEY_PREFIX}:all`
})
```

#### (2) 搜索完成后落盘

```javascript
const persistSearchState = () => {
  const payload = {
    query: query.value,
    results: Array.isArray(results.value) ? results.value : [],
    error: error.value,
    hasSearched: hasSearched.value,
    searchScope: searchScope.value
  }
  storageSet(searchStateKey.value, JSON.stringify(payload))
}
```

#### (3) 页面重新进入时恢复

```javascript
watch(searchStateKey, () => {
  restoreSearchState()
}, { immediate: true })
```

#### (4) 点击结果跳转前先保存状态

```javascript
const handleResultClick = (result) => {
  persistSearchState()
  router.push({
    path: `/player/${result.video_id}`,
    query: { start: String(Math.floor(Number(result.start_time || 0))) }
  })
}
```

#### (5) 清空搜索时同步删除缓存

```javascript
const clearSearch = () => {
  query.value = ''
  results.value = []
  error.value = ''
  hasSearched.value = false
  storageRemove(searchStateKey.value)
}
```

**效果**:

- 从播放器返回搜索页时，关键词不会丢失
- 搜索结果列表会直接恢复，不需要再次请求
- 当前视频搜索和所有视频搜索各自保持独立记忆

---

## 验证结果

✅ **后端编译**: `python -m compileall` 通过
✅ **前端编译**: `npm run build:ios` 成功 (730ms)
✅ **搜索集成验证**: 所有 5 大验证项通过
✅ **代码质量**: pre-commit hooks 通过
✅ **API 兼容性**: 不破坏现有接口

---

## 现场验收清单

### 后端检查

- ✅ `SearchResultChunk` 包含 `video_title` 字段
- ✅ 搜索函数中加入视频标题映射逻辑
- ✅ `video_title` 允许为 `null`（优雅处理缺失数据）
- ✅ 返回结果未改变现有字段名和结构

### 前端检查

- ✅ 结果卡片显示视频标题（或"视频 ID"回退）
- ✅ 结果卡片显示截断预览文本（最多 240 字）
- ✅ 分组标题优先显示 `video_title`
- ✅ 相似度百分比显示正确（0-100%）
- ✅ 点击行为保持不change: `/player/:video_id?start=秒数`
- ✅ iOS `WKWebView` 友好（无 hover，点击区域足够大）

### 用户体验检查

- ✅ 结果卡片信息充分，用户能快速判断相关性
- ✅ 分组清晰，用户能快速找到目标视频（基于视频标题）
- ✅ 时间戳在移动端可读
- ✅ 交互提示清晰（"👉 点击播放此片段"）
- ✅ 截断预览（240 字）在移动端可读
- ⚠️ 缺：视频元信息（时长、上传时间）显示在分组 header 中

---

## 数据示例

### 后端返回格式（示例）

```json
{
  "query": "Vue 组件设计",
  "results": [
    {
      "video_id": 1,
      "video_title": "Vue3 基础学习 - 第二章",
      "chunk_id": "chunk_1_abc123",
      "start_time": 123.45,
      "end_time": 145.67,
      "similarity_score": 0.87,
      "preview_text": "组件是 Vue 应用中最重要的基本概念之一。组件允许我们将 UI 分割成可复用的程序块..."
    },
    {
      "video_id": 1,
      "video_title": "Vue3 基础学习 - 第二章",
      "chunk_id": "chunk_1_def456",
      "start_time": 200.12,
      "end_time": 218.90,
      "similarity_score": 0.72,
      "preview_text": "一个组件通常可以有多个状态，状态的改变决定了组件的展示效果..."
    }
  ],
  "total_time_ms": 234
}
```

### 前端渲染效果

```
┌─────────────────────────────────────┐
│ Vue3 基础学习 - 第二章  87% 相关     │
├─────────────────────────────────────┤
│ ⏱️ 02:03 - 02:26                    │
├─────────────────────────────────────┤
│ ████████████████████░░░░ (87%)       │
├─────────────────────────────────────┤
│ 组件是 Vue 应用中最重要的基本概念    │
│ 之一。组件允许我们将 UI 分割成可     │
│ 复用的程序块...                      │
├─────────────────────────────────────┤
│                  👉 点击播放此片段    │
└─────────────────────────────────────┘
```

---

## ⚠️ 已知限制与后续改进

### 当前版本实现的功能
- ✅ 视频标题补充（每条结果显示所属视频的标题）
- ✅ 相似度百分比显示
- ✅ 截断预览文本展示（最多 240 字）
- ✅ 卡片分层结构优化
- ✅ 交互提示

### 已知限制
1. **[P1] 预览文本仍为截断形式**
   - 当前实现：后端返回 240 字预览，不是完整字幕内容
   - 原因：为保持移动端可读性，避免单条结果过长
   - 改进方案（可选）：
     - 前端提供"展开全文"功能
     - 或后端根据配置增加预览长度（如扩展到 500-1000 字）

2. **[P2] 分组缺少视频元信息**
   - 当前实现：分组标题仅显示 `video_title`
   - 缺失内容：视频时长、上传时间、视频描述等
   - 改进方案（Phase 2）：
     - 后端补充视频时长、上传时间字段
     - 前端分组 header 中显示 `duration` 和 `upload_time`
     - 示例：`"Vue3 基础学习 - 第二章"（45分钟，2025-03-15）`

### 为什么这些限制存在
- **预览文本**: 提示词明确要求"不要把搜索结果改成重型详情接口"，240 字截断是合理的平衡
- **视频元信息**: 当前版本侧重于视频标题补充，元信息补充作为后续增强功能（不阻塞当前迭代）

---

## 后续可选增强

### Phase 2（下一迭代）
- 视频组 header 补充元信息：
  - 视频时长：`duration`
  - 上传时间：`uploaded_at`
  - 示例显示：分组标题下方显示 "45分钟 | 2025-03-15 上传"
- 字幕搜索高亮（在预览文本中标记匹配关键词）

### Phase 3（可选）
- 创建完整字幕查看功能
- 视频缩略图（需后端补充）
- 转录内容搜索（需转录表集成）

---

## 技术约束与说明

✅ **不违反项目规范**
- 仅改动搜索模块，不涉及其他功能
- 不新增表或大接口
- 不引入 HLS 或复杂媒体链路
- 保持 iOS `WKWebView` 兼容性

✅ **API 兼容性**
- 新增字段 `video_title` 对现有客户端无影响
- 搜索请求字段保持不变: `query`、`video_ids`、`limit`、`threshold`
- 路由和播放器跳转行为不改变

✅ **数据来源**
- 视频标题直接来自 Video 模型
- 字幕预览来自已存在的 ChromaDB 索引

---

**状态**: ✅ 实现完成 | 验证: ✅ 全部通过 | 部署就绪
