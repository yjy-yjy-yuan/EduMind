# 项目路径与参考说明（给实现者与 AI）

在**任意工作目录**打开本仓库或跨文件夹实现时，请优先以本文档中的**绝对路径**为准，避免「找不到项目 / 参考错仓库」。

## 主工程（实现与修改发生在这里）

| 说明 | 绝对路径 |
|------|----------|
| **EduMind 主仓库** | `/Users/yuan/final-work/EduMind` |
| 后端（FastAPI） | `/Users/yuan/final-work/EduMind/backend_fastapi` |
| 移动端 H5 | `/Users/yuan/final-work/EduMind/mobile-frontend` |
| iOS 容器 | `/Users/yuan/final-work/EduMind/ios-app` |
| 文档与提示词 | `/Users/yuan/final-work/EduMind/docs` |
| 仓库级规范 | `/Users/yuan/final-work/EduMind/AGENTS.md` |

**约定**：所有本仓库内的提示词、重构说明、API 契约，均以 `EduMind` 根目录为**唯一实现目标**。

## 可选参考（仅架构/模式，不作为依赖）

| 说明 | 绝对路径 |
|------|----------|
| Claude Code CLI 源码补全版（泄漏源码 + 社区构建） | `/Users/yuan/final-work/claude-code补全版本` |

**用途**：仅供对照「编排、上下文、工具链、可观测」等**思路**；**不要**将其作为 EduMind 的运行时依赖或复制大段代码进生产（版权与维护成本见该目录 `CLAUDE.md`）。

## 在其它文件夹下开发时怎么用

1. 在 Cursor / 对话里**显式写出**：「实现目标仓库：`/Users/yuan/final-work/EduMind`」。
2. 需要读提示词时，路径为：
   - `/Users/yuan/final-work/EduMind/docs/LEARNING_FLOW_AGENT_PROMPT.md`
   - `/Users/yuan/final-work/EduMind/docs/VIDEO_RECOMMENDATION_FEASIBILITY_AND_PROMPT.md`
3. 若本机路径不同（例如换机器），请**全局替换**为你的 `EduMind` 根路径，并同步更新本文档。

---

*若路径变更，只改本文件与上述提示词中的引用即可。*
