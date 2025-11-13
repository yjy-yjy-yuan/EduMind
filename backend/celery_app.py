# 功能：创建和配置 Celery 实例，用于处理异步任务

from celery import Celery
from app import create_app
import platform

# 创建Flask应用实例
flask_app = create_app()

# 根据平台自动选择要导入的任务模块
# Mac 系统使用 MPS 优化版本，其他系统使用标准版本
task_modules = ['app.tasks.audio_processing']

if platform.system() == "Darwin":  # Mac
    # 同时导入两个版本，确保兼容性
    task_modules.extend([
        'app.tasks.video_processing',      # 标准版本（兼容性）
        'app.tasks.video_processing_mac'   # Mac MPS 优化版本
    ])
    print("🍎 Celery 配置: 使用 Mac MPS 优化版本")
else:
    # Windows/Linux 使用标准版本
    task_modules.append('app.tasks.video_processing')
    print("💻 Celery 配置: 使用标准版本")

# 创建Celery实例
celery = Celery(
    'app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=task_modules
)

# 🔥 关键：在应用上下文中显式导入任务模块以注册Celery任务
with flask_app.app_context():
    # 导入所有任务模块
    from app.tasks import subtitle_tasks
    from app.tasks import test
    
    # 根据平台导入相应的视频处理任务
    if platform.system() == "Darwin":  # Mac
        from app.tasks import video_processing_mac
        print("✅ 已导入 Mac 视频处理任务模块")
    else:  # Windows/Linux
        from app.tasks import video_processing
        print("✅ 已导入标准视频处理任务模块")

# 更新Celery配置
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=10800,  # 3小时硬超时 (中大型模型需要更长时间)
    worker_max_tasks_per_child=5,  # 减少到5个任务后重启worker,防止内存泄漏
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_transport_options={'visibility_timeout': 10800},  # 与任务超时保持一致
    task_soft_time_limit=10500,  # 软超时限制 (2.9小时)
    task_acks_late=True,  # 任务完成后再确认
    task_reject_on_worker_lost=True,  # 工作进程丢失时拒绝任务
    task_default_retry_delay=60,  # 默认重试延迟
    task_max_retries=2,  # 最大重试次数 (降低避免反复失败)
    
    # 🔥 关键修复：Mac 使用 solo 模式避免 MPS 设备 fork 崩溃
    # fork 模式在子进程中使用 MPS/CUDA 会导致 SIGSEGV
    worker_pool='solo' if platform.system() == "Darwin" else 'prefork',
    
    # 任务结果过期时间
    result_expires=3600,  # 1小时后清理任务结果
)

# Mac 系统额外配置说明
if platform.system() == "Darwin":
    print("⚠️  Mac 模式: 使用 solo pool (单进程) 避免 MPS fork 崩溃")
    print("💡 如需并发处理，建议启动多个 Celery worker 实例")
    print("⏱️  任务超时: 3小时 (适配大模型处理)")

# 将Flask应用上下文推送到Celery
class FlaskTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery.Task = FlaskTask
