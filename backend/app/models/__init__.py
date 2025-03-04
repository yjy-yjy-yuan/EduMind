"""
数据库模型
"""
from flask_sqlalchemy import SQLAlchemy

# 创建SQLAlchemy实例
db = SQLAlchemy()

from .video import Video
from .subtitle import Subtitle

__all__ = ['db', 'Video', 'Subtitle']
