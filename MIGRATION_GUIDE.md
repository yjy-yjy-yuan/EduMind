# Flask to FastAPI 迁移指南

> AI-EdVision 项目从 Flask 迁移到 FastAPI 的完整指导文档

## 目录

1. [迁移概述](#1-迁移概述)
2. [技术栈对比](#2-技术栈对比)
3. [准备工作](#3-准备工作)
4. [Phase 1: 基础设施搭建](#4-phase-1-基础设施搭建)
5. [Phase 2: 模型层迁移](#5-phase-2-模型层迁移)
6. [Phase 3: 路由层迁移](#6-phase-3-路由层迁移)
7. [Phase 4: 后台任务处理](#7-phase-4-后台任务处理)
   - [方案 A: 简化方案 (推荐毕设)](#方案-a-简化方案-推荐毕设)
   - [方案 B: Celery 方案 (生产环境)](#方案-b-celery-方案-生产环境)
8. [Phase 5: 测试迁移](#8-phase-5-测试迁移)
9. [迁移检查清单](#9-迁移检查清单)
10. [常见问题](#10-常见问题)

---

## 1. 迁移概述

### 1.1 为什么迁移到 FastAPI？

| 收益 | 说明 |
|------|------|
| **性能提升** | 原生 async/await，并发处理能力更强 |
| **自动 API 文档** | Swagger UI + ReDoc 自动生成 |
| **类型安全** | Pydantic 自动验证请求/响应 |
| **流式响应** | 原生 `StreamingResponse`，适合 Q&A 系统 |
| **现代化** | Python 类型提示，代码更易维护 |

### 1.2 迁移范围

```
需要迁移:
├── app/__init__.py          → main.py (应用入口)
├── app/routes/*.py          → app/routers/*.py (路由)
├── app/models/*.py          → app/models/*.py + app/schemas/*.py
├── app/extensions.py        → app/core/database.py
├── config.py                → app/core/config.py
└── tests/                   → tests/ (测试框架更换)

保持不变:
├── app/utils/*.py           → 工具类基本不变
├── app/services/*.py        → 服务层基本不变
└── 外部依赖                  → Neo4j, Whisper 不变

移除 (简化方案):
├── Celery                   → 用 ProcessPoolExecutor 替代
└── Redis                    → 不再需要，任务状态存数据库
```


## 2. 技术栈对比

### 2.1 依赖变更

```txt
# 移除的依赖
- Flask==3.0.2
- Flask-SQLAlchemy==3.1.1
- Flask-Migrate==4.0.5
- Flask-CORS==4.0.0
- celery==5.4.0          # 简化方案移除
- redis==5.0.1           # 简化方案移除

# 新增的依赖
+ fastapi==0.109.0
+ uvicorn[standard]==0.27.0
+ sqlalchemy==2.0.25
+ alembic==1.13.1
+ pydantic==2.5.3
+ pydantic-settings==2.1.0
+ python-multipart==0.0.6  # 文件上传

# 保持不变
neo4j==5.17.0
openai-whisper==20240930
# ... 其他依赖
```

### 2.2 核心概念映射

| Flask | FastAPI | 说明 |
|-------|---------|------|
| `Blueprint` | `APIRouter` | 路由组织方式 |
| `@app.route()` | `@router.get/post()` | 路由装饰器 |
| `request.get_json()` | Pydantic Model 参数 | 请求体解析 |
| `jsonify()` | `response_model` | 响应序列化 |
| `current_app` | 依赖注入 | 应用上下文 |
| `g` | 依赖注入 | 请求级别共享 |
| `before_request` | 中间件 / 依赖 | 请求前处理 |
| `Flask-SQLAlchemy` | SQLAlchemy 2.0 | ORM |

---

## 3. 准备工作

### 3.1 创建新的目录结构

```bash
# 在 backend 目录下创建新结构
mkdir -p backend_fastapi/{app/{routers,models,schemas,core,utils,services,tasks},tests/{unit,integration,api}}
```

**目标目录结构：**

```
backend_fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理 (Pydantic Settings)
│   │   ├── database.py         # 数据库连接
│   │   └── executor.py         # 后台任务执行器 (替代 Celery)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── video.py
│   │   ├── subtitle.py
│   │   ├── note.py
│   │   ├── user.py
│   │   └── qa.py
│   ├── schemas/                # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── video.py
│   │   ├── subtitle.py
│   │   ├── note.py
│   │   └── qa.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── video.py
│   │   ├── subtitle.py
│   │   ├── note.py
│   │   ├── qa.py
│   │   ├── chat.py
│   │   ├── auth.py
│   │   └── knowledge_graph.py
│   ├── services/               # 业务逻辑 (从原项目复制)
│   ├── tasks/                  # Celery 任务 (从原项目复制)
│   ├── utils/                  # 工具类 (从原项目复制)
│   └── dependencies.py         # 依赖注入
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── api/
├── alembic/                    # 数据库迁移
├── alembic.ini
├── requirements.txt
├── .env
└── run.py
```

### 3.2 安装依赖

```bash
# 创建新的 requirements.txt
cat > backend_fastapi/requirements.txt << 'EOF'
# FastAPI 核心
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# 数据库
sqlalchemy==2.0.25
alembic==1.13.1
pymysql==1.1.0

# 验证和配置
pydantic==2.5.3
pydantic-settings==2.1.0

# AI/ML (保持不变)
openai-whisper==20240930
torch==2.0.0
sentence-transformers==3.4.1
faiss-cpu==1.8.0

# 知识图谱
neo4j==5.17.0

# 工具
python-dotenv==1.0.0
yt-dlp==2024.3.10
opencv-python==4.9.0.80
pydub==0.25.1
jieba==0.42.1
scikit-learn==1.4.0

# 测试
pytest==8.0.0
pytest-asyncio==0.23.3
httpx==0.26.0
EOF

# 安装依赖
cd backend_fastapi
pip install -r requirements.txt
```

---

## 4. Phase 1: 基础设施搭建

### 4.1 配置管理 (Pydantic Settings)

**文件：`app/core/config.py`**

```python
"""配置管理 - 使用 Pydantic Settings"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "AI-EdVision"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 2004
    SECRET_KEY: str = "your-secret-key"

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost/ai_edvision"

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # LLM API 配置
    QWEN_API_KEY: str = ""
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Ollama 配置
    OLLAMA_BASE_URL: str = "http://localhost:11434/api"
    OLLAMA_MODEL: str = "qwen3:8b"

    # 文件上传配置
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    SUBTITLE_FOLDER: str = os.path.join(UPLOAD_FOLDER, "subtitles")
    MAX_CONTENT_LENGTH: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: set = {"mp4", "avi", "mov", "mkv", "webm"}

    # Whisper 配置
    WHISPER_MODEL: str = "base"
    WHISPER_MODEL_PATH: str = os.path.expanduser("~/Desktop/File/graduation/whisper")

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
```

### 4.2 数据库连接

**文件：`app/core/database.py`**

```python
"""数据库连接配置"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 Base 类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话 (依赖注入)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4.3 后台任务执行器 (替代 Celery)

**文件：`app/core/executor.py`**

```python
"""后台任务执行器 - 使用 ProcessPoolExecutor 替代 Celery"""
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Dict, Callable, Any
import logging
import atexit

logger = logging.getLogger(__name__)

# 全局进程池（用于 CPU 密集型任务如视频处理）
_executor: ProcessPoolExecutor = None

# 存储正在运行的任务
_running_tasks: Dict[int, Future] = {}


def get_executor() -> ProcessPoolExecutor:
    """获取全局进程池实例"""
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(max_workers=2)
        logger.info("✅ 进程池初始化完成 (max_workers=2)")
        # 注册退出时清理
        atexit.register(shutdown_executor)
    return _executor


def shutdown_executor():
    """关闭进程池"""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        logger.info("👋 进程池已关闭")
        _executor = None


def submit_task(task_func: Callable, *args, **kwargs) -> Future:
    """
    提交后台任务

    Args:
        task_func: 要执行的函数（必须是可序列化的顶层函数）
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Future 对象，可用于查询任务状态
    """
    executor = get_executor()
    future = executor.submit(task_func, *args, **kwargs)
    logger.info(f"📤 任务已提交: {task_func.__name__}")
    return future


def get_task_status(video_id: int) -> dict:
    """
    获取任务状态（从数据库读取）

    由于使用数据库存储状态，任务进度直接从 Video 模型读取
    """
    from app.core.database import SessionLocal
    from app.models.video import Video

    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            return {
                "status": video.status.value,
                "progress": video.process_progress,
                "current_step": video.current_step
            }
        return {"status": "not_found", "progress": 0, "current_step": ""}
    finally:
        db.close()
```

### 4.4 FastAPI 主应用

**文件：`app/main.py`**

```python
"""FastAPI 应用入口"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动 AI-EdVision API...")

    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库表创建成功")

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.SUBTITLE_FOLDER, exist_ok=True)
    logger.info(f"✅ 上传目录已就绪: {settings.UPLOAD_FOLDER}")

    yield

    # 关闭时执行
    logger.info("👋 关闭 AI-EdVision API...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="基于深度学习的视频智能伴学系统 API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
from app.routers import video, subtitle, note, qa, chat, auth, knowledge_graph

app.include_router(video.router, prefix="/api/videos", tags=["视频管理"])
app.include_router(subtitle.router, prefix="/api/subtitles", tags=["字幕管理"])
app.include_router(note.router, prefix="/api/notes", tags=["笔记管理"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答系统"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天系统"])
app.include_router(auth.router, prefix="/api/auth", tags=["用户认证"])
app.include_router(knowledge_graph.router, prefix="/api/knowledge-graph", tags=["知识图谱"])


# 根路由
@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Welcome to AI-EdVision API",
        "version": "2.0.0",
        "docs": "/docs"
    }


# 健康检查
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "services": {
            "database": "connected",
            "neo4j": "connected"
        }
    }
```

### 4.5 启动脚本

**文件：`run.py`**

```python
"""应用启动脚本"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
```

---

## 5. Phase 2: 模型层迁移

### 5.1 SQLAlchemy 2.0 模型基类

**文件：`app/models/base.py`**

```python
"""SQLAlchemy 模型基类"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
```

### 5.2 Video 模型迁移示例

**文件：`app/models/video.py`**

```python
"""视频模型 - SQLAlchemy 2.0 版本"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class VideoStatus(str, Enum):
    """视频状态枚举"""
    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DOWNLOADING = "downloading"


class Video(Base, TimestampMixin):
    """视频模型"""
    __tablename__ = "videos"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 基本信息
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filepath: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    md5: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # 处理后的文件
    processed_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    processed_filepath: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preview_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preview_filepath: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subtitle_filepath: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 状态信息
    status: Mapped[VideoStatus] = mapped_column(
        SQLEnum(VideoStatus),
        default=VideoStatus.UPLOADED
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 进度信息
    process_progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 视频属性
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 内容分析
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 字符串

    # 关系
    subtitles: Mapped[List["Subtitle"]] = relationship(
        "Subtitle",
        back_populates="video",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Video {self.title or self.filename}>"
```

### 5.3 Pydantic Schema 定义

**文件：`app/schemas/video.py`**

```python
"""视频 Pydantic Schema"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class VideoStatus(str, Enum):
    """视频状态"""
    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DOWNLOADING = "downloading"


# ============ 请求 Schema ============

class VideoUploadURL(BaseModel):
    """URL 上传请求"""
    url: str = Field(..., description="视频链接 (B站/YouTube/慕课)")


class VideoProcessRequest(BaseModel):
    """视频处理请求"""
    language: str = Field(default="Other", description="视频语言")
    model: str = Field(default="turbo", description="Whisper 模型")


# ============ 响应 Schema ============

class VideoBase(BaseModel):
    """视频基础信息"""
    id: int
    title: Optional[str] = None
    filename: Optional[str] = None
    status: VideoStatus

    model_config = ConfigDict(from_attributes=True)


class VideoUploadResponse(BaseModel):
    """上传响应"""
    id: int
    status: str
    message: str
    duplicate: bool = False
    data: Optional[dict] = None


class VideoDetail(VideoBase):
    """视频详情"""
    filepath: Optional[str] = None
    url: Optional[str] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_count: Optional[int] = None
    preview_filename: Optional[str] = None
    subtitle_filepath: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    upload_time: Optional[datetime] = None
    error_message: Optional[str] = None


class VideoStatus(BaseModel):
    """视频状态响应"""
    id: int
    status: str
    progress: float = 0
    current_step: str = ""
    task_id: Optional[str] = None


class VideoListResponse(BaseModel):
    """视频列表响应"""
    message: str
    videos: List[VideoDetail]
    total: int
    page: int
    per_page: int
    total_pages: int
```

---

## 6. Phase 3: 路由层迁移

### 6.1 Flask vs FastAPI 路由对比

| 功能 | Flask | FastAPI |
|------|-------|---------|
| 路由定义 | `@bp.route('/upload', methods=['POST'])` | `@router.post('/upload')` |
| 获取 JSON | `request.get_json()` | `body: VideoUploadURL` (自动) |
| 获取文件 | `request.files['file']` | `file: UploadFile` |
| 获取参数 | `request.args.get('page')` | `page: int = Query(1)` |
| 路径参数 | `<int:video_id>` | `{video_id}` + 类型注解 |
| 返回 JSON | `jsonify({...})` | 直接返回 dict |
| 流式响应 | `Response(generate())` | `StreamingResponse(generate())` |
| 错误处理 | `return jsonify({'error': ...}), 400` | `raise HTTPException(400, ...)` |

### 6.2 Video 路由迁移示例

**文件：`app/routers/video.py`**

```python
"""视频路由 - FastAPI 版本"""
import os
import hashlib
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    VideoUploadResponse,
    VideoUploadURL,
    VideoDetail,
    VideoProcessRequest,
    VideoListResponse
)
from app.tasks.video_processing_mac import process_video, cleanup_video

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============ 文件上传 ============

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    logger.info(f"收到文件上传请求: {file.filename}")

    # 检查文件类型
    if not file.filename or not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 读取文件内容计算 MD5
    content = await file.read()
    file_md5 = hashlib.md5(content).hexdigest()
    await file.seek(0)  # 重置文件指针

    # 检查重复
    existing_video = db.query(Video).filter(Video.md5 == file_md5).first()
    if existing_video:
        return VideoUploadResponse(
            id=existing_video.id,
            status=existing_video.status.value,
            message="视频已存在",
            duplicate=True
        )

    # 保存文件
    filename = file.filename
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 创建数据库记录
    video = Video(
        filename=filename,
        filepath=file_path,
        title=f"local-{os.path.splitext(filename)[0]}",
        status=VideoStatus.UPLOADED,
        md5=file_md5
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    logger.info(f"视频上传成功: ID={video.id}")

    return VideoUploadResponse(
        id=video.id,
        status="uploaded",
        message="视频上传成功",
        duplicate=False
    )


# ============ URL 上传 ============

@router.post("/upload-url", response_model=VideoUploadResponse)
async def upload_video_url(
    data: VideoUploadURL,  # 自动验证请求体
    db: Session = Depends(get_db)
):
    """通过 URL 上传视频"""
    video_url = data.url
    logger.info(f"处理视频URL: {video_url}")

    # 验证 URL 格式
    is_bilibili = 'bilibili.com' in video_url or 'b23.tv' in video_url
    is_youtube = 'youtube.com' in video_url or 'youtu.be' in video_url
    is_mooc = 'icourse163.org' in video_url

    if not (is_bilibili or is_youtube or is_mooc):
        raise HTTPException(
            status_code=400,
            detail="目前仅支持B站、YouTube和中国大学慕课视频"
        )

    # 创建临时视频记录
    video = Video(
        url=video_url,
        status=VideoStatus.DOWNLOADING
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # TODO: 实现视频下载逻辑 (使用 yt-dlp)
    # 可以参考原 Flask 代码中的下载逻辑

    return VideoUploadResponse(
        id=video.id,
        status="downloading",
        message="视频下载已开始"
    )


# ============ 视频列表 ============

@router.get("/list", response_model=VideoListResponse)
async def get_video_list(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(5, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取视频列表"""
    # 查询视频
    videos = db.query(Video).order_by(Video.created_at.desc()).limit(100).all()

    # 分页
    total = len(videos)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_videos = videos[start_idx:end_idx]

    return VideoListResponse(
        message="获取成功",
        videos=paginated_videos,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


# ============ 视频详情 ============

@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """获取视频详情"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video


# ============ 处理视频 ============

@router.post("/{video_id}/process")
async def process_video_route(
    video_id: int,
    request: VideoProcessRequest,
    db: Session = Depends(get_db)
):
    """开始处理视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 检查状态
    allowed_statuses = [
        VideoStatus.UPLOADED,
        VideoStatus.PENDING,
        VideoStatus.FAILED,
        VideoStatus.COMPLETED
    ]
    if video.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"视频状态不正确: {video.status.name}"
        )

    # 更新状态
    video.status = VideoStatus.PENDING
    db.commit()

    # 启动 Celery 任务
    whisper_language = 'en' if request.language == 'English' else 'zh'
    task = process_video.delay(video.id, whisper_language, request.model)

    # 保存任务 ID
    video.task_id = task.id
    db.commit()

    return {
        "status": "success",
        "message": "视频处理已开始",
        "task_id": task.id
    }


# ============ 视频流 ============

@router.get("/{video_id}/stream")
async def get_video_stream(
    video_id: int,
    db: Session = Depends(get_db)
):
    """流式传输视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not os.path.exists(video.filepath):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    def iterfile():
        with open(video.filepath, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(os.path.getsize(video.filepath))
        }
    )


# ============ 删除视频 ============

@router.delete("/{video_id}/delete")
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """删除视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 启动清理任务
    task = cleanup_video.delay(video.id)

    # 删除数据库记录
    db.delete(video)
    db.commit()

    return {
        "message": "视频删除任务已启动",
        "video_id": video_id,
        "task_id": task.id
    }
```

### 6.3 Q&A 流式响应迁移

**文件：`app/routers/qa.py`**

```python
"""问答系统路由 - FastAPI 版本"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.video import Video
from app.models.qa import Question
from app.utils.qa_utils import QASystem

logger = logging.getLogger(__name__)

router = APIRouter()

qa_system = QASystem()


class AskRequest(BaseModel):
    """问答请求"""
    video_id: Optional[int] = None
    question: str
    api_key: Optional[str] = None
    mode: str = "video"
    stream: bool = True
    use_ollama: bool = False
    deep_thinking: bool = False


@router.post("/ask")
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db)
):
    """提问并获取答案"""

    # 如果使用 Ollama，检查服务是否可用
    if request.use_ollama:
        from app.utils.qa_utils import check_ollama_service
        if not check_ollama_service():
            raise HTTPException(
                status_code=503,
                detail="Ollama服务不可用"
            )
    elif not request.api_key:
        raise HTTPException(
            status_code=400,
            detail="在线模式需要提供API密钥"
        )

    # 视频问答模式需要验证视频
    if request.mode == "video":
        if not request.video_id:
            raise HTTPException(
                status_code=400,
                detail="视频问答模式需要提供视频ID"
            )

        video = db.query(Video).filter(Video.id == request.video_id).first()
        if not video or not video.subtitle_filepath:
            raise HTTPException(
                status_code=400,
                detail="该视频尚未生成字幕"
            )

        # 创建知识库
        qa_system.create_knowledge_base(video.subtitle_filepath)

    # 创建问题记录
    question = Question(
        video_id=request.video_id if request.mode == "video" else None,
        content=request.question
    )
    db.add(question)
    db.commit()

    # 流式响应
    if request.stream:
        async def generate():
            full_answer = ""
            for chunk in qa_system.get_answer_stream(
                request.question,
                request.api_key,
                request.mode,
                use_ollama=request.use_ollama,
                deep_thinking=request.deep_thinking
            ):
                full_answer += chunk
                yield chunk

            # 更新答案
            question.answer = full_answer
            db.commit()

        return StreamingResponse(
            generate(),
            media_type="text/plain"
        )
    else:
        # 非流式响应
        answer = qa_system.get_answer(
            request.question,
            request.api_key,
            request.mode,
            use_ollama=request.use_ollama,
            deep_thinking=request.deep_thinking
        )
        question.answer = answer
        db.commit()

        return question.to_dict()
```

---

## 7. Phase 4: 后台任务处理

本项目提供两种后台任务处理方案，根据实际需求选择：

| 方案 | 适用场景 | 复杂度 | 需要的服务 |
|------|----------|--------|-----------|
| **方案 A: 简化方案** | 毕设/个人项目 | 低 | 无额外服务 |
| **方案 B: Celery 方案** | 生产环境/多用户 | 高 | Redis |

---

### 方案 A: 简化方案 (推荐毕设)

使用 Python 内置的 `ProcessPoolExecutor` 替代 Celery + Redis，架构更简单。

#### 架构对比

```
【Celery 方案 - 复杂】
Flask/FastAPI → Celery → Redis → Worker 进程
启动命令：4 条

【简化方案 - 推荐】
FastAPI → ProcessPoolExecutor (内置)
启动命令：2 条 (FastAPI + 前端)
```

#### 优缺点

| 优点 | 缺点 |
|------|------|
| 架构简单，少维护 2 个服务 | 服务重启时正在处理的任务会丢失 |
| 不需要安装 Redis | 无法分布式扩展 |
| 调试方便 | 同时处理任务数受限 |
| 代码量少 | 无自动重试 (需手动重新处理) |

> **对于毕设项目，以上缺点都可以接受**

#### 7.1 任务处理函数

**文件：`app/tasks/video_processing.py`**

```python
"""视频处理任务 - 简化版 (无 Celery)"""
import os
import logging
import cv2
import whisper
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.video import Video, VideoStatus

logger = logging.getLogger(__name__)


def process_video_task(video_id: int, language: str = 'zh', model: str = 'turbo'):
    """
    视频处理任务（在子进程中执行）

    注意：此函数必须是模块级别的顶层函数，才能被 ProcessPoolExecutor 序列化
    """
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"视频不存在: {video_id}")
            return {'status': 'failed', 'message': '视频不存在'}

        logger.info(f"🎬 开始处理视频: {video.title}")

        # 更新状态为处理中
        video.status = VideoStatus.PROCESSING
        video.process_progress = 0
        video.current_step = "初始化"
        db.commit()

        # ========== 1. 生成预览图 (10%) ==========
        video.current_step = "生成预览图"
        video.process_progress = 10
        db.commit()

        preview_dir = os.path.join(settings.UPLOAD_FOLDER, 'previews')
        os.makedirs(preview_dir, exist_ok=True)

        cap = cv2.VideoCapture(video.filepath)
        ret, frame = cap.read()
        if ret:
            preview_path = os.path.join(preview_dir, f"preview_{video.id}.jpg")
            cv2.imwrite(preview_path, frame)
            video.preview_filepath = preview_path
            video.preview_filename = f"preview_{video.id}.jpg"
        cap.release()
        db.commit()

        # ========== 2. 提取视频信息 (20%) ==========
        video.current_step = "提取视频信息"
        video.process_progress = 20
        db.commit()

        cap = cv2.VideoCapture(video.filepath)
        video.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video.fps = cap.get(cv2.CAP_PROP_FPS)
        video.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video.duration = video.frame_count / video.fps if video.fps > 0 else 0
        cap.release()
        db.commit()

        # ========== 3. 提取音频 (30%) ==========
        video.current_step = "提取音频"
        video.process_progress = 30
        db.commit()

        audio_dir = os.path.join(settings.UPLOAD_FOLDER, 'audio_temp')
        os.makedirs(audio_dir, exist_ok=True)
        audio_path = os.path.join(audio_dir, f"{video.id}.wav")

        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-i", video.filepath,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            audio_path
        ], capture_output=True)

        # ========== 4. Whisper 转录 (30% -> 80%) ==========
        video.current_step = "语音转录 (这一步较慢)"
        video.process_progress = 40
        db.commit()

        logger.info(f"🎤 开始 Whisper 转录: model={model}")
        whisper_model = whisper.load_model(model)
        result = whisper_model.transcribe(
            audio_path if os.path.exists(audio_path) else video.filepath,
            language=language,
            verbose=False
        )

        video.process_progress = 80
        db.commit()

        # ========== 5. 生成字幕文件 (90%) ==========
        video.current_step = "生成字幕"
        video.process_progress = 90
        db.commit()

        subtitle_dir = os.path.join(settings.UPLOAD_FOLDER, 'subtitles')
        os.makedirs(subtitle_dir, exist_ok=True)

        srt_path = os.path.join(subtitle_dir, f"{video.id}.srt")
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(result['segments'], 1):
                start = format_timestamp(seg['start'])
                end = format_timestamp(seg['end'])
                text = seg['text'].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

        video.subtitle_filepath = srt_path

        # ========== 6. 完成 (100%) ==========
        video.status = VideoStatus.COMPLETED
        video.process_progress = 100
        video.current_step = "处理完成"
        db.commit()

        # 清理临时文件
        if os.path.exists(audio_path):
            os.remove(audio_path)

        logger.info(f"✅ 视频处理完成: {video.title}")
        return {'status': 'success', 'message': '处理完成'}

    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        try:
            video.status = VideoStatus.FAILED
            video.error_message = str(e)
            video.current_step = f"处理失败: {str(e)}"
            db.commit()
        except:
            pass
        return {'status': 'failed', 'message': str(e)}

    finally:
        db.close()


def format_timestamp(seconds: float) -> str:
    """格式化时间戳为 SRT 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def cleanup_video_task(video_id: int):
    """清理视频文件任务"""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        # 删除文件
        for path in [video.filepath, video.preview_filepath, video.subtitle_filepath]:
            if path and os.path.exists(path):
                os.remove(path)

        logger.info(f"🧹 视频文件已清理: {video_id}")

    except Exception as e:
        logger.error(f"清理失败: {str(e)}")
    finally:
        db.close()
```

#### 7.2 路由中调用任务

**文件：`app/routers/video.py` (处理视频部分)**

```python
from app.core.executor import submit_task
from app.tasks.video_processing import process_video_task, cleanup_video_task


@router.post("/{video_id}/process")
async def process_video_route(
    video_id: int,
    request: VideoProcessRequest,
    db: Session = Depends(get_db)
):
    """开始处理视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 检查状态
    allowed_statuses = [VideoStatus.UPLOADED, VideoStatus.FAILED, VideoStatus.COMPLETED]
    if video.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"视频状态不正确: {video.status.name}")

    # 更新状态
    video.status = VideoStatus.PENDING
    db.commit()

    # 提交到后台进程池执行
    whisper_language = 'en' if request.language == 'English' else 'zh'
    submit_task(process_video_task, video.id, whisper_language, request.model)

    return {
        "status": "success",
        "message": "视频处理已开始"
    }


@router.get("/{video_id}/status")
async def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """获取处理进度 - 直接从数据库读取"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    return {
        "id": video.id,
        "status": video.status.value,
        "progress": video.process_progress,
        "current_step": video.current_step
    }


@router.delete("/{video_id}/delete")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """删除视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 提交清理任务
    submit_task(cleanup_video_task, video.id)

    # 删除数据库记录
    db.delete(video)
    db.commit()

    return {"message": "视频删除成功", "video_id": video_id}
```

#### 7.3 启动命令对比

```bash
# ========== Celery 方案 (4 条命令) ==========
redis-server                                    # 终端 1
celery -A app.celery_app worker --loglevel=info # 终端 2
python run.py                                   # 终端 3
npm run dev                                     # 终端 4

# ========== 简化方案 (2 条命令) ==========
python run.py                                   # 终端 1 (后台任务内置)
npm run dev                                     # 终端 2
```

---

### 方案 B: Celery 方案 (生产环境)

如果需要生产环境部署，保留 Celery + Redis 方案。

#### 7.4 Celery 任务改动点

1. **修改导入路径**

```python
# 原来 (Flask)
from ..extensions import db, celery
from flask import current_app

# 现在 (FastAPI)
from app.core.celery_app import celery_app as celery
from app.core.database import SessionLocal
from app.core.config import settings
```

2. **替换 `current_app` 为 `settings`**

```python
# 原来
upload_folder = current_app.config['UPLOAD_FOLDER']

# 现在
upload_folder = settings.UPLOAD_FOLDER
```

3. **数据库会话管理**

```python
# 原来 (Flask-SQLAlchemy 自动管理)
video = Video.query.get(video_id)

# 现在 (手动管理会话)
db = SessionLocal()
try:
    video = db.query(Video).filter(Video.id == video_id).first()
    db.commit()
finally:
    db.close()
```

#### 7.5 Celery 配置

**文件：`app/core/celery_app.py`**

```python
"""Celery 配置 (可选方案)"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'app',
    broker=settings.REDIS_URL,  # 需要在 config.py 中添加 REDIS_URL
    backend=settings.REDIS_URL,
    include=['app.tasks.video_processing']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
)
```

---

## 8. Phase 5: 测试迁移

### 8.1 测试框架变更

| Flask | FastAPI |
|-------|---------|
| `pytest` + `flask.testing.FlaskClient` | `pytest` + `httpx.AsyncClient` |
| `client.get('/api/videos')` | `await client.get('/api/videos')` |

### 8.2 测试配置

**文件：`tests/conftest.py`**

```python
"""pytest 配置和 fixtures"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base

# 测试数据库
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def sample_video(db):
    """创建示例视频"""
    from app.models.video import Video, VideoStatus

    video = Video(
        title="测试视频",
        filename="test.mp4",
        filepath="/tmp/test.mp4",
        status=VideoStatus.UPLOADED
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video
```

### 8.3 API 测试示例

**文件：`tests/api/test_video_api.py`**

```python
"""视频 API 测试"""
import pytest
from fastapi.testclient import TestClient


class TestVideoAPI:
    """视频 API 测试类"""

    def test_get_video_list(self, client: TestClient):
        """测试获取视频列表"""
        response = client.get("/api/videos/list")
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert "total" in data

    def test_get_video_list_with_pagination(self, client: TestClient):
        """测试分页"""
        response = client.get("/api/videos/list?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_get_video_detail(self, client: TestClient, sample_video):
        """测试获取视频详情"""
        response = client.get(f"/api/videos/{sample_video.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_video.id
        assert data["title"] == "测试视频"

    def test_get_video_not_found(self, client: TestClient):
        """测试视频不存在"""
        response = client.get("/api/videos/99999")
        assert response.status_code == 404

    def test_upload_video_url_invalid(self, client: TestClient):
        """测试无效 URL 上传"""
        response = client.post(
            "/api/videos/upload-url",
            json={"url": "https://invalid-site.com/video"}
        )
        assert response.status_code == 400

    def test_process_video(self, client: TestClient, sample_video):
        """测试处理视频"""
        response = client.post(
            f"/api/videos/{sample_video.id}/process",
            json={"language": "Chinese", "model": "base"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "task_id" in data
```

### 8.4 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/api/test_video_api.py -v

# 带覆盖率
pytest --cov=app --cov-report=html

# 只运行冒烟测试
pytest -m smoke
```

---

## 9. 迁移检查清单

### Phase 1: 基础设施 ✓

- [ ] 创建新目录结构
- [ ] 安装 FastAPI 依赖
- [ ] 配置 Pydantic Settings
- [ ] 配置 SQLAlchemy 2.0
- [ ] 配置 Celery
- [ ] 创建 FastAPI 应用入口
- [ ] 配置 CORS 中间件
- [ ] 验证应用能启动

### Phase 2: 模型层 ✓

- [ ] 迁移 Video 模型
- [ ] 迁移 Subtitle 模型
- [ ] 迁移 Note 模型
- [ ] 迁移 User 模型
- [ ] 迁移 Question 模型
- [ ] 创建对应的 Pydantic Schema
- [ ] 配置 Alembic 数据库迁移
- [ ] 验证数据库操作正常

### Phase 3: 路由层 ✓

- [ ] 迁移 video.py (最复杂)
- [ ] 迁移 subtitle.py
- [ ] 迁移 note.py
- [ ] 迁移 qa.py (流式响应)
- [ ] 迁移 chat.py (流式响应)
- [ ] 迁移 auth.py
- [ ] 迁移 knowledge_graph.py
- [ ] 验证所有 API 端点正常

### Phase 4: 后台任务处理 ✓

**简化方案 (推荐):**
- [ ] 创建 `app/core/executor.py`
- [ ] 修改 `app/tasks/video_processing.py`
- [ ] 更新路由中的任务调用方式
- [ ] 验证视频处理任务正常执行

**Celery 方案 (可选):**
- [ ] 配置 Redis
- [ ] 创建 `app/core/celery_app.py`
- [ ] 修改任务导入路径
- [ ] 验证 Worker 正常运行

### Phase 5: 测试 ✓

- [ ] 创建测试配置
- [ ] 编写 API 测试
- [ ] 编写单元测试
- [ ] 验证测试通过
- [ ] 生成测试覆盖率报告

### 最终验证 ✓

- [ ] 所有 API 功能正常
- [ ] 流式响应正常
- [ ] 视频处理任务正常
- [ ] 知识图谱功能正常
- [ ] 前端能正常连接
- [ ] 性能对比测试
- [ ] 文档生成正确 (/docs, /redoc)

---

## 10. 常见问题

### Q1: 迁移后如何保持数据库数据？

使用相同的数据库连接字符串，SQLAlchemy 2.0 与旧数据库完全兼容。

### Q2: Celery 任务需要重写吗？

不需要完全重写，只需修改：
- 导入路径
- `current_app.config` → `settings`
- 数据库会话管理

### Q3: 前端需要改动吗？

如果保持相同的 API 路径和响应格式，前端**不需要改动**。

### Q4: 如何处理 `current_app`？

FastAPI 使用依赖注入替代 Flask 的应用上下文：

```python
# Flask
from flask import current_app
upload_folder = current_app.config['UPLOAD_FOLDER']

# FastAPI - 在路由中
from app.core.config import settings
upload_folder = settings.UPLOAD_FOLDER

# FastAPI - 在 Celery 任务中 (无法使用依赖注入)
from app.core.config import settings
upload_folder = settings.UPLOAD_FOLDER
```

### Q5: 流式响应有什么不同？

```python
# Flask
from flask import Response, stream_with_context

def generate():
    for chunk in data:
        yield chunk

return Response(stream_with_context(generate()), content_type='text/plain')

# FastAPI
from fastapi.responses import StreamingResponse

async def generate():
    for chunk in data:
        yield chunk

return StreamingResponse(generate(), media_type="text/plain")
```

### Q6: 如何调试 FastAPI？

1. 使用 `--reload` 模式：`uvicorn app.main:app --reload`
2. 访问 `/docs` 查看 Swagger UI
3. 使用 `logging` 模块记录日志
4. 使用 VSCode/PyCharm 断点调试

---

## 附录：命令速查

```bash
# ========== 简化方案启动 (推荐) ==========
# 终端 1: 启动 FastAPI (后台任务内置)
uvicorn app.main:app --reload --host 0.0.0.0 --port 2004

# 终端 2: 启动前端
cd frontend && npm run dev


# ========== Celery 方案启动 (可选) ==========
# 终端 1: Redis
redis-server

# 终端 2: Celery Worker
celery -A app.core.celery_app worker --loglevel=info -P solo

# 终端 3: FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 2004

# 终端 4: 前端
cd frontend && npm run dev


# ========== 数据库迁移 ==========
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head


# ========== 运行测试 ==========
pytest -v
pytest --cov=app --cov-report=html
pytest -m smoke  # 只运行冒烟测试


# ========== 其他 ==========
pip freeze > requirements.txt
```

---

**文档版本**: 2.0 (简化方案)
**更新时间**: 2025年
**适用项目**: AI-EdVision (毕设项目)
**作者**: Claude Code

**更新记录**:
- v2.0: 新增简化方案，移除 Celery + Redis 依赖，使用 ProcessPoolExecutor 替代
- v1.0: 初始版本，包含 Celery 方案
