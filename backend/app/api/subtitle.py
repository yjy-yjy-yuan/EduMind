"""字幕路由 - FastAPI 版本"""
import os
import io
import json
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.video import Video
from app.models.subtitle import Subtitle
from app.schemas.subtitle import (
    SubtitleResponse,
    SubtitleUpdate,
    SubtitleListResponse,
    SubtitleGenerateRequest,
    SemanticMergedSubtitle,
)
from app.utils.subtitle_utils import (
    convert_to_srt, convert_to_vtt, convert_to_txt,
    validate_subtitle_time, merge_subtitles
)
from app.utils.semantic_utils import merge_subtitles_by_semantics_ollama

logger = logging.getLogger(__name__)

router = APIRouter()


def check_redis_connection() -> bool:
    """检查Redis连接"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except Exception as e:
        logger.error(f"Redis连接错误: {str(e)}")
        return False


def format_seconds_to_srt_time(seconds: float) -> str:
    """将秒数转换为SRT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def format_seconds_to_vtt_time(seconds: float) -> str:
    """将秒数转换为VTT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def format_seconds_to_display_time(seconds: float) -> str:
    """将秒数转换为显示时间格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def convert_merged_to_srt(merged_subtitles: list) -> str:
    """将合并字幕转换为SRT格式"""
    srt_content = ""
    for i, subtitle in enumerate(merged_subtitles):
        start_time = format_seconds_to_srt_time(subtitle['start_time'])
        end_time = format_seconds_to_srt_time(subtitle['end_time'])
        srt_content += f"{i+1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return srt_content


def convert_merged_to_vtt(merged_subtitles: list) -> str:
    """将合并字幕转换为VTT格式"""
    vtt_content = "WEBVTT\n\n"
    for i, subtitle in enumerate(merged_subtitles):
        start_time = format_seconds_to_vtt_time(subtitle['start_time'])
        end_time = format_seconds_to_vtt_time(subtitle['end_time'])
        vtt_content += f"{i+1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return vtt_content


def convert_merged_to_txt(merged_subtitles: list) -> str:
    """将合并字幕转换为TXT格式"""
    txt_content = ""
    for subtitle in merged_subtitles:
        start_time = format_seconds_to_display_time(subtitle['start_time'])
        end_time = format_seconds_to_display_time(subtitle['end_time'])
        title = subtitle.get('title', '无标题')
        txt_content += f"[{start_time} - {end_time}] {title}\n{subtitle['text']}\n\n"
    return txt_content


def parse_srt_content(subtitle_content: str) -> list:
    """解析SRT字幕内容"""
    subtitle_blocks = subtitle_content.strip().split('\n\n')
    subtitles = []

    for block in subtitle_blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            if '-->' in time_line:
                start_time_str, end_time_str = time_line.split('-->')

                start_time_parts = start_time_str.strip().split(':')
                if len(start_time_parts) == 2:
                    start_minutes = int(start_time_parts[0])
                    start_seconds = float(start_time_parts[1].replace(',', '.'))
                    start_time = start_minutes * 60 + start_seconds
                else:
                    start_hours = int(start_time_parts[0])
                    start_minutes = int(start_time_parts[1])
                    start_seconds = float(start_time_parts[2].replace(',', '.'))
                    start_time = start_hours * 3600 + start_minutes * 60 + start_seconds

                end_time_parts = end_time_str.strip().split(':')
                if len(end_time_parts) == 2:
                    end_minutes = int(end_time_parts[0])
                    end_seconds = float(end_time_parts[1].replace(',', '.'))
                    end_time = end_minutes * 60 + end_seconds
                else:
                    end_hours = int(end_time_parts[0])
                    end_minutes = int(end_time_parts[1])
                    end_seconds = float(end_time_parts[2].replace(',', '.'))
                    end_time = end_hours * 3600 + end_minutes * 60 + end_seconds

                text = '\n'.join(lines[2:])

                subtitles.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text
                })

    return subtitles


