"""知识图谱路由 - FastAPI 版本"""
import os
import re
import json
import logging
import traceback
import threading
import asyncio
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.schemas.knowledge_graph import (
    KnowledgeGraphResponse,
    GenerateQuestionsRequest,
    QuestionsResponse,
    CombineKnowledgeGraphsRequest,
    CombineMultipleRequest,
    SimilarVideoResponse,
)
from app.utils.knowledge_graph_utils import KnowledgeGraphManager

import sys
sys.path.append(str(settings.BASE_DIR))
from services.llm_similarity_service import llm_similarity_service

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建知识图谱管理器实例
kg_manager = KnowledgeGraphManager(
    uri=settings.NEO4J_URI,
    user=settings.NEO4J_USER,
    password=settings.NEO4J_PASSWORD
)

# 任务状态
generation_tasks = {}
TASK_PENDING = 'pending'
TASK_RUNNING = 'running'
TASK_COMPLETED = 'completed'
TASK_FAILED = 'failed'


def check_neo4j_connection() -> bool:
    """检查Neo4j数据库连接"""
    if not kg_manager.connect():
        logger.error("Neo4j连接失败")
        return False
    kg_manager.close()
    return True


def create_knowledge_graph_task(video_id: int, video_title: str, subtitle_text: str, video_tags: list = None):
    """知识图谱生成任务函数"""
    try:
        generation_tasks[str(video_id)] = TASK_RUNNING
        logger.info(f"开始生成视频 {video_id} 的知识图谱...")

        kg = KnowledgeGraphManager()

        if video_tags is None:
            video_tags = []

        logger.info(f"视频 {video_id} 的标签: {video_tags}")

        # 检查是否有标签相似的视频
        combined_with_video = None
        if video_tags and len(video_tags) > 0:
            existing_videos = kg.get_all_video_nodes()
            logger.info(f"找到 {len(existing_videos)} 个已有知识图谱的视频")

            similarity_threshold = 0.8
            similar_videos = []

            for existing_video in existing_videos:
                if str(existing_video['video_id']) == str(video_id):
                    continue

                existing_tags = []
                if existing_video['tags']:
                    try:
                        if isinstance(existing_video['tags'], str):
                            existing_tags = json.loads(existing_video['tags'])
                        else:
                            existing_tags = existing_video['tags']
                    except json.JSONDecodeError:
                        logger.warning(f"视频 {existing_video['video_id']} 的标签格式无效")

                if not existing_tags:
                    continue

                similarity = llm_similarity_service.calculate_tag_sets_similarity(video_tags, existing_tags)
                logger.info(f"视频 {video_id} 与视频 {existing_video['video_id']} 的标签相似度: {similarity}")

                if similarity >= similarity_threshold:
                    similar_videos.append({
                        'video_id': existing_video['video_id'],
                        'title': existing_video['title'],
                        'similarity': similarity
                    })

            if similar_videos:
                similar_videos.sort(key=lambda x: x['similarity'], reverse=True)
                most_similar_video = similar_videos[0]

                logger.info(f"找到标签相似的视频: {most_similar_video['video_id']}")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(
                    kg.generate_knowledge_graph(video_id, video_title, subtitle_text, video_tags)
                )

                if success:
                    logger.info(f"尝试合并视频 {video_id} 和视频 {most_similar_video['video_id']} 的知识图谱...")

                    combine_success = kg.combine_knowledge_graphs(
                        source_video_id=video_id,
                        target_video_id=most_similar_video['video_id']
                    )

                    if combine_success:
                        logger.info(f"成功合并知识图谱")
                        combined_with_video = most_similar_video

                loop.close()
                generation_tasks[str(video_id)] = TASK_COMPLETED

                if combined_with_video:
                    generation_tasks[f"{video_id}_combined_with"] = combined_with_video

                return

        # 正常生成知识图谱
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            kg.generate_knowledge_graph(video_id, video_title, subtitle_text, video_tags)
        )
        loop.close()

        if success:
            logger.info(f"视频 {video_id} 的知识图谱生成完成")

            graph_data = kg.get_knowledge_graph(video_id)
            if graph_data and graph_data["nodes"] and len(graph_data["nodes"]) > 0:
                logger.info(f"验证成功: 知识图谱包含 {len(graph_data['nodes'])} 个节点")
                generation_tasks[str(video_id)] = TASK_COMPLETED
            else:
                logger.error(f"验证失败: 知识图谱数据不存在")
                generation_tasks[str(video_id)] = TASK_FAILED
        else:
            logger.error(f"视频 {video_id} 的知识图谱生成失败")
            generation_tasks[str(video_id)] = TASK_FAILED

    except Exception as e:
        logger.error(f"视频 {video_id} 的知识图谱生成失败: {str(e)}")
        generation_tasks[str(video_id)] = TASK_FAILED
        logger.error(traceback.format_exc())


