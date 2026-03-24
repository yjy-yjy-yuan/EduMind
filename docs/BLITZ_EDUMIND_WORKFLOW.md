# Blitz / Codex / Claude Code 接管 EduMind 工作流

## 1. 项目真实架构说明

EduMind 当前是 iOS-only 项目，唯一有效链路如下：

1. `backend_fastapi/`
   真实后端能力层。上传、音频提取、Whisper 转录、摘要、问答、数据库写入、视频分析等都必须放在这里。
2. `mobile-frontend/`
   唯一前端 H5。负责 UI、状态、API 调用、`WKWebView` 页面展示，不允许写数据库逻辑或伪后端逻辑。
3. `ios-app/`
   iOS `WKWebView` 容器和原生桥层。负责加载本地打包资源、注入 `window.__edumindNativeConfig.apiBaseUrl`、接管原生日志和原生能力。

必须记住：

1. iOS 容器加载的是本地 `WebAssets/index.html`
2. 不是浏览器 dev server 直连模式
3. 前端改动后如果不重新同步 WebAssets，真机和 Xcode 里看到的仍然是旧页面

## 2. 正确启动顺序

推荐按下面顺序操作：

```bash
bash scripts/blitz_prepare_edumind.sh
bash scripts/blitz_start_backend.sh
bash scripts/blitz_backend_healthcheck.sh
bash scripts/blitz_build_ios.sh
```

说明：

1. `blitz_prepare_edumind.sh`
   检查或创建 `.venv`，安装后端依赖，必要时安装前端依赖，并执行 `bash ios-app/sync_ios_web_assets.sh`
2. `blitz_start_backend.sh`
   激活 `.venv` 并从仓库根目录启动 `backend_fastapi/run.py`
3. `blitz_backend_healthcheck.sh`
   默认检查 `http://127.0.0.1:2004/health`
4. `blitz_build_ios.sh`
   用 `xcodebuild` 构建 `ios-app/EduMindIOS/EduMindIOS.xcodeproj`

如果要做更完整的本地验证，继续执行：

```bash
bash ios-app/validate_ios_build.sh
```

这个脚本默认执行无签名构建，目标是验证当前 iOS 容器和 `WebAssets` 是否可编译，不依赖本机 Apple ID。

## 3. 前端修改后的必做操作

只要改了 `mobile-frontend/`，无论改的是页面、配置还是 bridge 调试代码，都必须执行：

```bash
bash ios-app/sync_ios_web_assets.sh
```

原因：

1. iOS 不走 dev server
2. `WKWebView` 从 App 包里的 `WebAssets/` 读取静态资源
3. 不同步就无法确认真机实际加载的是不是最新构建结果

同步脚本当前会做这些事：

1. 读取 `backend_fastapi/.env` 中的 `PORT`
2. 读取当前机器的 `LocalHostName`
3. 刷新 iOS 原生 `EDUMIND_API_BASE_URL`
4. 构建 `mobile-frontend`
5. 同步 `dist/` 到 `ios-app/EduMindIOS/EduMindIOS/WebAssets/`
6. 强校验 `index.html`、`index.js`、`index.css` 是否都存在

## 4. iOS 容器调试重点

优先看这几类信息：

1. Xcode 控制台中的 `[EduMindWeb]` 日志
2. 原生输出的 `native api base=...`
3. `Probe` 日志和 mount watchdog 输出
4. `ERR_WEB_ASSET_MISSING`、`ERR_WEB_BUILD_LAYOUT`、`ERR_NAVIGATION_FAIL` 等结构化错误码
5. 前端 `console.info` 输出的 API base 和来源

当前原生容器保留并依赖以下能力，不要删：

1. 本地资源加载策略
2. `window.__edumindNativeConfig.apiBaseUrl` 注入
3. console bridge
4. mount watchdog
5. WebView 失败兜底页
6. probe 诊断

当前还新增了页面状态上报入口：

```js
window.__edumindReportPageState({
  route: '/videos/123',
  pageName: 'VideoDetail',
  businessId: '123',
  mounted: true
})
```

即使前端还没有全面接入，上面的接口也已经能被原生接收并打印日志。

## 5. 白屏排查顺序

建议严格按下面顺序排：

1. 先执行 `bash ios-app/sync_ios_web_assets.sh`
2. 确认 `ios-app/EduMindIOS/EduMindIOS/WebAssets/` 下存在 `index.html`、`index.js`、`index.css`
3. 再执行 `bash ios-app/validate_ios_build.sh`
4. 打开 Xcode 控制台，看是否出现结构化错误码
5. 如果是 `ERR_WEB_ASSET_MISSING`
   说明包内缺资源，先检查同步结果和 Xcode 资源拷贝
6. 如果是 `ERR_WEB_BUILD_LAYOUT`
   说明前端可能使用了错误的 web 构建布局，而不是 iOS 需要的稳定 `index.js/index.css`
7. 如果是 `ERR_LEGACY_ASSET_PATH`
   说明 `index.html` 仍然在用绝对路径资源
8. 如果没有错误页但页面空白
   看 mount watchdog、probe、`console.error`、`unhandledrejection`
9. 如果页面能打开但数据全空
   优先排后端连通性，而不是先怀疑前端路由

## 6. 后端连通性排查顺序

建议按下面顺序排查：

1. 启动后端

```bash
bash scripts/blitz_start_backend.sh
```

2. 检查健康状态

```bash
bash scripts/blitz_backend_healthcheck.sh
```

3. 如果失败，再直接看：

```bash
curl http://127.0.0.1:2004/health
```

4. 检查 `backend_fastapi/.env` 中的 `HOST`、`PORT`
5. 检查 iOS 原生注入的 `apiBaseUrl` 是否已经被同步脚本刷新
6. 检查前端日志中的 API base 来源是 `query`、`storage`、`native`、`env` 还是 `empty`
7. 如果前端来源是 `storage`
   说明本地缓存可能覆盖了原生注入值
8. 如果前端来源是 `empty`
   说明前端根本没有拿到可用后端地址

## 7. 给 Codex / Claude / Blitz 的操作建议

1. 先读 `AGENTS.md`、`README.md`、`CHANGELOG.md`、`ios-app/README.md`
2. 不要把 Blitz 当成 App SDK 嵌入最终产品
3. 改动优先放在自动化、诊断、构建链路、可观测性和脚本层
4. 任何前端改动后都重新执行 `bash ios-app/sync_ios_web_assets.sh`
5. 任何 iOS 容器改动后都至少执行 `bash ios-app/validate_ios_build.sh`
6. 不要把数据库逻辑写进 `mobile-frontend/`
7. 不要把真实业务逻辑下沉到 iOS 原生层
8. 不要恢复桌面网页、旧 Flask 或 Android 模块
9. 修改文档时保持与当前 iOS-only 架构一致
10. 若白屏、资源缺失或后端不可达，优先增加明确日志和错误码，而不是先重构架构
