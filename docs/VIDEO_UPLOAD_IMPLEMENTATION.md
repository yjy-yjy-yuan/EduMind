# 视频上传功能实现方案

> 基于当前仓库通盘梳理，供「马上实现上传视频功能」时使用。  
> 涉及：`backend_fastapi/`、`mobile-frontend/`、`ios-app/`。  
> **连调逻辑**：真机 = 前端（H5/WebView），功能在后端（FastAPI 端口 2004），前后端通过 API 基地址（端口）连调；详见仓库根目录 `PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md` 第二节。

---

## 一、上传后视频去哪了？（磁盘 + 数据库）

通过接口 `POST /api/videos/upload` 或 `POST /api/videos/upload-url` 上传时，后端会同时做两件事：

1. **落盘**：把视频文件保存到 `UPLOAD_FOLDER` 目录下（见下文路径说明）。
2. **入库**：在数据库表 `videos` 中插入一条记录，包含 `filename`、`filepath`、`title`、`status`、`md5`、`upload_time` 等；列表、详情、播放、处理任务都依赖这条记录。

因此：**按提示词文档完成联调后，你上传的视频既会在磁盘里，也会在数据库里。** 提示词只负责让请求正确到达后端，不改变“既存文件又写库”的既有逻辑。

---

## 二、已上传视频放在哪里？（磁盘路径）

### 1. 后端实际落盘路径（你「已经上传」的视频应在此）

- **默认根目录**：`backend_fastapi/uploads/`  
  - 即配置里 `UPLOAD_FOLDER` 未设置时，由 `config.py` 计算为 `os.path.join(BASE_DIR, "uploads")`，`BASE_DIR` 为 `backend_fastapi` 目录。
- **单个视频文件**：直接放在该目录下，例如：
  - `backend_fastapi/uploads/local-我的视频.mp4`
  - `backend_fastapi/uploads/bilibili-某课程.mp4`
- **相关子目录**（由后端自动创建和使用）：
  - `backend_fastapi/uploads/subtitles/` — 字幕文件
  - `backend_fastapi/uploads/cache/` — 字幕/处理缓存
  - `backend_fastapi/uploads/audio_temp/` — 语音识别临时音频
  - `backend_fastapi/uploads/previews/` — 视频预览图（部分逻辑在 `video_processing` 里用此路径）
- **预览图**（若单独配置）：`backend_fastapi/previews/`（由 `PREVIEW_FOLDER` 默认）

**若你已有现成视频文件想被系统识别**：

1. 把视频文件放到 `backend_fastapi/uploads/` 下（文件名需符合后端允许的扩展名：mp4, avi, mov, mkv, webm, flv）。
2. 在数据库 `videos` 表中插入一条记录，字段至少包括：`filename`、`filepath`（指向该文件的绝对路径或与 `UPLOAD_FOLDER` 一致的相对路径）、`title`、`status='uploaded'` 等（参考 `app/models/video.py`）。
3. 或在后端提供「扫描 uploads 目录并导入」的脚本/接口（当前需自行按需实现）。

**自定义上传根目录**：在 `backend_fastapi/.env` 中设置：

```bash
# 可选：指定上传根目录（绝对路径或相对 backend_fastapi 的路径）
UPLOAD_FOLDER=/your/custom/uploads
```

不设置则一律使用 `backend_fastapi/uploads/`。

---

## 三、当前实现状态概览

| 层级 | 状态 | 说明 |
|------|------|------|
| 后端 FastAPI | 已实现 | `POST /api/videos/upload`（本地文件）、`POST /api/videos/upload-url`（链接），文件落盘到 `UPLOAD_FOLDER`，MD5 去重，DB 记录；流式播放 `GET /api/videos/{id}/stream`。 |
| 移动端 H5 | 已实现 | `Upload.vue`：本地选择 `video/*`、FormData 上传、链接提交；`api/video.js` 中 `uploadLocalVideo` / `uploadVideoUrl`，非 UI_ONLY 时调后端。 |
| iOS 容器 | 已支持 | WKWebView 加载 H5，H5 内 `<input type="file" accept="video/*">` 由系统提供选择器；无需额外原生上传模块即可用。 |
| 配置/联调 | 需核对 | 移动端需关闭 UI_ONLY 并配置正确 API 基地址，后端需 CORS、`.env` 中上传目录等。 |

---

## 四、推荐实现步骤（联调真实上传）

### 1. 后端准备

- 在 `backend_fastapi` 下执行：
  - `cp .env.example .env`（若无 `.env`）
  - 配置 `.env`：`DATABASE_URL`、可选 `UPLOAD_FOLDER`（不设则用 `backend_fastapi/uploads/`）。
- 启动服务：
  - `conda activate edumind`（或项目约定环境）
  - `python run.py` 或 `uvicorn app.main:app --reload --port 2004`