@router.get("/videos/{video_id}/subtitles", response_model=SubtitleListResponse)
async def get_video_subtitles(video_id: int, db: Session = Depends(get_db)):
    """获取视频的所有字幕"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail=f"未找到ID为{video_id}的视频")

    subtitles = db.query(Subtitle).filter(Subtitle.video_id == video_id).all()

    subtitle_list = [SubtitleResponse.model_validate(sub) for sub in subtitles]

    return SubtitleListResponse(
        video_id=video_id,
        video_status=video.status.value if hasattr(video.status, 'value') else str(video.status),
        subtitles=subtitle_list
    )


@router.post("/videos/{video_id}/subtitles/generate")
async def generate_video_subtitles(
    video_id: int,
    request: SubtitleGenerateRequest,
    db: Session = Depends(get_db)
):
    """生成视频字幕"""
    if not check_redis_connection():
        raise HTTPException(status_code=500, detail="Redis服务未运行或连接失败")

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail=f"未找到ID为{video_id}的视频")

    from app.tasks.subtitle_tasks import generate_subtitles as generate_subtitles_task
    task = generate_subtitles_task.delay(
        video_id=video_id,
        language=request.language,
        model_name=request.whisper_model
    )

    return {
        "status": "success",
        "message": "字幕生成任务已启动",
        "task_id": task.id
    }


@router.get("/videos/{video_id}/subtitles/semantic-merged")
async def get_merged_subtitles(
    video_id: int,
    force_refresh: bool = Query(False),
    format: str = Query(None, regex="^(srt|vtt|txt)$"),
    db: Session = Depends(get_db)
):
    """获取语义合并后的字幕"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
        raise HTTPException(status_code=404, detail="字幕文件不存在")

    # 缓存目录
    cache_dir = settings.CACHE_FOLDER
    cache_dir.mkdir(parents=True, exist_ok=True)

    video_name = video.filename.rsplit('.', 1)[0] if video.filename else f'video_{video_id}'
    cache_file = cache_dir / f'{video_name}_semantic.json'

    merged_subtitles = None

    # 尝试读取缓存
    if cache_file.exists() and not force_refresh:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                merged_subtitles = json.load(f)
            logger.info(f"使用缓存的语义合并字幕: {cache_file}")
        except Exception as e:
            logger.error(f"读取缓存文件时出错: {str(e)}")

    # 如果没有缓存，重新生成
    if merged_subtitles is None:
        with open(video.subtitle_filepath, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()

        subtitles = parse_srt_content(subtitle_content)
        logger.info(f"从文件中解析出{len(subtitles)}条字幕")

        if not subtitles:
            return []

        merged_subtitles = merge_subtitles_by_semantics_ollama(subtitles)
        logger.info(f"合并后的字幕数量: {len(merged_subtitles)}")

        # 保存到缓存
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(merged_subtitles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存文件时出错: {str(e)}")

    # 如果请求下载特定格式
    if format:
        if not merged_subtitles:
            raise HTTPException(status_code=404, detail="没有可用的合并字幕")

        if format == 'srt':
            content = convert_merged_to_srt(merged_subtitles)
            mimetype = 'text/plain'
        elif format == 'vtt':
            content = convert_merged_to_vtt(merged_subtitles)
            mimetype = 'text/vtt'
        else:  # txt
            content = convert_merged_to_txt(merged_subtitles)
            mimetype = 'text/plain'

        video_title = video.title or f"video_{video_id}"
        filename = f"merged-{video_title}.{format}"

        return StreamingResponse(
            iter([content.encode('utf-8')]),
            media_type=mimetype,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    return merged_subtitles


@router.post("/videos/{video_id}/subtitles/semantic-merge")
async def trigger_semantic_merge(video_id: int, db: Session = Depends(get_db)):
    """触发字幕的语义合并处理"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
        raise HTTPException(status_code=404, detail="字幕文件不存在")

    with open(video.subtitle_filepath, 'r', encoding='utf-8') as f:
        subtitle_content = f.read()

    subtitles = parse_srt_content(subtitle_content)
    logger.info(f"从文件中解析出{len(subtitles)}条字幕")

    if not subtitles:
        raise HTTPException(status_code=400, detail="没有解析出有效的字幕")

    # 缓存文件路径
    cache_dir = settings.CACHE_FOLDER
    cache_dir.mkdir(parents=True, exist_ok=True)

    video_name = video.filename.rsplit('.', 1)[0] if video.filename else f'video_{video_id}'
    cache_file = cache_dir / f'{video_name}_semantic.json'

    # 删除现有缓存
    if cache_file.exists():
        try:
            os.remove(cache_file)
        except Exception as e:
            logger.error(f"删除现有缓存文件时出错: {str(e)}")

    # 调用语义合并函数
    merged_subtitles = merge_subtitles_by_semantics_ollama(subtitles)
    logger.info(f"合并后的字幕数量: {len(merged_subtitles)}")

    if not merged_subtitles:
        raise HTTPException(status_code=500, detail="合并字幕失败，结果为空")

    # 保存到缓存
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(merged_subtitles, f, ensure_ascii=False, indent=2)

    return {"success": True, "message": "语义合并处理完成", "count": len(merged_subtitles)}


@router.get("/videos/{video_id}/subtitles/export")
async def export_subtitles(
    video_id: int,
    format: str = Query("srt", regex="^(srt|vtt|txt)$"),
    db: Session = Depends(get_db)
):
    """导出字幕文件"""
    subtitles = db.query(Subtitle).filter(Subtitle.video_id == video_id).order_by(Subtitle.start_time).all()
    if not subtitles:
        raise HTTPException(status_code=404, detail="未找到字幕数据")

    subtitle_list = [sub.to_dict() for sub in subtitles]

    if format == 'srt':
        content = convert_to_srt(subtitle_list)
        mime_type = 'application/x-subrip'
    elif format == 'vtt':
        content = convert_to_vtt(subtitle_list)
        mime_type = 'text/vtt'
    else:
        content = convert_to_txt(subtitle_list)
        mime_type = 'text/plain'

    video = db.query(Video).filter(Video.id == video_id).first()
    filename = f"{video.title}_{video.id}.{format}" if video else f"subtitles_{video_id}.{format}"

    return StreamingResponse(
        iter([content.encode('utf-8')]),
        media_type=mime_type,
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
    )


@router.put("/videos/{video_id}/subtitles/{subtitle_id}")
async def update_subtitle(
    video_id: int,
    subtitle_id: int,
    request: SubtitleUpdate,
    db: Session = Depends(get_db)
):
    """更新字幕内容"""
    subtitle = db.query(Subtitle).filter(
        Subtitle.id == subtitle_id,
        Subtitle.video_id == video_id
    ).first()

    if not subtitle:
        raise HTTPException(status_code=404, detail="未找到指定字幕")

    if request.text is not None:
        subtitle.update_text(request.text, editor=request.editor)

    if request.start_time is not None or request.end_time is not None:
        start_time = request.start_time if request.start_time is not None else subtitle.start_time
        end_time = request.end_time if request.end_time is not None else subtitle.end_time

        video = db.query(Video).filter(Video.id == video_id).first()
        is_valid, error_msg = validate_subtitle_time(
            start_time, end_time, video.duration if video else None
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        subtitle.start_time = start_time
        subtitle.end_time = end_time

    db.commit()
    db.refresh(subtitle)

    return {
        "status": "success",
        "message": "字幕更新成功",
        "subtitle": subtitle.to_dict()
    }


@router.post("/videos/{video_id}/subtitles/merge")
async def merge_subtitle_segments(video_id: int, db: Session = Depends(get_db)):
    """合并字幕片段"""
    subtitles = db.query(Subtitle).filter(Subtitle.video_id == video_id).order_by(Subtitle.start_time).all()
    if not subtitles:
        raise HTTPException(status_code=404, detail="未找到字幕数据")

    subtitle_list = [sub.to_dict() for sub in subtitles]
    merged_subtitles = merge_subtitles(subtitle_list)

    # 删除旧字幕
    db.query(Subtitle).filter(Subtitle.video_id == video_id).delete()

    # 添加新字幕
    for sub in merged_subtitles:
        new_subtitle = Subtitle(
            video_id=video_id,
            start_time=sub['start_time'],
            end_time=sub['end_time'],
            text=sub['text'],
            language=sub['language'],
            source='merged'
        )
        db.add(new_subtitle)

    db.commit()

    new_subtitles = db.query(Subtitle).filter(Subtitle.video_id == video_id).all()

    return {
        "status": "success",
        "message": "字幕合并成功",
        "subtitles": [sub.to_dict() for sub in new_subtitles]
    }
