# EduMind Video Recommendation UI Implementation Prompt

> 用途：给 Codex、Claude、Blitz 等编码助手直接使用，用于在当前 EduMind 仓库中优先推进“视频推荐 UI 页面”建设。
> 适用仓库：`/Users/yuan/final-work/EduMind`
> 当前产品边界：iOS-only，唯一有效链路为 `mobile-frontend/` + `../edumind-backend/` + `ios-app/`

## 一、当前任务定位

这一次不要优先扩展推荐后端能力，也不要重新设计推荐算法。
本轮目标是：**优先完成视频推荐相关的 UI 页面、交互结构和 iOS `WKWebView` 可用性打磨**，让推荐系统在移动端上有稳定、清晰、可点击、可跳转的页面体验。

你必须遵守以下事实：

1. `mobile-frontend/` 是唯一前端代码库，负责推荐页面、首页推荐卡片、上传跳转、来源标识、空态与交互状态。
2. `../edumind-backend/` 是唯一真实后端，但本轮默认不优先做新的推荐算法改造；如需调用推荐接口，只能复用已有接口或兼容现有字段。
3. `ios-app/` 是唯一 iOS 容器，所有前端交互改动最终都要考虑 `WKWebView` 的点击、滚动、路由跳转和安全区适配。
4. 本轮是 **UI-first**，不是 recommendation-engine-first。

## 二、当前推荐 UI 基础

仓库里已经有推荐相关的基础页面，不是从零开始：

- `mobile-frontend/src/views/Home.vue`
  - 已有首页推荐入口、推荐卡片和“推荐系统”入口位。
- `mobile-frontend/src/views/Recommendations.vue`
  - 已有独立「推荐学习中枢」页：当前为 **Hero + 单列表**（`scene=home`）、刷新与卡片动作；已移除多场景切换、页内「同主题」区与 hero 开发者说明卡片。
- `mobile-frontend/src/views/Upload.vue`
  - 已支持通过 query 参数预填 URL，适合承接“导入学习”动作。
- `mobile-frontend/src/api/recommendation.js`
  - 已有推荐接口封装。
- `mobile-frontend/src/api/mockGateway.js`
  - 已有 UI-only 模式的推荐 mock 数据。
- `mobile-frontend/src/views/VideoDetail.vue`
  - 视频详情：**上方**固定封面与基础信息（`.video-detail__shared`）；**下方**为「学习处理 / 相关推荐」页签与横向分页（`scroll-snap`），仅该区域随手势左右切换。
- `mobile-frontend/src/components/videoDetail/VideoDetailRecommendPanel.vue`、`VideoDetailRecommendCard.vue`
  - 相关推荐列表与卡片；数据来自 `scene=related` + `seed_video_id`。
- `mobile-frontend/src/services/recommendationPresentation.js`、`videoDetailTelemetry.js`
  - 字段映射、跳转与 `CustomEvent('edumind:telemetry')` 埋点（`detail.scope === 'video_detail'`）。

当前问题不是“完全没有推荐页”，而是：

1. 推荐页面还需要继续强化视觉层级、场景区分、卡片表达和导入动线。
2. 首页推荐入口与推荐页之间还需要更清晰的 UI 一致性。
3. 站内视频与站外候选的展示关系，还需要更明确的移动端表达。
4. 所有改动都必须优先服务真机体验，而不是桌面浏览器截图效果。

## 三、本轮 UI 目标

请围绕以下 UI 目标推进：

1. 让首页能够更明确地暴露“推荐系统”入口和推荐预览。
2. 让推荐页成为一个完整的学习推荐中枢，而不是零散卡片集合。
3. 让用户能够区分：
   - 首页推荐
   - 当前场景推荐
   - 当前视频相关推荐
   - 站外候选导入项
4. 让站外推荐项的动作表达足够清晰：
   - 明确标识来源平台
   - 明确这是“导入学习”，不是“直接播放”
5. 让整个页面在 iPhone 尺寸下保持：
   - 一眼可理解
   - 单手可点击
   - 卡片层级明确
   - 不拥挤、不漂浮、不桌面化

## 四、实现边界

本轮只优先推进 UI 页面与交互，不要越界：

1. 可以改：
   - `mobile-frontend/src/views/*.vue`
   - `mobile-frontend/src/api/*.js`
   - `mobile-frontend/src/router/*.js`
   - 与 UI 改动直接相关的 iOS `WebAssets` 同步产物
   - 与本轮 UI 改动直接相关的文档和 `CHANGELOG.md`
2. 不要优先改：
   - 推荐算法本身
   - 数据库表结构
   - 重型抓取任务
   - 新的推荐后端服务设计
3. 如果发现某个 UI 需要更多后端字段：
   - 优先兼容已有字段
   - 可以在代码注释或文档中明确指出期望字段
   - 但本轮不要把大块精力转去做后端重构

## 五、必须遵守的开发规范

