# Mac/Windows Whisper 模型优化指南

## 🚨 问题说明

在使用 Whisper 的 medium/large 模型时可能遇到:

1. **任务卡住** - 模型加载时间过长或转录卡死
2. **无法终止** - Celery worker 进程僵死,无法用 Ctrl+C 停止
3. **内存溢出** - GPU 显存不足导致系统挂起
4. **重复下载** - 每次都下载模型,浪费时间和带宽

## ✅ 已实施的优化方案

### 1. 智能设备选择

**Mac (Apple Silicon):**
- MPS (Metal Performance Shaders) 完全支持所有大小的模型
- `tiny`, `base`, `small`, `medium`, `large` 均可使用 MPS 加速
- MPS 比 CPU 快 **3-5 倍**

**Windows/Linux (NVIDIA GPU):**
- CUDA 加速支持所有模型
- 比 CPU 快 **5-10 倍**

**自动降级到 CPU:**
- 仅当 MPS/CUDA 不可用时才使用 CPU
- 确保所有平台都能运行

### 2. 超时保护机制

**智能模型加载超时:**
- 已下载模型: 60秒超时 (加载很快)
- 需下载模型: 300秒超时 (允许下载时间)
- 自动检测模型是否存在,动态调整超时

**任务超时:**
- 硬超时: 3小时 (10800秒)
- 软超时: 2.9小时 (10500秒)

**自定义模型路径:**
- 默认路径: `/Users/yuan/302_works/whisper_models`
- 避免重复下载,节省时间和空间
- 支持离线使用已下载的模型

### 3. 内存管理优化

**自动清理 MPS 缓存:**
```python
# 每次转录完成后清理
torch.mps.empty_cache()
```

**后台执行器隔离:**
- 当前仓库本地开发默认通过 FastAPI 后台执行器处理任务
- 转录完成后会释放模型引用并清理设备缓存，避免内存持续堆积

### 4. 使用 Python API 替代命令行

**优势:**
- 可控制超时和设备选择
- 直接内存管理
- 避免子进程僵死

**关键代码:**
```python
# 自定义模型路径
custom_model_path = "/Users/yuan/302_works/whisper_models"

# 加载模型(带超时保护和自定义路径)
device = get_whisper_device(model)
whisper_model = whisper.load_model(
    model,
    device=device,
    download_root=custom_model_path  # 使用自定义路径
)

# 转录
result = whisper_model.transcribe(
    audio_file,
    language=language,
    fp16=(device == "mps"),  # MPS用FP16,CPU用FP32
)

# 清理
del whisper_model
torch.mps.empty_cache()
```

### 5. 后台执行器模式

**当前仓库实现:**
- 本地开发默认使用 `../edumind-backend/app/core/executor.py` 中的后台执行器
- 不再依赖旧的 Celery worker / solo pool 配置
- 需要提升并发时，优先调整执行器配置而不是恢复旧 Worker 链路

## 📊 模型选择建议

### Mac M1/M2/M3/M4 芯片 (MPS)

| 模型 | 设备 | 速度 | 准确度 | 内存占用 | 推荐场景 |
|------|------|------|--------|----------|----------|
| **tiny** | MPS | ⚡⚡⚡⚡⚡ | ⭐⭐ | 1 GB | 快速测试 |
| **base** | MPS | ⚡⚡⚡⚡ | ⭐⭐⭐ | 1.5 GB | 日常使用 |
| **small** | MPS | ⚡⚡⚡ | ⭐⭐⭐⭐ | 2.5 GB | **推荐** |
| **medium** | MPS | ⚡⚡ | ⭐⭐⭐⭐⭐ | 5 GB | 高质量转录 |
| **large** | MPS | ⚡ | ⭐⭐⭐⭐⭐ | 10 GB | 专业场景 |

### Windows/Linux (NVIDIA CUDA)

| 模型 | 设备 | 速度 | 准确度 | 显存占用 | 推荐场景 |
|------|------|------|--------|----------|----------|
| **tiny** | CUDA | ⚡⚡⚡⚡⚡ | ⭐⭐ | 1 GB | 快速测试 |
| **base** | CUDA | ⚡⚡⚡⚡ | ⭐⭐⭐ | 1.5 GB | 日常使用 |
| **small** | CUDA | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 2 GB | **推荐** |
| **medium** | CUDA | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 5 GB | 高质量转录 |
| **large** | CUDA | ⚡⚡ | ⭐⭐⭐⭐⭐ | 10 GB | 专业场景 |

**💡 推荐配置:**
- **日常使用**: `small` 模型 (准确度和速度平衡最佳)
- **高质量**: `medium` 模型 (**GPU 加速,比 CPU 快 3-10 倍**)
- **快速测试**: `base` 模型 (快速验证功能)

**⚠️ 注意:**
- **Mac**: M4 芯片建议使用 32GB 内存以运行 `large` 模型
- **Windows**: 建议使用 8GB+ 显存的 NVIDIA 显卡运行 `large` 模型
- 16GB 内存/显存建议最大使用 `medium` 模型

## 🛠️ 故障排除

### 1. 后台任务卡住无法终止