@router.get("/{video_id}")
async def get_knowledge_graph(video_id: str, db: Session = Depends(get_db)):
    """获取知识图谱"""
    is_combined = '_' in str(video_id)

    if not is_combined:
        try:
            video_id_int = int(video_id)
            video = db.query(Video).filter(Video.id == video_id_int).first()
            if not video:
                raise HTTPException(status_code=404, detail="视频不存在")
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的视频ID格式")
    else:
        logger.info(f"正在获取合并视频 {video_id} 的知识图谱")

    if not check_neo4j_connection():
        raise HTTPException(status_code=500, detail="知识图谱数据库连接失败")

    graph_data = kg_manager.get_knowledge_graph(video_id)

    if not graph_data["nodes"]:
        raise HTTPException(status_code=404, detail="该视频的知识图谱不存在")

    return graph_data


@router.post("/generate/{video_id}")
async def generate_knowledge_graph(video_id: int, db: Session = Depends(get_db)):
    """生成知识图谱"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        status_value = video.status.value if hasattr(video.status, 'value') else str(video.status)
        raise HTTPException(status_code=400, detail=f"视频当前状态为 {status_value}，必须完成处理才能生成知识图谱")

    # 查找字幕文件
    cache_dir = settings.CACHE_FOLDER
    video_name = video.filename.rsplit('.', 1)[0] if video.filename else f'video_{video_id}'
    semantic_file = cache_dir / f'{video_name}_semantic.json'

    subtitle_text = None

    if semantic_file.exists():
        logger.info(f"找到语义合并字幕文件: {semantic_file}")
        with open(semantic_file, 'r', encoding='utf-8') as f:
            subtitle_data = json.load(f)
            if isinstance(subtitle_data, list):
                subtitle_texts = [item.get('text', '') for item in subtitle_data]
                subtitle_text = ' '.join(subtitle_texts)
    else:
        subtitles_dir = settings.SUBTITLE_FOLDER
        if subtitles_dir.exists():
            for file in os.listdir(subtitles_dir):
                if file.endswith('.json') and f'_{video_id}_' in file:
                    with open(subtitles_dir / file, 'r', encoding='utf-8') as f:
                        subtitle_data = json.load(f)
                        if isinstance(subtitle_data, list):
                            subtitle_texts = [item.get('text', '') for item in subtitle_data]
                            subtitle_text = ' '.join(subtitle_texts)
                    break

    if not subtitle_text:
        raise HTTPException(status_code=404, detail="没有找到字幕文件，无法生成知识图谱")

    if not check_neo4j_connection():
        raise HTTPException(status_code=500, detail="知识图谱数据库连接失败")

    # 设置任务状态
    generation_tasks[str(video_id)] = TASK_PENDING

    # 获取视频标签
    video_tags = []
    if video.tags:
        try:
            video_tags = json.loads(video.tags)
        except json.JSONDecodeError:
            logger.warning(f"视频 {video_id} 的标签格式无效")

    # 启动后台任务
    thread = threading.Thread(
        target=create_knowledge_graph_task,
        kwargs={
            'video_id': video_id,
            'video_title': video.title or video.filename,
            'subtitle_text': subtitle_text,
            'video_tags': video_tags
        }
    )
    thread.daemon = True
    thread.start()

    return {"message": "知识图谱生成任务已提交，请稍后查看"}


@router.get("/status/{video_id}")
async def get_knowledge_graph_status(video_id: int, db: Session = Depends(get_db)):
    """检查知识图谱生成状态"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    task_status = generation_tasks.get(str(video_id))

    if task_status is None:
        graph_data = kg_manager.get_knowledge_graph(video_id)

        if graph_data["nodes"]:
            generation_tasks[str(video_id)] = TASK_COMPLETED
            return {"status": TASK_COMPLETED}
        else:
            raise HTTPException(status_code=404, detail="视频的知识图谱生成任务不存在")

    return {"status": task_status}


