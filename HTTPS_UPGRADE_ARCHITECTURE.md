# EduMind HTTPS 升级架构设计文档

> 状态：待实施
> 作者：架构师 / 技术负责人
> 目标：为 47.84.228.226 补全 HTTPS，闭合安全链路

---

## 一、现状分析

### 1.1 当前链路

```
用户浏览器 / iOS App
  |  HTTP (无 TLS 加密)
  ↓
公网中间人 (MITM 风险)
  |
  ↓
阿里云安全组 → TCP 80 → Nginx (HTTP) → 反向代理 → FastAPI :2004
```

- **数据风险**：Bearer Token、用户内容、视频分析结果全部明文传输
- **认证风险**：攻击者可截获 token 后换域带走
- **依赖上游**：前端已做 token 域校验，但链路本身未加密，上游防护有上限

### 1.2 现状关键数据

| 项目 | 值 |
|------|-----|
| 服务器公网 IP | 47.84.228.226 |
| 服务器系统 | Alibaba Cloud Linux 3（RHEL 系） |
| Nginx 版本 | 1.20.1（已安装） |
| OpenSSL 版本 | 1.1.1k（FIPS，支持 TLS 1.2/1.3） |
| certbot / Let's Encrypt | **未安装** |
| 已有 SSL 证书 | 无 |
| Nginx 当前监听 | 80（HTTP） |
| FastAPI 运行端口 | 2004 |
| 当前 CORS 白名单 | `null, http://localhost:328, http://127.0.0.1:328, http://localhost:5173, http://127.0.0.1:5173`（无公网 HTTPS 源） |
| 服务器 Python 版本 | 3.6.8 |
| 服务器虚拟环境 | `/var/www/edumind/.venv` |
| .env 配置文件 | **不存在**（config.py 全用默认值） |

### 1.3 根本问题

1. **无 SSL 证书**：Let's Encrypt 未安装，无法申请免费证书
2. **Nginx 无 HTTPS 配置**：只有 HTTP 80 端口监听，无 TLS 层
3. **CORS 白名单缺失**：即使加了 HTTPS，后端也不认 `https://47.84.228.226`
4. **前端 API 地址未指定**：`VITE_MOBILE_API_BASE_URL` 为空，依赖 localStorage 动态配置
5. **.env 未配置**：所有密钥为空字符串，API Key 实际从代码默认值无法生效

---

## 二、目标架构

### 2.1 升级后链路

```
用户浏览器 / iOS App
  |  HTTPS + TLS 1.2/1.3
  ↓
阿里云安全组 → TCP 443 → Nginx (TLS 握手) → 反向代理 → FastAPI :2004
                                                ↓
                                          HTTP (内网 loopback)
```

### 2.2 目标组件矩阵

| 层级 | 组件 | 目标状态 |
|------|------|----------|
| 传输层 | TLS | TLS 1.2 + 1.3，禁用 TLS 1.0/1.1、SSLv3 |
| 证书 | Let's Encrypt 免费证书（shortlived） | 有效期约 6 天，自动续期 |
| 反向代理 | Nginx | 443 监听，TLS offload，安全响应头 |
| 应用层 | FastAPI | 仅监听 127.0.0.1:2004（对内） |
| 认证 | Bearer Token | 仍有效，但必须经 TLS 传输 |
| 降级保护 | HTTP→HTTPS 强制跳转 | 307 重定向，HSTS |
| iOS ATS | 强制 HTTPS | ATS 默认已通过 HTTPS 满足 |
| 前端 | API Base URL | 强制使用 https://47.84.228.226 |

---

## 三、安全设计要求

### 3.1 传输层加密

**TLS 版本策略**
- ✅ 启用：TLS 1.2、TLS 1.3
- ❌ 禁用：TLS 1.0、TLS 1.1、SSLv3、SSLv2

**密码套件（Cipher Suites）**
```
TLS_AES_256_GCM_SHA384
TLS_AES_128_GCM_SHA256
TLS_CHACHA20_POLY1305_SHA256
ECDHE-ECDSA-AES128-GCM-SHA256
ECDHE-RSA-AES128-GCM-SHA256
ECDHE-ECDSA-AES256-GCM-SHA384
ECDHE-RSA-AES256-GCM-SHA384
```
- ❌ 禁用：RC4、3DES、MD5、SHA1、出口级密码套件

### 3.2 HTTP 安全响应头（Nginx add_header）

