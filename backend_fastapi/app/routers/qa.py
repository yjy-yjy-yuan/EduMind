"""问答系统路由 - FastAPI 版本"""

from collections.abc import Mapping
import json
import logging
from typing import Optional

from app.core.database import get_db
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.qa import Question
from app.models.video import Video
from app.schemas.qa import AskRequest
from app.utils.qa_utils import QAConfigError
from app.utils.qa_utils import QAProviderError
from app.utils.qa_utils import QASystem
from app.utils.qa_utils import SUPPORTED_QA_PROVIDERS
from app.utils.qa_utils import resolve_provider_label
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi.responses import StreamingResponse
from sqlalchemy import inspect
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_QA_MODES = {"video", "free"}
QUESTION_SCOPE_COLUMNS = {"user_id", "provider", "mode"}
QUESTION_SELECTABLE_COLUMNS = [
    "id",
    "user_id",
    "video_id",
    "provider",
    "mode",
    "model",
    "content",
    "answer",
    "created_at",
    "updated_at",
]
LEGACY_QUESTION_SCHEMA_WARNED = False
QUESTION_TABLE_COLUMNS_CACHE: Optional[set[str]] = None


def serialize_stream_event(event: dict) -> str:
    return f"{json.dumps(event, ensure_ascii=False)}\n"


def validate_provider(provider: str) -> str:
    normalized_provider = str(provider or "").strip().lower()
    if normalized_provider not in SUPPORTED_QA_PROVIDERS:
        raise HTTPException(status_code=400, detail="provider 仅支持 qwen 或 deepseek，且不能为空")
    return normalized_provider


def get_question_table_columns(db: Session) -> set[str]:
    global QUESTION_TABLE_COLUMNS_CACHE
    if QUESTION_TABLE_COLUMNS_CACHE is not None:
        return QUESTION_TABLE_COLUMNS_CACHE

    inspector = inspect(db.get_bind())
    QUESTION_TABLE_COLUMNS_CACHE = {column["name"] for column in inspector.get_columns(Question.__tablename__)}
    return QUESTION_TABLE_COLUMNS_CACHE


def has_question_scope_columns(question_columns: set[str]) -> bool:
    return QUESTION_SCOPE_COLUMNS.issubset(question_columns)


def warn_legacy_question_schema() -> None:
    global LEGACY_QUESTION_SCHEMA_WARNED
    if LEGACY_QUESTION_SCHEMA_WARNED:
        return
    LEGACY_QUESTION_SCHEMA_WARNED = True
    logger.warning(
        "questions 表仍是旧结构，缺少 user_id/provider/mode 等隔离字段；"
        "当前将跳过数据库历史恢复，并以兼容模式写入基础问答记录。"
    )


def get_question_attr(record, field: str):
    if isinstance(record, Mapping):
        return record.get(field)
    return getattr(record, field, None)


