"""视频内容分析服务。"""

import json
import logging
import re
from collections import Counter
from typing import Iterable
from typing import Optional

import jieba
import jieba.analyse
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

SUMMARY_STYLE_BRIEF = "brief"
SUMMARY_STYLE_STUDY = "study"
SUMMARY_STYLE_DETAILED = "detailed"
SUPPORTED_SUMMARY_STYLES = {
    SUMMARY_STYLE_BRIEF,
    SUMMARY_STYLE_STUDY,
    SUMMARY_STYLE_DETAILED,
}
DEFAULT_ONLINE_MODEL = "qwen-plus"
DEFAULT_MAX_TAGS = 6

STOP_WORDS = {
    "",
    "的",
    "了",
    "和",
    "是",
    "在",
    "就",
    "都",
    "而",
    "及",
    "与",
    "着",
    "或",
    "一个",
    "一种",
    "我们",
    "你们",
    "他们",
    "以及",
    "因为",
    "所以",
    "这个",
    "那个",
    "如果",
    "然后",
    "进行",
    "可以",
    "需要",
    "通过",
    "这里",
    "就是",
    "这些",
    "那些",
    "已经",
    "还是",
    "并且",
    "主要",
    "关于",
    "一个",
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "are",
    "was",
    "were",
    "been",
    "have",
    "has",
    "had",
    "you",
    "your",
    "our",
    "their",
}


def normalize_summary_style(style: str) -> str:
    normalized = str(style or "").strip().lower()
    if normalized in SUPPORTED_SUMMARY_STYLES:
        return normalized
    return SUMMARY_STYLE_STUDY


def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def clean_multiline_text(text: str) -> str:
    normalized = str(text or "").replace("\r\n", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def ensure_sentence_tail(text: str) -> str:
    sentence = clean_whitespace(text).rstrip("；;，,、")
    if not sentence:
        return ""
    if sentence[-1] in "。！？!?":
        return sentence
    return f"{sentence}。"


def remove_srt_timing_markers(text: str) -> str:
    normalized = str(text or "").replace("\r\n", "\n")
    normalized = re.sub(r"^\d+\s*$", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(
        r"^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*$",
        "",
        normalized,
        flags=re.MULTILINE,
    )
    normalized = re.sub(r"<[^>]+>", " ", normalized)
    return clean_whitespace(normalized)


def read_subtitle_text(subtitle_path: str) -> str:
    if not subtitle_path:
        return ""
    try:
        with open(subtitle_path, "r", encoding="utf-8") as handle:
            return remove_srt_timing_markers(handle.read())
    except FileNotFoundError:
        return ""
    except Exception as exc:
        logger.warning("读取字幕文本失败 | path=%s | error=%s", subtitle_path, exc)
        return ""


def extract_transcript_text(result: Optional[dict]) -> str:
    payload = result or {}
    segments = payload.get("segments") or []
    texts = [clean_whitespace(segment.get("text")) for segment in segments if clean_whitespace(segment.get("text"))]
    if texts:
        return clean_whitespace(" ".join(texts))
    return clean_whitespace(payload.get("text") or "")


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"[\r\n]+", "\n", str(text or ""))
    chunks = re.split(r"(?<=[。！？!?；;])\s+|\n+", normalized)
    sentences = []
    for chunk in chunks:
        sentence = clean_whitespace(chunk)
        if len(sentence) < 6:
            continue
        sentences.append(sentence)
    return sentences


def tokenize_sentence(text: str) -> list[str]:
    if re.search(r"[\u4e00-\u9fff]", text):
        tokens = [token.strip().lower() for token in jieba.lcut(text, cut_all=False)]
    else:
        tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_]+", text)]
    return [token for token in tokens if len(token) >= 2 and token not in STOP_WORDS]


def sentence_limit_for_style(style: str) -> int:
    if style == SUMMARY_STYLE_BRIEF:
        return 3
    if style == SUMMARY_STYLE_DETAILED:
        return 7
    return 5


