"""视频相关的 Pydantic schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.video import VideoStatus


class VideoBase(BaseModel):
    """视频基础模型"""
    title: Optional[str] = None
    url: Optional[str] = None


class VideoCreate(VideoBase):
    """创建视频请求"""
    pass


class VideoResponse(BaseModel):
    """视频响应模型"""
    id: int
    title: Optional[str] = None
    filename: Optional[str] = None
    filepath: Optional[str] = None
    status: str
    upload_time: Optional[datetime] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_count: Optional[int] = None
    preview_filename: Optional[str] = None
    error_message: Optional[str] = None
    subtitle_filepath: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    md5: Optional[str] = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """视频列表响应"""
    message: str = "获取成功"
    videos: List[VideoResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class VideoStatusResponse(BaseModel):
    """视频状态响应"""
    id: int
    status: str
    progress: float = 0
    current_step: Optional[str] = None
    task_id: Optional[str] = None


class VideoUploadResponse(BaseModel):
    """视频上传响应"""
    id: int
    status: str
    message: str
    duplicate: bool = False
    data: Optional[dict] = None
    existingVideo: Optional[dict] = None


class VideoProcessRequest(BaseModel):
    """视频处理请求"""
    language: str = Field(default="Other", description="视频语言: English, Other")
    model: str = Field(default="turbo", description="Whisper模型: tiny, base, small, medium, large, turbo")


class VideoUrlUploadRequest(BaseModel):
    """视频URL上传请求"""
    url: str = Field(..., description="视频链接（支持B站、YouTube、中国大学慕课）")
