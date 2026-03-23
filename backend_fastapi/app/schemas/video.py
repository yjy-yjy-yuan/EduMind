"""视频 Pydantic Schema"""

from datetime import datetime
from enum import Enum
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class VideoStatusEnum(str, Enum):
    """视频状态"""

    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DOWNLOADING = "downloading"


# ============ 请求 Schema ============


class VideoUploadURL(BaseModel):
    """URL 上传请求"""

    url: str = Field(..., description="视频链接 (B站/YouTube/慕课)")
    language: str = Field(default="Other", description="视频语言")
    model: str = Field(default="base", description="Whisper 模型")
    auto_generate_summary: bool = Field(default=True, description="处理完成后自动生成摘要")
    auto_generate_tags: bool = Field(default=True, description="处理完成后自动生成标签")
    summary_style: str = Field(default="study", description="摘要风格: brief/study/detailed")


class VideoProcessRequest(BaseModel):
    """视频处理请求"""

    language: str = Field(default="Other", description="视频语言")
    model: str = Field(default="base", description="Whisper 模型")
    auto_generate_summary: bool = Field(default=True, description="处理完成后自动生成摘要")
    auto_generate_tags: bool = Field(default=True, description="处理完成后自动生成标签")
    summary_style: str = Field(default="study", description="摘要风格: brief/study/detailed")


class VideoSummaryRequest(BaseModel):
    """摘要生成请求"""

    style: str = Field(default="study", description="摘要风格: brief/study/detailed")


class TranscriptSummaryRequest(BaseModel):
    """基于转录文本的摘要生成请求"""

    transcript_text: str = Field(..., description="转录全文")
    title: str = Field(default="", description="转录标题")
    style: str = Field(default="study", description="摘要风格: brief/study/detailed")


class VideoTagRequest(BaseModel):
    """标签生成请求"""

    max_tags: int = Field(default=6, ge=1, le=12, description="最大标签数")


# ============ 响应 Schema ============


class VideoBase(BaseModel):
    """视频基础信息"""

    id: int
    title: Optional[str] = None
    filename: Optional[str] = None
    status: str
    requested_model: Optional[str] = None
    effective_model: Optional[str] = None
    requested_language: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VideoUploadResponse(BaseModel):
    """上传响应"""

    id: int
    status: str
    message: str
    duplicate: bool = False
    data: Optional[dict] = None


class VideoDetail(BaseModel):
    """视频详情"""

    id: int
    title: Optional[str] = None
    filename: Optional[str] = None
    filepath: Optional[str] = None
    url: Optional[str] = None
    status: str
    upload_time: Optional[datetime] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_count: Optional[int] = None
    md5: Optional[str] = None
    preview_filename: Optional[str] = None
    subtitle_filepath: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    process_progress: Optional[float] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    requested_model: Optional[str] = None
    effective_model: Optional[str] = None
    requested_language: Optional[str] = None
    upload_source: Optional[str] = None
    upload_source_label: Optional[str] = None
    upload_source_value: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VideoStatusResponse(BaseModel):
    """视频状态响应"""

    id: int
    status: str
    progress: float = 0
    current_step: str = ""
    task_id: Optional[str] = None
    error_message: Optional[str] = None
    requested_model: Optional[str] = None
    effective_model: Optional[str] = None
    requested_language: Optional[str] = None


class WhisperModelOption(BaseModel):
    """Whisper 模型选项"""

    value: str
    label: str
    highlight: str = ""
    downloaded: bool = False


class VideoProcessingOptionsResponse(BaseModel):
    """视频处理设置目录响应"""

    default_model: str
    models: List[WhisperModelOption]


class VideoListResponse(BaseModel):
    """视频列表响应"""

    message: str
    videos: List[VideoDetail]
    total: int
    page: int
    per_page: int
    total_pages: int
