# iOS 免费分发方案 - 完整指南索引

## 📚 指南列表

### 🚀 快速开始
1. [方案对比总结](./SOLUTION_COMPARISON.md) - **推荐首先阅读**
   - 所有方案的全面对比
   - 决策矩阵和推荐策略
   - 成本分析和实施时间表

### 📖 详细方案指南

#### 方案 1: AltStore 侧载
- [免费分发指南](./FREE_DISTRIBUTION_GUIDE.md)
- [用户安装指南](./USER_INSTALL_GUIDE.md)

#### 方案 2: Sideloadly（Windows+Mac）
- [Sideloadly 指南](./SIDELOADLY_GUIDE.md)

#### 方案 3: PWA（Progressive Web App）
- [PWA 部署指南](./PWA_GUIDE.md) - **强烈推荐**

#### 方案 4: TestFlight 内测
- [TestFlight 指南](./TESTFLIGHT_GUIDE.md)

#### 方案 5: 开源编译
- [开源编译指南](./OPEN_SOURCE_BUILD_GUIDE.md)

#### 方案 6: 企业签名（灰色地带）
- [企业签名指南](./ENTERPRISE_SIGNING_GUIDE.md)

#### 方案 7: ReProvision 自动续签
- [ReProvision 指南](./REPROVISION_GUIDE.md)

---

## 🎯 推荐阅读顺序

### 对于 EduMind 项目

```
第一步：阅读方案对比总结
         ↓
    SOLUTION_COMPARISON.md
         ↓
第二步：选择最适合的方案
         ↓
第三步：阅读对应详细指南
         ↓
第四步：开始实施
```

### 快速决策指南

| 如果您想... | 推荐方案 | 阅读文档 |
|------------|----------|----------|
| **最简单、最安全** | PWA | [PWA_GUIDE.md](./PWA_GUIDE.md) |
| **完全免费、无限制** | PWA | [PWA_GUIDE.md](./PWA_GUIDE.md) |
| **原生体验** | Sideloadly | [SIDELOADLY_GUIDE.md](./SIDELOADLY_GUIDE.md) |
| **Windows 用户** | Sideloadly | [SIDELOADLY_GUIDE.md](./SIDELOADLY_GUIDE.md) |
| **Mac 用户** | AltStore | [USER_INSTALL_GUIDE.md](./USER_INSTALL_GUIDE.md) |
| **技术用户** | 开源编译 | [OPEN_SOURCE_BUILD_GUIDE.md](./OPEN_SOURCE_BUILD_GUIDE.md) |
| **教育机构** | TestFlight | [TESTFLIGHT_GUIDE.md](./TESTFLIGHT_GUIDE.md) |
| **长期稳定** | 开源编译 | [OPEN_SOURCE_BUILD_GUIDE.md](./OPEN_SOURCE_BUILD_GUIDE.md) |

---

## 📋 工具和脚本

### 构建脚本

#### build_release_ipa.sh
```bash
# 用途：构建 Release 版本 IPA 文件
# 位置：./build_release_ipa.sh

# 使用方法：
FIXED_DOMAIN=https://api.yourdomain.com \
  bash ios-app/build_release_ipa.sh

# 注意：需要先设置后端 API 地址
```

#### sync_ios_web_assets.sh
```bash
# 用途：同步前端资源到 iOS 项目
# 位置：./sync_ios_web_assets.sh

# Debug 模式：
bash ios-app/sync_ios_web_assets.sh

# Release 模式：
FIXED_DOMAIN=https://api.yourdomain.com \
  bash ios-app/sync_ios_web_assets.sh --release
```

#### validate_ios_build.sh
```bash
# 用途：验证 iOS 构建是否成功
# 位置：./validate_ios_build.sh

# 使用方法：
bash ios-app/validate_ios_build.sh
```

---

## 🎓 关键概念

### iOS 证书类型

| 证书类型 | 有效期 | 用途 | 成本 |
|----------|--------|------|------|
| 免费个人证书 | 7 天 | 本地测试 | 免费 |
| 开发者证书 | 1 年 | 开发/测试 | $99/年 |
| 企业证书 | 1 年 | 企业内部 | $299/年 |

### 分发方式

