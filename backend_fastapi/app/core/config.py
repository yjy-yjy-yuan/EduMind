"""配置管理 - 使用 Pydantic Settings"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List
from typing import Set
from typing import Union

from pydantic import field_validator
from pydantic_settings import BaseSettings

ENV_FILE_PATH = str(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    """应用配置"""

    # 环境配置 (local/development/production)
    APP_ENV: str = "local"

    # 应用配置
    APP_NAME: str = "AI-EdVision"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 2004  # FastAPI 端口
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    AUTO_CREATE_TABLES: bool = False

    # 数据库配置 (MySQL)
    DATABASE_URL: str = "mysql+pymysql://root:password@127.0.0.1:3306/edumind"

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # LLM API 配置 (通义千问/OpenAI兼容)
    # 注意: 敏感密钥请在 .env 文件中配置，不要硬编码
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_API_KEY: str = ""
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Ollama 配置
    OLLAMA_BASE_URL: str = "http://localhost:11434/api"
    OLLAMA_MODEL: str = "qwen3:8b"

    # 文件上传配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_FOLDER: str = ""
    SUBTITLE_FOLDER: str = ""
    PREVIEW_FOLDER: str = ""
    TEMP_FOLDER: str = ""
    MAX_CONTENT_LENGTH: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: Set[str] = {"mp4", "avi", "mov", "mkv", "webm", "flv"}

    # Whisper 配置 (可选: tiny, base, small, medium, large, turbo)
    WHISPER_MODEL: str = "turbo"
    WHISPER_MODEL_PATH: str = os.path.expanduser("~/Desktop/File/graduation/whisper")

    # CORS 配置 (允许前端访问) - 使用字符串，支持逗号分隔
    CORS_ORIGINS: Union[str, List[str]] = (
        "null,http://localhost:328,http://127.0.0.1:328,http://localhost:5173,http://127.0.0.1:5173"
    )

    # Redis 配置 (可选，保留用于生产环境)
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS_ORIGINS，支持逗号分隔的字符串或列表"""
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        else:
            origins = list(v)
        if "null" not in origins:
            origins.append("null")
        return origins

    class Config:
        env_file = ENV_FILE_PATH
        case_sensitive = True
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置文件夹路径
        if not self.UPLOAD_FOLDER:
            self.UPLOAD_FOLDER = os.path.join(self.BASE_DIR, "uploads")
        if not self.SUBTITLE_FOLDER:
            self.SUBTITLE_FOLDER = os.path.join(self.UPLOAD_FOLDER, "subtitles")
        if not self.PREVIEW_FOLDER:
            self.PREVIEW_FOLDER = os.path.join(self.BASE_DIR, "previews")
        if not self.TEMP_FOLDER:
            self.TEMP_FOLDER = os.path.join(self.BASE_DIR, "temp")


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
