"""扩展模块配置"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from celery import Celery

# 所有扩展已移至__init__.py
# 这个文件保留用于未来可能的扩展

# 初始化数据库
db = SQLAlchemy()

# 初始化数据库迁移
migrate = Migrate()

# 初始化CORS
cors = CORS()

# 初始化Celery
celery = Celery(
    'app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['app.tasks.video_processing']
)

# Celery配置
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)
