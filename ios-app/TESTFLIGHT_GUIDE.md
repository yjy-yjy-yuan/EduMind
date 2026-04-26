# TestFlight 内测指南（无需 App Store 公开）

## 概述

TestFlight 是苹果官方的测试平台，通常需要 $99/年开发者账号，但有以下特殊情况：

### 优惠情况

1. **教育机构**
   - 如果您是教育机构，可申请免费的 Apple Developer Program for Higher Education
   - 需要验证教育身份
   - 详细信息: https://developer.apple.com/programs/higher-education/

2. **非营利组织**
   - 非营利组织可以申请免费开发者账号
   - 需要提供 501(c)(3) 等非营利证明
   - 详细信息: https://developer.apple.com/programs/non-profit/

3. **短期试用**
   - 苹果有时会提供 3 个月免费试用
   - 关注苹果官方活动

## TestFlight 优势

### 如果能获得免费/试用开发者账号

- ✅ **官方支持** - 苹果官方平台
- ✅ **无需数据线** - 通过 App Store 安装
- ✅ **自动更新** - 新版本自动推送
- ✅ **有效期长** - 测试版本 90 天有效期
- ✅ **大规模** - 最多 10,000 名测试用户
- ✅ **专业体验** - 类似 App Store 的安装体验
- ✅ **崩溃报告** - 自动收集崩溃日志

## 适用场景

- 教育机构内部应用
- 非营利组织项目
- 用户群体有限（<10,000人）
- 需要专业分发体验

## 申请步骤（教育机构）

### 1. 准备材料

- 教育机构营业执照
- 教育网站域名
- 教育邮箱（.edu 后缀）
- 学校/机构证明文件

### 2. 申请流程

1. 访问 https://developer.apple.com/programs/higher-education/
2. 点击「Request an enrollment」
3. 填写机构信息
4. 上传证明文件
5. 等待审核（通常 1-2 周）

### 3. 获得账号后

```bash
# 使用 TestFlight 分发的步骤
# 1. 在 Xcode 中配置 Team
# 2. 构建并上传到 App Store Connect
# 3. 创建 TestFlight 内测
# 4. 生成公开链接或邀请用户
```

## 有限制的方案（99美元/年）

如果您愿意付费 $99/年，TestFlight 是最佳选择：

### 对比其他方案

| 特性 | TestFlight ($99/年) | AltStore (免费) |
|------|-------------------|-----------------|
| 安装难度 | 简单（App Store） | 中等（需数据线） |
| 有效期 | 90 天自动续签 | 7 天手动续签 |
| 用户数量 | 最多 10,000 人 | 单个 Apple ID 3 台设备 |
| 更新方式 | 自动推送 | 用户手动下载 |
| 崩溃报告 | 支持 | 不支持 |
| 用户体验 | 官方体验 | 第三方工具 |

## 临时解决方案

### 混合策略

结合多种方案扩大覆盖范围：

1. **核心用户** - 使用 TestFlight（如果获得免费账号）
2. **Windows 用户** - 使用 Sideloadly
3. **Mac 用户** - 使用 AltStore
4. **技术用户** - 自己编译源码

## 注意事项

### TestFlight 限制

- ⚠️ 每个版本 90 天有效期（需要不断更新）
- ⚠️ 最多 10,000 名测试用户
- ⚠️ 需要定期上传新版本维持测试状态
- ⚠️ 最终仍需上架 App Store 才能公开发布

### 合规要求

- 遵守苹果 App Store 审核指南
- 不能滥用 TestFlight 进行商业分发
- 需要定期更新应用

## 替代方案对比

### 如果无法获得免费账号

| 方案 | 成本 | 用户数量 | 难度 |
|------|------|----------|------|
| **TestFlight** | $99/年 | 10,000 人 | 简单 |
| **AltStore** | 免费 | 小规模 | 中等 |
| **Sideloadly** | 免费 | 小规模 | 中等 |
| **企业签名** | $299/年 | 无限制 | 简单 |

## 相关资源

- Apple Developer Education: https://developer.apple.com/programs/higher-education/
- Apple Developer Non-Profit: https://developer.apple.com/programs/non-profit/
- TestFlight Guide: https://developer.apple.com/testflight/

## 建议

1. **先申请教育/非营利免费账号** - 如果符合条件
2. **考虑 $99/年性价比** - 对于 10,000 用户规模很划算
3. **混合使用多种方案** - 覆盖不同用户群体
4. **长期规划** - 如果应用成功，最终还是需要 App Store

## 总结

TestFlight 是最专业的免费（或低成本）分发方案，但需要：
- 符合教育/非营利条件
- 或者愿意支付 $99/年
- 接受 90 天版本有效期限制

如果您的应用面向教育领域，强烈建议尝试申请教育机构免费账号！
