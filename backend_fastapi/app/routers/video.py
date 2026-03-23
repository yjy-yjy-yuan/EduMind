"""视频管理路由 - FastAPI 版本"""

import hashlib
import json
import logging
import mimetypes
import os
import re
import tempfile
import traceback
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.subtitle import Subtitle
from app.models.video import Video
from app.models.video import VideoProcessingOrigin
from app.models.video import VideoStatus
from app.schemas.video import OfflineTranscriptSyncRequest
from app.schemas.video import TranscriptSummaryRequest
from app.schemas.video import VideoDetail
from app.schemas.video import VideoListResponse
from app.schemas.video import VideoProcessingOptionsResponse
from app.schemas.video import VideoProcessRequest
from app.schemas.video import VideoStatusResponse
from app.schemas.video import VideoSummaryRequest
from app.schemas.video import VideoTagRequest
from app.schemas.video import VideoUploadResponse
from app.schemas.video import VideoUploadURL
from app.services.video_content_service import generate_primary_topic_name
from app.services.video_content_service import generate_video_summary
from app.services.video_content_service import normalize_summary_style
from app.services.video_content_service import read_subtitle_text
from app.services.video_processing_registry import forget_video_processing_request
from app.services.video_processing_registry import get_video_processing_request
from app.services.video_processing_registry import remember_video_processing_request
from app.services.whisper_runtime import get_supported_whisper_models
from app.services.whisper_runtime import get_whisper_model_catalog
from app.services.whisper_runtime import normalize_whisper_model_name
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {ext.lower() for ext in settings.ALLOWED_EXTENSIONS}
UPLOAD_CHUNK_SIZE = 1024 * 1024
STREAM_CHUNK_SIZE = 1024 * 1024
BYTE_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")
MODEL_STEP_RE = re.compile(r"（([a-z0-9._-]+)）")


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def secure_filename_with_chinese(filename: str) -> str:
    """安全的文件名处理，保留中文字符"""
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = filename.strip(". ")
    return filename


def build_local_video_path(original_filename: str) -> tuple[str, str, str]:
    """构建本地上传视频的标题、文件名和落盘路径"""
    name, ext = os.path.splitext(original_filename)
    cleaned_name = secure_filename_with_chinese(name) or "video"
    title = f"local-{cleaned_name}"
    filename = f"{title}{ext.lower()}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)

    if os.path.exists(file_path):
        import time

        title = f"{title}_{int(time.time())}"
        filename = f"{title}{ext.lower()}"
        file_path = os.path.join(settings.UPLOAD_FOLDER, filename)

    return title, filename, file_path


def resolve_upload_source(video: Video) -> str:
    """计算上传来源标识"""
    return "url_import" if video.url else "local_file"


def resolve_upload_source_label(video: Video) -> str:
    """计算上传来源中文标签"""
    return "链接导入" if video.url else "本地上传"


def resolve_upload_source_value(video: Video) -> Optional[str]:
    """计算上传来源值：链接导入为 URL，本地上传为文件名"""
    if video.url:
        return video.url
    return video.filename


def resolve_video_media_type(video: Video) -> str:
    """根据文件名推断媒体类型，默认回退到 MP4。"""
    media_type, _ = mimetypes.guess_type(video.filename or video.filepath or "")
    return media_type or "video/mp4"


