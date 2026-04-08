"""向量索引后台任务"""

import logging
import os
from datetime import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.vector_index import VectorIndex
from app.models.vector_index import VectorIndexStatus
from app.models.video import Video
from app.models.video import VideoStatus
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def index_video_for_search(video_id: int, user_id: int, embedding_backend: str = None):
    """
    后台任务：为视频构建语义索引

    流程：
    1. 从 Video 获取视频文件路径
    2. 验证视频处理是否完成
    3. 使用 chunker 分割视频
    4. 使用 embedder 生成向量
    5. 使用 store 存储到 ChromaDB
    6. 更新 VectorIndex 表记录状态

    Args:
        video_id: 视频 ID
        user_id: 用户 ID
        embedding_backend: 嵌入后端（gemini 或 local）
    """
    db = SessionLocal()
    try:
        backend = embedding_backend or settings.SEARCH_BACKEND

        logger.info(f"Starting background indexing task: video={video_id}, user={user_id}")

        # 获取或创建 VectorIndex 记录
        vector_index = (
            db.query(VectorIndex).filter(VectorIndex.video_id == video_id, VectorIndex.user_id == user_id).first()
        )

        if vector_index is None:
            collection_name = f"user_{user_id}_video_{video_id}_chunks"
            vector_index = VectorIndex(
                video_id=video_id,
                user_id=user_id,
                collection_name=collection_name,
                embedding_backend=backend,
                embedding_model=settings.SEARCH_LOCAL_MODEL if backend == "local" else None,
                status=VectorIndexStatus.PROCESSING,
            )
            db.add(vector_index)
            db.commit()
        else:
            vector_index.status = VectorIndexStatus.PROCESSING
            db.commit()

        # 获取视频信息
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Video not found: {video_id}")
            if vector_index:
                vector_index.status = VectorIndexStatus.FAILED
                vector_index.error_message = "Video not found"
                db.commit()
            return

        # 检查视频是否已处理
        if video.status != VideoStatus.COMPLETED:
            logger.warning(f"Video not fully processed: {video_id}, status={video.status}")
            if vector_index:
                vector_index.status = VectorIndexStatus.FAILED
                vector_index.error_message = f"Video processing incomplete: {video.status}"
                db.commit()
            return

        # 优先使用处理后文件，若没有则回退到原始上传文件
        video_source_path = video.processed_filepath or video.filepath
        if not video_source_path:
            logger.error(f"No available video file for indexing: {video_id}")
            if vector_index:
                vector_index.status = VectorIndexStatus.FAILED
                vector_index.error_message = "No available video file for indexing"
                db.commit()
            return

        if not os.path.exists(video_source_path):
            logger.error(f"Video file does not exist: {video_source_path}")
            if vector_index:
                vector_index.status = VectorIndexStatus.FAILED
                vector_index.error_message = f"Video file missing: {video_source_path}"
                db.commit()
            return

        # 索引处理逻辑
        from app.services.search.search import build_video_index_internal

        chunk_count = build_video_index_internal(
            video_id=video_id,
            user_id=user_id,
            video_path=video_source_path,
            collection_name=vector_index.collection_name,
            backend=backend,
            db=db,
            subtitle_path=video.subtitle_filepath,
        )

        # 更新记录
        vector_index.chunk_count = chunk_count
        vector_index.status = VectorIndexStatus.COMPLETED
        vector_index.indexed_at = datetime.utcnow()
        vector_index.error_message = None

        video.has_semantic_index = True
        video.vector_index_id = vector_index.id

        db.commit()
        logger.info(f"Successfully indexed video {video_id}: {chunk_count} chunks")

    except Exception as e:
        logger.error(f"Semantic indexing failed for video {video_id}: {e}", exc_info=True)
        if vector_index:
            vector_index.status = VectorIndexStatus.FAILED
            vector_index.error_message = str(e)[:500]  # 限制错误信息长度
            db.commit()
    finally:
        db.close()
