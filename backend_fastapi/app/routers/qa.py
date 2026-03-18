"""问答系统路由 - FastAPI 版本"""

import json
import logging

from app.core.database import get_db
from app.core.database import SessionLocal
from app.models.qa import Question
from app.models.video import Video
from app.schemas.qa import AskRequest
from app.utils.qa_utils import QAConfigError
from app.utils.qa_utils import QAProviderError
from app.utils.qa_utils import QASystem
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_QA_MODES = {"video", "free"}


def serialize_stream_event(event: dict) -> str:
    return f"{json.dumps(event, ensure_ascii=False)}\n"


@router.post("/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """提问并获取答案"""
    try:
        normalized_mode = str(request.mode or "").strip().lower() or "video"
        if normalized_mode not in SUPPORTED_QA_MODES:
            raise HTTPException(status_code=400, detail="不支持的问答模式，仅支持 video 或 free")

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

        # 流式响应
        if request.stream:
            def generate():
                stream_db = SessionLocal()
                try:
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
                        }
                    )

                    for event in stream_qa_system.answer_stream(
                        request.question,
                        provider=request.provider,
                        model=request.model or "",
                        deep_thinking=request.deep_thinking,
                        mode=normalized_mode,
                        history=request.history,
                    ):
                        if event.get("type") == "answer":
                            question = Question(
                                video_id=request.video_id if normalized_mode == "video" else None,
                                content=request.question,
                                answer=event.get("answer"),
                            )
                            stream_db.add(question)
                            stream_db.commit()
                            stream_db.refresh(question)
                            event.update(question.to_dict())
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
            provider=request.provider,
            model=request.model or "",
            deep_thinking=request.deep_thinking,
            mode=normalized_mode,
            history=request.history,
        )
        question = Question(
            video_id=request.video_id if normalized_mode == "video" else None,
            content=request.question,
            answer=result["answer"],
        )
        db.add(question)
        db.commit()
        db.refresh(question)

        response_payload = question.to_dict()
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
async def get_qa_history(video_id: int, db: Session = Depends(get_db)):
    """获取视频的问答历史"""
    try:
        questions = db.query(Question).filter(Question.video_id == video_id).order_by(Question.created_at.desc()).all()
        return [q.to_dict() for q in questions]
    except Exception as e:
        logger.error(f"获取问答历史时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
