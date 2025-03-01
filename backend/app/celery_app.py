"""Celery配置"""
from celery import Celery

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
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=7200,  # 2小时超时
        task_soft_time_limit=7000,  # 软超时限制
        worker_max_tasks_per_child=10,  # 每个worker处理10个任务后重启，防止内存泄漏
        worker_prefetch_multiplier=1,  # 减少预取任务数量，避免任务分配不均
        broker_transport_options={'visibility_timeout': 7200},  # 与task_time_limit保持一致
    )
    
    class ContextTask(celery.Task):
        abstract = True
        
        def __call__(self, *args, **kwargs):
            from app import create_app
            flask_app = create_app()
            with flask_app.app_context():
                return super().__call__(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# 创建Celery实例
celery = create_celery_app()
