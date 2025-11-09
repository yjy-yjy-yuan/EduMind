#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery 任务注册测试脚本
验证所有任务是否正确注册到 Celery
"""

import sys
import platform
from celery_app import celery

print("=" * 70)
print("🔍 Celery 任务注册检查")
print("=" * 70)

# 显示系统信息
print(f"\n📱 系统信息:")
print(f"  平台: {platform.system()}")
print(f"  架构: {platform.machine()}")

# 显示 Celery 配置
print(f"\n⚙️  Celery 配置:")
print(f"  Broker: {celery.conf.broker_url}")
print(f"  Backend: {celery.conf.result_backend}")

# 获取所有注册的任务
print(f"\n📦 已注册的任务:")
registered_tasks = sorted(celery.tasks.keys())

for task in registered_tasks:
    if not task.startswith('celery.'):  # 过滤掉 Celery 内置任务
        print(f"  ✅ {task}")

# 检查关键任务 (根据平台选择正确的任务版本)
if platform.system() == "Darwin":  # Mac
    print(f"\n🎯 关键任务检查 (Mac MPS 优化版本):")
    critical_tasks = [
        'app.tasks.video_processing_mac.process_video',
        'app.tasks.video_processing_mac.cleanup_video',
    ]
else:  # Windows/Linux
    print(f"\n🎯 关键任务检查 (标准版本):")
    critical_tasks = [
        'app.tasks.video_processing.process_video',
        'app.tasks.video_processing.cleanup_video',
    ]

all_passed = True
for task_name in critical_tasks:
    if task_name in celery.tasks:
        print(f"  ✅ {task_name}")
    else:
        print(f"  ❌ {task_name} - 未注册")
        all_passed = False

# 统计
print(f"\n📊 统计:")
user_tasks = [t for t in registered_tasks if not t.startswith('celery.')]
print(f"  总任务数: {len(registered_tasks)}")
print(f"  用户任务数: {len(user_tasks)}")
print(f"  内置任务数: {len(registered_tasks) - len(user_tasks)}")

# 结果
print("\n" + "=" * 70)
if all_passed:
    print("✅ 所有关键任务已正确注册！")
    print("=" * 70)
    sys.exit(0)
else:
    print("❌ 部分任务未注册，请检查配置！")
    print("=" * 70)
    sys.exit(1)
