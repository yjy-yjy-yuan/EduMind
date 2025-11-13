#!/usr/bin/env python
"""
测试 MPS + Whisper 兼容性
验证 PyTorch 2.0.0 的 MPS 是否能正常工作
"""

import torch
import whisper
import os
import sys

def test_torch_mps():
    """测试 PyTorch MPS 支持"""
    print("=" * 60)
    print("🔍 PyTorch 环境检测")
    print("=" * 60)
    
    print(f"✓ PyTorch 版本: {torch.__version__}")
    print(f"✓ Python 版本: {sys.version.split()[0]}")
    
    # 检查 MPS 支持
    print(f"\n📱 MPS 支持检测:")
    print(f"  - torch.backends.mps 存在: {hasattr(torch.backends, 'mps')}")
    if hasattr(torch.backends, 'mps'):
        print(f"  - MPS 可用: {torch.backends.mps.is_available()}")
        print(f"  - MPS 内置: {torch.backends.mps.is_built()}")
    
    # 检查 torch.mps 模块
    print(f"\n🧹 缓存清理功能:")
    print(f"  - torch.mps 模块存在: {hasattr(torch, 'mps')}")
    if hasattr(torch, 'mps'):
        print(f"  - torch.mps.empty_cache 存在: {hasattr(torch.mps, 'empty_cache')}")
    else:
        print(f"  ⚠️  torch.mps 不存在 - 将使用 gc.collect() 代替")
    
    print("\n" + "=" * 60)

def test_mps_tensor():
    """测试 MPS tensor 操作"""
    print("🧪 测试 MPS Tensor 操作")
    print("=" * 60)
    
    if not torch.backends.mps.is_available():
        print("❌ MPS 不可用,跳过测试")
        return False
    
    try:
        # 创建简单的 tensor 操作
        print("创建 MPS tensor...")
        x = torch.randn(100, 100).to('mps')
        y = torch.randn(100, 100).to('mps')
        
        print("执行矩阵运算...")
        z = torch.matmul(x, y)
        
        print("✅ MPS tensor 操作成功!")
        
        # 测试缓存清理
        print("\n测试缓存清理...")
        if hasattr(torch, 'mps') and hasattr(torch.mps, 'empty_cache'):
            torch.mps.empty_cache()
            print("✅ torch.mps.empty_cache() 成功")
        else:
            import gc
            gc.collect()
            print("✅ gc.collect() 成功 (torch.mps.empty_cache 不可用)")
        
        return True
    except Exception as e:
        print(f"❌ MPS tensor 操作失败: {str(e)}")
        return False
    
    print("\n" + "=" * 60)

def test_whisper_model():
    """测试 Whisper 模型加载"""
    print("🎤 测试 Whisper 模型加载")
    print("=" * 60)
    
    try:
        # 使用自定义路径
        custom_model_path = os.path.expanduser("~/Desktop/File/graduation/whisper")
        model_name = "base"
        
        print(f"模型路径: {custom_model_path}")
        print(f"模型名称: {model_name}")
        
        # 检查模型文件是否存在
        model_file = os.path.join(custom_model_path, f"{model_name}.pt")
        if os.path.exists(model_file):
            print(f"✓ 模型文件存在: {model_file}")
            size_mb = os.path.getsize(model_file) / (1024**2)
            print(f"  文件大小: {size_mb:.1f} MB")
        else:
            print(f"⚠️  模型文件不存在,将从网络下载")
        
        # 加载模型
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"\n加载模型到设备: {device}")
        
        model = whisper.load_model(
            model_name,
            device=device,
            download_root=custom_model_path
        )
        
        print("✅ 模型加载成功!")
        
        # 清理
        del model
        if hasattr(torch, 'mps') and hasattr(torch.mps, 'empty_cache'):
            torch.mps.empty_cache()
        else:
            import gc
            gc.collect()
        
        print("✅ 模型清理成功!")
        
        return True
    except Exception as e:
        print(f"❌ Whisper 模型加载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)

def main():
    """运行所有测试"""
    print("\n🚀 开始 MPS + Whisper 兼容性测试\n")
    
    # 测试 1: PyTorch MPS 支持
    test_torch_mps()
    
    # 测试 2: MPS tensor 操作
    print()
    if test_mps_tensor():
        print()
        # 测试 3: Whisper 模型加载
        test_whisper_model()
    
    print("\n✅ 所有测试完成!")
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("  - 如果所有测试都通过,说明环境配置正确")
    print("  - 如果 torch.mps.empty_cache 不可用,会自动使用 gc.collect()")
    print("  - 建议升级到 PyTorch 2.1+ 获得更好的 MPS 支持")
    print("=" * 60)

if __name__ == "__main__":
    main()
