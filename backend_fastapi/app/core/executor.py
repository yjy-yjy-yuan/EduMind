"""后台任务执行器 - 使用 ProcessPoolExecutor 替代 Celery"""

import atexit
import logging
from concurrent.futures import Future
from concurrent.futures import ProcessPoolExecutor
from typing import Any
from typing import Callable
from typing import Dict

logger = logging.getLogger(__name__)

# 全局进程池（用于 CPU 密集型任务如视频处理）
_executor: ProcessPoolExecutor = None

# 存储正在运行的任务
_running_tasks: Dict[int, Future] = {}


def get_executor() -> ProcessPoolExecutor:
    """获取全局进程池实例"""
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(max_workers=2)
        logger.info("进程池初始化完成 (max_workers=2)")
        # 注册退出时清理
        atexit.register(shutdown_executor)
    return _executor


def shutdown_executor():
    """关闭进程池"""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        logger.info("进程池已关闭")
        _executor = None


def submit_task(task_func: Callable, *args, **kwargs) -> Future:
    """
    提交后台任务

    Args:
        task_func: 要执行的函数（必须是可序列化的顶层函数）
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Future 对象，可用于查询任务状态
    """
    executor = get_executor()
    future = executor.submit(task_func, *args, **kwargs)
    logger.info(f"任务已提交: {task_func.__name__}")
    return future


def get_task_status(video_id: int) -> dict:
    """
    获取任务状态（从数据库读取）

    由于使用数据库存储状态，任务进度直接从 Video 模型读取
    """
    from app.core.database import SessionLocal
    from app.models.video import Video

    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            return {
                "status": video.status.value if hasattr(video.status, "value") else video.status,
                "progress": video.process_progress,
                "current_step": video.current_step,
            }
        return {"status": "not_found", "progress": 0, "current_step": ""}
    finally:
        db.close()