| Header | 值 | 作用 |
|--------|-----|------|
| `Strict-Transport-Security` | `max-age=31536000` | 强制 HTTPS，1 年有效期 |
| `X-Frame-Options` | `SAMEORIGIN` | 防止点击劫持 |
| `X-Content-Type-Options` | `nosniff` | 禁止 MIME 类型嗅探 |
| `X-XSS-Protection` | `1; mode=block` | XSS 过滤器（兼容旧浏览器） |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | 控制 Referer 泄漏 |
| `Content-Security-Policy` | 限制外链脚本加载 | 防止 XSS |
| `Permissions-Policy` | 禁用非必要能力 | 减少攻击面 |

### 3.3 HSTS（HTTP Strict Transport Security）

- `max-age` 至少 1 年（`31536000`）
- 若未来切到域名（非 IP）再考虑 `includeSubDomains`
- 当前以 IP 直连为主，不建议使用 `preload`（HSTS 预加载面向域名场景）

### 3.4 OCSP Stapling

- Let’s Encrypt `shortlived` 证书（IP 证书必用）不依赖 OCSP；不建议强行开启 stapling 校验
- 如后续切换到支持 OCSP 的非短期证书，再评估启用 `ssl_stapling on`

### 3.5 Token 传输策略

| 场景 | 当前（HTTP） | 目标（HTTPS） |
|------|-------------|--------------|
| Bearer Token 传输 | 明文，可被中间人截获 | TLS 加密，截获成本极高 |
| Token 换域带走 | 前端域校验是唯一防线 | TLS + 域名绑定 + SameSite Cookie 多重保护 |
| CSRF 防护 | 仅依赖 CORS 白名单 | HTTPS + SameSite=Lax/Strict + CORS 白名单 |

> 注意：Bearer Token（存在 localStorage）作为 API 认证凭证，本项目继续沿用。最佳实践是改用 HttpOnly SameSite Cookie（后端签发），但这涉及较大改动，建议作为 Phase 2 优化。

### 3.6 证书自动续期

- Let’s Encrypt IP 证书（shortlived）有效期约 6 天
- 使用 `certbot` + `cron` 或 `systemd timer` 实现自动续期
- 续期后自动 `nginx -s reload`

---

## 四、实施步骤（Phase 1 — 核心升级）

### 步骤 1：服务器安装 certbot 并申请证书

```bash
# 安装 snapd（Alibaba Cloud Linux 3）
dnf install -y snapd
systemctl enable --now snapd.socket
ln -sf /var/lib/snapd/snap /snap

# 等待 snapd 就绪
snap wait system seed.loaded

# 安装 certbot
snap install --classic certbot

# 创建符号链接
ln -sf /snap/bin/certbot /usr/bin/certbot

# 版本要求：Certbot 5.4+（IP 证书支持完善）
certbot --version

# 申请证书（IP 证书必须 shortlived；standalone 模式需要临时停 Nginx 释放 80 端口）
systemctl stop nginx
certbot certonly --standalone \
  --preferred-profile shortlived \
  --ip-address 47.84.228.226 \
  --agree-tos \
  --email 你的邮箱@example.com \
  --non-interactive \
  --keep-until-expiring
systemctl start nginx

# 验证证书生成
ls /etc/letsencrypt/live/47.84.228.226/
```

> **注意**：申请前确保安全组已放行 80 与 443（`standalone` 验证使用 80）。

### 步骤 2：配置 Nginx HTTPS + 安全头

创建 `/etc/nginx/conf.d/edumind-api-https.conf`：

```nginx
# ── HTTP → HTTPS 强制跳转 ─────────────────────────────────────────────────
server {
    listen 80 default_server;
    server_name 47.84.228.226;
    return 307 https://$host$request_uri;
    access_log /var/log/nginx/edumind_http_access.log;
    error_log  /var/log/nginx/edumind_http_error.log;
}

# ── HTTPS 主服务 ───────────────────────────────────────────────────────────
server {
    listen 443 ssl http2;
    server_name 47.84.228.226;

    # ── SSL 证书 ──
    ssl_certificate     /etc/letsencrypt/live/47.84.228.226/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/47.84.228.226/privkey.pem;

    # ── TLS 版本与密码套件 ──
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:
                ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:
                ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:
                DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # ── SSL 性能优化 ──
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # ── OCSP Stapling ──
    # Let’s Encrypt shortlived 证书场景下不依赖 OCSP，避免无效 stapling 告警
    ssl_stapling off;
    ssl_stapling_verify off;

    # ── 日志 ──
    access_log /var/log/nginx/edumind_api_access.log;
    error_log  /var/log/nginx/edumind_api_error.log warn;

    # ── 安全响应头 ──
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    # 内容安全策略（根据实际资源域名调整）
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://47.84.228.226 https://dashscope.aliyuncs.com; frame-ancestors 'none';" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    # ── 上传文件大小 ──
    client_max_body_size 5G;

    # ── 反向代理到 FastAPI ──
    location / {
        proxy_pass http://127.0.0.1:2004;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;  # $scheme 此时为 https
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 步骤 3：验证 Nginx 配置并重载

```bash
# 备份原配置
cp /etc/nginx/conf.d/edumind-api-http.conf /etc/nginx/conf.d/edumind-api-http.conf.bak

