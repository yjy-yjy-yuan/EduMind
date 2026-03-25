"""FastAPI 应用入口"""

import logging
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.database import engine
from app.models.base import Base
from app.models.video import Video
from app.models.video import VideoStatus
from app.services.whisper_runtime import get_whisper_runtime_status
from app.services.whisper_runtime import shutdown_whisper_runtime
from app.services.whisper_runtime import start_whisper_background_preload
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def recover_interrupted_video_tasks():
    """将服务重启前中断的后台任务转为失败，避免状态永久卡住。"""
    db = SessionLocal()
    try:
        interrupted_statuses = [VideoStatus.PENDING, VideoStatus.PROCESSING, VideoStatus.DOWNLOADING]
        interrupted_videos = db.query(Video).filter(Video.status.in_(interrupted_statuses)).all()
        if not interrupted_videos:
            return

        for video in interrupted_videos:
            previous_status = video.status
            video.status = VideoStatus.FAILED
            video.process_progress = 0.0
            video.error_message = "服务重启后检测到后台任务已中断，请重新提交处理。"
            if previous_status == VideoStatus.DOWNLOADING:
                video.current_step = "下载任务已中断，请重新提交"
            else:
                video.current_step = "处理任务已中断，请重新提交"

        db.commit()
        logger.warning("已恢复中断的视频任务 | count=%s", len(interrupted_videos))
    except Exception as exc:
        db.rollback()
        logger.error("恢复中断的视频任务失败 | error=%s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动 AI-EdVision API...")

    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    else:
        logger.info("已跳过自动建表；如需初始化数据库，请运行 backend_fastapi/scripts/init_db.py")

    recover_interrupted_video_tasks()

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.SUBTITLE_FOLDER, exist_ok=True)
    os.makedirs(settings.PREVIEW_FOLDER, exist_ok=True)
    os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
    logger.info(f"上传目录已就绪: {settings.UPLOAD_FOLDER}")
    start_whisper_background_preload(settings.WHISPER_MODEL, settings.WHISPER_MODEL_PATH)

    yield

    # 关闭时执行
    shutdown_whisper_runtime()
    logger.info("关闭 AI-EdVision API...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="基于深度学习的视频智能伴学系统 API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url=None,  # 禁用默认 ReDoc，使用自定义路由
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
from app.routers import auth
from app.routers import chat
from app.routers import note
from app.routers import qa
from app.routers import recommendation
from app.routers import subtitle
from app.routers import video

app.include_router(video.router, prefix="/api/videos", tags=["视频管理"])
app.include_router(subtitle.router, prefix="/api/subtitles", tags=["字幕管理"])
app.include_router(note.router, prefix="/api/notes", tags=["笔记管理"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答系统"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天系统"])
app.include_router(auth.router, prefix="/api/auth", tags=["用户认证"])
app.include_router(recommendation.router, prefix="/api/recommendations", tags=["视频推荐"])


# 根路由
@app.get("/")
async def root():
    return {"status": "success", "message": "Welcome to AI-EdVision API", "version": "2.0.0", "docs": "/docs"}


# 健康检查
@app.get("/health")
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "whisper": get_whisper_runtime_status(),
        },
    }