def parse_byte_range(range_header: Optional[str], file_size: int) -> Optional[tuple[int, int]]:
    """解析 HTTP Range 头，支持 bytes=start-end 与 bytes=-suffix。"""
    if not range_header:
        return None

    match = BYTE_RANGE_RE.fullmatch(range_header.strip())
    if not match:
        raise HTTPException(
            status_code=416,
            detail="无效的 Range 请求",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    start_text, end_text = match.groups()
    if not start_text and not end_text:
        raise HTTPException(
            status_code=416,
            detail="无效的 Range 请求",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    if not start_text:
        suffix_size = int(end_text)
        if suffix_size <= 0:
            raise HTTPException(
                status_code=416,
                detail="无效的 Range 请求",
                headers={"Content-Range": f"bytes */{file_size}"},
            )
        start = max(file_size - suffix_size, 0)
        end = file_size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1

    if start < 0 or start >= file_size or end < start:
        raise HTTPException(
            status_code=416,
            detail="无效的 Range 请求",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    return start, min(end, file_size - 1)


def iter_file_chunk(filepath: str, start: int = 0, end: Optional[int] = None):
    """按范围分块读取视频文件，供 StreamingResponse 使用。"""
    with open(filepath, "rb") as file_obj:
        file_obj.seek(start)
        remaining = None if end is None else end - start + 1

        while True:
            chunk_size = STREAM_CHUNK_SIZE if remaining is None else min(STREAM_CHUNK_SIZE, remaining)
            if chunk_size <= 0:
                break
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk
            if remaining is not None:
                remaining -= len(chunk)


def build_processing_options(
    *,
    language: str = "Other",
    model: Optional[str] = None,
    auto_generate_summary: bool = True,
    auto_generate_tags: bool = True,
    summary_style: str = "study",
) -> dict:
    """规范化视频处理参数。"""
    whisper_language = "en" if str(language or "").strip() == "English" else "zh"
    auto_tags = bool(auto_generate_tags)
    try:
        normalized_model = normalize_whisper_model_name(model or settings.WHISPER_MODEL)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "language": whisper_language,
        "model": normalized_model,
        "auto_generate_summary": bool(auto_generate_summary or auto_tags),
        "auto_generate_tags": auto_tags,
        "summary_style": normalize_summary_style(summary_style),
    }


def infer_model_from_step(step: Optional[str]) -> Optional[str]:
    text = str(step or "").strip()
    if not text:
        return None
    match = MODEL_STEP_RE.search(text)
    return match.group(1).strip() if match else None


def build_processing_metadata(video: Video) -> dict:
    request_meta = get_video_processing_request(video.id) or {}
    requested_model = str(request_meta.get("requested_model") or "").strip() or infer_model_from_step(
        video.current_step
    )
    effective_model = str(request_meta.get("effective_model") or requested_model or "").strip() or None
    requested_language = str(request_meta.get("requested_language") or "").strip() or None
    return {
        "requested_model": requested_model or None,
        "effective_model": effective_model,
        "requested_language": requested_language,
    }


def serialize_video(video: Video) -> dict:
    payload = video.to_dict()
    payload.update(build_processing_metadata(video))
    return payload


def normalize_offline_filename(original_name: str, original_ext: str = "") -> str:
    text = secure_filename_with_chinese(str(original_name or "").strip()) or "ios-offline-video"
    ext = str(original_ext or "").strip().lower()
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    return f"{text}{ext}" if ext and not text.lower().endswith(ext) else text


def build_offline_video_title(summary: str, *, fallback_title: str = "") -> str:
    result = generate_primary_topic_name(summary, title=fallback_title)
    if result.get("success"):
        return str(result["name"]).strip()
    fallback = secure_filename_with_chinese(fallback_title) or "iOS离线视频"
    return fallback[:80]


def sync_offline_subtitles(db: Session, video_id: int, transcript_text: str, segments, *, locale: str = "") -> int:
    db.query(Subtitle).filter(Subtitle.video_id == video_id).delete()
    rows = []
    language = "en" if str(locale or "").lower().startswith("en") else "zh"

    for segment in segments or []:
        text = str(segment.text or "").strip()
        if not text:
            continue
        start = max(0.0, float(segment.start or 0.0))
        duration = max(0.0, float(segment.duration or 0.0))
        end = start + duration if duration > 0 else start
        rows.append(
            Subtitle(
                video_id=video_id,
                start_time=start,
                end_time=end,
                text=text,
                source="asr",
                language=language,
            )
        )

    if not rows and str(transcript_text or "").strip():
        rows.append(
            Subtitle(
                video_id=video_id,
                start_time=0.0,
                end_time=0.0,
                text=str(transcript_text).strip(),
                source="asr",
                language=language,
            )
        )

    if rows:
        db.add_all(rows)
    db.commit()
    return len(rows)


def extract_video_transcript_text(video: Video) -> str:
    """优先从字幕表读取纯文本，缺失时回退到字幕文件。"""
    subtitle_rows = getattr(video, "subtitles", None) or []
    subtitle_texts = [str(row.text or "").strip() for row in subtitle_rows if str(row.text or "").strip()]
    if subtitle_texts:
        return " ".join(subtitle_texts)
    return read_subtitle_text(video.subtitle_filepath or "")


def submit_video_processing(
    video: Video,
    db: Session,
    *,
    language: str = "zh",
    model: Optional[str] = None,
    auto_generate_summary: bool = True,
    auto_generate_tags: bool = True,
    summary_style: str = "study",
    raise_on_error: bool = False,
) -> bool:
    """提交视频处理任务并将状态写回当前视频记录。"""
    normalized_model = str(model or settings.WHISPER_MODEL).strip() or settings.WHISPER_MODEL
    previous_status = video.status
    previous_progress = video.process_progress or 0.0
    previous_step = video.current_step
    previous_error = video.error_message

    video.status = VideoStatus.PENDING
    video.process_progress = 0.0
    video.current_step = f"已提交，等待处理（{normalized_model}）"
    video.error_message = None
    db.commit()

    try:
        from app.core.executor import submit_task
        from app.tasks.video_processing import process_video_task

        submit_task(
            process_video_task,
            video.id,
            language,
            normalized_model,
            auto_generate_summary=auto_generate_summary,
            auto_generate_tags=auto_generate_tags,
            summary_style=normalize_summary_style(summary_style),
        )
        remember_video_processing_request(
            video.id,
            model=normalized_model,
            language=language,
            source="submit_video_processing",
        )
        return True
    except Exception as exc:
        logger.error("提交视频处理任务失败 | video_id=%s | error=%s", video.id, exc)
        video.status = previous_status
        video.process_progress = previous_progress
        video.current_step = previous_step
        video.error_message = str(exc)[:1000] if str(exc).strip() else previous_error
        db.commit()

        if raise_on_error:
            raise HTTPException(status_code=500, detail="提交视频处理任务失败，请稍后重试")
        return False


async def save_upload_to_temp(file: UploadFile) -> tuple[str, str, int]:
    """分块写入临时文件并计算 MD5"""
    os.makedirs(settings.TEMP_FOLDER, exist_ok=True)
    suffix = os.path.splitext(file.filename or "")[1]
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=settings.TEMP_FOLDER, suffix=suffix)
    digest = hashlib.md5()
    total_size = 0

    try:
        while True:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break

            total_size += len(chunk)
            if total_size > settings.MAX_CONTENT_LENGTH:
                raise HTTPException(
                    status_code=413,
                    detail=f"文件过大，当前上限为 {settings.MAX_CONTENT_LENGTH // (1024 * 1024)}MB",
                )

            digest.update(chunk)
            temp_file.write(chunk)

        if total_size <= 0:
            raise HTTPException(status_code=400, detail="上传文件为空")

        temp_file.flush()
        return temp_file.name, digest.hexdigest(), total_size
    except Exception:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise
    finally:
        temp_file.close()
        await file.seek(0)


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    language: str = Form("Other"),
    model: str = Form("base"),
    auto_generate_summary: bool = Form(True),
    auto_generate_tags: bool = Form(True),
    summary_style: str = Form("study"),
    db: Session = Depends(get_db),
):
    """上传视频文件"""
    logger.info(f"收到文件上传请求: {file.filename}")

    if not file.filename or not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    temp_path = None
    try:
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        temp_path, file_md5, file_size = await save_upload_to_temp(file)
        logger.info(f"文件MD5: {file_md5}")

        # 检查重复
        existing_video = db.query(Video).filter(Video.md5 == file_md5).first()
        if existing_video:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                temp_path = None
            return VideoUploadResponse(
                id=existing_video.id,
                status=(
                    existing_video.status.value
                    if hasattr(existing_video.status, "value")
                    else str(existing_video.status)
                ),
                message="视频已存在",
                duplicate=True,
                data=serialize_video(existing_video),
            )

        title, filename, file_path = build_local_video_path(file.filename)
        os.replace(temp_path, file_path)
        temp_path = None

        # 创建数据库记录
        video = Video(
            filename=filename,
            filepath=file_path,
            title=title,
            url=None,
            status=VideoStatus.UPLOADED,
            md5=file_md5,
            process_progress=0.0,
            current_step="已上传，等待处理",
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        process_options = build_processing_options(
            language=language,
            model=model,
            auto_generate_summary=auto_generate_summary,
            auto_generate_tags=auto_generate_tags,
            summary_style=summary_style,
        )

        task_submitted = submit_video_processing(video, db, **process_options)
        db.refresh(video)

        logger.info(f"视频上传成功: ID={video.id}, size={file_size}")

        return VideoUploadResponse(
            id=video.id,
            status=video.status.value if hasattr(video.status, "value") else str(video.status),
            message="视频上传成功，已开始后台处理" if task_submitted else "视频上传成功，请手动开始处理",
            duplicate=False,
            data=serialize_video(video),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传错误: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="上传失败，请重试")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/upload-url", response_model=VideoUploadResponse)
async def upload_video_url(data: VideoUploadURL, db: Session = Depends(get_db)):
    """通过 URL 上传视频"""
    video_url = data.url
    logger.info(f"处理视频URL: {video_url}")

    # 验证 URL 格式
    is_bilibili = "bilibili.com" in video_url or "b23.tv" in video_url
    is_youtube = "youtube.com" in video_url or "youtu.be" in video_url
    is_mooc = "icourse163.org" in video_url

    if not (is_bilibili or is_youtube or is_mooc):
        raise HTTPException(status_code=400, detail="目前仅支持B站、YouTube和中国大学慕课视频")

    existing_video = (
        db.query(Video)
        .filter(Video.url == video_url, Video.status != VideoStatus.FAILED)
        .order_by(Video.upload_time.desc())
        .first()
    )
    if existing_video:
        return VideoUploadResponse(
            id=existing_video.id,
            status=(
                existing_video.status.value if hasattr(existing_video.status, "value") else str(existing_video.status)
            ),
            message="该视频链接已提交过",
            duplicate=True,
            data=serialize_video(existing_video),
        )

    video_id = None
    title = None
    source_type = "video"

    if is_bilibili:
        bv_match = re.search(r"BV[0-9A-Za-z]+", video_url)
        av_match = re.search(r"av\d+", video_url.lower())
        if bv_match:
            video_id = bv_match.group(0)
            title = f"bilibili-{video_id}"
        elif av_match:
            video_id = av_match.group(0)
            title = f"bilibili-{video_id}"
        else:
            raise HTTPException(status_code=400, detail="无效的B站视频链接")
        source_type = "bilibili"
    elif is_youtube:
        if "youtube.com" in video_url:
            match = re.search(r"v=([^&]+)", video_url)
            if match:
                video_id = match.group(1)
        elif "youtu.be" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        if not video_id:
            raise HTTPException(status_code=400, detail="无效的YouTube视频链接")
        title = f"youtube-{video_id}"
        source_type = "youtube"
    elif is_mooc:
        course_match = re.search(r"learn/([^-]+)-(\d+)", video_url)
        if course_match:
            course_id = course_match.group(2)
            title = f"mooc-{course_id}"
            video_id = course_id
        else:
            raise HTTPException(status_code=400, detail="无效的慕课视频链接")
        source_type = "mooc"

    temp_video = Video(
        title=title,
        url=video_url,
        status=VideoStatus.DOWNLOADING,
        process_progress=0.0,
        current_step="已提交，等待下载",
    )
    db.add(temp_video)
    db.commit()
    db.refresh(temp_video)

    try:
        from app.core.executor import submit_task
        from app.tasks.video_download import download_video_from_url_task

        process_options = build_processing_options(
            language=data.language,
            model=data.model,
            auto_generate_summary=data.auto_generate_summary,
            auto_generate_tags=data.auto_generate_tags,
            summary_style=data.summary_style,
        )
        temp_video.current_step = f"已提交，等待下载（{process_options['model']}）"
        db.commit()
        db.refresh(temp_video)
        submit_task(download_video_from_url_task, temp_video.id, video_url, source_type, **process_options)
        remember_video_processing_request(
            temp_video.id,
            model=process_options["model"],
            language=process_options["language"],
            source="upload_video_url",
        )
        return VideoUploadResponse(
            id=temp_video.id,
            status="downloading",
            message="链接已提交，正在后台下载，下载完成后可自动开始处理",
            duplicate=False,
            data=serialize_video(temp_video),
        )
    except Exception as exc:
        logger.error(f"提交下载任务失败: {str(exc)}")
        temp_video.status = VideoStatus.FAILED
        temp_video.current_step = "下载任务提交失败"
        temp_video.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=500, detail="提交链接下载任务失败，请稍后重试")


