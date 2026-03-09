"""字幕相关的 Pydantic schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SubtitleBase(BaseModel):
    """字幕基础模型"""
    start_time: float
    end_time: float
    text: str
    language: str = "zh"


class SubtitleResponse(BaseModel):
    """字幕响应模型"""
    id: int
    video_id: int
    start_time: float
    end_time: float
    text: str
    source: str
    language: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubtitleUpdate(BaseModel):
    """字幕更新请求"""
    text: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    editor: Optional[str] = None


class SubtitleListResponse(BaseModel):
    """字幕列表响应"""
    status: str = "success"
    video_id: int
    video_status: Optional[str] = None
    subtitles: List[SubtitleResponse]


class SubtitleGenerateRequest(BaseModel):
    """字幕生成请求"""
    language: str = "zh"
    whisper_model: str = "base"


class SemanticMergedSubtitle(BaseModel):
    """语义合并后的字幕"""
    start_time: float
    end_time: float
    text: str
    title: Optional[str] = None
