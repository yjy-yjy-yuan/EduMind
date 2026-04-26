# EduMind iOS 免费分发指南

## 概述

本指南介绍如何在**不付费苹果开发者账号**的情况下发布 EduMind iOS 应用。

## 推荐方案：AltStore 侧载

### 优势
- ✅ 完全免费
- ✅ 无需苹果开发者账号
- ✅ 用户可自行安装
- ✅ 支持大部分 iOS 设备

### 限制
- ⚠️ 每 7 天需要重新签名（自动提醒）
- ⚠️ 用户需要有 Mac 和数据线（用于首次安装 AltStore）
- ⚠️ 单台设备最多安装 3 个应用

## 用户端安装步骤

### 1. 准备 AltStore

用户需要先安装 AltStore（侧载工具）：

1. **在 Mac 上安装 AltServer**
   - 访问 https://altstore.io/
   - 下载 AltServer（适用于 macOS）
   - 将 AltServer 安装到 Applications 文件夹

2. **在 iOS 设备上安装 AltStore**
   - 在 iPhone 上访问 https://altstore.io/download/
   - 点击蓝色按钮下载 AltStore
   - 系统会提示安装描述文件

3. **连接设备并信任**
   - 用数据线连接 iPhone 和 Mac
   - 在 Mac 上点击菜单栏的 AltServer 图标
   - 选择「Install AltStore」→ 选择你的 iPhone
   - 输入 Apple ID（免费个人账号即可）
   - 在 iPhone 上信任开发者证书：设置 → 通用 → VPN 与设备管理 → 信任

### 2. 安装 EduMind

1. **下载 IPA 文件**
   - 从 GitHub Release 或文件托管下载 `EduMindIOS.ipa`

2. **通过 AltStore 安装**
   - 在 Mac 上点击菜单栏的 AltServer 图标
   - 选择「Install Mail Plug-in」（如需要）
   - 双击 `EduMindIOS.ipa` 文件
   - 或者在手机上通过 AltStore 直接打开

3. **验证安装**
   - 桌面会出现 EduMind 图标
   - 首次启动可能需要信任证书

### 3. 延期签名（每 7 天）

AltStore 会自动提醒延期签名：

- 确保 iPhone 和 Mac 在同一 Wi-Fi 网络
- 在 Mac 上运行 AltServer
- 在 iPhone 上打开 AltStore，找到 EduMind，点击「Refresh」
- 输入 Apple ID 验证

## 开发者端构建步骤

### 1. 准备后端 API 地址

在构建前，需要确定后端 API 地址：

```bash
# 示例：使用你的生产环境地址
export FIXED_DOMAIN=https://api.yourdomain.com
```

### 2. 构建 IPA 文件

```bash
cd /Users/yuan/final-work/EduMind

# 构建 Release 版本 IPA
FIXED_DOMAIN=https://api.yourdomain.com bash ios-app/build_release_ipa.sh
```

### 3. 上传 IPA

- **GitHub Release**（推荐）
  - 在 GitHub 创建 Release
  - 上传 `EduMindIOS.ipa` 文件
  - 提供下载链接给用户

- **其他文件托管**
  - 网盘、CDN 等

## 替代方案对比

| 方案 | 成本 | 安装难度 | 有效期 | 推荐场景 |
|------|------|----------|--------|----------|
| AltStore 侧载 | 免费 | 中等（需 Mac） | 7 天可续期 | 个人/小范围 |
| 免费个人测试证书 | 免费 | 简单（面对面） | 7 天 | 面试、演示 |
| 开源编译 | 免费 | 困难（需 Xcode） | 永久 | 技术社区 |
| 企业签名 | $299/年 | 简单 | 1 年 | 企业内部分发 |
| App Store | $99/年 | 简单 | 永久 | 公开发布 |

## 常见问题

### Q1: AltStore 安全吗？
A: AltStore 是开源项目，代码透明，不会收集个人信息。但使用任何第三方工具都有风险，请自行评估。

### Q2: 可以多台设备共用一个 Apple ID 吗？
A: 可以，但不建议。每个设备应使用自己的 Apple ID。

### Q3: 7 天后不续签会怎样？
A: 应用会无法打开。重新续签即可恢复。

### Q4: 最多可以在多少台设备安装？
A: 单个 Apple ID 最多在 3 台设备上同时安装 AltStore 应用。

### Q5: 可以发布到 App Store 吗？
A: 需要 $99/年的开发者账号。

## 注意事项

1. **后端 API 必须使用 HTTPS**
   - iOS 要求 WebView 加载 HTTPS 内容
   - HTTP 会被拦截或失败

2. **更新版本**
   - 每次更新需要构建新 IPA
   - 用户下载后覆盖安装即可

3. **数据迁移**
   - 新版本安装不会删除本地数据
   - 但建议用户在更新前备份重要数据

4. **测试建议**
   - 先在个人设备上充分测试
   - 确保所有功能正常后再分发给用户

## 相关链接

- AltStore 官网: https://altstore.io/
- AltStore 常见问题: https://altstore.io/faq/
- Apple 免费开发者账号: https://developer.apple.com/

## 总结

对于不想付费发布 iOS 应用的场景，**AltStore 侧载是最平衡的方案**：
- 成本：完全免费
- 易用性：对技术用户友好
- 维护成本：每 7 天续签一次
- 适用范围：个人使用、小范围测试、开源项目

如果面向大众用户，仍建议付费加入苹果开发者计划并通过 App Store 发布。
