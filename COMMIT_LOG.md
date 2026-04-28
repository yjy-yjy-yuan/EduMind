# 分支提交日志

> 说明：
> - 参考 `CHANGELOG.md` 的写法整理，但这里按“分支 -> 日期 -> 提交”归档。
> - 起始分支为 `0319-feature/user-system`。
> - 分支创建记录单独写在每个分支标题下，不计入当日提交条目。
> - 如分支中发生 rebase，以当前分支最终保留的提交哈希为准。

## 0319-feature/user-system

- 分支创建：`2026-03-19`
- 创建基线：`0d323e6` `feat(backend): auto-rename local videos after processing (#8)`

### 2026-03-19
- `6867450` `feat(auth): add email-or-phone user authentication`
- `7da15a1` `chore(hooks): add pre-commit and pre-push quality gates`

### 2026-03-20
- `99b3c38` `feat(profile): support username/avatar updates and refine edit interactions`
- `2d91449` `fix(auth): disable silent mock fallback and verify users persistence`

## 0320-feature/offline-transcription

- 分支创建：`2026-03-20`
- 创建基线：`df494b6` `feat(auth): add users-table-backed mobile auth and profile editing(#9)`

### 2026-03-23
- `a3b98dd` `feat(mobile): add offline queue foundation for uploads`
- `8110829` `feat(mobile): queue failed uploads offline and auto-flush on reconnect`
- `4213297` `feat(mobile): enqueue failed uploads offline and auto-flush on reconnect`
- `4e9ca4c` `feat(ios): add native bridge foundation for offline transcription`
- `93ef16c` `feat(ios): add on-device offline transcription flow`
- `e366d6b` `feat(mobile): persist local offline transcripts and add detail view`
- `5eeada4` `fix(ios): normalize native offline transcription locale mapping`
- `346dfdd` `fix(ios): harden offline transcription flow and logging`
- `5284009` `feat(ios): add locale-aware offline transcription tuning`
- `1cacce1` `feat(mobile): generate summaries for local offline transcripts`
- `e05934e` `feat(video): sync ios offline transcripts into videos table`
- `6904560` `feat(video): sync ios offline transcripts into videos table`

## 0324-refactor/ios-architecture

- 分支创建：`2026-03-24`
- 创建基线：`2b29938` `feat(video): sync ios offline transcripts into videos table (#10)`

### 2026-03-24
- `6bcf62d` `feat(scripts): add agent bootstrap scripts`
- `184eaab` `chore(ios): improve web asset sync diagnostics`
- `4eff216` `feat(frontend): expose api base source diagnostics`
- `13d0c13` `feat(webview): add structured container diagnostics`
- `ce4c0c2` `docs(workflow): add blitz edumind workflow guide`
- `81206e0` `docs(readme): add blitz codex cli workflow`
- `eca5c4a` `docs(changelog): append agent automation diagnostics entry`

## 0324-feature/note-system

- 分支创建：`2026-03-24`
- 创建基线：`de0a9b6` `feat(workflow): add agent automation scripts and iOS diagnostics (#11)`
- 分支操作：`2026-03-24` 执行过一次 rebase，`feat(notes): add subtitle-assisted timestamp context` 最终保留为 `9c9478e`

### 2026-03-24
- `0bf24cb` `feat(notes): add note prompt and backend API`
- `d9798b2` `feat(notes): add note list filters`
- `f3a191e` `feat(notes): add note editor timestamps`
- `cb98188` `fix(notes): restore video note recall`
- `6a29d08` `feat(notes): import video summary as note`
- `10a3cff` `fix(ios): remove hardcoded signing from local builds`
- `9c9478e` `feat(notes): add subtitle-assisted timestamp context`

## 0325-feature/video-recommendation

- 分支创建：`2026-03-25`
- 创建基线：`430a4ee` `feat: add video recommendations and streamline iOS learning flow (#13)`

### 2026-03-25
- `7366fdd` `fix(frontend): restore previous mobile page layouts`
- `9b97cf1` `feat(mobile-frontend): add recommendation page`
- `4cdec16` `docs(project): add video recommendation prompt`
- `c733a7a` `feat(mobile-frontend): add home recommendation preview`
- `458ede6` `style(mobile-frontend): refresh home hero`
- `818e0b0` `feat(mobile-frontend): add home learning overview`
- `2d9dd8d` `style(mobile-frontend): polish home recommendation panel`
- `e68382f` `feat(mobile-frontend): add recommendation context surfaces`
- `666a895` `feat(backend-fastapi): add subject-aware recommendation tags`

### 2026-03-26
- `a40c536` `feat(backend-fastapi): add external candidate adapters`
- `98f329f` `feat(backend-fastapi): merge external recommendation candidates`
- `ac68c21` `docs(project): add recommendation ui prompt`
- `8428290` `style(project): refresh morandi branding`
- `2bd538c` `style(mobile-frontend): refresh recommendations page`
- `eab038a` `style(mobile-frontend): refine upload recommendation flow`
- `2b5796e` `style(mobile-frontend): retheme remaining app views`
- `e4212c5` `build(ios-app): refresh web assets`
- `f7d2cc5` `feat(design): add sleek design assistant integration`
- `afd8872` `chore(design): add edumind mobile pen source`