| 方式 | 用户限制 | 安装难度 | 更新方式 |
|------|----------|----------|----------|
| PWA | 无 | 极简 | 自动 |
| 侧载 | 小范围 | 中等 | 手动 |
| TestFlight | 10,000人 | 简单 | 自动 |
| 企业签名 | 无 | 简单 | 自动 |

---

## ⚠️ 重要提醒

### 安全第一

1. **企业签名**：存在高风险，不推荐
2. **ReProvision**：需要越狱，安全风险高
3. **第三方工具**：选择知名、开源的工具

### 合规考虑

1. **PWA**：完全合规
2. **开源编译**：完全合规
3. **侧载工具**：灰色地带，但相对安全
4. **企业签名**：可能违反服务条款

### 用户支持

1. **PWA**：用户自主，无需支持
2. **开源编译**：需要技术支持
3. **侧载工具**：需要定期答疑
4. **TestFlight**：官方支持

---

## 🚀 快速开始

### 方案 A：PWA（推荐）

```bash
# 1. 阅读 PWA 指南
cat ios-app/PWA_GUIDE.md

# 2. 配置 PWA
# 在 mobile-frontend/public/ 创建 manifest.json
# 添加图标
# 修改 index.html

# 3. 部署到服务器
cd mobile-frontend
npm run build:web
# 部署 dist/ 到服务器
```

### 方案 B：侧载工具

```bash
# 1. 构建 IPA
FIXED_DOMAIN=https://api.yourdomain.com \
  bash ios-app/build_release_ipa.sh

# 2. 选择侧载工具
# - Windows: Sideloadly
# - Mac: AltStore

# 3. 分发给用户
# - 上传 IPA 文件
# - 提供安装指南
```

### 方案 C：开源编译

```bash
# 1. 阅读开源编译指南
cat ios-app/OPEN_SOURCE_BUILD_GUIDE.md

# 2. 准备开源项目
# - 清理敏感信息
# - 编写编译文档
# - 添加 LICENSE

# 3. 发布到 GitHub
# - 创建仓库
# - 推送代码
# - 发布 Release
```

---

## 📞 获取帮助

### 问题排查

1. **阅读详细指南** - 每个方案都有详细的 FAQ
2. **查看 GitHub Issues** - 搜索类似问题
3. **参考官方文档** - Apple Developer 文档

### 社区支持

- **GitHub Issues**: 技术问题讨论
- **Discussions**: 使用经验分享
- **Stack Overflow**: 技术问答

---

## 📊 方案评分

| 方案 | 成本 | 易用性 | 稳定性 | 推荐度 |
|------|------|--------|--------|--------|
| **PWA** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **开源编译** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Sideloadly** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **AltStore** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **TestFlight** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **企业签名** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **ReProvision** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎯 总结

**对于 EduMind 项目的最佳策略：**

### 主推方案：PWA
- ✅ 完全符合项目架构
- ✅ 零成本、零风险
- ✅ 覆盖所有用户
- ✅ 部署简单

### 辅助方案：开源编译
- ✅ 建立技术社区
- ✅ 提供长期方案
- ✅ 适合技术用户

### 补充方案：Sideloadly
- ✅ 支持 Windows 用户
- ✅ 用户体验好
- ✅ 相对稳定

### 不推荐：企业签名、ReProvision
- ❌ 风险太高
- ❌ 成本不合理
- ❌ 门槛太高

---

## 🔗 相关资源

### 官方资源
- Apple Developer: https://developer.apple.com/
- PWA 指南: https://web.dev/progressive-web-apps/
- TestFlight: https://developer.apple.com/testflight/

### 社区资源
- AltStore: https://altstore.io/
- Sideloadly: https://sideloadly.io/
- PWA Builder: https://www.pwabuilder.com/

### 开源资源
- GitHub: https://github.com/
- 开源许可证: https://choosealicense.com/

---

## 📝 更新日志

- 2026-04-26: 初始版本，创建完整指南体系
- 包含 7 种方案的详细指南
- 添加方案对比和决策矩阵
- 提供构建脚本和工具

---

## 🎓 致谢

感谢所有提供免费工具和服务的开发者：
- AltStore 团队
- Sideloadly 团队
- PWA 社区
- 开源社区

---

**开始您的 iOS 免费分发之旅！选择最适合您的方案，立即开始实施！** 🚀
