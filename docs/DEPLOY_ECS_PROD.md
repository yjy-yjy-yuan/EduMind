# EduMind ECS 生产部署指南

> 本文档适用于 Alibaba Cloud ECS（新加坡节点）上 EduMind FastAPI 后端的长期稳定运行部署。
> 目标：通过 systemd 管理进程、Nginx 反向代理、HTTPS 证书，实现生产级可用服务。
> 假设：服务器已安装 Python 3.10+、Nginx、MySQL 8.0。

---

## 目录

- [1. 前置条件](#1-前置条件)
- [2. 服务器环境准备](#2-服务器环境准备)
- [3. 代码部署](#3-代码部署)
- [4. 环境变量配置](#4-环境变量配置)
- [5. systemd 服务安装](#5-systemd-服务安装)
- [6. Nginx 安装与配置](#6-nginx-安装与配置)
- [7. HTTPS 证书申请](#7-https-证书申请)
- [8. 服务启停与日志](#8-服务启停与日志)
- [9. 验收标准](#9-验收标准)
- [10. 回滚步骤](#10-回滚步骤)
- [11. 定时维护](#11-定时维护)

---

## 1. 前置条件

| 项目 | 要求 |
|------|------|
| 服务器 | Alibaba Cloud ECS 新加坡节点，公网 IP: `47.84.228.226` |
| 操作系统 | Alibaba Cloud Linux 3（等价 CentOS/RHEL 8 系）或 Ubuntu 22.04 LTS |
| Python | 3.10+（`python3 --version` 验证） |
| Nginx | 已安装（`nginx -v` 验证） |
| MySQL | 8.0+，数据库 `edumind` 已创建 |
| 域名 | 已将 DNS A 记录指向 ECS 公网 IP |
| 防火墙 | 开放 `80`（HTTP）、`443`（HTTPS）端口 |

---

## 2. 服务器环境准备

```bash
# 2.1 创建部署目录
sudo mkdir -p /var/www/edumind
sudo chown -R $USER:$USER /var/www/edumind

# 2.2 安装 Python 虚拟环境依赖
# Alibaba Cloud Linux / CentOS / RHEL:
sudo dnf install -y python3 python3-pip python3-venv
# Ubuntu / Debian（若使用 Ubuntu 系统则改用以下命令）:
# sudo apt update && sudo apt install -y python3-venv python3-pip

# 2.3 创建虚拟环境（放在 /var/www/edumind/.venv）
cd /var/www/edumind
python3 -m venv .venv

# 2.4 安装 pysqlite3（chromadb sqlite 兼容层）
./.venv/bin/pip install pysqlite3-binary

# 2.5 安装 certbot
# Alibaba Cloud Linux / CentOS / RHEL:
sudo dnf install -y certbot python3-certbot-nginx
# Ubuntu / Debian（若使用 Ubuntu 系统则改用以下命令）:
# sudo apt update && sudo apt install -y certbot python3-certbot-nginx
```

---

## 3. 代码部署

### 方式 A：Git 拉取（推荐，有版本管理）

```bash
cd /var/www/edumind

# 若为首次部署，克隆仓库
git clone https://github.com/yjy-yjy-yuan/EduMind.git .
# 若已有仓库，执行 pull
git pull origin main

# 确认工作目录干净（不包含未提交的密钥）
git status
```

### 方式 B：rsync 从本地同步（内网/快速迭代）

```bash
# 在本地开发机执行（替换 SOURCE_PATH 为实际项目路径）
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
      --exclude='node_modules' --exclude='.git' \
      /Users/yuan/final-work/edumind-backend/ \
      ubuntu@47.84.228.226:/var/www/edumind/
```

### 安装 Python 依赖

```bash
cd /var/www/edumind
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r ../edumind-backend/requirements.txt

# 验证 pysqlite3 可导入
./.venv/bin/python -c "import pysqlite3; print('pysqlite3 ok')"
```

---

## 4. 环境变量配置

```bash
# 4.1 创建生产环境 .env（从 .env.example 复制，.env 位于 ../edumind-backend/ 下）
cp /var/www/edumind-backend/.env.example /var/www/edumind-backend/.env

# 4.2 编辑 .env，替换以下关键配置
sudo nano /var/www/edumind-backend/.env
```

### 必须修改的配置项

```ini
# ── 环境标识 ────────────────────────────────────────────────
APP_ENV=production          # ← 必须设为 production，启用安全响应头

# ── 应用配置 ────────────────────────────────────────────────
DEBUG=false                # ← 必须为 false，禁止 uvicorn reload
HOST=127.0.0.1             # ← Nginx 反向代理时仅监听本地
PORT=2004                  # ← 与 Nginx proxy_pass 一致

# ── 数据库配置 ──────────────────────────────────────────────
# 替换 YOUR_PASSWORD 为 ECS MySQL 实际密码
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/edumind

# ── LLM API 配置 ─────────────────────────────────────────────
# 替换为真实 API Key（从阿里云 DashScope 控制台获取）
OPENAI_API_KEY=sk-your-real-qwen-api-key-here
QWEN_API_KEY=sk-your-real-qwen-api-key-here

# ── CORS 配置 ────────────────────────────────────────────────
# 替换 YOUR_DOMAIN 为实际域名；null 保留给 iOS WKWebView file:// 场景
CORS_ORIGINS=null,https://YOUR_DOMAIN

# ── Whisper 模型路径（ECS 本地路径）────────────────────────
# 需提前上传 whisper_models 目录到 ECS
WHISPER_MODEL_PATH=/var/www/edumind/models/whisper
```

### 占位符安全检查清单

> ⚠️ **严禁**在 `.env` 中保留以下占位符的真实值：
> - `OPENAI_API_KEY`、`QWEN_API_KEY`、`DEEPSEEK_API_KEY` → 必须替换为真实 Key
> - `DATABASE_URL` 中的密码 → 必须替换为实际密码
> - `SECRET_KEY` → 生产环境必须使用随机字符串（`openssl rand -hex 32` 生成）

```bash
# 验证 .env 中无明文密钥
grep -E "(OPENAI_API_KEY|QWEN_API_KEY|DATABASE_URL=.*@)" /var/www/edumind-backend/.env
# 若返回结果为空，说明已全部替换
```

---

## 5. systemd 服务安装

### 5.1 安装服务单元

```bash
# 复制服务文件
sudo cp /var/www/edumind/deploy/edumind-api.service /etc/systemd/system/

# 重载 systemd 守护进程（每次修改 .service 文件后必须执行）
sudo systemctl daemon-reload

# 开机自启
sudo systemctl enable edumind-api

# 立即启动
sudo systemctl start edumind-api
```

### 5.2 验证服务状态

```bash
# 查看服务状态
sudo systemctl status edumind-api

# 期望输出：active (running)，且 PID 存在
# 若为 failed，执行 journalctl -u edumind-api -n 50 查看错误原因
```

---

## 6. Nginx 安装与配置

### 6.1 安装 Nginx

```bash
# Alibaba Cloud Linux / CentOS / RHEL:
sudo dnf install -y nginx
# Ubuntu / Debian（若使用 Ubuntu 系统则改用）：
# sudo apt update && sudo apt install -y nginx

sudo systemctl enable nginx
```

### 6.2 部署 HTTP 配置（先验证域名可达）

```bash
# 6.2.1 创建 certbot 验证目录
sudo mkdir -p /var/www/edumind/certbot
sudo chown -R nginx:nginx /var/www/edumind/certbot

# 6.2.2 复制 HTTP 配置到 /etc/nginx/conf.d/（推荐方式，Alibaba Cloud Linux 默认加载此目录）
sudo cp /var/www/edumind/deploy/nginx-edumind-api-http.conf \
       /etc/nginx/conf.d/edumind-api-http.conf

# 6.2.3 替换占位域名为真实域名
sudo sed -i 's/YOUR_DOMAIN_HERE/你的真实域名/g' \
       /etc/nginx/conf.d/edumind-api-http.conf

# 6.2.4 验证语法并重载
sudo nginx -t
sudo systemctl reload nginx

# 6.2.5 验证 HTTP 反向代理
curl -s http://127.0.0.1:2004/health
curl -s http://你的真实域名/health
# 两个请求均应返回 JSON {"status": "healthy", ...}
```

---

## 7. HTTPS 证书申请

### 7.1 首次申请（HTTP-01 挑战，certbot --nginx 模式）

> **策略说明**：采用 `certbot --nginx` 模式，由 certbot 自动修改 Nginx 配置并注入证书路径。
> 不再单独部署 `nginx-edumind-api-https.conf` 模板文件，certbot 会将现有 HTTP 配置
> 原地升级为 HTTPS 配置（保留 server{} 块，在原文件中注入 SSL 指令）。

```bash
# 7.1.1 确保 HTTP 配置已生效（.well-known 路径可达，certbot HTTP-01 挑战依赖此路径）
curl -s http://你的真实域名/.well-known/acme-challenge/test

# 7.1.2 执行申请（--nginx 模式会直接修改 /etc/nginx/conf.d/edumind-api-http.conf）
# 注意：不要同时指定 --webroot，--nginx 和 --webroot 互斥
sudo certbot --nginx \
  -d 你的真实域名 \
  --redirect \
  --hsts \
  --staple-ocsp \
  --agree-tos \
  -m 你的邮箱@example.com \
  --non-interactive

# certbot --nginx 执行完毕后：
#   - /etc/nginx/conf.d/edumind-api-http.conf 被原地升级为 HTTPS 配置
#   - HTTP→HTTPS 强制重定向自动写入
#   - SSL 证书路径自动写入 ssl_certificate / ssl_certificate_key
# 无需再手动复制 nginx-edumind-api-https.conf

# 参数说明：
#   --nginx           certbot 自动修改 Nginx 配置并注入证书路径（勿与 --webroot 混用）
#   --redirect        自动添加 301 HTTP→HTTPS 重定向
#   --hsts           添加 HSTS 响应头
#   --staple-ocsp    启用 OCSP Stapling
#   --non-interactive 无交互模式（适合脚本/CI）
```

### 7.2 验证证书

```bash
# 查看证书信息
sudo certbot certificates

# 手动测试续期（dry-run 模式，不实际续期）
sudo certbot renew --dry-run
```

### 7.3 自动续期

certbot 安装后通过 systemd timer 自动续期（Alibaba Cloud Linux 方式）：

```bash
# 查看续期定时器
sudo systemctl status certbot-renewal.timer

# 手动触发一次续期测试
sudo certbot renew --dry-run
```

---

## 8. 服务启停与日志

### systemd 核心命令

```bash
# ── 服务控制 ─────────────────────────────────────────────────
sudo systemctl start    edumind-api   # 启动
sudo systemctl stop     edumind-api   # 停止
sudo systemctl restart  edumind-api   # 重启（reload 不被 uvicorn 支持，勿用）
sudo systemctl status   edumind-api   # 查看状态
sudo systemctl enable   edumind-api   # 开机自启
sudo systemctl disable  edumind-api   # 取消开机自启

# ── 日志查看 ─────────────────────────────────────────────────
sudo journalctl -u edumind-api -f                    # 实时跟踪日志（Ctrl+C 退出）
sudo journalctl -u edumind-api -n 100                 # 最近 100 行
sudo journalctl -u edumind-api --since "1 hour ago"   # 最近 1 小时
sudo journalctl -u edumind-api -p err                 # 仅错误级别

# ── 日志归档（防止 journalctl 日志无限增长）────────────────
sudo journalctl --vacuum-time=30d    # 保留最近 30 天日志
sudo journalctl --vacuum-size=500M   # 最多保留 500MB 日志
```

### Nginx 日志与控制

```bash
# ── 日志 ─────────────────────────────────────────────────────
sudo tail -f /var/log/nginx/edumind_api_access.log   # 实时访问日志
sudo tail -f /var/log/nginx/edumind_api_error.log    # 实时错误日志

# ── 配置重载（不中断连接）───────────────────────────────────
sudo nginx -t                                  # 验证配置语法
sudo systemctl reload nginx                    # 重载配置

# ── 强制重启（Nginx 配置变更后）────────────────────────────
sudo systemctl restart nginx
```

### 快速定位问题

```bash
# 1. 检查 systemd 服务是否 running
sudo systemctl is-active edumind-api

# 2. 检查端口是否监听
sudo ss -tlnp | grep 2004

# 3. 检查 Nginx upstream 连通性
curl -s http://127.0.0.1:2004/health

# 4. 检查 Nginx 是否转发正确
curl -sI -H "Host: 你的真实域名" http://127.0.0.1/health

# 5. 完整请求链路测试（外网 HTTPS）
curl -s https://你的真实域名/health
curl -s https://你的真实域名/api/videos
```

---

## 9. 验收标准

> 在服务器上逐条执行以下命令，全部通过即为验收成功。

### 9.1 系统层

- [ ] `sudo systemctl is-active edumind-api` 输出 `active`
- [ ] `sudo systemctl status edumind-api` 显示 `active (running)`，无 `failed`
- [ ] `sudo journalctl -u edumind-api --since "2 minutes ago"` 无 ERROR 日志

### 9.2 后端 API 层（本地）

- [ ] `curl -s http://127.0.0.1:2004/health` 返回 `{"status": "healthy", ...}`
- [ ] `curl -s http://127.0.0.1:2004/` 返回包含 `"Welcome to EduMind API"` 的 JSON
- [ ] `curl -s http://127.0.0.1:2004/docs` 返回 Swagger UI HTML（200）

### 9.3 Nginx 反向代理层（HTTP 过渡期）

- [ ] `curl -s http://你的真实域名/health` 返回与上述相同的健康响应
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://你的真实域名/` 返回 `200`
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://你的真实域名/health` 返回 `200`

### 9.4 HTTPS 层（证书申请完成后）

- [ ] `curl -s https://你的真实域名/health` 返回健康响应（无 SSL 错误）
- [ ] `curl -s -o /dev/null -w "%{http_code}" https://你的真实域名/` 返回 `200`（非 301）
- [ ] `curl -s -I https://你的真实域名/ | grep Strict-Transport-Security` 有值
- [ ] `openssl s_client -connect 你的真实域名:443 -servername 你的真实域名 </dev/null 2>/dev/null | grep "SSL handshake has read"` 有输出

### 9.5 iOS 客户端配置（验收后配置）

> iOS Release/TestFlight 打包时，`VITE_MOBILE_API_BASE_URL` 应指向：

```bash
# 替换为实际域名
VITE_MOBILE_API_BASE_URL=https://你的真实域名
```

iOS `WKWebView` 加载此域名下的前端页面，前端 API 请求发往 `https://你的真实域名/api/...`，由 Nginx 转发至 `http://127.0.0.1:2004`。

### 9.6 压测验证（可选）

```bash
# 使用 Apache Bench 进行简单压测
# Alibaba Cloud Linux / CentOS / RHEL:
sudo dnf install -y httpd-tools
# Ubuntu / Debian:
# sudo apt install -y apache2-utils
ab -n 100 -c 10 https://你的真实域名/health
# 期望：100% 请求成功，无超时错误
```

---

## 10. 回滚步骤

### 场景 A：代码更新后服务异常

```bash
# 10A.1 查看失败原因
sudo journalctl -u edumind-api -n 50

# 10A.2 回滚到上一个 Git 提交
cd /var/www/edumind
git log --oneline -3
git revert HEAD   # 或 git reset --hard HEAD~1

# 10A.3 重启服务
sudo systemctl restart edumind-api

# 10A.4 验证
sudo systemctl status edumind-api
curl -s http://127.0.0.1:2004/health
```

### 场景 B：Nginx 配置错误导致 502

```bash
# 10B.1 立即回滚 Nginx 配置（移除故障配置，切回 HTTP 状态）
sudo rm -f /etc/nginx/conf.d/edumind-api-https.conf
sudo cp /var/www/edumind/deploy/nginx-edumind-api-http.conf \
       /etc/nginx/conf.d/edumind-api-https.conf
sudo sed -i 's/YOUR_DOMAIN_HERE/你的真实域名/g' \
       /etc/nginx/conf.d/edumind-api-https.conf
sudo nginx -t && sudo systemctl reload nginx

# 10B.2 验证回退
curl -s http://你的真实域名/health
```

### 场景 C：证书续期失败

```bash
# 10C.1 手动强制续期
sudo certbot renew --force-renewal

# 10C.2 若 certbot 无法访问（防火墙原因），暂时恢复纯 HTTP 访问
sudo rm -f /etc/nginx/conf.d/edumind-api-https.conf
sudo cp /var/www/edumind/deploy/nginx-edumind-api-http.conf \
       /etc/nginx/conf.d/edumind-api-https.conf
sudo sed -i 's/YOUR_DOMAIN_HERE/你的真实域名/g' \
       /etc/nginx/conf.d/edumind-api-https.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

## 11. 定时维护

### 11.1 代码更新流程

```bash
# 1. 停止服务
sudo systemctl stop edumind-api

# 2. 拉取最新代码
cd /var/www/edumind && git pull origin main

# 3. 更新依赖（如 requirements.txt 有变更）
./.venv/bin/pip install -r ../edumind-backend/requirements.txt

# 4. 重启服务
sudo systemctl start edumind-api

# 5. 验证
sudo systemctl status edumind-api
curl -s http://127.0.0.1:2004/health
```

### 11.2 日志轮转配置

```bash
# 创建 /etc/logrotate.d/edumind-api（已有 systemd journal 则不需要）
sudo nano /etc/logrotate.d/edumind-api
```

```bash
/var/log/nginx/edumind_api_*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 11.3 数据库备份（建议加入 crontab）

```bash
# 每天凌晨 3 点备份，保留 7 天
sudo crontab -e
# 添加：
# 0 3 * * * mysqldump -u root -pYOUR_PASSWORD edumind | gzip > /var/www/edumind/backups/edumind_$(date +\%Y\%m\%d).sql.gz && find /var/www/edumind/backups -name "*.sql.gz" -mtime +7 -delete
```

### 11.4 健康检查自动告警（可选）

```bash
# 使用 systemd watchdog 实现自动重启
# 在 /etc/systemd/system/edumind-api.service [Service] 中添加：
# WatchdogSec=30
# Restart=on-failure
# 则服务 30 秒无心跳时自动重启
```

---

## 文件清单

本部署涉及的所有配置文件均存放在仓库 `deploy/` 目录：

| 文件 | 说明 |
|------|------|
| `deploy/edumind-api.service` | systemd 服务单元 |
| `deploy/nginx-edumind-api-http.conf` | Nginx HTTP 反向代理配置 |
| `deploy/nginx-edumind-api-https.conf` | Nginx HTTPS 反向代理配置 |
| `../edumind-backend/run_prod.py` | 生产启动脚本（pysqlite3 注入） |
| `../edumind-backend/.env` | 生产环境变量（不提交，含真实密钥） |

---

## 附录：本地开发参考

```bash
# 本地开发仍使用 run.py（reload=True）
python run.py

# 生产验证（在本地服务器环境执行）
python run_prod.py
```

生产启动脚本 `run_prod.py` 与开发脚本 `run.py` 的区别：

| 特性 | `run.py`（开发） | `run_prod.py`（生产） |
|------|----------------|---------------------|
| `reload` | `DEBUG` 环境变量控制 | 强制 `False` |
| `pysqlite3` 注入 | 无 | 有 |
| `workers` | 单进程 | 单进程（建议配合 systemd） |
| `log_level` | `debug` 或 `info` | 强制 `info` |
| `proxy_headers` | 无 | `True`（读取 Nginx 头） |
