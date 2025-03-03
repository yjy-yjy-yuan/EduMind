"""Celery配置"""
from celery import Celery
from flask import current_app

def create_celery_app():
    """创建Celery应用"""
    celery = Celery(
        'app',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0',
        include=['app.tasks.video_processing']
    )
    
    # 更新Celery配置
    celery.conf.update(
        # 基本配置
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,
        
        # 任务跟踪和超时设置
        task_track_started=True,
        task_time_limit=7200,  # 2小时超时
        task_soft_time_limit=7000,  # 软超时限制
        
        # Worker 配置
        worker_max_tasks_per_child=10,  # 每个worker处理10个任务后重启，防止内存泄漏
        worker_prefetch_multiplier=1,  # 减少预取任务数量，避免任务分配不均
        worker_max_memory_per_child=2000000,  # 2GB内存限制
        
        # 任务重试设置
        task_acks_late=True,  # 任务完成后再确认
        task_reject_on_worker_lost=True,  # worker异常终止时重试任务
        
        # 性能优化
        worker_proc_alive_timeout=60.0,  # worker进程存活超时时间
        worker_pool_restarts=True,  # 允许重启worker池
        
        # Broker 配置
        broker_transport_options={
            'visibility_timeout': 7200,  # 与task_time_limit保持一致
            'max_retries': 3,  # 连接重试次数
            'interval_start': 0,  # 重试间隔起始时间
            'interval_step': 0.2,  # 重试间隔步长
            'interval_max': 0.5,  # 最大重试间隔
        },
        broker_connection_retry=True,  # 允许broker连接重试
        broker_connection_retry_on_startup=True,  # 启动时允许broker连接重试
        broker_connection_max_retries=None,  # 无限重试直到连接成功
        
        # 结果后端配置
        result_expires=7200,  # 结果过期时间
        result_cache_max=10000,  # 结果缓存上限
    )
    
    class ContextTask(celery.Task):
        abstract = True
        
        def __call__(self, *args, **kwargs):
            if not current_app:
                from app import create_app
                flask_app = create_app()
                with flask_app.app_context():
                    return super().__call__(*args, **kwargs)
            return super().__call__(*args, **kwargs)
        
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            """任务失败处理"""
            from ..models.video import Video, VideoStatus
            if args and isinstance(args[0], int):
                video_id = args[0]
                with create_app().app_context():
                    video = Video.query.get(video_id)
                    if video:
                        video.status = VideoStatus.ERROR
                        video.error_message = str(exc)
                        db.session.commit()
    
    celery.Task = ContextTask
    return celery

# 创建Celery实例
celery = create_celery_app()