请严格参考仓库根目录 `AGENTS.md`，尤其遵守以下规则：

1. 不要把所有代码一次性改完后才总结。
2. 必须按“可独立提交”的粒度推进。
3. 如果某一组改动超过 800 行，必须继续拆分。
4. 如果某项文档更新只是为了配合某个功能改动，应跟该功能相邻提交，而不是全部堆到最后。
5. `CHANGELOG.md` 只能追加，不能改历史。
6. 不要只给计划，不要只给 TODO，要直接完成改动。
7. 前端改动后必须考虑 iOS `WKWebView`，不能只按浏览器思维写页面。

## 六、UI 实施重点

请优先从下面几个方向推进推荐 UI：

### 1. 首页推荐区

目标：

1. 让用户在首页一眼看到“推荐系统”入口。
2. 让首页推荐卡片具备更清晰的学习导向，而不是泛推荐感。
3. 强化“继续学习 / 相关推荐 / 站外导入”之间的差异。

建议关注：

1. 推荐预览卡片层级
2. 推荐理由短标签
3. 来源标识
4. CTA 文案是否足够明确
5. 统计卡与推荐入口之间是否存在视觉割裂

### 2. 独立推荐页与视频详情内嵌推荐

**视频详情（`/videos/:id`）**：在 **封面与基础信息固定于上方** 的前提下，在其 **下方** 用页签 + 横向分页并列 **「学习处理」** 与 **「相关推荐」**（不要把整页含封面一起滑进分页）。数据源为 `scene=related` 的真实推荐接口（`seed_video_id`、排除种子）；卡片纵向列表、教育向稳重配色，与 `Recommendations.vue` 契约一致（不展示切片化 `summary/reason_text/tags`）。分页面板避免对子层使用 `touch-action: pan-y` 锁死，以便在推荐卡片上横滑仍能切换分页。需在 iOS `WKWebView` 验证：**横滑切页发生在封面区以下**；列表纵向滚动与横向分页不互相抢手势。

目标：

1. 推荐页应成为“推荐学习中枢”。
2. 顶部要有明确的当前场景说明。
3. 中部要能清晰区分站内推荐与外部候选。
4. 下部相关推荐与种子视频关系要表达清楚。

建议关注：

1. Hero 区信息密度
2. 场景切换是否足够清楚（切换后同主题区是否应清空、与主列表是否易区分）
3. 同主题区与主列表是否避免“同一批视频出现两次”的重复感
4. 当前上下文说明是否能防止用户迷失
5. 外部候选区是否明确传达“导入学习”而非“直接打开视频”

### 3. 站外候选卡片

目标：

1. 必须让用户清楚知道这是站外内容。
2. 必须让用户知道点击后会走导入链路。
3. 必须在小屏幕上保持紧凑、可点、可识别。

建议关注：

1. 平台来源徽标或来源 badge
2. 推荐理由文案
3. 标签展示数量
4. 按钮文案统一为学习动作，例如“导入学习”
5. 不要让它看起来像已经进入视频库的本地视频

### 4. 上传页承接

目标：

1. 推荐页跳去上传页时，用户要清楚自己是从推荐导入而来。
2. URL 预填、来源展示、导入意图需要足够明确。

建议关注：

1. 是否自动切到 URL 导入模式
2. 是否展示来源说明
3. 是否减少多余操作步骤

## 七、视觉要求

本轮 UI 不能写成普通后台列表页，也不要写成桌面感过强的卡片堆叠。请坚持移动端学习产品的界面方向：

1. 信息密度适中，不要堆满说明文字。
2. 卡片尺寸、留白、圆角、边界要统一。
3. 一级动作要明显，二级动作要克制。
4. 字体层级要清楚，标题、摘要、标签、来源不能混在一起。
5. 页面应服务“快速决策下一步学习动作”，而不是展示一堆技术字段。
6. 保持现有产品视觉语言的连续性，不要突然换成另一套设计系统。

## 八、验证要求

如果本轮进行了前端 UI 改动，完成后至少要跑：

```bash
cd mobile-frontend
npm run build:ios
cd ..
bash ios-app/sync_ios_web_assets.sh
bash ios-app/validate_ios_build.sh
```

如果本轮只是提示词文档修改，则不需要跑构建，但要明确说明未执行构建。

## 九、可直接复制给编码助手的主提示词

复制下面整段内容给编码助手即可：