@router.post("/generate-questions", response_model=QuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest):
    """生成与知识点相关的问题"""
    concept = request.concept
    context = request.context
    count = request.count
    use_ollama = request.use_ollama

    if use_ollama:
        from app.utils.semantic_utils import is_ollama_available
        if not is_ollama_available():
            logger.warning("Ollama服务不可用，将使用在线API")
            use_ollama = False

    try:
        if use_ollama:
            import requests

            prompt = f"""
            基于以下知识点，生成{count}个用户可能想要学习或询问的问题。
            只返回问题列表，格式为JSON数组。

            知识点: {concept}
            背景信息: {context}
            """

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen3:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')

                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    try:
                        questions = json.loads(json_match.group())
                        return QuestionsResponse(questions=questions[:count])
                    except json.JSONDecodeError:
                        pass

                questions = re.findall(r'\d+\.\s*(.+?)(?=\d+\.\s*|$)', response_text, re.DOTALL)
                if not questions:
                    questions = [q.strip() for q in response_text.split('\n') if q.strip() and '?' in q]

                questions = [q.strip().strip('"').strip() for q in questions if q and len(q) > 5]
                return QuestionsResponse(questions=questions[:count])
        else:
            from openai import OpenAI

            client = OpenAI(
                api_key="sk-59a6a7690bfb42cd887365795e114002",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )

            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一个教育助手，负责生成与特定知识点相关的学习问题。"},
                    {"role": "user", "content": f"基于以下知识点，生成{count}个问题，格式为JSON数组。\n\n知识点: {concept}\n背景信息: {context}"}
                ],
                temperature=0.7
            )

            response_text = response.choices[0].message.content

            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    questions = json.loads(json_match.group())
                    return QuestionsResponse(questions=questions[:count])
                except json.JSONDecodeError:
                    pass

            questions = re.findall(r'\d+\.\s*(.+?)(?=\d+\.\s*|$)', response_text, re.DOTALL)
            questions = [q.strip().strip('"').strip() for q in questions if q and len(q) > 5]
            return QuestionsResponse(questions=questions[:count])

    except Exception as e:
        logger.error(f"生成问题失败: {str(e)}")

        default_questions = [
            f"什么是{concept}？",
            f"{concept}的主要特点是什么？",
            f"{concept}在实际应用中有哪些例子？"
        ]
        return QuestionsResponse(questions=default_questions[:count])


