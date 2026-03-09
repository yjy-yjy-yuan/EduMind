"""问答相关的 Pydantic schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    """问题创建请求"""
    video_id: Optional[int] = None
    question: str = Field(..., min_length=1, description="问题内容")
    api_key: Optional[str] = None
    mode: str = Field(default="video", description="问答模式: video, free")
    stream: bool = Field(default=True, description="是否流式响应")
    use_ollama: bool = Field(default=False, description="是否使用Ollama")
    deep_thinking: bool = Field(default=False, description="是否启用深度思考")


class QuestionResponse(BaseModel):
    """问题响应模型"""
    id: int
    video_id: Optional[int] = None
    content: str
    answer: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QAHistoryResponse(BaseModel):
    """问答历史响应"""
    questions: List[QuestionResponse]