def render_summary(sentences: list[str], title: str, style: str) -> str:
    cleaned = [ensure_sentence_tail(sentence) for sentence in sentences if ensure_sentence_tail(sentence)]
    if not cleaned:
        return ""

    if style == SUMMARY_STYLE_BRIEF:
        prefix = f"《{title}》" if title else "本视频"
        compact = "；".join(sentence.rstrip("。") for sentence in cleaned[:3])
        return f"{prefix}主要内容：{compact}。"

    lines = []
    if title:
        lines.append(f"主题：{title}")
    intro = "学习重点：" if style == SUMMARY_STYLE_STUDY else "详细梳理："
    lines.append(intro)
    for index, sentence in enumerate(cleaned, start=1):
        lines.append(f"{index}. {sentence}")
    return "\n".join(lines)


def fallback_summary(text: str, *, title: str = "", style: str = SUMMARY_STYLE_STUDY) -> str:
    sentences = split_sentences(text)
    if not sentences:
        trimmed = clean_whitespace(text)[:220]
        return render_summary([trimmed], title, style) if trimmed else ""

    if len(sentences) <= sentence_limit_for_style(style):
        return render_summary(sentences, title, style)

    token_scores = Counter()
    sentence_tokens: list[list[str]] = []
    for sentence in sentences:
        tokens = tokenize_sentence(sentence)
        sentence_tokens.append(tokens)
        token_scores.update(tokens)

    scored = []
    for index, sentence in enumerate(sentences):
        tokens = sentence_tokens[index]
        if not tokens:
            score = 0.0
        else:
            score = sum(token_scores[token] for token in tokens) / len(tokens)
            if index == 0:
                score += 0.15
        scored.append((score, index, sentence))

    limit = sentence_limit_for_style(style)
    selected_indexes = sorted(index for _, index, _ in sorted(scored, reverse=True)[:limit])
    selected_sentences = [sentences[index] for index in selected_indexes]
    return render_summary(selected_sentences, title, style)


def parse_json_array(text: str) -> list[str]:
    raw = str(text or "").strip()
    if not raw:
        return []

    candidates = [raw]
    matched = re.search(r"\[[\s\S]*\]", raw)
    if matched:
        candidates.insert(0, matched.group(0))

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            return [clean_whitespace(item) for item in payload if clean_whitespace(item)]
    return []


def normalize_tags(tags: Iterable[str], *, max_tags: int = DEFAULT_MAX_TAGS) -> list[str]:
    normalized = []
    seen = set()
    for tag in tags:
        text = clean_whitespace(tag).strip("#")
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
        if len(normalized) >= max(1, int(max_tags)):
            break
    return normalized


def fallback_tags(summary: str, *, title: str = "", max_tags: int = DEFAULT_MAX_TAGS) -> list[str]:
    seed = clean_whitespace(f"{title} {summary}")
    tags = []
    try:
        tags = jieba.analyse.extract_tags(seed, topK=max(1, int(max_tags)))
    except Exception as exc:
        logger.warning("离线标签提取失败，回退到词频统计 | error=%s", exc)

    if not tags:
        counter = Counter(tokenize_sentence(seed))
        tags = [token for token, _ in counter.most_common(max(1, int(max_tags)))]
    return normalize_tags(tags, max_tags=max_tags)


def ollama_available() -> bool:
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def call_online_chat(prompt: str, *, system_prompt: str, model: str = DEFAULT_ONLINE_MODEL) -> Optional[str]:
    api_key = clean_whitespace(settings.OPENAI_API_KEY or settings.QWEN_API_KEY)
    base_url = clean_whitespace(settings.OPENAI_BASE_URL or settings.QWEN_API_BASE).rstrip("/")
    if not api_key or not base_url:
        return None

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        return clean_multiline_text(payload["choices"][0]["message"]["content"])
    except Exception as exc:
        logger.warning("在线摘要/标签生成失败，准备回退 | error=%s", exc)
        return None


