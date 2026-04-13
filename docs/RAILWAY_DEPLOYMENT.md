# Railway 部署指南

## 概述

本文档说明如何将 EduMind 后端部署到 Railway 平台，配合 GitHub 实现自动化部署。

**优点：**
- 固定子域名（永久有效，重启不变）
- 海外节点，无需备案
- GitHub 推送自动触发部署
- 免费额度（每月 500 小时）

**限制：**
- 免费版 512MB RAM，视频本地转录（Whisper）会 OOM
- 无持久化存储，上传的视频文件会在容器重启后丢失
- 建议使用「链接导入」方式添加视频（yt-dlp 后端下载）

---

## 前提条件

- GitHub 账户，且 EduMind 仓库已推送
- [Railway 账户](https://railway.app)（推荐用 GitHub 登录）
- 通义千问 API Key（用于 AI 问答）

---

## 步骤一：本地配置检查

确保以下文件已就绪：

```
/Users/yuan/final-work/EduMind/
├── railway.json                    ✅ 已创建
├── backend_fastapi/
│   ├── Dockerfile                   ✅ 已创建
│   └── .env.example                 ✅ 已更新
└── .dockerignore                   ✅ 已创建
```

---

## 步骤二：推送代码到 GitHub

如果还没推送过，执行：

```bash
cd /Users/yuan/final-work/EduMind

# 确认 git 状态
git status

# 添加所有更改
git add .

# 提交
git commit -m "feat: 添加 Railway 部署配置"

# 推送到 GitHub
git push origin main
```

---

## 步骤三：在 Railway 创建项目

1. 访问 [railway.app](https://railway.app)，用 GitHub 登录
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 选择 `yjy-yjy-yuan/EduMind` 仓库
4. Railway 会自动检测 `railway.json`，部署 `backend_fastapi` 子目录

---

## 步骤四：配置环境变量

在 Railway 项目控制台，添加以下环境变量：

### 必需

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `APP_ENV` | `production` | 切换到生产模式 |
| `DEBUG` | `false` | 关闭调试模式 |
| `DATABASE_URL` | （Railway MySQL 插件提供） | MySQL 连接字符串 |
| `OPENAI_API_KEY` | `你的通义千问API Key` | 用于 AI 问答功能 |
| `CORS_ORIGINS` | `null,https://xxxxx.up.railway.app` | **部署后填入实际域名** |

### 可选

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `QWEN_API_KEY` | `你的通义千问API Key` | 同 OPENAI_API_KEY |
| `SEARCH_ENABLED` | `false` | 关闭语义搜索（节省内存） |
| `WHISPER_PRELOAD_ON_STARTUP` | `false` | 关闭 Whisper 预加载 |
| `SECRET_KEY` | `随机字符串` | 生产环境密钥 |

---

## 步骤五：添加 MySQL 插件

1. 在 Railway 项目中，点击 **New** → **Database** → **Add MySQL**
2. Railway 会自动创建 MySQL 实例并配置 `DATABASE_URL`
3. 等待 MySQL 启动完成（通常 1-2 分钟）

---

## 步骤六：获取部署域名

1. 部署完成后，Railway 会在 **Settings** → **Networking** 中显示公网地址
2. 格式：`https://xxxxx.up.railway.app`
3. **这个域名是固定的**，可以永久使用

---

## 步骤七：更新 CORS 配置

1. 回到 Railway 环境变量
2. 将 `CORS_ORIGINS` 更新为实际域名：

```
CORS_ORIGINS=null,https://xxxxx.up.railway.app,https://xxxxx.up.railway.app:8000
```

3. 点击 **Deploy** 重新部署

---

## 步骤八：验证部署

访问健康检查端点：

```
https://xxxxx.up.railway.app/health
```

预期响应：

```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "whisper": "disabled",
    "ollama": "disabled"
  }
}
```

---

## 步骤九：更新前端 API 地址

Railway 部署成功后，更新 `mobile-frontend` 的 API 地址：

```bash
cd /Users/yuan/final-work/EduMind/mobile-frontend

# 设置新的 API 地址
export VITE_MOBILE_API_BASE_URL=https://xxxxx.up.railway.app

# 重新构建 iOS Web 资源
npm run build:ios

# 同步到 iOS 项目
bash ../ios-app/sync_ios_web_assets.sh
```

---

## 视频功能说明

Railway 部署后，**本地视频上传功能受限**（无持久化存储）。

推荐工作流：
1. 用户通过「链接导入」添加 B 站/YouTube 视频
2. 后端使用 `yt-dlp` 下载并处理
3. 字幕由外部平台提供（无需 Whisper 本地转录）

如需完整视频上传功能，建议：
- 升级 Railway 付费版（$5/月起）
- 或使用对象存储（阿里云 OSS / Cloudflare R2）存储视频

---

## 常见问题

### Q: 部署失败怎么办？
A: 查看 Railway 控制台的 **Logs** 标签页，常见原因：
- 依赖安装超时 → 重试
- 内存不足 → 关闭 Whisper/语义搜索

### Q: 如何查看实时日志？
A: Railway 控制台 → **Deployments** → 点击当前部署 → **Logs**

### Q: 如何回滚到旧版本？
A: Railway 控制台 → **Deployments** → 点击历史部署 → **Redeploy**

### Q: 域名会变吗？
A: Railway 分配的子域名是**永久固定**的，只要项目不删除就不会变。

---

## 架构总结

```
┌─────────────────────────────────────────────────────────────┐
│                        Railway                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  EduMind Backend (Docker)                          │   │
│  │  • FastAPI API (端口 8000)                         │   │
│  │  • MySQL (Railway 插件)                            │   │
│  │  • yt-dlp 视频下载                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  公网地址: https://xxxxx.up.railway.app  ← 固定不变        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    iOS App (WKWebView)                      │
│  • mobile-frontend H5 界面                                  │
│  • 连接 Railway 后端                                        │
└─────────────────────────────────────────────────────────────┘
```
