import platform
import time

import torch

print("=" * 60)
print("🚀 M4 芯片 PyTorch 验证（改进版）")
print("=" * 60)

# 系统信息
print(f"\n📱 系统信息:")
print(f"  芯片: {platform.machine()}")
print(f"  系统: {platform.system()} {platform.release()}")
print(f"  Python: {platform.python_version()}")

# PyTorch 信息
print(f"\n🔥 PyTorch 信息:")
print(f"  版本: {torch.__version__}")
print(f"  MPS 构建: {torch.backends.mps.is_built()}")
print(f"  MPS 可用: {torch.backends.mps.is_available()}")

# 推荐设备
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(f"  ✅ 推荐设备: MPS (Apple GPU)")
else:
    device = torch.device("cpu")
    print(f"  ⚠️  推荐设备: CPU")

# 基础测试
print(f"\n🧪 基础测试:")
try:
    # CPU 测试
    x_cpu = torch.rand(3, 3)
    y_cpu = torch.rand(3, 3)
    z_cpu = x_cpu + y_cpu
    print(f"  ✅ CPU 运算正常")

    # MPS 测试
    if torch.backends.mps.is_available():
        x_mps = torch.rand(3, 3).to('mps')
        y_mps = torch.rand(3, 3).to('mps')
        z_mps = x_mps + y_mps
        print(f"  ✅ MPS 运算正常")

        # 神经网络测试
        model = torch.nn.Linear(10, 5).to('mps')
        input_data = torch.randn(32, 10).to('mps')
        output = model(input_data)
        print(f"  ✅ MPS 神经网络正常")

        # 测试将结果移回 CPU
        output_cpu = output.cpu()
        print(f"  ✅ MPS -> CPU 数据传输正常")

except Exception as e:
    print(f"  ❌ 错误: {e}")

# 性能测试（改进版，兼容 PyTorch 2.0.0）
print(f"\n⚡ 性能测试 (矩阵乘法 5000x5000):")


def benchmark(device_name, runs=5):
    """性能基准测试（兼容版本）"""
    device = torch.device(device_name)
    size = 5000

    # 创建随机矩阵
    x = torch.randn(size, size).to(device)
    y = torch.randn(size, size).to(device)

    # 预热
    _ = torch.matmul(x, y)
    if device_name == "mps":
        # 在 MPS 上确保操作完成
        _ = _.cpu()

    # 计时
    start = time.time()
    for _ in range(runs):
        result = torch.matmul(x, y)
        if device_name == "mps":
            # 将结果移到 CPU 以确保操作完成
            _ = result.cpu()
    end = time.time()

    avg_time = (end - start) / runs
    return avg_time


try:
    print(f"  正在测试 CPU 性能...")
    cpu_time = benchmark("cpu", runs=3)
    print(f"  CPU: {cpu_time:.3f} 秒/次")

    if torch.backends.mps.is_available():
        print(f"  正在测试 MPS 性能...")
        mps_time = benchmark("mps", runs=3)
        speedup = cpu_time / mps_time
        print(f"  MPS: {mps_time:.3f} 秒/次")
        print(f"  🚀 M4 加速比: {speedup:.2f}x")

        if speedup > 1:
            print(f"  ✅ MPS 比 CPU 快 {speedup:.2f} 倍！")
        else:
            print(f"  ⚠️  对于小规模运算，CPU 可能更快")

except Exception as e:
    print(f"  ⚠️  性能测试失败: {e}")

# 额外的实用测试
print(f"\n🔬 实用功能测试:")
try:
    if torch.backends.mps.is_available():
        # 测试梯度计算
        x = torch.randn(10, 5, requires_grad=True).to('mps')
        y = x.sum()
        y.backward()
        print(f"  ✅ MPS 梯度计算正常")

        # 测试卷积操作
        conv = torch.nn.Conv2d(3, 16, 3).to('mps')
        img = torch.randn(1, 3, 32, 32).to('mps')
        out = conv(img)
        print(f"  ✅ MPS 卷积运算正常")

        # 测试批归一化
        bn = torch.nn.BatchNorm2d(16).to('mps')
        out = bn(out)
        print(f"  ✅ MPS 批归一化正常")

except Exception as e:
    print(f"  ⚠️  某些操作可能不支持: {e}")

print("\n" + "=" * 60)
print("✅ M4 芯片 PyTorch 环境完全就绪！")
print("💡 提示: 在训练时使用 .to('mps') 将模型和数据移到 GPU")
print("=" * 60)
