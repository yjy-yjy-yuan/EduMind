"""问答系统工具 - FastAPI 版本

用于处理视频相关的 AI 问答功能
"""

import logging
from typing import Generator
from typing import List
from typing import Optional

import requests
from app.core.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def check_ollama_service() -> bool:
    """检查 Ollama 服务是否可用"""
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def build_qa_prompt(question: str, context: str = None, video_title: str = None) -> str:
    """构建问答提示词"""
    prompt_parts = []

    if video_title:
        prompt_parts.append(f"你正在回答关于视频《{video_title}》的问题。")

    if context:
        prompt_parts.append(f"以下是相关的视频内容摘要：\n{context}\n")

    prompt_parts.append(f"用户问题：{question}")
    prompt_parts.append("\n请基于视频内容提供准确、简洁的回答。如果内容中没有相关信息，请诚实说明。")

    return "\n".join(prompt_parts)


def stream_ollama_qa(
    question: str,
    context: str = None,
    video_title: str = None,
    model: str = None,
) -> Generator[str, None, None]:
    """使用 Ollama 进行流式问答

    Args:
        question: 用户问题
        context: 视频内容上下文
        video_title: 视频标题
        model: 模型名称

    Yields:
        回答内容片段
    """
    model = model or settings.OLLAMA_MODEL
    prompt = build_qa_prompt(question, context, video_title)

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024,
                },
            },
            stream=True,
            timeout=120,
        )

        if response.status_code != 200:
            yield f"Ollama 请求失败: {response.status_code}"
            return

        import json

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    except Exception as e:
        logger.error(f"Ollama 流式问答出错: {str(e)}")
        yield f"问答出错: {str(e)}"


def stream_api_qa(
    question: str,
    context: str = None,
    video_title: str = None,
    api_key: str = None,
    model: str = "qwen-plus",
) -> Generator[str, None, None]:
    """使用在线 API 进行流式问答

    Args:
        question: 用户问题
        context: 视频内容上下文
        video_title: 视频标题
        api_key: API 密钥
        model: 模型名称

    Yields:
        回答内容片段
    """
    api_key = api_key or settings.OPENAI_API_KEY
    prompt = build_qa_prompt(question, context, video_title)

    try:
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的视频内容问答助手，擅长根据视频内容回答用户问题。",
                },
                {"role": "user", "content": prompt},
            ],
            stream=True,
            temperature=0.7,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"API 流式问答出错: {str(e)}")
        yield f"问答出错: {str(e)}"


def get_ollama_answer(
    question: str,
    context: str = None,
    video_title: str = None,
    model: str = None,
) -> str:
    """使用 Ollama 获取非流式回答

    Args:
        question: 用户问题
        context: 视频内容上下文
        video_title: 视频标题
        model: 模型名称

    Returns:
        回答内容
    """
    model = model or settings.OLLAMA_MODEL
    prompt = build_qa_prompt(question, context, video_title)

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024,
                },
            },
            timeout=120,
        )

        if response.status_code == 200:
            return response.json().get("response", "")
        return f"Ollama 请求失败: {response.status_code}"

    except Exception as e:
        logger.error(f"Ollama 问答出错: {str(e)}")
        return f"问答出错: {str(e)}"


def get_api_answer(
    question: str,
    context: str = None,
    video_title: str = None,
    api_key: str = None,
    model: str = "qwen-plus",
) -> str:
    """使用在线 API 获取非流式回答

    Args:
        question: 用户问题
        context: 视频内容上下文
        video_title: 视频标题
        api_key: API 密钥
        model: 模型名称

    Returns:
        回答内容
    """
    api_key = api_key or settings.OPENAI_API_KEY
    prompt = build_qa_prompt(question, context, video_title)

    try:
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的视频内容问答助手，擅长根据视频内容回答用户问题。",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"API 问答出错: {str(e)}")
        return f"问答出错: {str(e)}"


def extract_subtitle_context(subtitles: List[dict], max_length: int = 2000) -> str:
    """从字幕中提取上下文

    Args:
        subtitles: 字幕列表
        max_length: 最大长度

    Returns:
        提取的上下文文本
    """
    if not subtitles:
        return ""

    texts = [sub.get("text", "") for sub in subtitles if sub.get("text")]
    full_text = " ".join(texts)

    if len(full_text) > max_length:
        return full_text[:max_length] + "..."
    return full_text
