"""语义搜索服务 API"""

import logging
import time
from typing import List
from typing import Optional

from app.core.config import settings
from app.models.vector_index import VectorIndex
from app.schemas.search import SearchResultChunk
from app.services.search.chunker import chunk_video
from app.services.search.chunker import get_video_duration
from app.services.search.embedder import get_embedder
from app.services.search.store import EduMindStore
from app.services.search.store import make_chunk_id
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_video_index_internal(
    video_id: int,
    user_id: int,
    video_path: str,
    collection_name: str,
    backend: str = "gemini",
    db: Optional[Session] = None,
) -> int:
    """
    构建视频的语义索引

    Args:
        video_id: 视频 ID
        user_id: 用户 ID
        video_path: 视频文件路径
        collection_name: ChromaDB 集合名
        backend: 嵌入后端
        db: 数据库会话

    Returns:
        构建的分片总数
    """
    logger.info(f"Starting semantic indexing for video {video_id}")

    try:
        # 初始化存储
        store = EduMindStore(
            db_path=settings.SEARCH_CHROMA_DB_DIR,
            collection_name=collection_name,
            backend=backend,
            model=settings.SEARCH_LOCAL_MODEL if backend == "local" else None,
        )

        # 检查是否已索引
        if store.is_indexed(video_path):
            logger.warning(f"Video {video_id} already indexed, skipping")
            return store.get_chunk_count()

        # 获取嵌入器
        embedder = get_embedder(backend=backend)

        # 切片视频
        logger.info(f"Chunking video {video_id}")
        chunks = chunk_video(
            video_path,
            chunk_duration=settings.SEARCH_CHUNK_DURATION,
            overlap=settings.SEARCH_CHUNK_OVERLAP,
            preprocess=settings.SEARCH_PREPROCESS,
            target_resolution=settings.SEARCH_PREPROCESS_RESOLUTION,
            target_fps=settings.SEARCH_PREPROCESS_FPS,
        )

        if not chunks:
            logger.warning(f"No chunks created for video {video_id}")
            return 0

        # 嵌入分片
        logger.info(f"Embedding {len(chunks)} chunks")
        for chunk in chunks:
            try:
                embedding = embedder.embed_video_chunk(chunk["chunk_path"])
                chunk["embedding"] = embedding
            except Exception as e:
                logger.error(f"Failed to embed chunk: {e}")
                raise

        # 批量存储
        logger.info(f"Storing {len(chunks)} chunks")
        store.add_chunks_batch(chunks)

        # 清理临时文件
        import os

        for chunk in chunks:
            try:
                os.unlink(chunk["chunk_path"])
            except Exception as e:
                logger.warning(f"Failed to cleanup chunk file: {e}")

        logger.info(f"Successfully indexed video {video_id} with {len(chunks)} chunks")
        return len(chunks)

    except Exception as e:
        logger.error(f"Failed to index video {video_id}: {e}", exc_info=True)
        raise


def semantic_search_videos(
    query: str,
    video_ids: List[int],
    user_id: int,
    limit: int = 10,
    threshold: float = 0.5,
    db: Optional[Session] = None,
) -> List[SearchResultChunk]:
    """
    语义搜索视频

    Args:
        query: 搜索查询
        video_ids: 视频 ID 列表
        user_id: 用户 ID
        limit: 返回结果数
        threshold: 相似度阈值
        db: 数据库会话

    Returns:
        搜索结果列表
    """
    logger.info(f"Starting semantic search: query='{query[:50]}', videos={video_ids}")

    if not video_ids:
        logger.warning("No videos to search")
        return []

    try:
        # 获取嵌入器（使用配置的后端）
        backend = settings.SEARCH_BACKEND
        model = settings.SEARCH_LOCAL_MODEL if backend == "local" else None
        embedder = get_embedder(backend=backend, model=model) if model else get_embedder(backend=backend)

        # 嵌入查询
        logger.info(f"Embedding query using {backend} backend")
        query_embedding = embedder.embed_query(query)

        # 搜索所有视频的索引
        all_results = []
        for video_id in video_ids:
            try:
                # 构建集合名
                collection_name = f"user_{user_id}_video_{video_id}_chunks"

                # 初始化存储
                store = EduMindStore(
                    db_path=settings.SEARCH_CHROMA_DB_DIR,
                    collection_name=collection_name,
                    backend=settings.SEARCH_BACKEND,
                    model=settings.SEARCH_LOCAL_MODEL if settings.SEARCH_BACKEND == "local" else None,
                )

                # 搜索
                results = store.search(
                    query_embedding=query_embedding,
                    n_results=limit,
                    threshold=threshold,
                )

                # 转换为 SearchResultChunk
                for result in results:
                    chunk = SearchResultChunk(
                        video_id=video_id,
                        chunk_id=result["chunk_id"],
                        start_time=result["start_time"],
                        end_time=result["end_time"],
                        similarity_score=result["similarity_score"],
                        preview_text=None,  # TODO: 从字幕中获取
                    )
                    all_results.append(chunk)

            except Exception as e:
                logger.warning(f"Failed to search video {video_id}: {e}")
                continue

        # 按相似度排序并限制结果数
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        all_results = all_results[:limit]

        logger.info(f"Found {len(all_results)} results")
        return all_results

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise
