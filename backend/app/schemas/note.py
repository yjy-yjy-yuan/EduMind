"""笔记相关的 Pydantic schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TimestampCreate(BaseModel):
    """时间戳创建请求"""
    time_seconds: float
    subtitle_text: Optional[str] = None


class TimestampResponse(BaseModel):
    """时间戳响应"""
    id: int
    note_id: int
    time_seconds: float
    subtitle_text: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    """笔记基础模型"""
    title: str = Field(..., min_length=1, description="笔记标题")
    content: str = Field(default="", description="笔记内容")
    note_type: str = Field(default="text", description="笔记类型")
    video_id: Optional[int] = None
    tags: Optional[List[str]] = None


class NoteCreate(NoteBase):
    """创建笔记请求"""
    timestamps: Optional[List[TimestampCreate]] = None


class NoteUpdate(BaseModel):
    """更新笔记请求"""
    title: str = Field(..., min_length=1)
    content: Optional[str] = None
    note_type: Optional[str] = None
    tags: Optional[List[str]] = None
    timestamps: Optional[List[TimestampCreate]] = None


class NoteResponse(BaseModel):
    """笔记响应模型"""
    id: int
    title: str
    content: str
    note_type: str
    video_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = []
    keywords: List[str] = []
    timestamps: List[TimestampResponse] = []

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """笔记列表响应"""
    status: str = "success"
    data: List[NoteResponse]


class SimilarNotesRequest(BaseModel):
    """相似笔记请求"""
    content: str = Field(..., min_length=10, description="查询内容")
    limit: int = Field(default=5, ge=1, le=20)


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    note_ids: List[int]


class TagResponse(BaseModel):
    """标签响应"""
    name: str
    count: int
