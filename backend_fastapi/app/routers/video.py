"""视频管理路由 - FastAPI 版本"""

import hashlib
import json
import logging
import os
import re
import tempfile
import traceback
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.video import Video
from app.models.video import VideoStatus
from app.schemas.video import VideoDetail
from app.schemas.video import VideoListResponse
from app.schemas.video import VideoProcessRequest
from app.schemas.video import VideoUploadResponse
from app.schemas.video import VideoUploadURL
from app.schemas.video import VideoStatusResponse
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import Query
from fastapi import UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {ext.lower() for ext in settings.ALLOWED_EXTENSIONS}
UPLOAD_CHUNK_SIZE = 1024 * 1024


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


def submit_video_processing(
    video: Video,
    db: Session,
    *,
    language: str = "zh",
    model: Optional[str] = None,
    raise_on_error: bool = False,
) -> bool:
    """提交视频处理任务并将状态写回当前视频记录。"""
    previous_status = video.status
    previous_progress = video.process_progress or 0.0
    previous_step = video.current_step
    previous_error = video.error_message

    video.status = VideoStatus.PENDING
    video.process_progress = 0.0
    video.current_step = "已提交，等待处理"
    video.error_message = None
    db.commit()

    try:
        from app.core.executor import submit_task
        from app.tasks.video_processing import process_video_task

        submit_task(process_video_task, video.id, language, model or settings.WHISPER_MODEL)
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
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
                data=existing_video.to_dict(),
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

        task_submitted = submit_video_processing(video, db)
        db.refresh(video)

        logger.info(f"视频上传成功: ID={video.id}, size={file_size}")

        return VideoUploadResponse(
            id=video.id,
            status=video.status.value if hasattr(video.status, "value") else str(video.status),
            message="视频上传成功，已开始后台处理" if task_submitted else "视频上传成功，请手动开始处理",
            duplicate=False,
            data=video.to_dict(),
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
            status=existing_video.status.value if hasattr(existing_video.status, "value") else str(existing_video.status),
            message="该视频链接已提交过",
            duplicate=True,
            data=existing_video.to_dict(),
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

        submit_task(download_video_from_url_task, temp_video.id, video_url, source_type)
        return VideoUploadResponse(
            id=temp_video.id,
            status="downloading",
            message="链接已提交，正在后台下载，下载完成后可自动开始处理",
            duplicate=False,
            data=temp_video.to_dict(),
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
                }
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


@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """获取视频详情"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video.to_dict()


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
    }


@router.post("/{video_id}/process")
async def process_video_route(video_id: int, request: VideoProcessRequest, db: Session = Depends(get_db)):
    """开始处理视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    allowed_statuses = [VideoStatus.UPLOADED, VideoStatus.PENDING, VideoStatus.FAILED, VideoStatus.COMPLETED]
    if video.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"视频状态不正确: {video.status}")

    whisper_language = "en" if request.language == "English" else "zh"
    submit_video_processing(video, db, language=whisper_language, model=request.model, raise_on_error=True)

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

    return {"message": "视频删除成功", "video_id": video_id}


@router.get("/{video_id}/stream")
async def get_video_stream(video_id: int, db: Session = Depends(get_db)):
    """流式传输视频"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if not video.filepath or not os.path.exists(video.filepath):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    file_size = os.path.getsize(video.filepath)

    def iterfile():
        with open(video.filepath, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)},
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
async def generate_summary(video_id: int, db: Session = Depends(get_db)):
    """为视频生成内容摘要"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成，请先处理视频")

    if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
        raise HTTPException(status_code=400, detail="字幕文件不存在")

    try:
        from services.summary_generator import generate_video_summary

        result = generate_video_summary(video_id, video.subtitle_filepath)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"生成摘要失败: {result['error']}")

        video.summary = result["summary"]
        db.commit()

        return {"success": True, "summary": result["summary"]}
    except ImportError:
        raise HTTPException(status_code=500, detail="摘要生成服务未配置")


@router.post("/{video_id}/generate-tags")
async def generate_tags(video_id: int, db: Session = Depends(get_db)):
    """为视频生成标签"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="视频尚未处理完成")

    if not video.summary:
        raise HTTPException(status_code=400, detail="视频没有摘要，请先生成摘要")

    try:
        from services.tag_generator import generate_video_tags

        result = generate_video_tags(video_id, video.summary)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"生成标签失败: {result['error']}")

        video.tags = json.dumps(result["tags"], ensure_ascii=False)
        db.commit()

        return {"success": True, "tags": result["tags"]}
    except ImportError:
        raise HTTPException(status_code=500, detail="标签生成服务未配置")