@router.get("/list", response_model=VideoListResponse)
async def get_video_list(
    page: int = Query(1, ge=1), per_page: int = Query(5, ge=1, le=100), db: Session = Depends(get_db)
):
    """获取视频列表"""
    try:
        videos = db.query(Video).order_by(Video.upload_time.desc()).limit(100).all()

        result = []
        for video in videos:
            try:
                status = video.status.value if hasattr(video.status, "value") else str(video.status)
                tags = []
                if video.tags:
                    try:
                        tags = json.loads(video.tags)
                    except Exception:
                        pass

                video_data = {
                    "id": video.id,
                    "title": video.title or "",
                    "filename": video.filename or "",
                    "status": status,
                    "upload_time": video.upload_time.isoformat() if video.upload_time else None,
                    "preview_filename": video.preview_filename,
                    "duration": video.duration,
                    "width": video.width,
                    "height": video.height,
                    "fps": video.fps,
                    "summary": video.summary,
                    "tags": tags,
                    "url": video.url,
                    "upload_source": resolve_upload_source(video),
                    "upload_source_label": resolve_upload_source_label(video),
                    "upload_source_value": resolve_upload_source_value(video),
                    "process_progress": video.process_progress or 0,
                    "current_step": video.current_step,
                    "error_message": video.error_message,
                    "task_id": video.task_id,
                    "processing_origin": (
                        video.processing_origin.value
                        if hasattr(video.processing_origin, "value")
                        else str(video.processing_origin)
                    ),
                    "processing_origin_label": (
                        "iOS 离线处理" if video.processing_origin == VideoProcessingOrigin.IOS_OFFLINE else "在线处理"
                    ),
                }
                video_data.update(build_processing_metadata(video))
                result.append(video_data)
            except Exception as e:
                logger.error(f"处理视频记录时出错: {str(e)}")
                continue

        total = len(result)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_result = result[start_idx:end_idx] if start_idx < total else []

        return {
            "message": "获取成功",
            "videos": paginated_result,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    except Exception as e:
        logger.error(f"获取视频列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取视频列表失败: {str(e)}")


@router.get("/processing-options", response_model=VideoProcessingOptionsResponse)
async def get_video_processing_options():
    """返回前端可用的视频处理配置目录。"""
    catalog = get_whisper_model_catalog(settings.WHISPER_MODEL_PATH)
    try:
        default_model = normalize_whisper_model_name(settings.WHISPER_MODEL)
    except ValueError:
        supported_models = get_supported_whisper_models()
        default_model = supported_models[0] if supported_models else "base"

    if not catalog:
        catalog = [
            {"value": model_name, "label": model_name, "highlight": "", "downloaded": False}
            for model_name in get_supported_whisper_models()
        ]

    return {
        "default_model": default_model,
        "models": catalog,
    }


@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """获取视频详情"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return serialize_video(video)


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """获取视频状态"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    status = video.status.value if hasattr(video.status, "value") else str(video.status)

    return {
        "id": video.id,
        "status": status,
        "progress": video.process_progress or 0,
        "current_step": video.current_step or "",
        "task_id": video.task_id,
        "error_message": video.error_message,
        "processing_origin": (
            video.processing_origin.value if hasattr(video.processing_origin, "value") else str(video.processing_origin)
        ),
        "processing_origin_label": (
            "iOS 离线处理" if video.processing_origin == VideoProcessingOrigin.IOS_OFFLINE else "在线处理"
        ),
        **build_processing_metadata(video),
    }


@router.post("/{video_id}/process")
async def process_video_route(video_id: int, request: VideoProcessRequest, db: Session = Depends(get_db)):
    """开始处理视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    if video.processing_origin == VideoProcessingOrigin.IOS_OFFLINE:
        raise HTTPException(status_code=400, detail="该记录来自 iOS 本地离线处理，不能走后端重新处理")

    allowed_statuses = [VideoStatus.UPLOADED, VideoStatus.PENDING, VideoStatus.FAILED, VideoStatus.COMPLETED]
    if video.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"视频状态不正确: {video.status}")

    process_options = build_processing_options(
        language=request.language,
        model=request.model,
        auto_generate_summary=request.auto_generate_summary,
        auto_generate_tags=request.auto_generate_tags,
        summary_style=request.summary_style,
    )
    submit_video_processing(video, db, raise_on_error=True, **process_options)

    return {"status": "success", "message": "视频处理已开始"}


@router.delete("/{video_id}/delete")
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """删除视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 删除关联的问题记录
    from app.models.qa import Question

    db.query(Question).filter(Question.video_id == video_id).delete()

    # 提交清理任务
    try:
        from app.core.executor import submit_task
        from app.tasks.video_processing import cleanup_video_task

        submit_task(cleanup_video_task, video.id)
    except Exception as exc:
        logger.warning("提交视频清理任务失败，改为同步删除 | video_id=%s | error=%s", video.id, exc)
        # 直接删除文件
        if video.filepath and os.path.exists(video.filepath):
            os.remove(video.filepath)
        if video.preview_filepath and os.path.exists(video.preview_filepath):
            os.remove(video.preview_filepath)

    db.delete(video)
    db.commit()
    forget_video_processing_request(video_id)

    return {"message": "视频删除成功", "video_id": video_id}


@router.get("/{video_id}/stream")
async def get_video_stream(video_id: int, request: Request, db: Session = Depends(get_db)):
    """流式传输视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.filepath or not os.path.exists(video.filepath):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    file_size = os.path.getsize(video.filepath)
    media_type = resolve_video_media_type(video)
    byte_range = parse_byte_range(request.headers.get("range"), file_size)

    headers = {"Accept-Ranges": "bytes"}
    if byte_range is None:
        headers["Content-Length"] = str(file_size)
        return StreamingResponse(
            iter_file_chunk(video.filepath),
            media_type=media_type,
            headers=headers,
        )

    start, end = byte_range
    content_length = end - start + 1
    headers.update(
        {
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
        }
    )
    return StreamingResponse(
        iter_file_chunk(video.filepath, start=start, end=end),
        media_type=media_type,
        status_code=206,
        headers=headers,
    )


@router.get("/{video_id}/preview")
async def get_video_preview(video_id: int, db: Session = Depends(get_db)):
    """获取视频预览图"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.preview_filepath or not os.path.exists(video.preview_filepath):
        raise HTTPException(status_code=404, detail="预览图不存在")

    return FileResponse(video.preview_filepath, media_type="image/jpeg")


@router.get("/{video_id}/subtitle")
async def get_subtitle(video_id: int, format: str = "srt", download: bool = False, db: Session = Depends(get_db)):
    """获取字幕文件"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
        raise HTTPException(status_code=404, detail="字幕文件不存在")

    with open(video.subtitle_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if format.lower() == "vtt":
        vtt_content = "WEBVTT\n\n" + content.replace(",", ".")
        return Response(content=vtt_content, media_type="text/vtt; charset=utf-8")
    elif format.lower() == "txt":
        import re

        txt_content = re.sub(
            r"^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n", "", content, flags=re.MULTILINE
        )
        txt_content = re.sub(r"^\s*\n", "", txt_content, flags=re.MULTILINE)
        return Response(content=txt_content, media_type="text/plain; charset=utf-8")
    else:
        return Response(content=content, media_type="text/plain; charset=utf-8")


@router.post("/{video_id}/generate-summary")
async def generate_summary(video_id: int, request: VideoSummaryRequest, db: Session = Depends(get_db)):
    """为视频生成内容摘要"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成，请先处理视频")

    transcript_text = extract_video_transcript_text(video)
    if not transcript_text:
        raise HTTPException(status_code=400, detail="字幕内容不存在，无法生成摘要")

    try:
        from app.services.video_content_service import generate_video_summary

        result = generate_video_summary(
            video_id,
            video.subtitle_filepath or "",
            transcript_text=transcript_text,
            title=video.title or "",
            style=request.style,
        )
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"生成摘要失败: {result['error']}")

        video.summary = result["summary"]
        db.commit()

        return {"success": True, "summary": result["summary"], "style": result.get("style")}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("生成视频摘要失败 | video_id=%s | error=%s", video_id, exc)
        raise HTTPException(status_code=500, detail="摘要生成失败，请稍后重试")


