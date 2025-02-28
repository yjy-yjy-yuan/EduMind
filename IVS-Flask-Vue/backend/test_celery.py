# 功能：测试Celery是否正常工作

from app.tasks.test import add
from celery.result import AsyncResult
import time

def test_celery():
    print("正在测试 Celery...")
    
    # 发送测试任务
    result = add.delay(4, 4)
    
    print(f"任务ID: {result.id}")
    print("等待任务完成...")
    
    # 等待任务完成
    while not result.ready():
        time.sleep(0.5)
        print("任务状态:", result.state)
    
    # 获取结果
    if result.successful():
        print("任务成功完成！")
        print("结果:", result.get())
    else:
        print("任务失败:", result.get(propagate=False))

if __name__ == '__main__':
    test_celery()
