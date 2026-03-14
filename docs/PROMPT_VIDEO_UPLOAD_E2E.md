# 视频上传端到端联调 — 切实可行提示词

> 用途：复制整段提示词给 AI 或开发者，按步骤完成「后端 + 移动端 + iOS」视频上传联调，可验收。  
> 参考：`docs/VIDEO_UPLOAD_IMPLEMENTATION.md`（落盘路径与接口说明）。

---

## 可直接复制的总提示词（给 AI / 执行者）

```
你是本仓库 EduMind 的开发助手。请按下列要求完成「视频上传功能」的端到端联调，使“在 iOS App 或浏览器中选择本地视频 → 上传到后端 → 在列表中看到并播放”这一链路可运行。

一、项目上下文
- 后端：backend_fastapi（FastAPI），端口 2004；上传接口已实现：POST /api/videos/upload（FormData 字段名 file）、POST /api/videos/upload-url。
- 上传文件落盘路径：backend_fastapi/uploads/（可由 .env 的 UPLOAD_FOLDER 覆盖）。
- 移动端：mobile-frontend（Vue 3 + Vite），当前默认 UI_ONLY_MODE=true，走 mock；需改为调用真实后端。
- iOS：ios-app/EduMindIOS，WKWebView 加载 mobile-frontend 的 H5；H5 内 <input type="file" accept="video/*"> 已存在，无需改原生代码。

二、你必须完成的任务（按顺序）

1. 后端可运行且上传目录就绪
   - 确认 backend_fastapi/.env 存在（可复制 .env.example），且 DATABASE_URL 有效。
   - 确认 UPLOAD_FOLDER 未设置或指向合法路径；未设置则使用默认 backend_fastapi/uploads/。
   - 启动命令：在 backend_fastapi 目录下执行 python run.py 或 uvicorn app.main:app --reload --port 2004；启动日志中须出现「上传目录已就绪」。
   - 若 .env.example 中尚无 UPLOAD_FOLDER 的注释说明，请添加一行注释说明“不设置时默认为 backend_fastapi/uploads”。

2. 移动端指向真实后端并关闭 UI 仅展示模式
   - 在 mobile-frontend 的 .env（或 .env.local）中设置：
     VITE_MOBILE_UI_ONLY=false
     VITE_MOBILE_API_BASE_URL=http://127.0.0.1:2004
   - 若需真机访问本机后端，将 127.0.0.1 改为本机局域网 IP（如 192.168.1.10），并确保后端 CORS_ORIGINS 包含该 Origin。
   - 确认 mobile-frontend 的 src/api/video.js 中 uploadLocalVideo 在非 UI_ONLY 时请求 POST ${API_BASE_URL}/api/videos/upload，FormData 字段名为 file（与后端 File(...) 一致）；无需改字段名。

3. CORS 与网络
   - 在 backend_fastapi/.env 的 CORS_ORIGINS 中至少包含：http://localhost:5173,http://127.0.0.1:5173；真机调试时加入 http://<本机IP>:5173。
   - 若后端仅监听 127.0.0.1，真机无法访问；需在 .env 中设置 HOST=0.0.0.0 或通过启动参数绑定到 0.0.0.0。

4. 验收步骤（你必须给出明确结论）
   - 在 backend_fastapi 下启动后端，确认无报错且日志有“上传目录已就绪”。
   - 在 mobile-frontend 下执行 npm run dev，浏览器打开 http://localhost:5173，进入上传页，选择本地视频文件并点击上传；应请求 POST http://127.0.0.1:2004/api/videos/upload，返回 200 且 backend_fastapi/uploads/ 下出现新文件。
   - 上传成功后，前端应跳转到视频详情或列表，并可从详情页进入播放；播放地址为 GET /api/videos/{id}/stream。
   - 若使用 iOS 真机：VITE_MOBILE_API_BASE_URL 改为本机 IP 后重新构建/同步 H5，在 WebView 中选择视频上传，应同样成功并在 uploads 目录可见文件。

三、输出要求
- 列出你修改或新增的文件路径及简要说明。
- 若有无法满足的条件（如数据库未安装），明确写出并给出替代方案（例如仅写出 .env 示例与验收命令）。
- 最后给出“验收通过”或“验收未通过：原因”的明确结论。
```

---

## 分步提示词（需要逐步执行时使用）

### 步骤 A：后端就绪

```
在 EduMind 仓库中，请检查并保证 backend_fastapi 可正常启动且上传目录有效：
1) 若不存在 .env，从 .env.example 复制并配置 DATABASE_URL；
2) 不设置 UPLOAD_FOLDER 时，默认上传目录为 backend_fastapi/uploads/，启动时创建；
3) 在 .env.example 中为 UPLOAD_FOLDER 添加注释：“不设置时默认为 backend_fastapi/uploads”；
4) 给出启动命令与预期日志片段（包含“上传目录已就绪”）。
```

### 步骤 B：移动端接真实接口

```
在 EduMind 的 mobile-frontend 中，请把视频上传从“仅 UI 展示”改为“调用真实后端”：
1) 在 .env 或 .env.local 中设置 VITE_MOBILE_UI_ONLY=false 和 VITE_MOBILE_API_BASE_URL=http://127.0.0.1:2004；
2) 确认 src/api/video.js 中 uploadLocalVideo 在非 UI_ONLY 时请求的 URL 为 baseURL + /api/videos/upload，FormData 字段名为 file；
3) 确认 src/config/index.js 中 UI_ONLY_MODE 读取 VITE_MOBILE_UI_ONLY，API_BASE_URL 读取 VITE_MOBILE_API_BASE_URL；
4) 无需修改 Upload.vue 的表单字段名或请求方式。
```

### 步骤 C：CORS 与真机

```
在 EduMind 的 backend_fastapi 中，请保证移动端和 iOS WebView 能访问 API：
1) .env 的 CORS_ORIGINS 包含 http://localhost:5173 和 http://127.0.0.1:5173；
2) 若需真机访问，加入 http://<本机局域网IP>:5173，且 HOST=0.0.0.0 或绑定到 0.0.0.0；
3) 说明：真机调试时 mobile-frontend 的 VITE_MOBILE_API_BASE_URL 须为本机 IP:2004。
```

### 步骤 D：验收清单

```
请按以下清单逐项确认并回复“通过”或“未通过 + 原因”：
1) 后端启动后，backend_fastapi/uploads/ 目录存在且可写；
2) 浏览器打开 mobile-frontend 上传页，选择视频上传，Network 中可见 POST .../api/videos/upload 返回 200，且 uploads 下出现新文件；
3) 上传成功后跳转至视频详情/列表，可点击播放，播放请求 GET .../api/videos/{id}/stream 正常；
4) （可选）iOS 真机在 WebView 中上传同一视频，uploads 中可见新文件。
```

---

## 使用说明

- **一次性执行**：复制「可直接复制的总提示词」整段到对话中，让 AI 按顺序完成并给出验收结论。
- **分步执行**：按步骤 A → B → C → D 依次粘贴分步提示词，每步确认后再进行下一步。
- **已上传视频位置**：所有通过接口上传的视频文件均在 `backend_fastapi/uploads/`（或你配置的 `UPLOAD_FOLDER`），详见 `docs/VIDEO_UPLOAD_IMPLEMENTATION.md`。