def serialize_question_record(
    record,
    *,
    user_id: Optional[int] = None,
    provider: Optional[str] = None,
    mode: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    created_at = get_question_attr(record, "created_at")
    updated_at = get_question_attr(record, "updated_at")
    return {
        "id": get_question_attr(record, "id"),
        "user_id": get_question_attr(record, "user_id") if get_question_attr(record, "user_id") is not None else user_id,
        "video_id": get_question_attr(record, "video_id"),
        "provider": get_question_attr(record, "provider") or provider,
        "mode": get_question_attr(record, "mode") or mode,
        "model": get_question_attr(record, "model") or model,
        "content": get_question_attr(record, "content"),
        "answer": get_question_attr(record, "answer"),
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def fetch_inserted_question_record(
    db: Session,
    *,
    question_id: Optional[int],
    question_columns: set[str],
    user_id: Optional[int],
    provider: str,
    mode: str,
    model: Optional[str],
    fallback_payload: dict,
) -> dict:
    if question_id is None:
        return serialize_question_record(
            fallback_payload,
            user_id=user_id,
            provider=provider,
            mode=mode,
            model=model,
        )

    selectable_columns = [
        getattr(Question.__table__.c, column_name)
        for column_name in QUESTION_SELECTABLE_COLUMNS
        if column_name in question_columns
    ]
    row = (
        db.execute(select(*selectable_columns).where(Question.__table__.c.id == question_id))
        .mappings()
        .first()
    )
    if row is None:
        fallback_payload["id"] = question_id
        return serialize_question_record(
            fallback_payload,
            user_id=user_id,
            provider=provider,
            mode=mode,
            model=model,
        )

    return serialize_question_record(
        row,
        user_id=user_id,
        provider=provider,
        mode=mode,
        model=model,
    )


def persist_question_record(
    db: Session,
    *,
    question_columns: set[str],
    user_id: Optional[int],
    video_id: Optional[int],
    provider: str,
    mode: str,
    model: Optional[str],
    content: str,
    answer: Optional[str],
) -> dict:
    insert_payload = {
        "video_id": video_id,
        "content": content,
        "answer": answer,
    }
    if "user_id" in question_columns:
        insert_payload["user_id"] = user_id
    if "provider" in question_columns:
        insert_payload["provider"] = provider
    if "mode" in question_columns:
        insert_payload["mode"] = mode
    if "model" in question_columns:
        insert_payload["model"] = model

    result = db.execute(Question.__table__.insert().values(**insert_payload))
    db.commit()

    inserted_id = None
    inserted_primary_key = getattr(result, "inserted_primary_key", None) or []
    if inserted_primary_key:
        inserted_id = inserted_primary_key[0]
    if inserted_id is None:
        inserted_id = getattr(result, "lastrowid", None)

    return fetch_inserted_question_record(
        db,
        question_id=inserted_id,
        question_columns=question_columns,
        user_id=user_id,
        provider=provider,
        mode=mode,
        model=model,
        fallback_payload=insert_payload,
    )


def apply_question_scope(
    query,
    *,
    user_id: Optional[int],
    video_id: int,
    provider: str,
    mode: str,
):
    scoped_query = query.filter(
        Question.video_id == video_id,
        Question.provider == provider,
        Question.mode == mode,
    )
    if user_id is None:
        return scoped_query.filter(Question.user_id.is_(None))
    return scoped_query.filter(Question.user_id == user_id)


def build_history_messages_from_questions(questions: list[Question]) -> list[dict]:
    history_messages: list[dict] = []
    for question in questions:
        normalized = serialize_question_record(question)
        if normalized["content"]:
            history_messages.append({"role": "user", "content": normalized["content"]})
        if normalized["answer"]:
            history_messages.append({"role": "assistant", "content": normalized["answer"]})
    return history_messages


def build_history_response_messages(questions: list[Question]) -> list[dict]:
    messages: list[dict] = []
    for question in questions:
        normalized = serialize_question_record(question)
        if normalized["content"]:
            messages.append(
                {
                    "question_id": normalized["id"],
                    "role": "user",
                    "text": normalized["content"],
                    "video_id": normalized["video_id"],
                    "provider": normalized["provider"],
                    "mode": normalized["mode"],
                    "model": normalized["model"],
                }
            )
        if normalized["answer"]:
            messages.append(
                {
                    "question_id": normalized["id"],
                    "role": "ai",
                    "text": normalized["answer"],
                    "video_id": normalized["video_id"],
                    "provider": normalized["provider"],
                    "provider_label": resolve_provider_label(normalized["provider"]),
                    "mode": normalized["mode"],
                    "model": normalized["model"],
                    "references": [],
                }
            )
    return messages


def load_video_scope_history(
    db: Session,
    *,
    question_columns: set[str],
    user_id: Optional[int],
    video_id: int,
    provider: str,
    mode: str,
) -> list[dict]:
    if not has_question_scope_columns(question_columns):
        warn_legacy_question_schema()
        return []

    history_limit = max(1, int(settings.QA_MAX_HISTORY_MESSAGES))
    rows = (
        apply_question_scope(
            db.query(Question),
            user_id=user_id,
            video_id=video_id,
            provider=provider,
            mode=mode,
        )
        .order_by(Question.created_at.desc())
        .limit(history_limit)
        .all()
    )
    rows.reverse()
    return build_history_messages_from_questions(rows)


@router.post("/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """提问并获取答案"""
    try:
        normalized_mode = str(request.mode or "").strip().lower() or "video"
        if normalized_mode not in SUPPORTED_QA_MODES:
            raise HTTPException(status_code=400, detail="不支持的问答模式，仅支持 video 或 free")
        normalized_provider = validate_provider(request.provider)

        video = None

        # 视频问答模式需要验证视频
        if normalized_mode == "video":
            if not request.video_id:
                raise HTTPException(status_code=400, detail="视频问答模式需要提供视频ID")

            video = db.query(Video).filter(Video.id == request.video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="视频不存在")
        qa_system = QASystem(video=video)
        if normalized_mode == "video" and not qa_system.has_context():
            raise HTTPException(status_code=400, detail="该视频暂无可用于问答的字幕或摘要内容")

        question_columns = get_question_table_columns(db)
        effective_history = request.history
        if normalized_mode == "video" and request.video_id and has_question_scope_columns(question_columns):
            effective_history = load_video_scope_history(
                db,
                question_columns=question_columns,
                user_id=request.user_id,
                video_id=request.video_id,
                provider=normalized_provider,
                mode=normalized_mode,
            )
        elif normalized_mode == "video":
            warn_legacy_question_schema()

        # 流式响应
        if request.stream:
            def generate():
                stream_db = SessionLocal()
                try:
                    stream_question_columns = get_question_table_columns(stream_db)
                    stream_video = None
                    if normalized_mode == "video":
                        stream_video = stream_db.query(Video).filter(Video.id == request.video_id).first()
                        if not stream_video:
                            yield serialize_stream_event(
                                {
                                    "type": "error",
                                    "stage": "validation",
                                    "message": "视频不存在",
                                    "detail": "视频不存在",
                                    "progress": 100,
                                }
                            )
                            return

                    stream_qa_system = QASystem(video=stream_video)
                    if normalized_mode == "video" and not stream_qa_system.has_context():
                        yield serialize_stream_event(
                            {
                                "type": "error",
                                "stage": "validation",
                                "message": "该视频暂无可用于问答的字幕或摘要内容",
                                "detail": "该视频暂无可用于问答的字幕或摘要内容",
                                "progress": 100,
                            }
                        )
                        return

                    yield serialize_stream_event(
                        {
                            "type": "status",
                            "stage": "accepted",
                            "message": "问题已提交，等待处理",
                            "progress": 5,
                            "provider": normalized_provider,
                            "provider_label": resolve_provider_label(normalized_provider),
                        }
                    )

                    stream_history = request.history
                    if normalized_mode == "video" and request.video_id and has_question_scope_columns(stream_question_columns):
                        stream_history = load_video_scope_history(
                            stream_db,
                            question_columns=stream_question_columns,
                            user_id=request.user_id,
                            video_id=request.video_id,
                            provider=normalized_provider,
                            mode=normalized_mode,
                        )
                    elif normalized_mode == "video":
                        warn_legacy_question_schema()

                    for event in stream_qa_system.answer_stream(
                        request.question,
                        provider=normalized_provider,
                        model=request.model or "",
                        deep_thinking=request.deep_thinking,
                        mode=normalized_mode,
                        history=stream_history,
                    ):
                        if event.get("type") == "answer":
                            stored_question = persist_question_record(
                                stream_db,
                                question_columns=stream_question_columns,
                                user_id=request.user_id,
                                video_id=request.video_id if normalized_mode == "video" else None,
                                provider=normalized_provider,
                                mode=normalized_mode,
                                model=event.get("model"),
                                content=request.question,
                                answer=event.get("answer"),
                            )
                            event.update(stored_question)
                        logger.info(
                            "QA stream event | type=%s | stage=%s | provider=%s | model=%s | video_id=%s",
                            event.get("type"),
                            event.get("stage"),
                            event.get("provider"),
                            event.get("model"),
                            request.video_id,
                        )
                        yield serialize_stream_event(event)
                except QAConfigError as exc:
                    logger.error("问答流配置错误 | error=%s", exc)
                    stream_db.rollback()
                    yield serialize_stream_event(
                        {
                            "type": "error",
                            "stage": "config_error",
                            "message": str(exc),
                            "detail": str(exc),
                            "progress": 100,
                        }
                    )
                except QAProviderError as exc:
                    logger.error("问答流模型调用失败 | error=%s", exc)
                    stream_db.rollback()
                    yield serialize_stream_event(
                        {
                            "type": "error",
                            "stage": "provider_error",
                            "message": "模型调用失败",
                            "detail": str(exc),
                            "progress": 100,
                        }
                    )
                except Exception as exc:
                    logger.error("问答流处理失败 | error=%s", exc)
                    stream_db.rollback()
                    yield serialize_stream_event(
                        {
                            "type": "error",
                            "stage": "server_error",
                            "message": "问答处理失败，请稍后重试",
                            "detail": "问答处理失败，请稍后重试",
                            "progress": 100,
                        }
                    )
                finally:
                    stream_db.close()

            return StreamingResponse(generate(), media_type="application/x-ndjson; charset=utf-8")

        result = qa_system.ask(
            request.question,
            provider=normalized_provider,
            model=request.model or "",
            deep_thinking=request.deep_thinking,
            mode=normalized_mode,
            history=effective_history,
        )
        stored_question = persist_question_record(
            db,
            question_columns=question_columns,
            user_id=request.user_id,
            video_id=request.video_id if normalized_mode == "video" else None,
            provider=normalized_provider,
            mode=normalized_mode,
            model=result["model"],
            content=request.question,
            answer=result["answer"],
        )

        response_payload = stored_question
        response_payload.update(
            {
                "provider": result["provider"],
                "provider_label": result["provider_label"],
                "model": result["model"],
                "references": result["references"],
            }
        )
        return response_payload

    except HTTPException:
        raise
    except QAConfigError as exc:
        logger.error("问答配置错误 | error=%s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except QAProviderError as exc:
        logger.error("问答模型调用失败 | error=%s", exc)
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.error("处理问题时出错 | error=%s", exc)
        raise HTTPException(status_code=500, detail="问答处理失败，请稍后重试")


@router.get("/history/{video_id}")
async def get_qa_history(
    video_id: int,
    provider: str = Query(..., description="模型提供方: qwen, deepseek"),
    user_id: Optional[int] = Query(default=None, description="当前用户ID，用于隔离问答空间"),
    mode: str = Query(default="video", description="问答模式，视频问答固定为 video"),
    db: Session = Depends(get_db),
):
    """获取视频的问答历史"""
    try:
        normalized_mode = str(mode or "").strip().lower() or "video"
        if normalized_mode not in SUPPORTED_QA_MODES:
            raise HTTPException(status_code=400, detail="不支持的问答模式，仅支持 video 或 free")

        normalized_provider = validate_provider(provider)
        question_columns = get_question_table_columns(db)
        if not has_question_scope_columns(question_columns):
            warn_legacy_question_schema()
            return {
                "message": "获取成功",
                "total": 0,
                "questions": [],
                "messages": [],
            }
        scoped_questions = (
            apply_question_scope(
                db.query(Question),
                user_id=user_id,
                video_id=video_id,
                provider=normalized_provider,
                mode=normalized_mode,
            )
            .order_by(Question.created_at.asc())
            .all()
        )
        return {
            "message": "获取成功",
            "total": len(scoped_questions),
            "questions": [question.to_dict() for question in scoped_questions],
            "messages": build_history_response_messages(scoped_questions),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取问答历史时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
