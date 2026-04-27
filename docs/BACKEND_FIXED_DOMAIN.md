# 后端固定域名方案

> 目标：后端使用固定域名（如 `https://api.xxx.com`），前端/iOS 构建时写入该地址，换 Wi‑Fi、换地点后无需改配置，TestFlight 分发包不因本机 IP 变化而请求失败。

---

## 一、方案概要

| 项目 | 说明 |
|------|------|
| 后端 | 部署到有公网 IP 的机器，通过 Nginx/云厂商做反向代理，对外提供固定域名（建议 HTTPS）。 |
| 前端 | 构建时通过环境变量 `VITE_MOBILE_API_BASE_URL` 写入固定域名，打包进 H5/iOS；运行时不再依赖本机 IP。 |
| iOS | `project.pbxproj` Release 配置中硬编码固定域名；Debug 配置由脚本动态注入本机 `.local` 地址；两者完全隔离。 |
| 效果 | 用户在任何 Wi‑Fi、任何地点打开 App，请求都发往固定域名，不会因「本机 IP 变了」或「换了 Wi‑Fi」而失败。 |

---

## 二、前置条件

1. **已有固定域名（公网可用）**
   - 公网：已备案域名并解析到服务器（如 `api.xxx.com`）。
   - HTTPS 证书：可用 Let's Encrypt 或云厂商证书。

2. **后端可被公网访问**
   - 服务器开放 80/443，配置 Nginx 反向代理到本机 2004。
   - `/health` 端点必须返回 200（发布前核验）。

3. **iOS App Transport Security**
   - Release 构建必须使用 HTTPS；HTTP 会在 App Store 审核时被拒绝。
   - 当前 iOS 工程已开启 `NSAllowsArbitraryLoadsInWebContent = YES`（仅 WebView 内），但固定域名仍建议使用 HTTPS。

---

## 三、双通道配置设计

### 通道说明

| 通道 | 用途 | API 地址来源 | 触发条件 |
|------|------|------------|---------|
| Debug | 本地开发联调 | `bash ios-app/sync_ios_web_assets.sh`（默认） | 脚本不带 `--release` |
| Release / TestFlight | App Store / TestFlight 分发 | `project.pbxproj` Release 配置（已硬编码固定域名） | 脚本带 `--release` |

### iOS project.pbxproj 配置现状

```
Debug 配置（UUID: 1C23BC312F62C3DC00D572F8）:
  INFOPLIST_KEY_EDUMIND_API_BASE_URL = "__DEBUG_DYNAMIC__"
  （由 sync_ios_web_assets.sh 动态注入当前机器 LocalHostName）

Release 配置（UUID: 1C23BC322F62C3DC00D572F8）:
  INFOPLIST_KEY_EDUMIND_API_BASE_URL = "https://api.xxx.com"
  （占位值，Release 模式由脚本真正写入，详见下方脚本行为说明）
```

### 安全保护机制

Release 构建时若检测到 `.local` / `127.0.0.1` / 私网 IP，脚本会报错退出：

```bash
# 示例：禁止在 Release 中使用 .local
FIXED_DOMAIN=http://my-mac.local bash ios-app/sync_ios_web_assets.sh --release
# 输出: [ios:sync][error] Release 模式检测到非固定域名地址: http://my-mac.local
#       禁止在 TestFlight/Release 中使用 .local、127.0.0.1 或私网 IP。
```

---

## 四、后端配置（固定域名环境）

在 **`../edumind-backend`** 的 `.env`（生产环境配置）中：

```bash
# 应用监听所有网卡（若前面有 Nginx 反向代理，可仍用 127.0.0.1:2004）
HOST=0.0.0.0
PORT=2004

# CORS：允许前端来源（固定域名下的 H5 或 App 的 Origin）
# 关键：必须包含 "null"（支持 iOS WKWebView 本地 file:// 资源加载时的远程请求）
# 固定域名部署时改为实际前端来源：
CORS_ORIGINS=null,https://api.xxx.com
```

### Nginx 反向代理配置示例

```nginx
server {
    listen 443 ssl;
    server_name api.xxx.com;
    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:2004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 500M;
    }
}
```

### 后端健康检查

固定域名部署后，通过以下方式核验后端可用性：

```bash
# 直接检查后端
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:2004/health

# 通过域名检查（需等待 Nginx 配置生效）
curl -s -o /dev/null -w "%{http_code}" https://api.xxx.com/health
```

---

## 五、前端构建配置

### 文件说明

| 文件 | 用途 | 构建命令 |
|------|------|---------|
| `.env` | 本地开发（默认 `127.0.0.1:2004`） | `npm run dev` |
| `.env.ios` | iOS 打包（固定域名） | `npm run build:ios`（自动读取 `--mode ios`） |
| `.env.production` | Web 生产部署（固定域名） | `npm run build` |

### iOS 打包命令（固定域名）

```bash
# 1. 准备 iOS 环境文件（一次性）
cp mobile-frontend/.env.ios.example mobile-frontend/.env.ios
# 编辑 .env.ios，将 https://api.xxx.com 替换为实际固定域名

# 2. 同步 WebAssets 并打包（Release 模式）
FIXED_DOMAIN=https://api.xxx.com bash ios-app/sync_ios_web_assets.sh --release

# 或分步执行：
cd mobile-frontend && cp .env.ios.example .env.ios && npm run build:ios
```

### 本地 Debug 开发（不破坏）

