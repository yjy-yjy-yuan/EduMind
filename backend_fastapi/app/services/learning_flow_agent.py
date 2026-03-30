"""学习流智能体编排服务。

第一版仅负责把用户意图映射为现有能力的顺序执行，不引入新的业务表。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional

from app.models.note import Note
from app.models.note import NoteTimestamp
from app.models.qa import Question
from app.models.video import Video
from app.services.video_content_service import fallback_summary
from app.services.video_content_service import fallback_tags
from app.services.video_content_service import normalize_summary_style
from app.utils.qa_utils import QASystem
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    video: Optional[Video]
    subtitle_text: str
    current_time_seconds: Optional[float]
    recent_qa_messages: list[dict]
    page_context: str
    user_input: str


def normalize_user_input(text: str) -> str:
    return str(text or "").strip()


def infer_intent(user_input: str) -> str:
    normalized = normalize_user_input(user_input)
    if any(keyword in normalized for keyword in ["记成笔记", "做成笔记", "保存为笔记", "生成笔记", "记笔记"]):
        return "create_note"
    if any(keyword in normalized for keyword in ["总结", "概括", "摘要"]):
        return "summarize"
    if any(keyword in normalized for keyword in ["问", "解释", "什么意思", "怎么理解"]):
        return "qa"
    return "mixed"


def build_plan(intent: str, ctx: AgentContext) -> list[str]:
    plan = ["读取视频上下文", "整理字幕与最近问答"]
    if intent in {"create_note", "mixed"}:
        plan.append("生成学习笔记草稿")
    if intent in {"summarize", "mixed"}:
        plan.append("提炼片段摘要")
    if ctx.current_time_seconds is not None:
        plan.append("绑定时间戳")
    if ctx.video is not None:
        plan.append("写回视频关联记录")
    return plan


def _build_note_title(video: Optional[Video], user_input: str, summary_text: str) -> str:
    base = (video.title or "").strip() if video else ""
    if base:
        return f"{base} · 学习笔记"
    if summary_text:
        return summary_text.splitlines()[0][:40]
    return normalize_user_input(user_input)[:40] or "学习笔记"


def _subtitle_excerpt_for_time(video: Optional[Video], current_time_seconds: Optional[float]) -> str:
    if video is None or current_time_seconds is None:
        return ""

    subtitles = list(getattr(video, "subtitles", []) or [])
    if not subtitles:
        return ""

    ordered = sorted(subtitles, key=lambda item: float(getattr(item, "start_time", 0) or 0))
    target = float(current_time_seconds)
    best_index = 0
    best_distance = None
    for index, item in enumerate(ordered):
        start_time = float(getattr(item, "start_time", 0) or 0)
        end_time = float(getattr(item, "end_time", start_time) or start_time)
        midpoint = (start_time + end_time) / 2
        distance = abs(midpoint - target)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_index = index

    fragment_indexes = range(max(0, best_index - 1), min(len(ordered), best_index + 2))
    excerpts = []
    for index in fragment_indexes:
        fragment = ordered[index]
        text = str(getattr(fragment, "text", "") or "").strip()
        if not text:
            continue
        start_time = float(getattr(fragment, "start_time", 0) or 0)
        end_time = float(getattr(fragment, "end_time", start_time) or start_time)
        excerpts.append(f"[{start_time:.1f}-{end_time:.1f}] {text}")

    return "\n".join(excerpts).strip()


def _build_note_content(ctx: AgentContext, summary_text: str, subtitle_excerpt: str = "", qa_answer: str = "") -> str:
    parts = []
    if subtitle_excerpt.strip():
        parts.append(f"字幕片段：\n{subtitle_excerpt.strip()}")
    elif ctx.subtitle_text.strip():
        parts.append(f"字幕片段：{ctx.subtitle_text.strip()}")
    if summary_text.strip():
        parts.append(f"摘要：{summary_text.strip()}")
    if qa_answer.strip():
        parts.append(f"问答补充：{qa_answer.strip()}")
    return "\n".join(parts).strip()


def execute_learning_flow_agent(db: Session, *, request) -> dict[str, Any]:
    logger.debug(
        "agent request | video_id=%s | page_context=%s | current_time_seconds=%s | subtitle_len=%s | qa_messages=%s | user_input=%s",
        request.video_id,
        request.page_context,
        request.current_time_seconds,
        len(str(request.subtitle_text or "")),
        len(request.recent_qa_messages or []),
        normalize_user_input(request.user_input),
    )
    video = None
    if request.video_id is not None:
        video = db.query(Video).filter(Video.id == request.video_id).first()
        if not video:
            logger.debug("agent validation failed | reason=video_not_found | video_id=%s", request.video_id)
            raise ValueError("视频不存在")
        logger.debug(
            "agent context loaded | video_id=%s | title=%s | status=%s | subtitles=%s | has_summary=%s | has_tags=%s",
            video.id,
            video.title,
            video.status,
            len(getattr(video, "subtitles", []) or []),
            bool(video.summary),
            bool(video.tags),
        )

    ctx = AgentContext(
        video=video,
        subtitle_text=str(request.subtitle_text or ""),
        current_time_seconds=request.current_time_seconds,
        recent_qa_messages=list(request.recent_qa_messages or []),
        page_context=str(request.page_context or "video_detail"),
        user_input=normalize_user_input(request.user_input),
    )

    intent = infer_intent(ctx.user_input)
    plan = build_plan(intent, ctx)
    logger.debug("agent intent inferred | intent=%s | plan=%s", intent, plan)
    actions: list[str] = []
    action_records: list[dict[str, Any]] = []
    result: dict[str, Any] = {}

    if video is not None:
        qa_system = QASystem(video=video)
        qa_answer = ""
        subtitle_excerpt = _subtitle_excerpt_for_time(video, ctx.current_time_seconds)
        if intent == "qa" and qa_system.has_context():
            logger.debug(
                "agent qa dispatch | mode=video | provider=qwen | history_messages=%s", len(ctx.recent_qa_messages)
            )
            qa_answer = qa_system.ask(
                ctx.user_input,
                provider="qwen",
                model="",
                deep_thinking=False,
                mode="video",
                history=ctx.recent_qa_messages,
            )["answer"]
            actions.append("qa_answered")
            action_records.append({"type": "qa_answered", "message": "已基于视频上下文回答", "data": {}})
            logger.debug("agent qa answered | answer_len=%s", len(qa_answer))

        summary_text = ""
        if subtitle_excerpt.strip() or ctx.subtitle_text.strip():
            summary_text = fallback_summary(
                subtitle_excerpt or ctx.subtitle_text,
                title=video.title or "",
                style=normalize_summary_style("study"),
            )
            actions.append("summary_generated")
            action_records.append({"type": "summary_generated", "message": "已生成片段摘要", "data": {}})
            logger.debug("agent summary generated | summary_len=%s", len(summary_text))

        if intent in {"create_note", "mixed"} or ctx.current_time_seconds is not None:
            note_title = _build_note_title(video, ctx.user_input, summary_text)
            note_content = _build_note_content(
                ctx, summary_text, subtitle_excerpt=subtitle_excerpt, qa_answer=qa_answer
            )
            if not note_content:
                note_content = summary_text or subtitle_excerpt or video.summary or video.title or "学习笔记"
            logger.debug(
                "agent create note | title=%s | content_len=%s | has_timestamp=%s",
                note_title,
                len(note_content),
                ctx.current_time_seconds is not None,
            )
            note = Note(
                title=note_title,
                content=note_content,
                note_type="text",
                video_id=video.id,
                tags=",".join(fallback_tags(summary_text or note_content, title=note_title, max_tags=5)),
                keywords=",".join(fallback_tags(note_content, title=note_title, max_tags=5)),
            )
            db.add(note)
            db.commit()
            db.refresh(note)
            actions.append("note_created")
            action_records.append({"type": "note_created", "message": "已创建笔记", "data": {"note_id": note.id}})
            logger.debug("agent note persisted | note_id=%s | video_id=%s", note.id, video.id)

            if ctx.current_time_seconds is not None:
                timestamp = NoteTimestamp(
                    note_id=note.id,
                    time_seconds=float(ctx.current_time_seconds),
                    subtitle_text=ctx.subtitle_text.strip() or None,
                )
                db.add(timestamp)
                db.commit()
                db.refresh(timestamp)
                actions.append("timestamp_attached")
                action_records.append(
                    {
                        "type": "timestamp_attached",
                        "message": "已绑定时间戳",
                        "data": {"timestamp_id": timestamp.id, "time_seconds": timestamp.time_seconds},
                    }
                )
                logger.debug(
                    "agent timestamp persisted | note_id=%s | timestamp_id=%s | time_seconds=%s",
                    note.id,
                    timestamp.id,
                    timestamp.time_seconds,
                )

            result = {
                "note_id": note.id,
                "title": note.title,
                "summary": summary_text,
                "video_id": video.id,
            }

        if qa_answer:
            question = Question(video_id=video.id, content=ctx.user_input, answer=qa_answer)
            db.add(question)
            db.commit()
            db.refresh(question)
            actions.append("qa_recorded")
            action_records.append(
                {"type": "qa_recorded", "message": "已写回问答记录", "data": {"question_id": question.id}}
            )
            logger.debug("agent qa record persisted | question_id=%s | video_id=%s", question.id, video.id)
            result.setdefault("question_id", question.id)
            result.setdefault("answer", qa_answer)

        if not result:
            result = {
                "video_id": video.id,
                "preview": ctx.subtitle_text[:200],
            }

    else:
        result = {
            "video_id": None,
            "preview": ctx.user_input[:200],
        }

    if "summary_generated" not in actions and ctx.subtitle_text.strip():
        actions.append("summary_generated")

    logger.debug(
        "agent completed | intent=%s | actions=%s | note_id=%s | question_id=%s | result_keys=%s",
        intent,
        actions,
        result.get("note_id"),
        result.get("question_id"),
        sorted(result.keys()),
    )
    return {
        "intent": intent,
        "plan": plan,
        "actions": actions,
        "result": result,
        "note_id": result.get("note_id"),
        "question_id": result.get("question_id"),
        "video_id": result.get("video_id"),
        "created_at": datetime.utcnow(),
        "action_records": action_records,
    }
