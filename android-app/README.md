# EduMind Android (`android-app`)

这是 Android Studio 工程，使用 WebView 加载 `mobile-frontend` 构建出的 H5 页面。

## 当前模式

工程默认加载离线页面：

```text
file:///android_asset/index.html
```

这比直接连开发机 dev server 更稳定，能避免真机无法访问宿主网络时出现白屏。

## 开发流程

1. 构建移动端离线资源

```bash
cd mobile-frontend
npm install
npm run build -- --mode android
```

2. 同步静态资源到 Android 资产目录

将 `mobile-frontend/dist/` 复制到 `android-app/app/src/main/assets/`

3. 使用 Android Studio 打开 `android-app/` 并运行 `app`

4. 在应用内配置 API 基地址

示例：

- `http://192.168.1.8:2004`
- `https://api.example.com`

## 说明

- 当前推荐移动端后端默认是 FastAPI `2004`，不再以旧文档中的 `5002` 为默认值
- `mobile-frontend/src/config/index.js` 支持通过 URL 参数或运行时设置传入 `apiBase`
- 页面布局和交互主要在 `mobile-frontend/src/views/` 中维护，Android 工程负责容器能力和资源加载
