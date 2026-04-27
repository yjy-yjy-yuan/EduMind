# iOS 离线模型评估与切换说明

本文只覆盖当前 EduMind iOS-only 链路里和“本地离线视频处理”直接相关的两类能力：

1. iOS 端本地离线转录
2. 后端本地 LLM 摘要、标题、语义整理回退链路

结论先说：

- 当前 iOS 端离线视频转录实际使用的是 Apple `Speech` 端侧识别，不是 Whisper，也不是 Ollama，更不是 GGUF 大模型。
- 你截图里的 `Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF` 更适合做本地总结、标题、语义整理、结构化输出，不适合直接替代视频语音转录引擎。
- 如果你想在“不大改现有后端代码”的前提下接入这类 GGUF，本项目当前最合适的加载方式仍然是 `Ollama`，因为现有本地 LLM 回退路径全部走的是 Ollama HTTP API。

## 1. 当前模型与目标模型记录

说明：

- 下表中的“输出质量分”“通用理解”“推荐结论”属于当前项目语境下的工程评估，不是官方 benchmark。
- “最低显存”按当前项目实际可落地方式填写；Apple `Speech` 没有独立显存要求，因此记为“不适用”。
- 你截图里的模型名带 `GGUF`，但公开页面同时存在 `v2` 多模态版本和 GGUF 量化版本；本项目切换时按“GGUF 本地推理模型”理解。

