"""FastAPI 应用入口"""

import logging
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动 AI-EdVision API...")

    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建成功")

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.SUBTITLE_FOLDER, exist_ok=True)
    os.makedirs(settings.PREVIEW_FOLDER, exist_ok=True)
    os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
    logger.info(f"上传目录已就绪: {settings.UPLOAD_FOLDER}")

    yield

    # 关闭时执行
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
from app.routers import knowledge_graph
from app.routers import knowledge_graph_integration
from app.routers import note
from app.routers import qa
from app.routers import subtitle
from app.routers import video

app.include_router(video.router, prefix="/api/videos", tags=["视频管理"])
app.include_router(subtitle.router, prefix="/api/subtitles", tags=["字幕管理"])
app.include_router(note.router, prefix="/api/notes", tags=["笔记管理"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答系统"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天系统"])
app.include_router(auth.router, prefix="/api/auth", tags=["用户认证"])
app.include_router(knowledge_graph.router, prefix="/api/knowledge-graph", tags=["知识图谱"])
app.include_router(
    knowledge_graph_integration.router,
    prefix="/api/knowledge-graph/integration",
    tags=["知识图谱整合"],
)


# 根路由
@app.get("/")
async def root():
    return {"status": "success", "message": "Welcome to AI-EdVision API", "version": "2.0.0", "docs": "/docs"}


# 健康检查
@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "healthy", "services": {"database": "connected", "neo4j": "connected"}}