def call_ollama(prompt: str, *, system_prompt: str, model: Optional[str] = None) -> Optional[str]:
    if not ollama_available():
        return None

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/generate",
            json={
                "model": model or settings.OLLAMA_MODEL,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1024,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        return clean_multiline_text(response.json().get("response", ""))
    except Exception as exc:
        logger.warning("Ollama 摘要/标签生成失败，准备回退 | error=%s", exc)
        return None


def build_summary_prompt(transcript_text: str, *, title: str, style: str) -> tuple[str, str]:
    style_instruction = {
        SUMMARY_STYLE_BRIEF: "输出 1 段精炼摘要，突出主题和结论，控制在 90 字以内。",
        SUMMARY_STYLE_STUDY: "输出适合学习复盘的摘要，先写一句总述，再列 3 到 5 条学习重点。",
        SUMMARY_STYLE_DETAILED: "输出较详细的学习摘要，先总述，再列 5 到 7 条关键知识点或推导脉络。",
    }[style]
    system_prompt = "你是一个课程视频学习助手，负责基于字幕生成准确、可复习的中文摘要。不要编造字幕中没有出现的事实。"
    prompt = (
        f"视频标题：{title or '未命名视频'}\n"
        f"摘要风格：{style}\n"
        f"{style_instruction}\n"
        "请直接输出摘要正文，不要解释你的思路。\n\n"
        f"字幕内容：\n{transcript_text[:9000]}"
    )
    return system_prompt, prompt


def build_tag_prompt(summary: str, *, title: str, max_tags: int) -> tuple[str, str]:
    system_prompt = "你是一个课程视频标签助手。请基于视频摘要提炼简短中文标签，只返回 JSON 数组。"
    prompt = (
        f"视频标题：{title or '未命名视频'}\n"
        f"请提取 {max(1, int(max_tags))} 个标签。\n"
        "要求：标签应简短、可检索、避免重复，不要输出解释文字。\n"
        f"摘要内容：\n{summary}\n\n"
        '输出格式示例：["导数定义", "几何意义", "求导法则"]'
    )
    return system_prompt, prompt


def generate_video_summary(
    video_id: int,
    subtitle_path: str = "",
    *,
    transcript_text: str = "",
    title: str = "",
    style: str = SUMMARY_STYLE_STUDY,
) -> dict:
    normalized_style = normalize_summary_style(style)
    source_text = clean_whitespace(transcript_text) or read_subtitle_text(subtitle_path)
    if not source_text:
        return {"success": False, "error": "无法提取字幕文本"}

    system_prompt, prompt = build_summary_prompt(source_text, title=title, style=normalized_style)
    summary = call_online_chat(prompt, system_prompt=system_prompt) or call_ollama(prompt, system_prompt=system_prompt)
    provider = "ai"
    if not summary:
        summary = fallback_summary(source_text, title=title, style=normalized_style)
        provider = "fallback"

    summary = clean_multiline_text(summary)
    if not summary:
        return {"success": False, "error": "摘要内容为空"}

    logger.info("视频摘要生成完成 | video_id=%s | provider=%s | style=%s", video_id, provider, normalized_style)
    return {"success": True, "summary": summary, "provider": provider, "style": normalized_style}


def generate_video_tags(video_id: int, summary: str, *, title: str = "", max_tags: int = DEFAULT_MAX_TAGS) -> dict:
    clean_summary = clean_whitespace(summary)
    if not clean_summary:
        return {"success": False, "error": "摘要内容为空"}

    system_prompt, prompt = build_tag_prompt(clean_summary, title=title, max_tags=max_tags)
    raw_tags = call_online_chat(prompt, system_prompt=system_prompt) or call_ollama(prompt, system_prompt=system_prompt)
    provider = "ai"

    tags = normalize_tags(parse_json_array(raw_tags), max_tags=max_tags) if raw_tags else []
    if not tags:
        tags = fallback_tags(clean_summary, title=title, max_tags=max_tags)
        provider = "fallback"

    if not tags:
        return {"success": False, "error": "标签生成失败"}

    logger.info("视频标签生成完成 | video_id=%s | provider=%s | count=%s", video_id, provider, len(tags))
    return {"success": True, "tags": tags, "provider": provider}
