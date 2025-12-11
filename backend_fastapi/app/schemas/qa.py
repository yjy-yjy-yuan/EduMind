"""问答 Pydantic Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AskRequest(BaseModel):
    """问答请求"""

    video_id: Optional[int] = None
    question: str = Field(..., min_length=1)
    api_key: Optional[str] = None
    mode: str = Field(default="video", description="问答模式: video, free")
    stream: bool = Field(default=True, description="是否流式返回")
    use_ollama: bool = Field(default=False, description="是否使用本地 Ollama")
    deep_thinking: bool = Field(default=False, description="是否启用深度思考")


class QuestionResponse(BaseModel):
    """问题响应"""

    id: int
    video_id: Optional[int] = None
    content: str
    answer: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionHistoryResponse(BaseModel):
    """问答历史响应"""

    message: str
    questions: list[QuestionResponse]
    total: int
