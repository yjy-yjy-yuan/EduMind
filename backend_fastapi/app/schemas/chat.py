"""聊天 Pydantic Schema"""

from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ChatMessage(BaseModel):
    """聊天消息"""

    role: str = Field(..., description="消息角色: user, assistant, system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求"""

    messages: List[ChatMessage]
    api_key: Optional[str] = None
    use_ollama: bool = Field(default=False, description="是否使用本地 Ollama")
    stream: bool = Field(default=True, description="是否流式返回")
    model: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应 (非流式)"""

    message: str
    content: str