```bash
# Debug 模式：脚本自动注入本机 LocalHostName
bash ios-app/sync_ios_web_assets.sh
# 输出示例: [ios:sync]【Debug 模式】iOS native API base URL: http://yuandeMacBook-Pro.local:2004
```

---

## 六、iOS ContentView.swift 安全改进

`ContentView.swift` 中原有的硬编码 fallback 地址（`http://yuandeMacBook-Pro.local:2004`）已移除，改为：

- 若 `EDUMIND_API_BASE_URL` 未配置，输出 **error 日志**，告知开发者检查 Xcode Build Settings
- 不再静默 fallback 到开发机地址，避免 TestFlight 包请求错误机器

---

## 七、验收步骤

### 后端验收

```bash
# 1. 后端本地健康检查
curl -s http://127.0.0.1:2004/health
# 预期: {"status":"ok"}

# 2. 后端日志中确认 CORS 来源（不含敏感信息）
# 启动后端，日志中应有:
# CORS 允许来源（已过滤敏感项）: ['null', 'https://api.xxx.com']
```

### 前端构建验收

```bash
# 3. 验证构建产物中的 API 地址
cd mobile-frontend
# 使用固定域名构建
cp .env.ios.example .env.ios
# 编辑 .env.ios，替换域名为实际值
npm run build:ios

# 4. 确认构建产物包含固定域名（grep 验证）
grep -r "api.xxx.com" dist/
# 预期: index.js 中包含 "https://api.xxx.com"
```

### iOS TestFlight 验收

```bash
# 5. iOS Release 同步 + 验证
# validate_ios_build.sh --release 会：调用 sync --release + xcodebuild Release
FIXED_DOMAIN=https://api.xxx.com bash ios-app/validate_ios_build.sh --release

# 6. 在 Xcode 中创建 Release 构建并上传 TestFlight
# 上传后，在 TestFlight App 中：
# - 打开 App，检查网络请求是否发送到 https://api.xxx.com
# - 登录、首页加载等基础功能是否正常
```

---

## 八、一键命令汇总

### 发布前完整流程

```bash
# Step 1: 后端健康检查
curl -s http://127.0.0.1:2004/health

# Step 2: 后端 CORS 确认（日志）
# 启动后端: python ../edumind-backend/run.py
# 检查日志中 "CORS 允许来源" 行

# Step 3: 前端固定域名构建（使用 .env.ios）
cd mobile-frontend
cp .env.ios.example .env.ios
# 手动编辑 .env.ios 中的 VITE_MOBILE_API_BASE_URL

# Step 4: iOS Release 同步 + 验证
# validate_ios_build.sh --release 会：
#   a. 调用 sync_ios_web_assets.sh --release（真正写入 Release UUID）
#   b. 执行 xcodebuild -configuration Release
#   c. 若 FIXED_DOMAIN 含占位符域名，自动失败
FIXED_DOMAIN=https://api.xxx.com bash ios-app/validate_ios_build.sh --release

# Step 5: Xcode 中执行签名构建并上传 TestFlight
```

### 回滚命令

```bash
# 回滚到 Debug 本地开发模式
bash ios-app/sync_ios_web_assets.sh
# project.pbxproj Debug 配置恢复为 __DEBUG_DYNAMIC__，脚本下次运行注入本机 LocalHostName

# 回滚前端到本地开发版本
cd mobile-frontend
cp .env.example .env  # 恢复默认 127.0.0.1:2004
npm run build:ios
```

---

## 九、故障排查

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| TestFlight 包请求失败 | `project.pbxproj` Release 配置仍为 `.local` | 确认 Release 配置为 `https://api.xxx.com`，执行 `--release` 模式 |
| CORS 报错 | 后端 CORS_ORIGINS 未包含前端域名 | 检查 `../edumind-backend/.env` 中 `CORS_ORIGINS` 是否包含 `null` 和前端固定域名 |
| H5 404 | 后端未启动或域名解析失败 | 确认后端在 `https://api.xxx.com` 可访问 |
| iOS 无法构建 | Swift 编译错误 | 检查 ContentView.swift 中是否仍有 `yuandeMacBook-Pro` 硬编码 |
| 脚本报错 "Release 模式检测到非固定域名" | FIXED_DOMAIN 使用了 `.local` | 确保 FIXED_DOMAIN 使用公网固定域名 |

---

## 十、回滚策略

### 层面 1：前端包层面

- 前端 `dist/` 产物已嵌入 API 地址
- 回滚：恢复上一个可用版本的 `.env.ios`，重新 `npm run build:ios`

### 层面 2：iOS 配置层面

- `project.pbxproj` Release 配置为固定域名
- 回滚：使用 `git checkout` 恢复 pbxproj 到上一个版本，或手动将 Release 配置改回 `https://api.xxx.com`

### 层面 3：后端配置层面

- `../edumind-backend/.env` 中的 `CORS_ORIGINS`
- 回滚：恢复 `.env` 到上一个版本，或重新设置 `CORS_ORIGINS`

### 回滚触发条件

| 条件 | 操作 |
|------|------|
| `/health` 返回非 200 | 立即回滚后端配置或重启服务 |
| TestFlight 用户报告"请求失败" | 确认 pbxproj Release 配置，必要时切换到备用域名 |
| CORS 报错大量出现 | 检查并修正 `CORS_ORIGINS` |

---

## 十一、相关文档

- `mobile-frontend/README.md` — 前端环境变量说明与构建命令
- `ios-app/README.md` — iOS 容器配置与一键同步脚本说明
- `docs/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md` — 移动端实现规范
- `CHANGELOG.md` — 本次固定域名方案变更记录