```md
你正在 `/Users/yuan/final-work/EduMind` 仓库中继续构建 EduMind 的视频推荐功能，但这一轮必须 **优先进行 UI 页面修改**，而不是优先做推荐后端或算法重构。

必须严格遵守以下项目事实：

1. 本项目是 iOS-only，唯一有效链路是 `mobile-frontend/` + `../edumind-backend/` + `ios-app/`。
2. `mobile-frontend/` 是唯一前端，负责推荐页、首页入口、上传跳转和 iOS `WKWebView` 中的 H5 UI。
3. `../edumind-backend/` 是唯一真实后端，但这一轮默认不优先扩展推荐算法，只在前端 UI 需要时复用现有接口与现有字段。
4. `ios-app/` 是唯一 iOS 容器；任何前端交互改动最终都要考虑 `WKWebView` 真实点击、滚动、跳转和安全区表现。

先理解当前现状：

- 首页和推荐页已经存在基础实现：
  - `mobile-frontend/src/views/Home.vue`
  - `mobile-frontend/src/views/Recommendations.vue`
- 上传页已经能承接 URL 导入：
  - `mobile-frontend/src/views/Upload.vue`
- 推荐接口封装与 mock 已存在：
  - `mobile-frontend/src/api/recommendation.js`
  - `mobile-frontend/src/api/mockGateway.js`
- 视频详情双页（学习处理 + 相关推荐）已实现：
  - `mobile-frontend/src/views/VideoDetail.vue`
  - `mobile-frontend/src/components/videoDetail/VideoDetailRecommendPanel.vue`
  - `mobile-frontend/src/components/videoDetail/VideoDetailRecommendCard.vue`
  - `mobile-frontend/src/services/recommendationPresentation.js`
  - `mobile-frontend/src/services/videoDetailTelemetry.js`

这一轮不要把重心放在推荐算法、数据库设计、爬虫调度或新后端服务上。
请把重心放在“推荐 UI 页面要更完整、更清晰、更适合 iPhone 使用”这件事上。

请优先完成以下目标：

1. 优化首页的推荐系统入口和推荐预览表达
2. 强化独立推荐页的信息层级和场景切换体验
3. 明确区分站内推荐与站外候选
4. 强化“导入学习”动作链路，让用户知道站外项不是直接播放，而是导入到学习系统
5. 让整个推荐体验在 iPhone 屏幕下可点击、可理解、不卡顿、不拥挤

必须遵守这些边界：

1. 不要把推荐逻辑写进 Vue 页面里，前端只做 UI、状态和 API 调用。
2. 不要伪造“已导入视频”；站外项必须明确标识为外部候选。
3. 不要优先改数据库或重做后端推荐逻辑。
4. 不要恢复桌面 Web、Android、旧前端分支。
5. 如需文档更新，只更新与本轮 UI 改动直接相关的内容，并追加写入 `CHANGELOG.md`。

实现时必须严格遵守以下硬约束：

1. 不要把所有代码一次性改完后才总结。
2. 必须按“可独立提交”的粒度推进。
3. 如果某一组改动超过 800 行，必须继续拆分。
4. `CHANGELOG.md` 只能追加，绝不能改历史。
5. 不要只给计划，不要只给 TODO，直接完成改动。

前端 UI 修改重点建议如下：

1. 首页：
   - 强化推荐系统入口
   - 明确推荐预览卡片的来源、推荐理由和下一步动作
2. 推荐页：
   - 优化 Hero 区、场景切换、标签筛选、上下文总览
   - 强化相关推荐与当前种子视频的关系表达
3. 站外候选卡片：
   - 明确平台来源
   - 明确“导入学习”动作
   - 避免看起来像站内已入库视频
4. 上传页承接：
   - 优化从推荐页跳转过来的 URL 预填和来源说明
5. 视频详情（如需继续打磨）：
   - 保持封面区固定、分页仅在页签下方；推荐列表与横滑切页不冲突

如果你修改了前端 UI，完成后至少要执行：

```bash
cd mobile-frontend
npm run build:ios
cd ..
bash ios-app/sync_ios_web_assets.sh
bash ios-app/validate_ios_build.sh
```

每完成一个切片后，请输出：

1. 本切片改了什么
2. 涉及哪些文件
3. 执行了哪些验证
4. 当前还剩什么 UI 问题
5. 下一步准备改哪里

如果用户要求提交 commit，在提交前必须提醒用户检查：

1. 当前分支
2. `git status`
3. `git diff --staged`
4. `git log --oneline -5`
5. 测试/构建/同步状态
6. 是否误包含 secrets 或 machine-local 配置
```

## 十、使用建议

推荐这样使用这份提示词：

1. 先附上本文件。
2. 再附上仓库根目录 `AGENTS.md`。
3. 如果你只想做一个小切片，可以再补一句：
   - “这一轮只改首页推荐入口和推荐卡片，不动推荐页。”
   - “这一轮只改推荐页 Hero、场景切换和站外候选卡片。”
   - “这一轮只打磨推荐页到上传页的导入承接体验。”

## 十一、验收底线

本轮 UI 优化完成后，至少要满足：

1. 推荐功能在移动端上不再只是零散卡片，而是有清晰页面结构。
2. 首页入口、推荐页、上传页导入链路彼此连贯。
3. 站内视频和站外候选在视觉上明确区分。
4. 用户能一眼理解“推荐给我什么、为什么推荐、点下去会发生什么”。
