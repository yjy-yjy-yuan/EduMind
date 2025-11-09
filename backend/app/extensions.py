"""扩展模块配置"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from celery import Celery
import platform

# 所有扩展已移至__init__.py
# 这个文件保留用于未来可能的扩展

# 初始化数据库
db = SQLAlchemy()

# 初始化数据库迁移
migrate = Migrate()

# 初始化CORS
cors = CORS()

# 根据平台自动选择要导入的任务模块
task_modules = []

if platform.system() == "Darwin":  # Mac
    # Mac 系统同时导入两个版本，确保兼容性
    task_modules = [
        'app.tasks.video_processing',      # 标准版本（兼容性）
        'app.tasks.video_processing_mac'   # Mac MPS 优化版本
    ]
else:
    # Windows/Linux 使用标准版本
    task_modules = ['app.tasks.video_processing']

# 初始化Celery
celery = Celery(
    'app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=task_modules
)

# Celery配置
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)
