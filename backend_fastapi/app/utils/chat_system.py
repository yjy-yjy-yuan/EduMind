"""聊天系统工具 - FastAPI 版本"""

import logging
from typing import Generator
from typing import List

from app.utils.qa_utils import call_provider_chat
from app.utils.qa_utils import normalize_provider
from app.utils.qa_utils import resolve_model

logger = logging.getLogger(__name__)


def normalize_chat_messages(messages: List[dict]) -> List[dict]:
    """将聊天消息统一转换为 OpenAI 兼容结构。"""
    normalized = []
    for item in messages or []:
        if isinstance(item, dict):
            role = str(item.get("role") or "").strip()
            content = str(item.get("content") or "").strip()
        else:
            role = str(getattr(item, "role", "") or "").strip()
            content = str(getattr(item, "content", "") or "").strip()

        if not role or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def stream_chat(messages: List[dict], provider: str = "qwen", model: str = "") -> Generator[str, None, None]:
    """在线模型聊天流式输出。当前以单次返回内容形式输出。"""
    normalized_provider = normalize_provider(provider, model)
    resolved_model = resolve_model(normalized_provider, model)
    normalized_messages = normalize_chat_messages(messages)
    yield call_provider_chat(normalized_messages, provider=normalized_provider, model=resolved_model)


def get_chat_response(messages: List[dict], provider: str = "qwen", model: str = "") -> dict:
    """在线模型聊天非流式响应。"""
    normalized_provider = normalize_provider(provider, model)
    resolved_model = resolve_model(normalized_provider, model)
    normalized_messages = normalize_chat_messages(messages)
    content = call_provider_chat(normalized_messages, provider=normalized_provider, model=resolved_model)
    return {
        "content": content,
        "provider": normalized_provider,
        "model": resolved_model,
    }
