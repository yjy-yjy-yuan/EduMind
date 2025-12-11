"""知识图谱整合路由 - FastAPI 版本"""

import json
import logging
from typing import List
from typing import Optional

from app.core.database import get_db
from app.models.video import Video
from app.utils.knowledge_graph_utils import KnowledgeGraphManager
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


class CombineRequest(BaseModel):
    """知识图谱合并请求"""

    source_video_id: int
    target_video_id: int
    threshold: float = 0.7
    force_combine: bool = False


class CombineMultipleRequest(BaseModel):
    """多视频知识图谱合并请求"""

    video_ids: List[int]
    threshold: float = 0.7
    force_combine: bool = False


def get_llm_similarity_service():
    """延迟加载 LLM 相似度服务"""
    try:
        from app.services.llm_similarity_service import llm_similarity_service

        return llm_similarity_service
    except ImportError:
        return None


@router.get("/find-similar/{video_id}")
async def find_similar_videos(
    video_id: int,
    threshold: float = Query(0.6, description="相似度阈值"),
    limit: int = Query(5, description="返回数量限制"),
    db: Session = Depends(get_db),
):
    """查找与指定视频标签相似的其他视频"""
    try:
        llm_service = get_llm_similarity_service()
        if not llm_service:
            raise HTTPException(status_code=503, detail="LLM相似度服务不可用")

        target_video = db.query(Video).filter(Video.id == video_id).first()
        if not target_video:
            raise HTTPException(status_code=404, detail="视频不存在")

        target_tags = []
        if target_video.tags:
            try:
                target_tags = json.loads(target_video.tags)
            except json.JSONDecodeError:
                logger.warning(f"视频 {video_id} 的标签格式无效")

        if not target_tags:
            raise HTTPException(status_code=400, detail="目标视频没有标签")

        all_videos = db.query(Video).filter(Video.id != video_id).all()
        all_video_data = [{"id": v.id, "title": v.title or v.filename, "tags": v.tags} for v in all_videos]

        similar_videos = llm_service.find_similar_videos(target_tags, all_video_data, threshold=threshold, limit=limit)

        result = []
        for item in similar_videos:
            video = item["video"]
            result.append(
                {
                    "id": video["id"],
                    "title": video["title"],
                    "similarity": item["similarity"],
                    "tags": json.loads(video["tags"]) if isinstance(video["tags"], str) else video["tags"],
                }
            )

        return {
            "target_video": {
                "id": target_video.id,
                "title": target_video.title or target_video.filename,
                "tags": target_tags,
            },
            "similar_videos": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查找相似视频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查找相似视频失败: {str(e)}")


@router.post("/combine")
async def combine_knowledge_graphs(request: CombineRequest, db: Session = Depends(get_db)):
    """整合两个视频的知识图谱"""
    try:
        llm_service = get_llm_similarity_service()

        source_video = db.query(Video).filter(Video.id == request.source_video_id).first()
        target_video = db.query(Video).filter(Video.id == request.target_video_id).first()

        if not source_video:
            raise HTTPException(status_code=404, detail=f"源视频(ID={request.source_video_id})不存在")
        if not target_video:
            raise HTTPException(status_code=404, detail=f"目标视频(ID={request.target_video_id})不存在")

        source_tags = []
        target_tags = []

        if source_video.tags:
            try:
                source_tags = json.loads(source_video.tags)
            except json.JSONDecodeError:
                pass

        if target_video.tags:
            try:
                target_tags = json.loads(target_video.tags)
            except json.JSONDecodeError:
                pass

        if not request.force_combine and llm_service:
            can_combine = llm_service.can_combine_knowledge_graphs(
                source_tags, target_tags, threshold=request.threshold
            )
            if not can_combine:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "视频标签相似度不足，无法自动整合知识图谱",
                        "source_tags": source_tags,
                        "target_tags": target_tags,
                        "can_force": True,
                    },
                )

        kg_manager = KnowledgeGraphManager()
        success = kg_manager.combine_knowledge_graphs(request.source_video_id, request.target_video_id)

        if success:
            return {
                "success": True,
                "message": f"成功整合视频 {request.source_video_id} 和视频 {request.target_video_id} 的知识图谱",
            }
        else:
            raise HTTPException(status_code=500, detail={"error": "知识图谱整合失败", "can_force": True})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"整合知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"整合知识图谱失败: {str(e)}")


@router.get("/check-combined/{video_id}")
async def check_combined_video(video_id: int):
    """检查视频是否参与了合并"""
    try:
        kg_manager = KnowledgeGraphManager()

        is_combined = kg_manager.is_combined_video(video_id)
        if is_combined:
            return {"is_combined": True, "combined_video_id": str(video_id)}

        combined_video_id = kg_manager.find_combined_video_id(video_id)
        if combined_video_id:
            return {
                "is_combined": False,
                "is_part_of_combined": True,
                "combined_video_id": combined_video_id,
            }
        else:
            return {"is_combined": False, "is_part_of_combined": False}

    except Exception as e:
        logger.error(f"检查视频合并状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查视频合并状态失败: {str(e)}")


@router.post("/combine-multiple")
async def combine_multiple_knowledge_graphs(request: CombineMultipleRequest, db: Session = Depends(get_db)):
    """整合多个视频的知识图谱"""
    try:
        if len(request.video_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要两个视频才能进行合并")

        llm_service = get_llm_similarity_service()

        videos = []
        all_tags = []

        for video_id in request.video_ids:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail=f"视频(ID={video_id})不存在")

            videos.append(video)
            if video.tags:
                try:
                    tags = json.loads(video.tags)
                    all_tags.append(tags)
                except json.JSONDecodeError:
                    all_tags.append([])
            else:
                all_tags.append([])

        if not request.force_combine and llm_service:
            similarity_results = []
            can_combine_all = True

            for i in range(len(request.video_ids)):
                for j in range(i + 1, len(request.video_ids)):
                    can_combine = llm_service.can_combine_knowledge_graphs(
                        all_tags[i], all_tags[j], threshold=request.threshold
                    )
                    similarity_results.append(
                        {
                            "source_id": request.video_ids[i],
                            "target_id": request.video_ids[j],
                            "can_combine": can_combine,
                        }
                    )
                    if not can_combine:
                        can_combine_all = False

            if not can_combine_all:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "部分视频标签相似度不足，无法自动整合知识图谱",
                        "similarity_results": similarity_results,
                        "can_force": True,
                    },
                )

        kg_manager = KnowledgeGraphManager()
        combined_video_id = kg_manager.combine_multiple_knowledge_graphs(request.video_ids, request.threshold)

        if combined_video_id:
            return {
                "success": True,
                "message": f"成功整合 {len(request.video_ids)} 个视频的知识图谱",
                "combined_video_id": combined_video_id,
            }
        else:
            raise HTTPException(status_code=500, detail={"error": "知识图谱整合失败", "can_force": True})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"整合多个知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"整合多个知识图谱失败: {str(e)}")
