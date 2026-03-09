"""视频路由 - FastAPI 版本"""
import os
import re
import json
import hashlib
import logging
import traceback
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.models.qa import Question
from app.schemas.video import (
    VideoResponse,
    VideoListResponse,
    VideoStatusResponse,
    VideoUploadResponse,
    VideoProcessRequest,
    VideoUrlUploadRequest,
)

import sys
sys.path.append(str(settings.BASE_DIR))
from services.summary_generator import generate_video_summary
from services.tag_generator import generate_video_tags

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def secure_filename_with_chinese(filename: str) -> str:
    """安全的文件名处理，保留中文字符"""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip('. ')
    return filename


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    logger.info(f'收到上传请求: {file.filename}')

    if not file.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 读取文件内容并计算MD5
    file_content = await file.read()
    file_md5 = hashlib.md5(file_content).hexdigest()
    await file.seek(0)
    logger.info(f'文件MD5: {file_md5}')

    # 检查是否存在相同MD5的视频
    existing_video = db.query(Video).filter(Video.md5 == file_md5).first()
    if existing_video:
        logger.info(f'发现重复视频: {existing_video.filename}')
        return VideoUploadResponse(
            id=existing_video.id,
            status=existing_video.status.value if isinstance(existing_video.status, VideoStatus) else existing_video.status,
            message='视频已存在',
            duplicate=True,
            existingVideo=existing_video.to_dict()
        )

    # 确保上传目录存在
    upload_folder = settings.UPLOAD_FOLDER
    upload_folder.mkdir(parents=True, exist_ok=True)

    # 处理文件名
    original_filename = file.filename
    name, ext = os.path.splitext(original_filename)
    cleaned_name = secure_filename_with_chinese(name)
    title = f"local-{cleaned_name}"
    filename = f"{title}{ext}"
    file_path = upload_folder / filename

    # 如果文件已存在，添加时间戳
    if file_path.exists():
        title = f"{title}_{int(datetime.now().timestamp())}"
        filename = f"{title}{ext}"
        file_path = upload_folder / filename

    # 保存文件
    with open(file_path, 'wb') as f:
        f.write(file_content)
    logger.info(f'保存文件: {file_path}')

    # 创建视频记录
    video = Video(
        filename=filename,
        filepath=str(file_path),
        title=title,
        status=VideoStatus.UPLOADED,
        md5=file_md5
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    logger.info(f'创建视频记录: {video.id}')

    return VideoUploadResponse(
        id=video.id,
        status='uploaded',
        message='视频上传成功',
        duplicate=False,
        data=video.to_dict()
    )


@router.post("/upload-url", response_model=VideoUploadResponse)
async def upload_video_url(
    request: VideoUrlUploadRequest,
    db: Session = Depends(get_db)
):
    """通过URL上传视频（支持B站、YouTube、慕课）"""
    import yt_dlp

    video_url = request.url
    logger.info(f'处理视频URL: {video_url}')

    # 验证URL格式
    is_bilibili = 'bilibili.com' in video_url or 'b23.tv' in video_url
    is_youtube = 'youtube.com' in video_url or 'youtu.be' in video_url
    is_mooc = 'icourse163.org' in video_url

    if not (is_bilibili or is_youtube or is_mooc):
        raise HTTPException(status_code=400, detail='目前仅支持B站、YouTube和中国大学慕课视频')

    video_id = None
    title = None

    if is_bilibili:
        bv_match = re.search(r'BV[0-9A-Za-z]+', video_url)
        av_match = re.search(r'av\d+', video_url.lower())

        if bv_match:
            video_id = bv_match.group(0)
            title = f'bilibili-{video_id}'
        elif av_match:
            video_id = av_match.group(0)
            title = f'bilibili-{video_id}'
        else:
            raise HTTPException(status_code=400, detail='无效的B站视频链接')

    elif is_youtube:
        if 'youtube.com' in video_url:
            video_id_match = re.search(r'v=([^&]+)', video_url)
            if video_id_match:
                video_id = video_id_match.group(1)
        elif 'youtu.be' in video_url:
            video_id = video_url.split('/')[-1].split('?')[0]

        if not video_id:
            raise HTTPException(status_code=400, detail='无效的YouTube视频链接')
        title = f'youtube-{video_id}'

    elif is_mooc:
        mooc_url = video_url.split('#')[0]
        course_id_match = re.search(r'learn/([^-]+)-(\d+)', mooc_url)
        if not course_id_match:
            course_id_match = re.search(r'courseId=(\d+)', mooc_url)

        if course_id_match:
            if len(course_id_match.groups()) > 1:
                course_id = course_id_match.group(2)
            else:
                course_id = course_id_match.group(1)
            title = f'mooc-{course_id}'
        else:
            raise HTTPException(status_code=400, detail='无效的慕课视频链接')

    # 创建临时视频记录
    temp_video = Video(
        title=title,
        url=video_url,
        status=VideoStatus.DOWNLOADING
    )
    db.add(temp_video)
    db.commit()
    db.refresh(temp_video)
    logger.info(f'创建临时视频记录: {temp_video.id}')

    # 确保下载目录存在
    download_folder = settings.UPLOAD_FOLDER
    download_folder.mkdir(parents=True, exist_ok=True)

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    try:
        common_opts = {
            'merge_output_format': 'mp4',
            'outtmpl': str(download_folder / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        if is_bilibili:
            ydl_opts = {
                **common_opts,
                'format': 'bestvideo*+bestaudio/best',
                'http_headers': {
                    'Referer': 'https://www.bilibili.com',
                    'User-Agent': user_agent
                }
            }
        elif is_youtube:
            ydl_opts = {
                'outtmpl': str(download_folder / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'concurrent_fragment_downloads': 4,
                'retries': 10,
                'fragment_retries': 10,
                'proxy': 'http://127.0.0.1:7890',
                'http_headers': {'User-Agent': user_agent},
                'nocheckcertificate': True,
                'cookiesfrombrowser': ('chrome',),
            }
        else:  # is_mooc
            ydl_opts = {
                **common_opts,
                'format': 'best',
                'http_headers': {
                    'User-Agent': user_agent,
                    'Referer': 'https://www.icourse163.org/',
                },
                'nocheckcertificate': True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', '未知标题')
            video_title = secure_filename_with_chinese(video_title)
            prefix = 'bilibili-' if is_bilibili else ('youtube-' if is_youtube else 'mooc-')
            title = f"{prefix}{video_title}"

            ydl_opts['outtmpl'] = str(download_folder / f'{title}.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                ydl2.download([video_url])

            filename = f"{title}.mp4"
            filepath = download_folder / filename

            if not filepath.exists():
                raise FileNotFoundError(f"下载的视频文件不存在: {filepath}")

            logger.info(f'✅ 视频下载成功: {filepath}')

        # 更新视频记录
        temp_video.filename = filename
        temp_video.filepath = str(filepath)
        temp_video.title = title
        temp_video.status = VideoStatus.UPLOADED
        db.commit()

        return VideoUploadResponse(
            id=temp_video.id,
            status='uploaded',
            message='视频上传成功',
            duplicate=False
        )

    except Exception as e:
        logger.error(f"下载视频失败: {str(e)}")
        temp_video.status = VideoStatus.FAILED
        temp_video.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f'下载视频失败: {str(e)}')


@router.get("/list", response_model=VideoListResponse)
async def get_video_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取视频列表"""
    logger.info(f"获取视频列表: page={page}, per_page={per_page}")

    videos = db.query(Video).order_by(Video.upload_time.desc()).limit(100).all()

    result = []
    for video in videos:
        status = video.status.value if hasattr(video.status, 'value') else str(video.status)
        tags = []
        if video.tags:
            try:
                tags = json.loads(video.tags)
            except Exception:
                pass

        video_data = {
            'id': video.id,
            'title': video.title or '',
            'filename': video.filename or '',
            'status': status,
            'upload_time': video.upload_time.isoformat() if video.upload_time else None,
            'preview_filename': video.preview_filename,
            'duration': video.duration,
            'width': video.width,
            'height': video.height,
            'fps': video.fps,
            'summary': video.summary,
            'tags': tags,
        }
        result.append(video_data)

    # 手动分页
    total = len(result)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_result = result[start_idx:end_idx] if start_idx < total else []

    return VideoListResponse(
        videos=paginated_result,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """获取单个视频信息"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    return VideoResponse(**video.to_dict())


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """获取视频处理状态"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    status_map = {
        VideoStatus.COMPLETED: 'completed',
        VideoStatus.PROCESSING: 'processing',
        VideoStatus.FAILED: 'failed',
        VideoStatus.UPLOADED: 'uploaded',
        VideoStatus.PENDING: 'pending',
        VideoStatus.DOWNLOADING: 'downloading',
    }

    status = status_map.get(video.status, str(video.status.value if hasattr(video.status, 'value') else video.status))

    return VideoStatusResponse(
        id=video.id,
        status=status,
        progress=video.process_progress or 0,
        current_step=video.current_step,
        task_id=video.task_id
    )


@router.post("/{video_id}/process")
async def process_video(
    video_id: int,
    request: VideoProcessRequest,
    db: Session = Depends(get_db)
):
    """开始处理视频"""
    from app.utils.platform_utils import import_video_processing

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    valid_statuses = [VideoStatus.UPLOADED, VideoStatus.PENDING, VideoStatus.FAILED, VideoStatus.COMPLETED]
    if video.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f'视频状态不正确: {video.status.name}')

    whisper_language = 'en' if request.language == 'English' else 'zh'
    whisper_model = request.model

    video.status = VideoStatus.PENDING
    db.commit()

    process_video_task = import_video_processing()
    task = process_video_task.delay(video.id, whisper_language, whisper_model)

    video.task_id = task.id
    db.commit()

    return {"status": "success", "message": "视频处理已开始", "task_id": task.id}


@router.delete("/{video_id}/delete")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """删除视频"""
    import platform as plat

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 删除关联的问题记录
    db.query(Question).filter(Question.video_id == video_id).delete()
    db.commit()

    # 导入清理任务
    if plat.system() == "Darwin":
        from app.tasks.video_processing_mac import cleanup_video
    else:
        from app.tasks.video_processing import cleanup_video

    task = cleanup_video.delay(video.id)

    db.delete(video)
    db.commit()

    return {"message": "视频删除任务已启动", "video_id": video_id, "task_id": task.id}


@router.get("/{video_id}/stream")
async def get_video_stream(video_id: int, db: Session = Depends(get_db)):
    """流式传输视频"""
    from starlette.requests import Request

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not os.path.exists(video.filepath):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    file_size = os.path.getsize(video.filepath)

    def iterfile(start: int = 0, end: int = None):
        with open(video.filepath, 'rb') as f:
            f.seek(start)
            remaining = (end - start + 1) if end else file_size - start
            while remaining:
                chunk_size = min(8192, remaining)
                data = f.read(chunk_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Type': 'video/mp4',
    }

    return StreamingResponse(
        iterfile(),
        headers=headers,
        media_type='video/mp4'
    )


@router.get("/{video_id}/preview")
async def get_video_preview(video_id: int, db: Session = Depends(get_db)):
    """获取视频预览图"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.preview_filepath or not os.path.exists(video.preview_filepath):
        raise HTTPException(status_code=404, detail="预览图不存在")

    return FileResponse(video.preview_filepath, media_type='image/jpeg')


@router.get("/{video_id}/subtitle")
async def get_subtitle(
    video_id: int,
    format: str = Query("srt", regex="^(srt|vtt|txt)$"),
    download: bool = Query(False),
    db: Session = Depends(get_db)
):
    """获取视频字幕"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 查找字幕文件
    subtitle_path = None
    possible_paths = [
        video.subtitle_filepath,
        str(settings.SUBTITLE_FOLDER / f"{video.filename}.srt"),
        str(settings.SUBTITLE_FOLDER / f"{os.path.splitext(video.filename)[0]}.srt") if video.filename else None,
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            subtitle_path = path
            break

    if not subtitle_path:
        raise HTTPException(status_code=404, detail="字幕文件不存在")

    with open(subtitle_path, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.splitext(video.filename)[0] if video.filename else f"video_{video_id}"

    if format == 'vtt':
        vtt_content = 'WEBVTT\n\n' + content.replace(',', '.')
        response = Response(content=vtt_content, media_type='text/vtt; charset=utf-8')
    elif format == 'txt':
        txt_content = re.sub(
            r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n',
            '', content, flags=re.MULTILINE
        )
        txt_content = re.sub(r'^\s*\n', '', txt_content, flags=re.MULTILINE)
        response = Response(content=txt_content, media_type='text/plain; charset=utf-8')
    else:
        response = Response(content=content, media_type='text/plain; charset=utf-8')

    if download:
        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename}.{format}"

    return response


@router.post("/{video_id}/generate-summary")
async def generate_summary(video_id: int, db: Session = Depends(get_db)):
    """为视频生成内容摘要"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成，请先处理视频")

    # 查找字幕文件
    subtitle_path = None
    if video.subtitle_filepath:
        possible_paths = [
            video.subtitle_filepath,
            str(settings.UPLOAD_FOLDER / 'subtitles' / os.path.basename(video.subtitle_filepath)),
            str(settings.UPLOAD_FOLDER / os.path.basename(video.subtitle_filepath)),
        ]
        for path in possible_paths:
            if path and os.path.exists(path):
                subtitle_path = path
                break

    if not subtitle_path:
        raise HTTPException(status_code=400, detail="视频没有字幕文件，无法生成摘要")

    result = generate_video_summary(video_id, subtitle_path)

    if not result['success']:
        raise HTTPException(status_code=500, detail=f"生成摘要失败: {result['error']}")

    video.summary = result['summary']
    db.commit()

    return {"success": True, "summary": result['summary']}


@router.post("/{video_id}/generate-tags")
async def generate_tags(video_id: int, db: Session = Depends(get_db)):
    """为视频生成标签"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成，请先处理视频")

    if not video.summary:
        raise HTTPException(status_code=400, detail="视频没有摘要，请先生成摘要")

    result = generate_video_tags(video_id, video.summary)

    if not result['success']:
        raise HTTPException(status_code=500, detail=f"生成标签失败: {result['error']}")

    video.tags = json.dumps(result['tags'], ensure_ascii=False)
    db.commit()

    return {"success": True, "tags": result['tags']}