@router.post("/generate-summary-from-transcript")
async def generate_summary_from_transcript(request: TranscriptSummaryRequest):
    """基于转录文本直接生成摘要，供本地离线转录结果复用在线摘要能力。"""
    transcript_text = (request.transcript_text or "").strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="转录文本为空，无法生成摘要")

    try:
        from app.services.video_content_service import generate_video_summary

        result = generate_video_summary(
            0,
            "",
            transcript_text=transcript_text,
            title=request.title or "",
            style=request.style,
        )
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"生成摘要失败: {result['error']}")

        return {
            "success": True,
            "summary": result["summary"],
            "style": result.get("style"),
            "provider": result.get("provider"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("基于转录文本生成摘要失败 | error=%s", exc)
        raise HTTPException(status_code=500, detail="摘要生成失败，请稍后重试")


@router.post("/sync-offline-transcript")
async def sync_offline_transcript(request: OfflineTranscriptSyncRequest, db: Session = Depends(get_db)):
    """将 iOS 本地离线转录结果同步到 videos 表与 subtitles 表。"""
    transcript_text = str(request.transcript_text or "").strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="转录文本为空，无法同步到视频库")

    summary_text = str(request.summary or "").strip()
    normalized_style = normalize_summary_style(request.summary_style)
    if not summary_text:
        summary_result = generate_video_summary(
            0,
            "",
            transcript_text=transcript_text,
            title=request.file_name or "",
            style=normalized_style,
        )
        if not summary_result.get("success"):
            raise HTTPException(status_code=500, detail=f"生成摘要失败: {summary_result.get('error')}")
        summary_text = str(summary_result.get("summary") or "").strip()

    title = build_offline_video_title(summary_text, fallback_title=request.file_name or "")
    filename = normalize_offline_filename(request.file_name, request.file_ext)
    task_id = str(request.task_id or "").strip()
    video = (
        db.query(Video)
        .filter(Video.task_id == task_id, Video.processing_origin == VideoProcessingOrigin.IOS_OFFLINE)
        .first()
    )
    is_new = video is None

    if is_new:
        video = Video(
            title=title,
            filename=filename,
            filepath=None,
            status=VideoStatus.COMPLETED,
            process_progress=100.0,
            current_step="iOS 本地离线转录已同步",
            summary=summary_text,
            task_id=task_id,
            processing_origin=VideoProcessingOrigin.IOS_OFFLINE,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
    else:
        video.title = title
        video.filename = filename
        video.status = VideoStatus.COMPLETED
        video.process_progress = 100.0
        video.current_step = "iOS 本地离线转录已同步"
        video.summary = summary_text
        video.error_message = None
        video.processing_origin = VideoProcessingOrigin.IOS_OFFLINE
        db.commit()
        db.refresh(video)

    subtitle_count = sync_offline_subtitles(
        db,
        video.id,
        transcript_text,
        request.segments,
        locale=request.locale,
    )
    payload = serialize_video(video)
    payload["offline_engine"] = request.engine
    payload["offline_locale"] = request.locale
    payload["subtitle_count"] = subtitle_count
    payload["file_size"] = request.file_size

    return {
        "success": True,
        "id": video.id,
        "duplicate": not is_new,
        "message": "本地离线转录结果已同步到视频库",
        "video": payload,
    }


@router.post("/{video_id}/generate-tags")
async def generate_tags(video_id: int, request: VideoTagRequest, db: Session = Depends(get_db)):
    """为视频生成标签"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成")

    if not video.summary:
        raise HTTPException(status_code=400, detail="视频没有摘要，请先生成摘要")

    try:
        from app.services.video_content_service import generate_video_tags

        result = generate_video_tags(video_id, video.summary, title=video.title or "", max_tags=request.max_tags)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"生成标签失败: {result['error']}")

        video.tags = json.dumps(result["tags"], ensure_ascii=False)
        db.commit()

        return {"success": True, "tags": result["tags"]}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("生成视频标签失败 | video_id=%s | error=%s", video_id, exc)
        raise HTTPException(status_code=500, detail="标签生成失败，请稍后重试")
