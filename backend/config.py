# 功能：配置项目的环境变量

import os
from dotenv import load_dotenv

# 加载环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))  # 默认端口设置为5001
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Qw242015@localhost/ai_edvision')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Neo4j配置
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
    
    # 通义千问API配置
    QWEN_API_KEY = os.getenv('QWEN_API_KEY')
    QWEN_API_BASE = os.getenv('QWEN_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 限制上传大小为500MB
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    
    # Whisper模型配置
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')
    
    # Celery配置
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'Asia/Shanghai'
    enable_utc = True
    task_track_started = True
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        # 确保上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
