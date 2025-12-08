# 平台特定配置指南

本项目现在支持两种平台的GPU加速：
- **Windows/Linux**: CUDA 加速
- **Mac (Apple Silicon)**: MPS 加速

## 📁 文件结构

### 原始文件（Windows/Linux CUDA版本）
- `backend/app/utils/rag_system.py` - 使用 CUDA 加速
- `backend/app/tasks/video_processing.py` - 使用 CUDA 加速

### Mac优化版本（Apple Silicon MPS版本）
- `backend/app/utils/rag_system_mac.py` - 使用 MPS 加速
- `backend/app/tasks/video_processing_mac.py` - 使用 MPS 加速

## 🚀 使用方法

### 方案1: 修改导入（推荐）

根据你的平台，修改相应的导入语句：

#### Windows/Linux 用户
保持原有导入不变：
```python
# 在需要使用的文件中
from app.utils.rag_system import RAGSystem
from app.tasks.video_processing import process_video
```

#### Mac 用户
修改导入为 Mac 版本：
```python
# 在需要使用的文件中
from app.utils.rag_system_mac import RAGSystem
from app.tasks.video_processing_mac import process_video
```

### 方案2: 自动检测平台

创建一个平台检测模块（推荐用于生产环境）：

```python
# backend/app/utils/platform_utils.py
import platform
import torch

def get_device():
    """自动检测最佳设备"""
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"

def is_mac():
    """检测是否为Mac系统"""
    return platform.system() == "Darwin"

# 自动导入正确的模块
if is_mac():
    from app.utils.rag_system_mac import RAGSystem
    from app.tasks.video_processing_mac import process_video
else:
    from app.utils.rag_system import RAGSystem
    from app.tasks.video_processing import process_video
```

## 🔧 主要差异

### 1. GPU 加速方式

**Windows/Linux (CUDA)**:
```python
if torch.cuda.is_available():
    device = torch.device("cuda")
    x = x.cuda()
```

**Mac (MPS)**:
```python
if torch.backends.mps.is_available():
    device = torch.device("mps")
    x = x.to('mps')
```

### 2. FAISS GPU 支持

- **Windows/Linux**: 支持 FAISS GPU 索引
- **Mac**: FAISS 仅支持 CPU 索引（MPS 不支持）

### 3. Float16 支持

- **Windows/Linux**: 支持 fp16 加速
- **Mac**: 使用 fp32（MPS 对 fp16 支持有限）

## 📊 性能对比

根据测试文件 `test_pytorch_m4.py` 的结果：

| 操作 | M4 (MPS) | CUDA | CPU |
|------|----------|------|-----|
| 矩阵运算 | ⚡️ 快 | ⚡️⚡️ 更快 | 🐌 慢 |
| 向量编码 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| FAISS GPU | ❌ 不支持 | ✅ 支持 | ✅ CPU版 |

## 🛠️ 环境配置

### Mac (Apple Silicon)
```bash
# PyTorch with MPS support
pip install torch torchvision torchaudio

# 验证 MPS
python test_pytorch_m4.py
```

### Windows/Linux (CUDA)
```bash
# PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证 CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

## 📝 修改建议

### 当前需要修改的文件位置：

1. **RAG 系统调用处**:
   - `backend/app/routes/chat.py`
   - `backend/app/routes/qa.py`
   - 其他使用 RAGSystem 的地方

2. **视频处理任务调用处**:
   - `backend/app/routes/video.py`
   - Celery 任务配置文件

### 示例修改：

```python
# backend/app/routes/qa.py
import platform

# 根据平台导入
if platform.system() == "Darwin":  # Mac
    from app.utils.rag_system_mac import RAGSystem
else:  # Windows/Linux
    from app.utils.rag_system import RAGSystem
```

## ✅ 验证

### 验证 Mac MPS 支持
```bash
cd backend
python -c "
import torch
print(f'MPS 可用: {torch.backends.mps.is_available()}')
print(f'MPS 构建: {torch.backends.mps.is_built()}')
"
```

### 验证 Windows/Linux CUDA 支持
```bash
cd backend
python -c "
import torch
print(f'CUDA 可用: {torch.cuda.is_available()}')
print(f'CUDA 版本: {torch.version.cuda}')
"
```

## 🐛 故障排除

### Mac MPS 问题
1. 确保 macOS >= 12.3
2. 使用最新版 PyTorch (>= 2.0.0)
3. 某些操作可能不支持 MPS，会自动回退到 CPU

### Windows/Linux CUDA 问题
1. 检查 NVIDIA 驱动版本
2. 确保 CUDA toolkit 已安装
3. PyTorch 版本需与 CUDA 版本匹配

## 📚 相关文档

- [PyTorch MPS 文档](https://pytorch.org/docs/stable/notes/mps.html)
- [PyTorch CUDA 文档](https://pytorch.org/docs/stable/cuda.html)
- [FAISS 文档](https://github.com/facebookresearch/faiss)

---

**最后更新**: 2025年11月6日
**测试环境**:
- Mac M4 芯片 + MPS ✅
- Windows + CUDA (待测试)