**现象:** 后端进程长时间卡住，Ctrl+C 无法正常停止

**Mac 解决方法:**
```bash
# 结束当前 FastAPI 启动进程
pkill -f "python ../edumind-backend/run.py"
```

**Windows 解决方法:**
```cmd
# 打开任务管理器 (Ctrl+Shift+Esc)
# 找到 python.exe 或 uvicorn 相关进程
# 右键 -> 结束任务

# 或使用命令行
taskkill /F /IM python.exe
```

### 2. 模型加载超时

**错误信息:** `加载 medium 模型超时 (超过60秒)`

**原因分析:**
1. **首次使用** - 模型未下载,需要从网络下载 1.4GB 文件
2. **文件损坏** - 缓存的模型文件 SHA256 校验失败,需重新下载
3. **网络问题** - 下载速度慢或连接不稳定

**解决方法:**

**方法1: 使用预下载脚本(推荐)**
```bash
# 在项目根目录运行
python download_whisper.py

# 选择要下载的模型
# 默认保存到: /Users/yuan/302_works/whisper_models
```

**方法2: 手动移动已下载的模型**
```bash
# Mac/Linux
cp /Users/yuan/302_works/whisper_models/*.pt ~/.cache/whisper/

# Windows (PowerShell)
Copy-Item "C:\Users\yuan\302_works\whisper_models\*.pt" "$env:USERPROFILE\.cache\whisper\"
```

**方法3: 修改代码使用自定义路径**
代码已默认配置为使用 `/Users/yuan/302_works/whisper_models`,无需修改。

**验证模型完整性:**
```bash
# Mac/Linux
ls -lh /Users/yuan/302_works/whisper_models/

# Windows (PowerShell)
Get-ChildItem "C:\Users\yuan\302_works\whisper_models" | Format-Table Name, Length

# 预期输出:
# medium.pt      1.4G
# small.pt       461M
# large-v3-turbo.pt   1.5G
```

### 3. 内存不足

**现象:** 系统变慢,任务失败

**解决方法:**
1. 使用更小的模型 (如 `small` 替代 `medium`)
2. 关闭其他占用内存的应用
3. 重启当前 FastAPI 服务，释放 Whisper 模型与后台执行器占用

### 4. 转录质量不佳

**解决方法:**
1. 使用更大的模型 (`medium` 或 `large`)
2. 确保音频质量清晰
3. 指定正确的语言代码 (如 `zh` 中文, `en` 英文)

## 🚀 性能优化建议

### 1. 音频预处理

系统已自动进行音频预处理:
- 提取音频轨道 (避免处理视频流)
- 转换为 16kHz 单声道 WAV
- 使用多线程加速 FFmpeg

### 2. 后台执行并发

当前仓库在本地开发环境下默认使用后台执行器处理任务，而不是 Celery Worker。

**建议做法:**
- 先用 `small` 或 `base` 模型验证链路，再视情况升级到 `medium` 或 `large`
- 如需提高并发，优先检查 [`../edumind-backend/app/core/executor.py`](/Users/yuan/final-work/EduMind/../edumind-backend/app/core/executor.py) 和 [`../edumind-backend/app/core/config.py`](/Users/yuan/final-work/EduMind/../edumind-backend/app/core/config.py) 中的执行器配置
- 不建议沿用旧文档中的 Celery 多 Worker 命令

### 3. 监控任务进度

**查看健康状态与 Whisper 运行时:**
```bash
curl http://127.0.0.1:8000/health
```

**查看上传与处理日志:**
- 直接观察 `python ../edumind-backend/run.py` 所在终端输出
- 上传后在前端视频列表或详情页查看当前步骤和处理进度

## 📝 最佳实践

1. **首次使用先测试小模型** - 确保环境配置正确
2. **使用 small 模型作为默认选择** - 速度和质量的最佳平衡
3. **定期重启本地后端服务** - 需要时可快速释放模型占用和执行器状态
4. **监控系统资源** - 使用活动监视器查看内存/CPU 使用情况
5. **保留日志** - 遇到问题时方便排查

## 🔧 配置文件位置

**Mac:**
- **后台执行器**: `../edumind-backend/app/core/executor.py`
- **Whisper 运行时**: `../edumind-backend/app/services/whisper_runtime.py`
- **视频处理任务**: `../edumind-backend/app/tasks/video_processing.py`

**Windows:**
- **后台执行器**: `../edumind-backend/app/core/executor.py`
- **视频处理任务**: `../edumind-backend/app/tasks/video_processing.py`

**模型存储路径 (跨平台):**
- 当前仓库默认路径: `/Users/yuan/302_works/whisper_models`
- Mac 示例: `/Users/<用户名>/302_works/whisper_models`
- Windows 示例: `C:\Users\<用户名>\302_works\whisper_models`

## 📞 获取帮助

如遇到问题,查看日志:
```bash
# 直接查看本地启动终端输出
python ../edumind-backend/run.py
```

---

**最后更新:** 2026-03-19
**适用版本:** EduMind Whisper 运行时
**支持平台:** Mac (Apple Silicon MPS) / Windows (NVIDIA CUDA) / Linux (CPU/CUDA)