# 知识图谱整合路由
@router.get("/integration/find-similar/{video_id}")
async def find_similar_videos(
    video_id: int,
    threshold: float = Query(0.6, ge=0, le=1),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """查找与指定视频标签相似的其他视频"""
    target_video = db.query(Video).filter(Video.id == video_id).first()
    if not target_video:
        raise HTTPException(status_code=404, detail="视频不存在")

    target_tags = []
    if target_video.tags:
        try:
            target_tags = json.loads(target_video.tags)
        except json.JSONDecodeError:
            pass

    if not target_tags:
        raise HTTPException(status_code=400, detail="目标视频没有标签")

    all_videos = db.query(Video).filter(Video.id != video_id).all()
    all_video_data = []

    for video in all_videos:
        all_video_data.append({
            'id': video.id,
            'title': video.title or video.filename,
            'tags': video.tags
        })

    similar_videos = llm_similarity_service.find_similar_videos(
        target_tags, all_video_data,
        threshold=threshold, limit=limit
    )

    result = []
    for item in similar_videos:
        video = item['video']
        result.append({
            'id': video['id'],
            'title': video['title'],
            'similarity': item['similarity'],
            'tags': json.loads(video['tags']) if isinstance(video['tags'], str) else video['tags']
        })

    return {
        'target_video': {
            'id': target_video.id,
            'title': target_video.title or target_video.filename,
            'tags': target_tags
        },
        'similar_videos': result
    }


@router.post("/integration/combine")
async def combine_knowledge_graphs(request: CombineKnowledgeGraphsRequest, db: Session = Depends(get_db)):
    """整合两个视频的知识图谱"""
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

    if not request.force_combine:
        can_combine = llm_similarity_service.can_combine_knowledge_graphs(
            source_tags, target_tags, threshold=request.threshold
        )

        if not can_combine:
            raise HTTPException(
                status_code=400,
                detail="视频标签相似度不足，无法自动整合知识图谱"
            )

    kg = KnowledgeGraphManager()
    success = kg.combine_knowledge_graphs(request.source_video_id, request.target_video_id)

    if success:
        return {
            "success": True,
            "message": f"成功整合视频 {request.source_video_id} 和视频 {request.target_video_id} 的知识图谱"
        }
    else:
        raise HTTPException(status_code=500, detail="知识图谱整合失败")


@router.get("/integration/check-combined/{video_id}")
async def check_combined_video(video_id: int):
    """检查视频是否参与了合并"""
    kg = KnowledgeGraphManager()

    is_combined = kg.is_combined_video(video_id)
    if is_combined:
        return {
            'is_combined': True,
            'combined_video_id': str(video_id)
        }

    combined_video_id = kg.find_combined_video_id(video_id)

    if combined_video_id:
        return {
            'is_combined': False,
            'is_part_of_combined': True,
            'combined_video_id': combined_video_id
        }
    else:
        return {
            'is_combined': False,
            'is_part_of_combined': False
        }


@router.post("/integration/combine-multiple")
async def combine_multiple_knowledge_graphs(request: CombineMultipleRequest, db: Session = Depends(get_db)):
    """整合多个视频的知识图谱"""
    video_ids = request.video_ids

    if len(video_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要两个视频才能进行合并")

    all_tags = []

    for vid in video_ids:
        video = db.query(Video).filter(Video.id == vid).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"视频(ID={vid})不存在")

        if video.tags:
            try:
                tags = json.loads(video.tags)
                all_tags.append(tags)
            except json.JSONDecodeError:
                all_tags.append([])
        else:
            all_tags.append([])

    if not request.force_combine:
        for i in range(len(video_ids)):
            for j in range(i + 1, len(video_ids)):
                can_combine = llm_similarity_service.can_combine_knowledge_graphs(
                    all_tags[i], all_tags[j], threshold=request.threshold
                )

                if not can_combine:
                    raise HTTPException(
                        status_code=400,
                        detail="部分视频标签相似度不足，无法自动整合知识图谱"
                    )

    kg = KnowledgeGraphManager()
    combined_video_id = kg.combine_multiple_knowledge_graphs(video_ids, request.threshold)

    if combined_video_id:
        return {
            "success": True,
            "message": f"成功整合 {len(video_ids)} 个视频的知识图谱",
            "combined_video_id": combined_video_id
        }
    else:
        raise HTTPException(status_code=500, detail="知识图谱整合失败")