# 验证语法
nginx -t -c /etc/nginx/nginx.conf

# 重载（如 standalone 模式申请证书时停过 nginx，此处重启即可）
systemctl reload nginx
```

### 步骤 4：更新安全组，开放 TCP 443

阿里云控制台 → ECS → 安全组 → 入方向规则：

| 方向 | 协议 | 端口 | 来源 |
|------|------|------|------|
| 入方向 | TCP | 80/80 | 0.0.0.0/0 |
| 入方向 | TCP | 443/443 | 0.0.0.0/0 |

### 步骤 5：验证 HTTPS 访问

```bash
# 方式一：curl 测试（忽略自签验证，因为 Let's Encrypt 是真实证书，无需 -k）
curl -I https://47.84.228.226/

# 方式二：检查 TLS 版本
curl -I --tlsv1.2 https://47.84.228.226/
curl -I --tlsv1.3 https://47.84.228.226/

# 方式三：在线检测
# 浏览器访问 https://47.84.228.226/docs
# 查看锁标是否显示绿色，TLS 版本是否为 1.3
```

### 步骤 6：更新后端 CORS 白名单

在服务器创建 `/var/www/edumind/backend_fastapi/.env`：

```env
# 基础配置
APP_ENV=production
DEBUG=false
HOST=127.0.0.1
PORT=2004

# 数据库
DATABASE_URL=mysql+pymysql://edumind:你的MySQL密码@127.0.0.1:3306/edumind

# LLM API（通义千问）
QWEN_API_KEY=sk-你的DashScope密钥

# CORS（生产环境公网 HTTPS）
CORS_ORIGINS=null,https://47.84.228.226,http://localhost:328,http://127.0.0.1:328

# 文件存储
BASE_DIR=/var/www/edumind/backend_fastapi
WHISPER_MODEL=base
WHISPER_MODEL_PATH=/var/www/edumind/models/whisper
```

重启 FastAPI 服务使 .env 生效：

```bash
systemctl restart edumind-api
systemctl status edumind-api
```

### 步骤 7：前端构建（VITE_MOBILE_API_BASE_URL 设为 HTTPS）

在 `mobile-frontend/` 根目录执行：

```bash
# 开发构建（供本地 iOS WebView 测试）
VITE_MOBILE_API_BASE_URL=https://47.84.228.226 npm run build:ios

# 或生产构建
VITE_MOBILE_API_BASE_URL=https://47.84.228.226 npm run build
```

同步到 iOS 项目（必须走 Release 通道，避免被 Debug `.local` 覆盖）：

```bash
FIXED_DOMAIN=https://47.84.228.226 bash ios-app/sync_ios_web_assets.sh --release
```

### 步骤 8：iOS 端 EDUMIND_API_BASE_URL 更新

在 Xcode → EduMindIOS → Build Settings 中：

```
INFOPLIST_KEY_EDUMIND_API_BASE_URL = https://47.84.228.226
```

或在 `ContentView.swift` 第 262 行硬编码修改（仅备用）：

```swift
// 修改前
Bundle.main.object(forInfoDictionaryKey: "EDUMIND_API_BASE_URL") as? String

// 建议：确保 Info.plist 或 Build Settings 中 EDUMIND_API_BASE_URL = https://47.84.228.226
```

### 步骤 9：配置证书自动续期（systemd timer）

```bash
cat > /etc/systemd/system/certbot-renewal.service << 'EOF'
[Unit]
Description=Let's Encrypt Certificate Renewal
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --deploy-hook "nginx -s reload"
PrivateTmp=true
EOF

cat > /etc/systemd/system/certbot-renewal.timer << 'EOF'
[Unit]
Description=Let's Encrypt Certificate Renewal Timer
Requires=certbot-renewal.service

