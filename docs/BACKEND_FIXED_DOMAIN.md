# 后端固定域名方案

> 目标：后端使用固定域名（如 `https://api.edumind.com`），前端构建时写入该地址，换 Wi‑Fi、换地点后无需改配置，小程序/App 不因本机 IP 变化而请求失败。

---

## 一、方案概要

| 项目 | 说明 |
|------|------|
| 后端 | 部署到有公网 IP 或内网域名的机器，通过 Nginx/云厂商做反向代理，对外提供固定域名（建议 HTTPS）。 |
| 前端 | 构建时通过环境变量 `VITE_MOBILE_API_BASE_URL` 写入该固定域名，打包进 H5/iOS；运行时不再依赖本机 IP。 |
| 效果 | 用户在任何 Wi‑Fi、任何地点打开 App，请求都发往固定域名，不会因「本机 IP 变了」而失败。 |

---

## 二、前置条件

1. **已有固定域名**  
   - 公网：已备案域名并解析到服务器（如 `api.yourdomain.com`）。  
   - 内网：内网 DNS 或 hosts 可解析的域名（如 `api.edumind.local`）。

2. **后端可被访问**  
   - 公网：服务器开放 80/443，配置 Nginx 反向代理到本机 2004。  
   - 内网：同一内网设备能访问该域名或 IP:2004。

3. **HTTPS（推荐）**  
   - 小程序、部分 WebView 要求生产环境使用 HTTPS；可用 Let's Encrypt 或云厂商证书。

---

## 三、后端配置（固定域名环境）

在 **backend_fastapi** 的 `.env`（或生产环境配置）中：

```bash
# 应用监听所有网卡（若前面有 Nginx 反向代理，可仍用 127.0.0.1:2004）
HOST=0.0.0.0
PORT=2004

# CORS：允许前端来源（固定域名下的 H5 或 App 的 Origin）
# 若 H5 部署在 https://h5.yourdomain.com，则加入 https://h5.yourdomain.com
# 若为 App 内 WebView 且无固定 Origin，可配置 * 或具体包名/ scheme（视后端 CORS 实现而定）
CORS_ORIGINS=https://h5.yourdomain.com,https://yourdomain.com

# 其他不变：DATABASE_URL、UPLOAD_FOLDER 等
```

若使用 **Nginx 反向代理**（域名 → 本机 2004）：

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
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

后端无需改代码，只需通过 `.env` 和 Nginx 暴露在固定域名下。

---

## 四、前端配置（构建时写入固定域名）

在 **mobile-frontend** 中：

1. **生产/固定域名构建**  
   - 新建 `.env.production`（或构建时传入环境变量）：
   ```bash
   VITE_MOBILE_API_BASE_URL=https://api.yourdomain.com
   VITE_MOBILE_UI_ONLY=false
   ```
   - 将 `https://api.yourdomain.com` 替换为你的实际固定域名，**不要带末尾斜杠**。

2. **构建命令**  
   - 复制示例并改为实际域名：`cp .env.production.example .env.production`，编辑将 `https://api.yourdomain.com` 改为实际固定域名。  
   - 本地/内网 H5：`npm run build` 或 `npm run build:web`（会读 `.env.production`）。  
   - iOS 打包：`npm run build:ios` 使用 mode `ios`，会读 `.env.ios`；可将 `.env.production.example` 复制为 `.env.ios` 并改域名后执行 `npm run build:ios`。

3. **与本地开发隔离**  
   - 本地开发仍用 `.env`：`VITE_MOBILE_API_BASE_URL=http://127.0.0.1:2004`，真机联调时可改为本机 IP。  
   - 固定域名只用于「生产/内网正式」构建，不覆盖开发环境。

4. **可选：运行时覆盖**  
   - 当前项目已支持通过「我的 → 开发设置」或 URL 参数 `apiBase`、localStorage `m_api_base_url` 覆盖 API 基地址；若希望生产包不允许改，可在前端逻辑中根据环境判断是否展示开发设置入口。

---

## 五、验收步骤

1. 后端在固定域名下可访问：`curl -I https://api.yourdomain.com/health` 返回 200。  
2. 前端使用该域名构建：构建产物中请求地址为 `https://api.yourdomain.com/api/...`（可搜打包后的 JS 确认）。  
3. 换 Wi‑Fi 或换地点后，在真机/浏览器打开同一 H5 或 App，上传、登录等请求仍发往固定域名并成功。

---

## 六、实施本方案的提示词（给 AI / 执行者）

以下提示词可直接复制使用，用于在项目中落实「后端固定域名」配置：

```
你正在为 EduMind 项目落实「后端使用固定域名」方案，以便换 Wi‑Fi、换地点后小程序/App 不因本机 IP 变化而请求失败。请严格按仓库内 docs/BACKEND_FIXED_DOMAIN.md 执行，并遵守 AGENTS.md、PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md 的规范。

一、要求
1. 后端：不要求你部署服务器或配置 Nginx，只需在 backend_fastapi/.env.example 中增加注释说明：生产/固定域名环境下应设置 HOST、CORS_ORIGINS 为允许前端固定域名来源；若使用 Nginx 反向代理，给出示例片段（可引用 docs/BACKEND_FIXED_DOMAIN.md）。
2. 前端：在 mobile-frontend 中新增 .env.production.example（或等价示例），内容为：
   - VITE_MOBILE_API_BASE_URL=https://api.yourdomain.com（占位，说明替换为实际固定域名）
   - VITE_MOBILE_UI_ONLY=false
   并在 mobile-frontend/README.md 或 docs/BACKEND_FIXED_DOMAIN.md 中补充一句：生产/固定域名构建时使用该文件（或 set VITE_MOBILE_API_BASE_URL）再执行 npm run build / npm run build:ios。
3. 文档：确保 docs/BACKEND_FIXED_DOMAIN.md 中「后端配置」「前端配置」「验收步骤」与上述一致；若有 .env.production.example，在文档中引用。

二、禁止
- 不得修改后端 CORS 或路由逻辑，仅通过配置与文档完成。
- 不得删除现有 .env.example 或开发环境配置。

三、输出
- 列出修改/新增的文件与变更要点。
- 给出「固定域名构建」的完整命令示例（例如：cp .env.production.example .env.production && 将域名改为实际值 && npm run build:ios）。
```

---

## 七、小结

- **固定域名**：后端通过域名（如 `https://api.yourdomain.com`）对外提供服务，前端构建时将该地址写入 `VITE_MOBILE_API_BASE_URL`。  
- **可实行步骤**：后端部署 + Nginx（可选）+ `.env` 的 CORS/HOST；前端 `.env.production` + 构建命令；验收时换网络验证。  
- **提示词**：见上文第六节，复制给 AI 或执行者即可按文档落实配置与示例，无需改业务代码。

---

## 八、MacBook 本地开发的无 IP 方案

如果当前阶段仍然是“MacBook 跑 `backend_fastapi`，iPhone 真机调试”，又不想继续依赖局域网 IP，可分成两档：

1. 同一局域网内稳定：
   - 直接使用 macOS 的 `LocalHostName.local`
   - 例如本机名为 `yuandeMacBook-Pro`，则地址可写为 `http://yuandeMacBook-Pro.local:2004`
   - 后端必须监听 `0.0.0.0`，并允许 `Origin: null`（iOS `WKWebView` 本地资源远程请求通常如此）

2. 跨网络、跨地点完全稳定：
   - 必须使用固定域名或稳定隧道
   - 例如 `https://api.edumind.com`
   - 这是唯一真正意义上“地址完全不变”的方案
