# EduMind Note System Implementation Prompt

> 用途：给 Codex、Claude、Blitz 等编码助手直接使用，用于在当前 EduMind 仓库中推进笔记系统建设。
> 适用仓库：`/Users/yuan/final-work/EduMind`
> 当前产品边界：iOS-only，唯一有效链路为 `mobile-frontend/` + `backend_fastapi/` + `ios-app/`

## 一、当前项目现状

你面对的不是一个空白项目，而是一个已经收敛为 iOS-only 的移动学习系统：

1. `mobile-frontend/` 是唯一前端，负责 `WKWebView` 中的 H5 UI。
2. `backend_fastapi/` 是唯一真实后端，负责 MySQL、业务逻辑、视频处理、字幕、摘要、问答和笔记能力。
3. `ios-app/` 是唯一 iOS 容器，负责 `WKWebView`、原生桥接、本地资源加载与真机验证。

必须严格遵守以下边界：

1. 前端只能做 UI、状态和 API 调用，不能把数据库逻辑、NLP、摘要、关键词提取或“假装真实处理”的逻辑写在页面里。
2. 笔记系统默认基于现有 MySQL 表实现，优先复用 `notes`、`note_timestamps`、`videos`、`subtitles`、`questions`。
3. 不要轻易新增平行表；如确实需要扩展，优先扩展现有表，并同步更新 SQL、测试、README、主提示词文档和 `CHANGELOG.md`。
4. 产品目标是 iOS App，不是桌面网站；任何前端交互改动最终都要在 `WKWebView` 中验证。

## 二、当前笔记系统基础

仓库中已经存在以下笔记相关实现，请先在此基础上扩展，而不是推倒重来：

### 后端现状

- `backend_fastapi/app/models/note.py`
  - 已有 `Note` 模型，字段包括 `title`、`content`、`content_vector`、`note_type`、`video_id`、`tags`、`keywords`、时间字段。
  - 已有 `NoteTimestamp` 模型，支持 `note_id`、`time_seconds`、`subtitle_text`。
- `backend_fastapi/app/schemas/note.py`
  - 已有创建、更新、响应和时间戳相关 schema。
- `backend_fastapi/app/routers/note.py`
  - 已有笔记列表、详情、创建、更新、删除。
  - 已有时间戳新增/删除。
  - 已有标签汇总、相似笔记、批量删除、批量导出、单条导出、标签同步。

### 数据库现状

- `backend_fastapi/scripts/mysql_managed_schema.sql`
  - 已明确管理 `notes` 和 `note_timestamps`。
  - 当前 `notes` 通过 `video_id` 与 `videos` 关联。

### 前端现状

- `mobile-frontend/src/api/note.js`
  - 已接入 `getNotes / getNote / createNote / updateNote / deleteNote`。
- `mobile-frontend/src/views/Notes.vue`
  - 当前只有基础列表、刷新和新建入口。
- `mobile-frontend/src/views/NoteEdit.vue`
  - 当前只有标题和内容编辑，暂未体现视频上下文、标签、时间戳等学习型能力。
- 路由已存在：
  - `/notes`
  - `/notes/new`
  - `/notes/:id`

## 三、当前缺口

虽然仓库里已经有基础 CRUD，但它还不是一个真正可用的学习笔记系统。当前主要缺口包括：

1. 笔记创建入口仍然孤立，没有很好接入视频详情、播放器、问答等学习流。
2. 前端编辑页没有管理 `video_id`、标签、时间戳、引用字幕等上下文。
3. 列表页没有把视频关联、标签筛选、搜索、时间点信息展示出来。
4. 后端已有部分能力（时间戳、导出、标签、相似笔记），但前端没有把这些能力真正接起来。
5. 当前体验更像“普通记事本”，而不是“围绕视频学习过程的笔记系统”。

## 四、推荐本轮目标

如果你要正式开始建设笔记系统，默认优先实现“第一版真实可用闭环”，而不是一次性做成很重的知识管理平台。

本轮目标建议是：

1. 让用户可以在普通笔记页和视频学习上下文中都能创建笔记。
2. 让笔记能够稳定关联 `video_id`，并支持一个或多个时间点。
3. 让笔记列表可以按视频、标签、关键词、更新时间查看和筛选。
4. 让笔记详情/编辑页展示并管理时间戳、标签和视频关联信息。
5. 优先复用现有后端接口与表结构，把“已有但未打通”的能力真正落到 UI。
6. 保持 iOS `WKWebView` 可点按、可滚动、可跳转，不做只适合桌面浏览器的交互。

本轮默认不优先做：

1. 全新知识图谱体系
2. 多人协作编辑
3. 独立搜索引擎或向量数据库
4. 脱离现有表结构的大规模重构

## 五、可直接复制给编码助手的主提示词

复制下面整段内容给编码助手即可：

