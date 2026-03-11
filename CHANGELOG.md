# 变更日志

## 2026-03-10

### 目录调整
- 将 `mobile-android/` 重命名为 `android-app/`。
- 全仓检查完成，已清理旧路径 `mobile-android` 的文档引用。

### 文档修正
- 更新 [`android-app/README.md`](/Users/yuan/final-work/EduMind/android-app/README.md)：同步新的目录路径与标题。
- 更新 [`docs/MOBILE_MODULE_PROMPTS.md`](/Users/yuan/final-work/EduMind/docs/MOBILE_MODULE_PROMPTS.md)：统一为 `android-app` 表述。
- 更新 [`PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`](/Users/yuan/final-work/EduMind/PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md)：统一为 `android-app` 表述。

### Android 工程命名统一
- 更新 [`android-app/app/src/main/res/values/strings.xml`](/Users/yuan/final-work/EduMind/android-app/app/src/main/res/values/strings.xml)：应用显示名改为 `EduMind Android`。
- 更新 [`android-app/settings.gradle.kts`](/Users/yuan/final-work/EduMind/android-app/settings.gradle.kts)：工程名改为 `EduMindAndroid`。

### 新增文件
- 新增 [`AGENTS.md`](/Users/yuan/final-work/EduMind/AGENTS.md)：仓库协作与提交规范说明。

## 2026-03-11

### 文档对齐
- 重写 [`README.md`](/Users/yuan/final-work/EduMind/README.md)：按当前仓库结构更新为 `backend_fastapi`、`mobile-frontend`、`android-app` 方案。
- 重写 [`backend_fastapi/README.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README.md)：移除旧项目名与过时说明，统一为当前 FastAPI 主后端。
- 重写 [`backend_fastapi/README_RUN.md`](/Users/yuan/final-work/EduMind/backend_fastapi/README_RUN.md)：统一运行步骤、环境名和启动命令。
- 重写 [`README_test.md`](/Users/yuan/final-work/EduMind/README_test.md)：修正测试入口与命令示例。