[Timer]
OnCalendar=daily
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now certbot-renewal.timer
systemctl list-timers --all | grep certbot
```

### 步骤 10：删除旧的 HTTP 配置（可选但建议）

```bash
# 确认 HTTPS 稳定运行后，可删除旧配置
# mv /etc/nginx/conf.d/edumind-api-http.conf /etc/nginx/conf.d/edumind-api-http.conf.bak
# nginx -s reload
```

---

## 五、安全验收标准

### 5.1 传输层

| 检查项 | 通过标准 |
|--------|----------|
| SSL Labs 评级 | A 或以上（当前无评级→升级后目标 A+） |
| TLS 版本 | 仅 TLS 1.2 + 1.3 |
| 证书有效性 | Let's Encrypt 真实证书，非自签 |
| 证书自动续期 | systemd timer 已激活并运行 |
| HTTP→HTTPS | 307 重定向生效 |
| HSTS 头 | `Strict-Transport-Security: max-age=31536000` 存在于响应头 |

### 5.2 应用层

| 检查项 | 通过标准 |
|--------|----------|
| CORS 白名单 | `https://47.84.228.226` 在后端 CORS_ORIGINS 中 |
| 前端 API 请求 | 发出请求的协议为 https |
| iOS App Transport Security | 默认通过（目标域为 HTTPS） |
| API `/health` | `https://47.84.228.226/health` 返回 200 |
| API `/docs` | `https://47.84.228.226/docs` 可正常访问 |

### 5.3 日志与监控

| 检查项 | 通过标准 |
|--------|----------|
| Nginx 错误日志 | 无 TLS 相关错误 |
| Nginx 访问日志 | 请求协议为 https |
| OCSP Stapling | LE shortlived IP 证书场景不作为强制验收项 |

---

## 六、Phase 2 建议（安全持续加固）

### 6.1 Token 认证升级（高优先级）

**当前方案**（Bearer Token 存 localStorage）：
- ✅ 简单易实现
- ❌ localStorage 可被 XSS 读取（攻击面：前端 JS 注入）

**Phase 2 方案**：改用 HttpOnly SameSite=Lax Cookie
- Cookie 由后端签发，前端 JS 无法读取
- XSS 无法直接获取 token
- 与 HTTPS 配合，双重保护

### 6.2 速率限制（Nginx 层）

```nginx
# 防止暴力破解和 CC 攻击
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
location / {
    limit_req zone=api_limit burst=20 nodelay;
}
```

### 6.3 强制安全头 Content-Security-Policy 微调

上线后根据实际外链资源调整 CSP，去掉 `'unsafe-inline'`（需要 nonce/hash 配合），实现真正的 XSS 防护。

### 6.4 全站 HTTPS + HTTP/2 或 HTTP/3（QUIC）

- HTTP/2 多路复用提升性能
- HTTP/3（QUIC）减少连接建立延迟（需要 Nginx 1.25+ 编译支持）

---

## 七、回滚方案

如升级失败，执行以下步骤恢复 HTTP 服务：

```bash
# 1. 停用 HTTPS 配置
mv /etc/nginx/conf.d/edumind-api-https.conf /etc/nginx/conf.d/edumind-api-https.conf.bak

# 2. 恢复 HTTP 配置
mv /etc/nginx/conf.d/edumind-api-http.conf.bak /etc/nginx/conf.d/edumind-api-http.conf

# 3. 重载 Nginx
nginx -s reload

# 4. 验证 HTTP 恢复
curl http://47.84.228.226/health
```

> 证书文件保留在 `/etc/letsencrypt/`，随时可重新启用 HTTPS。

---

## 八、关键风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Let's Encrypt 申请失败（端口被占用） | 低 | 高 | 申请前确认 80 无其他进程；用 `--standalone` 模式时先停 Nginx |
| certbot 续期失败 | 低 | 中 | systemd timer 每日检查；监控 `certbot-renewal.service` 状态 |
| CORS 配置错误导致 API 请求失败 | 中 | 高 | 先在 `/etc/hosts` 本地测试，或用 `curl -H "Origin: https://47.84.228.226"` 验证 |
| 前端构建后 API 地址硬编码错误 | 中 | 高 | 构建前双重确认 `VITE_MOBILE_API_BASE_URL=https://47.84.228.226` |
| 旧 iOS App 缓存了 HTTP URL | 中 | 低 | iOS App 重新构建即可；iOS ATS 不会阻止 HTTPS 请求 |