```md
你正在 `/Users/yuan/final-work/EduMind` 仓库中继续构建 EduMind 的笔记系统。请直接在代码库里实施，不要只停留在方案描述。

必须严格遵守以下项目事实：

1. 本项目已经收敛为 iOS-only，唯一有效链路是 `mobile-frontend/` + `backend_fastapi/` + `ios-app/`。
2. `mobile-frontend/` 只负责 UI、路由、状态和 API 调用，不能在页面里实现数据库逻辑、关键词提取、向量计算、摘要推理或伪造“真实笔记处理”。
3. `backend_fastapi/` 是唯一真实业务层；笔记的持久化、关键词、时间戳写入、筛选、导出、相似笔记等真实逻辑必须继续落在后端。
4. 数据库必须继续使用 MySQL，并优先复用现有表：`notes`、`note_timestamps`、`videos`、`subtitles`、`questions`。不要轻易新增平行表。
5. 任何前端交互改动完成后，都要考虑 iOS `WKWebView` 的可点击、可滚动、可跳转和安全区适配；不能只按桌面浏览器验证。

先理解当前现状：

- 后端已有笔记模型和路由：
  - `backend_fastapi/app/models/note.py`
  - `backend_fastapi/app/schemas/note.py`
  - `backend_fastapi/app/routers/note.py`
- 当前后端已支持：
  - 笔记 CRUD
  - 时间戳新增/删除
  - 标签汇总
  - 相似笔记
  - 批量删除
  - 批量导出
  - 单条导出
- 前端当前只接了基础 CRUD：
  - `mobile-frontend/src/api/note.js`
  - `mobile-frontend/src/views/Notes.vue`
  - `mobile-frontend/src/views/NoteEdit.vue`
- 当前路由为：
  - `/notes`
  - `/notes/new`
  - `/notes/:id`

当前问题不是“没有笔记模块”，而是“笔记模块还停留在基础 CRUD，尚未形成真实学习闭环”。

请在现有实现基础上，把笔记系统推进到“第一版真实可用”的状态。默认优先级如下：

1. 强化笔记与视频学习链路的关联：
   - 支持从普通笔记页创建笔记
   - 支持从视频相关上下文进入笔记创建/编辑
   - 笔记应可稳定关联 `video_id`
2. 落实时间点笔记能力：
   - 笔记可挂接一个或多个时间戳
   - 时间戳在前端可见、可新增、可删除
   - 如有视频上下文，尽量带上对应字幕片段或引用文本
3. 提升笔记页的真实可用性：
   - 支持列表展示视频关联、标签、更新时间、时间点摘要
   - 支持搜索、筛选或至少为这些能力打通接口与 UI
   - 不要只保留“标题 + 内容”的最简页面
4. 优先复用现有后端能力：
   - 若已有接口能支撑，就不要新造重复接口
   - 若接口返回结构或校验不足，可在保持兼容的前提下补强
5. 与现有学习流协同：
   - 如改动视频详情、播放器或问答页，请让“记笔记”入口把上下文传到笔记页
   - 不要只做独立的笔记岛

实现时必须遵守这些约束：

1. 不要恢复桌面 Web、旧 Flask、Android 或知识图谱旧分支。
2. 不要把 mock 逻辑包装成真实能力；如果某路径暂时还是占位态，必须明确标识。
3. 不要随意改表；如确实需要改动 schema，必须优先考虑扩展现有 `notes` 或 `note_timestamps`，并同步更新：
   - `backend_fastapi/scripts/mysql_managed_schema.sql`
   - 后端测试
   - `README.md`
   - `PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`
   - `CHANGELOG.md`
4. 新增后端能力必须补测试，至少覆盖 API 主路径和关键失败路径。
5. 前端改动完成后，至少要跑：
   - `npm run build:ios`
   - `bash ios-app/sync_ios_web_assets.sh`
   - 如涉及 iOS 容器或桥接，补 `bash ios-app/validate_ios_build.sh`

请按以下方式推进：

1. 先审查现有笔记链路与缺口。
2. 再直接落代码，不要只给建议。
3. 优先交付最小但真实可用的版本，而不是一次性铺开很多远期能力。
4. 若出现多个实现路径，优先选择最符合现有架构、对现有表结构侵入最小的方案。

完成后请输出：

1. 本次实际修改了什么
2. 涉及哪些文件
3. 运行了哪些测试/构建/同步命令
4. 还有哪些剩余风险或下一步建议
```

## 六、使用建议

如果你准备把这份提示词交给编码助手，推荐这样使用：

1. 先附上本文件。
2. 再附上 `AGENTS.md`。
3. 如果你只想推进某一个子任务，再补一句明确范围，例如：
   - “这一轮只做前后端真实打通，不做视觉重构。”
   - “这一轮重点是视频详情页进入笔记创建，并支持时间戳。”
   - “这一轮先不改表，只在现有 schema 上完成可用版。”

## 七、验收底线

笔记系统这一轮完成后，至少应满足以下底线：

1. 不是只有静态 UI，而是接入真实后端。
2. 不是只有孤立文本框，而是能体现学习上下文。
3. 不是只能在 `/notes` 页面自说自话，而是能进入主学习链路。
4. 不是只在浏览器里看起来正常，而是在 iOS `WKWebView` 中也可正常使用。
