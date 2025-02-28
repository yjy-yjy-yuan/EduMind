from celery import shared_task
import time

@shared_task
def add(x, y):
    """测试任务：简单的加法"""
    time.sleep(2)  # 模拟耗时操作
    return x + y