### 2026-03-27
- `0fc6041` `docs(backend-fastapi): clarify test layout`
- `61f0472` `feat(backend-fastapi): expose recommendation source summaries`
- `bb0d000` `feat(backend-fastapi): import external recommendations`
- `6a945a8` `feat(backend-fastapi): resolve mooc recommendation links`
- `e9ae066` `perf(backend-fastapi): cache external recommendation lookups`
- `94f75b5` `refactor(backend-fastapi): share video api helpers`
- `ef6a931` `feat(mobile-frontend): connect recommendation response flows`
- `1996f6e` `feat(mobile-frontend): summarize recommendation metadata on home`

### 2026-03-28
- `c76192b` `style(project): refresh morandi purple branding`
- `089a234` `style(mobile-frontend): refine upload and tab bar chrome`

## 0329-feature/notes-video-enhancemen

- 分支创建：`2026-03-29`
- 创建基线：`fa02f96` `fix(agent): stabilize note metadata`

### 2026-03-30
- `6c4fe40` `fix(note-edit): compact timestamp card layout`
  - 继续收缩单个笔记编辑页，压平重点时间点为轻量单行结构，保留删除笔记卡片。
  - 调整视频详情页，将「开始处理/播放/问答」卡片移动到「Whisper 模型」下方，保持「删除视频」位置不变。

### 2026-03-29
- `3bcee95` `feat(agent): add backend learning flow`
- `1984502` `feat(frontend): add learning flow entry points`
- `428215f` `feat(player): add timestamp note composer`

### 2026-03-30
- `bb7c5f6` `feat(player): simplify auto note titles`
- `cd15a84` `fix(agent): simplify note title fallback`
- `c79f30e` `fix(frontend): ignore abort bootstrap errors`

## 0331-refactor/recommendation-flow

- 分支创建：`2026-03-31`
- 创建基线：`8d4542a` `feat(learning): converge note workflow into player-first timestamp capture (#17)`

### 2026-03-31
- `dae4292` `fix(auth): enforce expiring auth tokens across mobile and ios flows`

### 2026-04-01
- `a007418` `feat(recommendation): harden pipeline and align note-QA learning flow`
- `67bc068` `feat(mobile): refine guide accordion and home layout`

## 0411-feature/video-recommendation-enhancement

- 分支创建：`2026-04-11`
- 创建基线：`ff86a447` `feat(recommendation): harden auth isolation and land agent governance pipeline`

### 2026-04-11
- `3beabfc5` `feat(recommendation): auto-materialize external candidates for logged-in users`

### 2026-04-12
- `54419d52` `feat(recommendation): contract v2, sanitize responses, similarity fusion, hub UX`
- `5827f3c5` `feat(backend): recommendation title filter, delete cascade, purge script`

## 0422-codex/edumind-vinci-integration-operable-maintainable（edumind-backend）

- 分支创建：`2026-04-22`
- 创建基线：`cad1c23` `Initial commit: EduMind Backend FastAPI service`

### 2026-04-22
- `f4b3a9b` `docs: sync backend docs and harden hook pipeline for reliable local/CI checks (#1)`
- `9c20a22` `feat: add vinci adapter baseline and sync m1 docs`
- `04e3546` `feat: enforce vinci governance path and sync m1-3 docs`

### 2026-04-23
- `dabaa5d` `feat: add vinci m1-4 observability metrics and runbook`
- `b3faf6a` `feat: add vinci ops metrics endpoint and alert rule templates`
- `066da7f` `feat(agent): route vinci summary through governance pipeline`
- `e137fba` `fix(agent): enforce governance context in vinci adapter`
- `d2f6076` `test(agent): add vinci whitelist denial api regression`
- `cbf4c41` `test(agent): assert denied audit event for vinci whitelist block`
- `4e4c3c2` `docs(monitoring): align vinci alert templates with runbook thresholds`
- `c48cb0d` `feat(vinci): add circuit breaker and graceful fallback in learning flow`
- `c6e5e3f` `docs: add M3 alerting acceptance evidence and sync vinci docs`
- `daffcca` `feat: add vinci alerting acceptance prep tooling`

### 2026-04-23（待提交）
- `TBD` `feat(m4): align backend/frontend contracts, stream normalization and integration docs`
# 2026-04-28

- `PENDING` `fix(mobile): one-click delete and cross-page immediate removal sync`
  - 删除按钮改为单击即执行，不再展示二次确认弹层。
  - 删除时广播 `VIDEO_DELETED_EVENT_NAME`，首页与视频库实时剔除已删项。
  - 同步 iOS WebAssets，确保真机加载到本次删除链路修正。

- `b7734a1d` `fix(mobile+ios+docs): frame description timeout degrade, instant delete UX, debug api base sync script fix`
  - 移动端实时画面描述新增连接超时快速降级，避免长时间停留 connecting。
  - 删除视频改为前端即时跳转首页并本地过滤已删视频，消除“删除后仍显示”的卡顿感。
  - 修复 `ios-app/sync_ios_web_assets.sh` 对 `__DEBUG_DYNAMIC__` 无引号占位符无法替换的问题，确保 Debug API Base 真实写入。
  - 修正文档中关于 Debug API Base 占位符的过时说明并同步 CHANGELOG。
