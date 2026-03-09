"""API路由模块"""
from fastapi import APIRouter
from app.api import video, subtitle, note, qa, auth, knowledge_graph

api_router = APIRouter()

# 注册所有路由
api_router.include_router(video.router, prefix="/videos", tags=["视频管理"])
api_router.include_router(subtitle.router, prefix="/subtitles", tags=["字幕管理"])
api_router.include_router(note.router, prefix="/notes", tags=["笔记管理"])
api_router.include_router(qa.router, prefix="/qa", tags=["问答系统"])
api_router.include_router(auth.router, prefix="/auth", tags=["用户认证"])
api_router.include_router(
    knowledge_graph.router, prefix="/knowledge-graph", tags=["知识图谱"]
)
