"""语义搜索服务 API"""

import logging
import time
from typing import List
from typing import Optional
from typing import Tuple

from app.core.config import settings
from app.models.vector_index import VectorIndex
from app.schemas.search import SearchResultChunk
from app.services.search.chunker import chunk_video
from app.services.search.chunker import get_video_duration
from app.services.search.embedder import get_embedder
from app.services.search.search_logging import SearchEventLogger
from app.services.search.store import EduMindStore
from app.services.search.store import make_chunk_id
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_adaptive_chunk_params(video_duration_seconds: float) -> Tuple[int, int]:
    """
    根据视频时长获取自适应切片参数

    Args:
        video_duration_seconds: 视频时长（秒）

    Returns:
        (chunk_duration, overlap) 元组
    """
    if not settings.SEARCH_ADAPTIVE_CHUNKING:
        return settings.SEARCH_CHUNK_DURATION, settings.SEARCH_CHUNK_OVERLAP

    # 遍历自适应参数规则，找到第一个满足上限的规则
    # 规则格式已改为 (max_duration, chunk_duration, overlap)，使用单值上限完全避免边界歧义
    for max_dur, chunk_dur, overlap in settings.SEARCH_ADAPTIVE_PARAMS:
        if video_duration_seconds <= max_dur:
            logger.info(
                f"Adaptive chunking: duration={video_duration_seconds:.1f}s → "
                f"chunk={chunk_dur}s, overlap={overlap}s"
            )
            return chunk_dur, overlap

    # fallback 到全局配置
    logger.warning(
        f"No adaptive rule for duration {video_duration_seconds}s, "
        f"using fallback: chunk={settings.SEARCH_CHUNK_DURATION}s, "
        f"overlap={settings.SEARCH_CHUNK_OVERLAP}s"
    )
    return settings.SEARCH_CHUNK_DURATION, settings.SEARCH_CHUNK_OVERLAP


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
    total_start_time = time.time()

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

        # 获取视频时长并计算自适应参数
        video_duration = get_video_duration(video_path)
        chunk_duration, overlap = get_adaptive_chunk_params(video_duration)

        # 记录自适应切片参数选择
        SearchEventLogger.log_adaptive_chunking_selected(
            video_id=video_id, video_duration_seconds=video_duration, chunk_duration=chunk_duration, overlap=overlap
        )

        # 切片视频
        logger.info(
            f"Chunking video {video_id}: duration={video_duration:.0f}s, "
            f"chunk={chunk_duration}s, overlap={overlap}s"
        )
        chunk_start_time = time.time()
        chunks = chunk_video(
            video_path,
            chunk_duration=chunk_duration,
            overlap=overlap,
            preprocess=settings.SEARCH_PREPROCESS,
            target_resolution=settings.SEARCH_PREPROCESS_RESOLUTION,
            target_fps=settings.SEARCH_PREPROCESS_FPS,
        )

        chunk_time_ms = (time.time() - chunk_start_time) * 1000
        SearchEventLogger.log_video_chunking_completed(
            video_id=video_id, chunk_count=len(chunks), duration_ms=chunk_time_ms
        )

        if not chunks:
            logger.warning(f"No chunks created for video {video_id}")
            return 0

        # 嵌入分片
        logger.info(f"Embedding {len(chunks)} chunks")
        embedding_start_time = time.time()
        for chunk in chunks:
            try:
                embedding = embedder.embed_video_chunk(chunk["chunk_path"])
                chunk["embedding"] = embedding
            except Exception as e:
                logger.error(f"Failed to embed chunk: {e}")
                raise
        embedding_time_ms = (time.time() - embedding_start_time) * 1000
        SearchEventLogger.log_embedding_batch_completed(
            video_id=video_id, batch_size=len(chunks), duration_ms=embedding_time_ms
        )

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

        # 记录索引完成
        SearchEventLogger.log_indexing_completed(
            video_id=video_id,
            chunk_count=len(chunks),
            backend=backend,
            duration_ms=(time.time() - total_start_time) * 1000,
            user_id=user_id,
        )

        return len(chunks)

    except Exception as e:
        error_stage = "unknown"
        if "chunking" in str(e).lower() or "chunk_video" in str(e).lower():
            error_stage = "chunking"
        elif "embedding" in str(e).lower() or "embedder" in str(e).lower():
            error_stage = "embedding"
        elif "storage" in str(e).lower() or "chroma" in str(e).lower() or "add_chunks" in str(e).lower():
            error_stage = "storage"

        SearchEventLogger.log_indexing_failed(
            video_id=video_id, error_stage=error_stage, error_message=str(e), user_id=user_id
        )
        logger.error(f"Failed to index video {video_id} at {error_stage}: {e}", exc_info=True)
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
    total_start_time = time.time()

    # 记录搜索请求
    SearchEventLogger.log_search_request(
        user_id=user_id, query_text=query, video_ids=video_ids, threshold=threshold, limit=limit
    )

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
        chromadb_start_time = time.time()
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
                SearchEventLogger.log_search_failed(user_id=user_id, error_message=str(e))
                continue

        SearchEventLogger.log_chromadb_search_executed(
            videos_searched=len(video_ids),
            results_found=len(all_results),
            duration_ms=(time.time() - chromadb_start_time) * 1000,
        )

        # 按相似度排序并限制结果数
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        all_results = all_results[:limit]

        max_similarity = all_results[0].similarity_score if all_results else None
        SearchEventLogger.log_search_completed(
            user_id=user_id,
            query_text=query,
            video_count=len(video_ids),
            result_count=len(all_results),
            duration_ms=(time.time() - total_start_time) * 1000,
            max_similarity=max_similarity,
        )

        logger.info(f"Found {len(all_results)} results")
        return all_results

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        SearchEventLogger.log_search_failed(user_id=user_id, error_message=str(e))
        raise
