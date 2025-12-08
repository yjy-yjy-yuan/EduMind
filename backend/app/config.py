"""Flask应用配置"""

import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery配置
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'Asia/Shanghai'
    task_time_limit = 30 * 60  # 30分钟
    broker_connection_retry_on_startup = True  # 添加此配置

    # 文件上传配置
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PREVIEW_FOLDER = os.path.join(BASE_DIR, 'previews')
    SUBTITLE_FOLDER = os.path.join(BASE_DIR, 'subtitles')
    TEMP_FOLDER = os.path.join(BASE_DIR, 'temp')

    # CORS配置
    CORS_HEADERS = [
        'Content-Type',
        'Authorization',
        'X-Requested-With',
        'Accept',
        'Origin',
        'Access-Control-Request-Method',
        'Access-Control-Request-Headers',
    ]

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 创建必要的目录
        required_dirs = [
            app.config['UPLOAD_FOLDER'],
            app.config['PREVIEW_FOLDER'],
            app.config['SUBTITLE_FOLDER'],
            app.config['TEMP_FOLDER'],
        ]

        for directory in required_dirs:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    logger.info(f'创建目录: {directory}')
            except Exception as e:
                logger.error(f'创建目录失败 {directory}: {str(e)}')
                raise


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    DEBUG = False
    # 生产环境特定配置
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
