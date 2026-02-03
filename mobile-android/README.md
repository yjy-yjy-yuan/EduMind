# EduMind Mobile Android (WebView 壳)

这是一个 Android Studio 工程，用 WebView 加载 `mobile-frontend`（开发时走本地 dev server；也可配置为加载打包后的离线资源）。

## 开发模式（固定离线页面，推荐）

该工程默认**固定加载离线 H5**：`file:///android_asset/index.html`，避免真机访问不到电脑 dev server 导致白屏。

1. 构建并同步离线页面：
   - `cd mobile-frontend`
   - `npm install`
   - `npm run build -- --mode android`
   - 将 `mobile-frontend/dist/` 复制到 `mobile-android/app/src/main/assets/`
2. Android Studio 打开本目录 `mobile-android/`，Run `app`
3. 设置移动应用后端地址（API 基地址）：
   - Debug 下右上角齿轮 → “API 基地址”
   - 示例：`http://192.168.1.8:5002` 或 `https://api.example.com`

> 提示：如果你的移动应用后端不是同域，请在 `mobile-frontend/.env` 配 `VITE_MOBILE_API_BASE_URL` 指向移动后端。

## 说明

- 页面固定布局在 `mobile-frontend/src/views/` 中实现，适配小屏/安全区，避免底部遮挡。
- `mobile-frontend/src/config/index.js` 支持通过 URL 参数传 `apiBase`（Android 侧也可通过设置写入）。
