"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings, init_directories
from app.core.database import init_db
from app.api import api_router

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
    logger.info("正在初始化应用...")
    init_directories()
    logger.info("目录初始化完成")

    init_db()
    logger.info("数据库初始化完成")

    yield

    # 关闭时执行
    logger.info("应用正在关闭...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="EduMind - 基于深度学习的视频智能伴学系统",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Content-Range", "Accept-Ranges"],
    )

    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"请求: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"响应状态: {response.status_code}")
        return response

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误", "detail": str(exc)}
        )

    # 注册 API 路由
    app.include_router(api_router, prefix="/api")

    # 根路由
    @app.get("/")
    async def root():
        return {
            "status": "success",
            "message": "Welcome to EduMind API",
            "version": settings.APP_VERSION
        }

    # 健康检查路由
    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "services": {
                "database": "connected",
                "redis": "connected"
            }
        }

    return app


# 创建应用实例
app = create_app()