| 项目 | 当前 iOS 离线模型 | 目标模型 |
| --- | --- | --- |
| 模型名称 | Apple Speech On-Device Recognition | Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF |
| 模型家族 | Apple Speech Framework | Qwen 3.5 Distilled / GGUF |
| 参数规模 | 官方未公开 | 9B |
| 是否离线 | 是 | 是 |
| 官方链接 | [Apple Speech](https://developer.apple.com/documentation/speech) | [Hugging Face 模型页](https://huggingface.co/Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF) |
| 中文能力 | 中，依赖 Apple 端侧语言包与 locale | 强 |
| OCR 能力 | 无 | 不建议作为稳定 OCR 方案；若你实际下载的是多模态 `v2` 非 GGUF 版本则可做图文理解 |
| 转录能力 | 有，当前项目正在使用 | 无原生语音转文字能力，不适合替代 ASR |
| 最低显存 | 不适用，依赖 iPhone/iPad 设备能力 | 约 6GB 起可尝试 `Q4` 量化，8GB 以上更稳 |
| 通用理解 | 低，偏 ASR 工具能力 | 强，适合摘要、结构化提取、推理 |
| 输出质量分 (0-100) | 42 | 82 |
| 速度 | 快 | 中 |
| 幻觉程度 | 低到中，主要表现为误识别而非编造推理 | 中 |
| 推荐结论 | 适合“纯本地转录”，不适合高质量中文课程整理 | 适合做本地总结/标题/语义整理，不适合替代视频转录引擎 |

## 2. 现有项目里的真实使用位置

当前仓库里，iOS 离线视频处理的转录链路是：

- [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：使用 `SFSpeechRecognizer`
- [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：`request.requiresOnDeviceRecognition = true`
- [`ios-app/EduMindIOS/EduMindIOS/ContentView.swift`](/Users/yuan/final-work/EduMind/ios-app/EduMindIOS/EduMindIOS/ContentView.swift)：完成后回传 `engine = apple_speech_on_device`

当前仓库里，本地 LLM 回退链路在后端：

- [`../edumind-backend/app/services/video_content_service.py`](/Users/yuan/final-work/edumind-backend/app/services/video_content_service.py)：摘要、标签生成可回退到 Ollama
- [`../edumind-backend/app/utils/semantic_utils.py`](/Users/yuan/final-work/edumind-backend/app/utils/semantic_utils.py)：字幕语义分段、标题生成可走 Ollama
- [`../edumind-backend/app/services/llm_similarity_service.py`](/Users/yuan/final-work/edumind-backend/app/services/llm_similarity_service.py)：标签相似度可走 Ollama

另外，当前 iOS 离线转录在同步回后端时，仍然写入原有数据库主链路：

- `POST /api/videos/sync-offline-transcript` 端点已从当前项目移除（返回 `410 Gone`）。iOS 离线转录结果不再同步回后端主流水线；前端链路中已移除所有离线同步调用（`syncOfflineTranscriptToVideo` 等）。

如果需要将本地转录结果汇入后端，请改用后端 Whisper 直传接口 `POST /api/videos/transcribe-audio` 或在上传链路中处理。

所以“切换为你图片上的模型”在本项目里能真实落地的含义是：

- 切换后端本地 LLM 默认模型
- 不伪装成已经替换 iOS 端本地 ASR

## 3. 是否需要 Ollama

分成两个问题看：

### 3.1 如果你只是保留当前 iOS 离线转录

不需要 Ollama。

原因：

- 当前 iOS 端离线转录完全走 Apple 原生 `Speech`
- 这条链路不依赖 Python，也不依赖 Ollama

### 3.2 如果你要在当前项目里加载这个 GGUF 模型

建议需要 Ollama。

原因：

- 当前代码里所有本地 LLM 调用都已经写成了 Ollama API 形态
- 不用 Ollama 也能做，但意味着你要额外改造为 `llama.cpp`、`MLX`、`Core ML` 或自建推理服务
- 对当前仓库来说，这不是“小切换”，而是“重写本地模型接入层”

因此当前最稳妥的结论是：

- 想提升“转录质量”：不要把这个 GGUF 当成 ASR 替身
- 想提升“转录后的理解、摘要、标题、结构化输出”：可以切到这个 GGUF，并继续保留 Ollama

## 4. 是否需要用 Ollama 来加载

当前项目下，答案是“建议用”。

原因很直接：

- 代码里现成的本地接口是 `http://localhost:11434/api`
- 切换成本最低
- 你只需要把 GGUF 导入成一个 Ollama 本地模型名，然后把 `OLLAMA_MODEL` 指到这个别名

如果你后面坚持“完全不要 Ollama”，那要额外做这些事：

1. 新增 GGUF 直接加载层
2. 改写所有 `call_ollama(...)` / `requests.post(.../generate)` 调用
3. 统一流式、超时、模型热切换、错误回退逻辑

这对当前仓库不划算。

## 5. 本次切换后的建议

推荐组合：

1. iOS 端继续用 Apple `Speech` 做本地离线转录
2. 后端本地 LLM 默认模型切到 `Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF`
3. 通过 Ollama 导入 GGUF，并把项目配置里的 `OLLAMA_MODEL` 改成该模型的本地别名

当前仓库已经补了一个兼容脚本，二选一即可：

1. 本地 GGUF 文件：`bash ../edumind-backend/scripts/import_qwen35_gguf_to_ollama.sh /absolute/path/to/model.gguf`
2. Hugging Face 直接拉取：`bash ../edumind-backend/scripts/import_qwen35_gguf_to_ollama.sh hf.co/Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-GGUF:Q4_K_M`

如果你真正想提升“离线视频处理总体效果”，下一步更值得做的是：

1. 保留当前 Apple 端侧转录作为极速模式
2. 另外增加一个高质量离线转录模式，例如 Whisper/Whisper.cpp/MLX Whisper
3. 再把这次切换的 Qwen GGUF 用在摘要、标题、问答整理上

这样才是能力对位，而不是让推理模型去做它本身不擅长的 ASR。

## 6. 参考链接

- Apple Speech: [https://developer.apple.com/documentation/speech](https://developer.apple.com/documentation/speech)
- Ollama Import GGUF: [https://docs.ollama.com/import](https://docs.ollama.com/import)
- 目标模型页: [https://huggingface.co/Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF](https://huggingface.co/Jackrong/Qwen3.5-9B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF)
