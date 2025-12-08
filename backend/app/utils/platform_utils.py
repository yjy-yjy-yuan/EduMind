"""
平台检测和自动配置工具
自动检测运行平台（Mac/Windows/Linux）并选择最佳的GPU加速方案
"""

import logging
import platform
import sys

logger = logging.getLogger(__name__)

# 尝试导入 torch
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("⚠️  PyTorch 未安装，将使用 CPU 模式")


def get_system_info():
    """获取系统信息"""
    return {
        'system': platform.system(),  # Darwin, Windows, Linux
        'machine': platform.machine(),  # arm64, x86_64, AMD64
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }


def get_device():
    """自动检测最佳计算设备"""
    if not TORCH_AVAILABLE:
        logger.info("💻 使用 CPU 模式（PyTorch 未安装）")
        return "cpu"

    # 优先检测 MPS (Apple Silicon)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        logger.info("🍎 使用 MPS 加速 (Apple Silicon)")
        return "mps"

    # 检测 CUDA (NVIDIA GPU)
    if torch.cuda.is_available():
        logger.info(f"🚀 使用 CUDA 加速 (GPU: {torch.cuda.get_device_name(0)})")
        return "cuda"

    # 默认使用 CPU
    logger.info("💻 使用 CPU 模式")
    return "cpu"


def is_mac():
    """检测是否为 Mac 系统"""
    return platform.system() == "Darwin"


def is_windows():
    """检测是否为 Windows 系统"""
    return platform.system() == "Windows"


def is_linux():
    """检测是否为 Linux 系统"""
    return platform.system() == "Linux"


def is_apple_silicon():
    """检测是否为 Apple Silicon (M1/M2/M3/M4)"""
    return is_mac() and platform.machine() == "arm64"


def get_pytorch_info():
    """获取 PyTorch 配置信息"""
    if not TORCH_AVAILABLE:
        return {'available': False, 'version': None, 'cuda_available': False, 'mps_available': False, 'device': 'cpu'}

    info = {
        'available': True,
        'version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'mps_available': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
        'device': get_device(),
    }

    # 添加 CUDA 详细信息
    if info['cuda_available']:
        info['cuda_version'] = torch.version.cuda
        info['cudnn_version'] = torch.backends.cudnn.version()
        info['gpu_count'] = torch.cuda.device_count()
        info['gpu_name'] = torch.cuda.get_device_name(0)

    # 添加 MPS 详细信息
    if info['mps_available']:
        info['mps_built'] = torch.backends.mps.is_built()

    return info


def print_system_info():
    """打印系统和 PyTorch 配置信息"""
    print("=" * 60)
    print("🖥️  系统信息")
    print("=" * 60)

    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("🔥 PyTorch 配置")
    print("=" * 60)

    pt_info = get_pytorch_info()
    if pt_info['available']:
        print(f"  版本: {pt_info['version']}")
        print(f"  推荐设备: {pt_info['device'].upper()}")

        if pt_info['cuda_available']:
            print(f"\n  ✅ CUDA 加速可用")
            print(f"    CUDA 版本: {pt_info['cuda_version']}")
            print(f"    cuDNN 版本: {pt_info['cudnn_version']}")
            print(f"    GPU 数量: {pt_info['gpu_count']}")
            print(f"    GPU 型号: {pt_info['gpu_name']}")
        else:
            print(f"  ❌ CUDA 加速不可用")

        if pt_info['mps_available']:
            print(f"\n  ✅ MPS 加速可用 (Apple Silicon)")
            print(f"    MPS 构建: {pt_info['mps_built']}")
        else:
            print(f"  ❌ MPS 加速不可用")
    else:
        print("  ⚠️  PyTorch 未安装")

    print("=" * 60)


def get_recommended_module():
    """根据平台返回推荐的模块名称"""
    if is_mac():
        return {
            'rag_system': 'app.utils.rag_system_mac',
            'video_processing': 'app.tasks.video_processing_mac',
            'suffix': '_mac',
        }
    else:
        return {'rag_system': 'app.utils.rag_system', 'video_processing': 'app.tasks.video_processing', 'suffix': ''}


def import_rag_system():
    """自动导入适合当前平台的 RAG 系统"""
    modules = get_recommended_module()

    try:
        if is_mac():
            from app.utils.rag_system_mac import RAGSystem

            logger.info(f"✅ 已加载 Mac 优化版 RAG 系统")
        else:
            from app.utils.rag_system import RAGSystem

            logger.info(f"✅ 已加载标准版 RAG 系统")

        return RAGSystem
    except ImportError as e:
        logger.error(f"❌ 导入 RAG 系统失败: {e}")
        # 尝试导入标准版作为备用
        try:
            from app.utils.rag_system import RAGSystem

            logger.warning("⚠️  使用标准版 RAG 系统作为备用")
            return RAGSystem
        except ImportError:
            raise


def import_video_processing():
    """自动导入适合当前平台的视频处理模块"""
    try:
        if is_mac():
            from app.tasks.video_processing_mac import process_video

            logger.info(f"✅ 已加载 Mac 优化版视频处理")
        else:
            from app.tasks.video_processing import process_video

            logger.info(f"✅ 已加载标准版视频处理")

        return process_video
    except ImportError as e:
        logger.error(f"❌ 导入视频处理模块失败: {e}")
        # 尝试导入标准版作为备用
        try:
            from app.tasks.video_processing import process_video

            logger.warning("⚠️  使用标准版视频处理作为备用")
            return process_video
        except ImportError:
            raise


# 模块级别的便捷变量
DEVICE = get_device()
IS_MAC = is_mac()
IS_WINDOWS = is_windows()
IS_LINUX = is_linux()
IS_APPLE_SILICON = is_apple_silicon()


if __name__ == "__main__":
    # 命令行运行时打印系统信息
    print_system_info()

    print("\n" + "=" * 60)
    print("📦 推荐模块")
    print("=" * 60)

    modules = get_recommended_module()
    print(f"  RAG 系统: {modules['rag_system']}")
    print(f"  视频处理: {modules['video_processing']}")
    print("=" * 60)
