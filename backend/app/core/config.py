"""FastAPI应用配置"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    # 基础配置
    APP_NAME: str = "EduMind"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 5001

    # 安全配置
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # 数据库配置
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'sqlite:///./app.db')
    SQLALCHEMY_ECHO: bool = False

    # Redis配置 (用于Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # 文件上传配置
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    PREVIEW_FOLDER: Path = BASE_DIR / "previews"
    SUBTITLE_FOLDER: Path = BASE_DIR / "subtitles"
    TEMP_FOLDER: Path = BASE_DIR / "temp"
    CACHE_FOLDER: Path = UPLOAD_FOLDER / "cache"
    MAX_CONTENT_LENGTH: int = 500 * 1024 * 1024  # 500MB

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # Neo4j配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "cjx20040328"

    # LLM API配置
    QWEN_API_KEY: Optional[str] = os.environ.get('QWEN_API_KEY')
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def init_directories():
    """初始化必要的目录"""
    directories = [
        settings.UPLOAD_FOLDER,
        settings.PREVIEW_FOLDER,
        settings.SUBTITLE_FOLDER,
        settings.TEMP_FOLDER,
        settings.CACHE_FOLDER,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