- 确认启动日志中有「上传目录已就绪: …」，确认该目录存在且可写。
- 如需从本机或局域网访问，确保 `HOST=0.0.0.0`，并在 `CORS_ORIGINS` 中加入移动端 Origin，例如 `http://192.168.1.10:5173`（将 `192.168.1.10` 改为你 Mac 的局域网 IP：终端执行 `ipconfig getifaddr en0` 可得）。

### 2. 移动端 H5 配置（关闭 UI 仅展示、指向后端）

- 在 `mobile-frontend` 的 `.env`（或构建时环境变量）中：
  - `VITE_MOBILE_UI_ONLY=false`（关闭纯 UI 模式，走真实接口）。
  - `VITE_MOBILE_API_BASE_URL=http://<后端地址>:2004`  
    本机浏览器：`http://127.0.0.1:2004`；真机连调：`http://<Mac的局域网IP>:2004`（Mac 终端执行 `ipconfig getifaddr en0` 得到 IP，例如 `http://192.168.1.10:2004`）。
- 重新构建或启动 dev：`npm run dev` / `npm run build:ios` 等，确保请求会发到上述基地址。

### 3. 上传流程核对（无需改代码即可联调）

- **本地文件上传**：
  - `Upload.vue` 中 `uploadFile` 使用 `FormData`，字段名为 `file`，与后端 `upload_video(file: UploadFile = File(...))` 一致。
  - 请求 URL：`POST {API_BASE_URL}/api/videos/upload`，由 `api/video.js` 的 `uploadLocalVideo` 在非 UI_ONLY 时发出。
- **链接上传**：
  - `uploadVideoUrl({ url })` → `POST {API_BASE_URL}/api/videos/upload-url`，后端使用 yt-dlp 下载到 `UPLOAD_FOLDER`。
- 上传成功后，后端返回 `id`、`status`、`data` 等，前端会跳转到视频详情并可按需触发「开始处理」。

### 4. iOS 真机 / WebView 注意点

- 若 H5 在 WebView 中打开，`<input type="file" accept="video/*">` 会调起系统相册/文件选择，选中的文件会由前端通过 FormData 发给当前配置的 `API_BASE_URL`。
- 真机要能访问后端：`VITE_MOBILE_API_BASE_URL` 改为 Mac 的局域网地址（如 `http://192.168.1.10:2004`，IP 在 Mac 上执行 `ipconfig getifaddr en0` 获取），手机与电脑同一 Wi‑Fi；后端 `HOST=0.0.0.0` 且 `CORS_ORIGINS` 包含 `http://<该IP>:5173`。

### 5. 可选增强（按需做）

- **大文件 / 超时**：后端已支持 500MB（`MAX_CONTENT_LENGTH`），前端 `uploadLocalVideo` 已有较长 timeout；若需要可再调大或做分片上传。
- **进度**：前端已有 `onUploadProgress`，进度条已接好。
- **错误提示**：前端 `extractErrorMessage` 已处理常见错误，可按后端返回的 `detail` 再细化文案。
- **已有视频导入**：若希望把「已放在服务器某目录」的视频纳入系统，可写一个脚本或管理接口：扫描 `UPLOAD_FOLDER`，为每个视频在 `videos` 表插入记录（或调用现有创建逻辑），保证 `filepath` 与磁盘路径一致。

---

## 五、小结

- **已经上传的视频放在哪里**：**`backend_fastapi/uploads/`**（或你在 `.env` 里配置的 `UPLOAD_FOLDER`）。原始视频文件直接在该目录下，字幕、缓存等在其子目录。
- **要实现上传功能**：后端已就绪；把移动端切到「非 UI_ONLY」并配置正确的 `VITE_MOBILE_API_BASE_URL`，即可在 H5/iOS WebView 中完成真实上传；无需改后端上传接口或前端表单字段名。

若你希望增加「扫描 uploads 目录并导入已有视频」的脚本或接口，可以说明运行环境（本地/服务器）和期望的调用方式，我可以按当前项目结构给出具体代码位置和示例。

---

## 六、2026-03-14 实现收口说明

- **本地文件上传**：后端已改为**分块写入临时文件后再落盘**，不再把整段视频一次性读入内存；同时会在写入过程中按 `MAX_CONTENT_LENGTH` 拦截超大文件。
- **链接上传**：`POST /api/videos/upload-url` 现在会**立即创建 `downloading` 状态的视频记录并返回**，真正的视频下载放到后台任务中执行；移动端可立刻跳转到详情页查看下载状态。
- **移动端自动处理**：链接上传后若携带 `autostart=1`，详情页会在后台下载结束、状态从 `downloading` 变为 `uploaded` 后自动调用 `/process`，不需要用户二次点击。
- **列表状态展示**：`GET /api/videos/list` 现已返回 `process_progress`、`current_step`、`error_message`，移动端列表与最近上传卡片可以直接展示下载/处理阶段。
