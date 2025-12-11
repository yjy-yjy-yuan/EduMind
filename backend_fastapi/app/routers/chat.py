"""聊天系统路由 - FastAPI 版本"""

import logging

from app.schemas.chat import ChatRequest
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/completions")
async def chat_completions(request: ChatRequest):
    """聊天完成接口（流式/非流式）"""
    try:
        if request.stream:
            # 流式响应
            async def generate():
                try:
                    if request.use_ollama:
                        # 使用 Ollama
                        try:
                            from app.utils.chat_system import stream_ollama_chat

                            for chunk in stream_ollama_chat(request.messages, request.model):
                                yield chunk
                        except ImportError:
                            yield "Ollama 聊天系统尚未配置。"
                    else:
                        # 使用在线 API
                        if not request.api_key:
                            yield "在线模式需要提供API密钥"
                            return

                        try:
                            from app.utils.chat_system import stream_api_chat

                            for chunk in stream_api_chat(request.messages, request.api_key, request.model):
                                yield chunk
                        except ImportError:
                            yield "API 聊天系统尚未配置。"
                except Exception as e:
                    logger.error(f"聊天生成出错: {str(e)}")
                    yield f"聊天生成出错: {str(e)}"

            return StreamingResponse(generate(), media_type="text/plain")
        else:
            # 非流式响应
            try:
                if request.use_ollama:
                    from app.utils.chat_system import get_ollama_response

                    content = get_ollama_response(request.messages, request.model)
                else:
                    if not request.api_key:
                        raise HTTPException(status_code=400, detail="在线模式需要提供API密钥")
                    from app.utils.chat_system import get_api_response

                    content = get_api_response(request.messages, request.api_key, request.model)

                return {"message": "success", "content": content}
            except ImportError:
                return {"message": "success", "content": "聊天系统尚未完全配置。"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models():
    """获取可用的模型列表"""
    return {
        "models": [
            {"id": "qwen-plus", "name": "通义千问 Plus", "type": "online"},
            {"id": "qwen-turbo", "name": "通义千问 Turbo", "type": "online"},
            {"id": "qwen3:8b", "name": "Qwen3 8B (本地)", "type": "ollama"},
            {"id": "llama3:8b", "name": "Llama3 8B (本地)", "type": "ollama"},
        ]
    }
