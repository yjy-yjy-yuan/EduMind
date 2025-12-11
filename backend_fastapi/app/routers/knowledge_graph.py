"""知识图谱路由 - FastAPI 版本"""

import logging
import os
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.video import Video
from app.models.video import VideoStatus
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


def get_knowledge_graph_utils():
    """获取知识图谱工具"""
    try:
        from app.utils.knowledge_graph_utils import KnowledgeGraphManager

        return KnowledgeGraphManager()
    except ImportError:
        logger.warning("KnowledgeGraphManager 未实现")
        return None


@router.post("/build")
async def build_knowledge_graph(video_id: int, rebuild: bool = False, db: Session = Depends(get_db)):
    """构建知识图谱"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成")

    if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
        raise HTTPException(status_code=400, detail="字幕文件不存在")

    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        raise HTTPException(status_code=500, detail="知识图谱服务未配置")

    try:
        # 读取字幕内容
        with open(video.subtitle_filepath, "r", encoding="utf-8") as f:
            subtitle_content = f.read()

        # 构建知识图谱
        result = kg_manager.build_from_subtitle(video_id, subtitle_content, rebuild=rebuild)

        return {
            "success": True,
            "message": "知识图谱构建成功",
            "node_count": result.get("node_count", 0),
            "edge_count": result.get("edge_count", 0),
        }
    except Exception as e:
        logger.error(f"构建知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"构建知识图谱失败: {str(e)}")


@router.get("/query")
async def query_knowledge_graph(
    query: str = Query(..., min_length=1),
    video_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询知识图谱"""
    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        raise HTTPException(status_code=500, detail="知识图谱服务未配置")

    try:
        results = kg_manager.query(query, video_id=video_id, limit=limit)
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"查询知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询知识图谱失败: {str(e)}")


@router.get("/video/{video_id}")
async def get_video_knowledge_graph(video_id: int, db: Session = Depends(get_db)):
    """获取视频的知识图谱数据"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        # 返回模拟数据
        return {
            "success": True,
            "video_id": video_id,
            "nodes": [],
            "edges": [],
            "message": "知识图谱服务未配置，返回空数据",
        }

    try:
        graph_data = kg_manager.get_video_graph(video_id)
        return {
            "success": True,
            "video_id": video_id,
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", []),
        }
    except Exception as e:
        logger.error(f"获取视频知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取视频知识图谱失败: {str(e)}")


@router.get("/status/{video_id}")
async def get_knowledge_graph_status(video_id: int, db: Session = Depends(get_db)):
    """获取知识图谱状态"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        return {"video_id": video_id, "status": "not_configured", "node_count": 0, "edge_count": 0}

    try:
        status = kg_manager.get_status(video_id)
        return {
            "video_id": video_id,
            "status": status.get("status", "unknown"),
            "node_count": status.get("node_count", 0),
            "edge_count": status.get("edge_count", 0),
        }
    except Exception as e:
        logger.error(f"获取知识图谱状态失败: {str(e)}")
        return {"video_id": video_id, "status": "error", "node_count": 0, "edge_count": 0}


@router.delete("/video/{video_id}")
async def delete_video_knowledge_graph(video_id: int, db: Session = Depends(get_db)):
    """删除视频的知识图谱"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        return {"success": True, "message": "知识图谱服务未配置"}

    try:
        kg_manager.delete_video_graph(video_id)
        return {"success": True, "message": "知识图谱删除成功"}
    except Exception as e:
        logger.error(f"删除知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除知识图谱失败: {str(e)}")


@router.get("/concepts")
async def get_all_concepts(limit: int = Query(50, ge=1, le=200)):
    """获取所有概念"""
    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        return {"success": True, "concepts": []}

    try:
        concepts = kg_manager.get_all_concepts(limit=limit)
        return {"success": True, "concepts": concepts}
    except Exception as e:
        logger.error(f"获取概念列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取概念列表失败: {str(e)}")


@router.get("/related/{concept}")
async def get_related_concepts(concept: str, depth: int = Query(1, ge=1, le=3)):
    """获取相关概念"""
    kg_manager = get_knowledge_graph_utils()
    if not kg_manager:
        return {"success": True, "concept": concept, "related": []}

    try:
        related = kg_manager.get_related_concepts(concept, depth=depth)
        return {"success": True, "concept": concept, "related": related}
    except Exception as e:
        logger.error(f"获取相关概念失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取相关概念失败: {str(e)}")
