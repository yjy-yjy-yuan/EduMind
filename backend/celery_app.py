# 功能：创建和配置 Celery 实例，用于处理异步任务

from celery import Celery
from app import create_app

# 创建Flask应用实例
flask_app = create_app()

# 创建Celery实例
celery = Celery(
    'app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['app.tasks.video_processing', 'app.tasks.audio_processing']
)

# 更新Celery配置
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_max_tasks_per_child=50,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True
)

# 将Flask应用上下文推送到Celery
class FlaskTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery.Task = FlaskTask
