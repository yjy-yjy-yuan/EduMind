"""聊天系统工具 - FastAPI 版本"""

import logging
from typing import Generator
from typing import List

import requests
from app.core.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def check_ollama_service() -> bool:
    """检查 Ollama 服务是否可用"""
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama 服务不可用: {str(e)}")
        return False


def stream_ollama_chat(messages: List[dict], model: str = None) -> Generator[str, None, None]:
    """Ollama 流式聊天"""
    model = model or settings.OLLAMA_MODEL

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
            },
            stream=True,
            timeout=120,
        )

        for line in response.iter_lines():
            if line:
                import json

                try:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.error(f"Ollama 流式聊天出错: {str(e)}")
        yield f"聊天出错: {str(e)}"


def get_ollama_response(messages: List[dict], model: str = None) -> str:
    """Ollama 非流式聊天"""
    model = model or settings.OLLAMA_MODEL

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            },
            timeout=120,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("message", {}).get("content", "")
        else:
            return f"Ollama 请求失败: {response.status_code}"

    except Exception as e:
        logger.error(f"Ollama 聊天出错: {str(e)}")
        return f"聊天出错: {str(e)}"


def stream_api_chat(messages: List[dict], api_key: str, model: str = "qwen-plus") -> Generator[str, None, None]:
    """在线 API 流式聊天"""
    try:
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"API 流式聊天出错: {str(e)}")
        yield f"聊天出错: {str(e)}"


def get_api_response(messages: List[dict], api_key: str, model: str = "qwen-plus") -> str:
    """在线 API 非流式聊天"""
    try:
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"API 聊天出错: {str(e)}")
        return f"聊天出错: {str(e)}"
