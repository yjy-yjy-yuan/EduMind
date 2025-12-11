"""问答系统路由 - FastAPI 版本"""

import logging
import os
from typing import Optional

from app.core.database import get_db
from app.models.qa import Question
from app.models.video import Video
from app.schemas.qa import AskRequest
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# QA 系统实例（延迟初始化）
_qa_system = None


def get_qa_system():
    """获取 QA 系统实例"""
    global _qa_system
    if _qa_system is None:
        try:
            from app.utils.qa_utils import QASystem

            _qa_system = QASystem()
        except ImportError:
            logger.warning("QASystem 未实现，使用模拟实现")
            _qa_system = None
    return _qa_system


@router.post("/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """提问并获取答案"""
    try:
        qa_system = get_qa_system()

        # 如果使用 Ollama 模式，检查服务是否可用
        if request.use_ollama:
            try:
                from app.utils.qa_utils import check_ollama_service

                if not check_ollama_service():
                    raise HTTPException(status_code=503, detail="Ollama服务不可用，请检查服务是否运行")
            except ImportError:
                logger.warning("check_ollama_service 未实现")
        elif not request.api_key:
            raise HTTPException(status_code=400, detail="在线模式需要提供API密钥")

        # 视频问答模式需要验证视频
        if request.mode == "video":
            if not request.video_id:
                raise HTTPException(status_code=400, detail="视频问答模式需要提供视频ID")

            video = db.query(Video).filter(Video.id == request.video_id).first()
            if not video:
                raise HTTPException(status_code=404, detail="视频不存在")
            if not video.subtitle_filepath:
                raise HTTPException(status_code=400, detail="该视频尚未生成字幕")
            if not os.path.exists(video.subtitle_filepath):
                raise HTTPException(status_code=400, detail="字幕文件不存在")

            # 创建知识库
            if qa_system:
                try:
                    qa_system.create_knowledge_base(video.subtitle_filepath)
                except Exception as e:
                    logger.error(f"创建知识库时出错: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"创建知识库时出错: {str(e)}")

        # 创建问题记录
        question = Question(video_id=request.video_id if request.mode == "video" else None, content=request.question)
        db.add(question)
        db.commit()
        db.refresh(question)

        # 流式响应
        if request.stream:

            async def generate():
                full_answer = ""
                try:
                    if qa_system:
                        for chunk in qa_system.get_answer_stream(
                            request.question,
                            request.api_key,
                            request.mode,
                            use_ollama=request.use_ollama,
                            deep_thinking=request.deep_thinking,
                        ):
                            full_answer += chunk
                            yield chunk
                    else:
                        # 模拟响应
                        mock_answer = f"这是对问题「{request.question}」的模拟回答。QA系统尚未完全配置。"
                        full_answer = mock_answer
                        yield mock_answer

                    # 更新答案
                    question.answer = full_answer
                    db.commit()
                except Exception as e:
                    logger.error(f"流式响应出错: {str(e)}")
                    yield f"回答生成出错: {str(e)}"

            return StreamingResponse(generate(), media_type="text/plain")
        else:
            # 非流式响应
            if qa_system:
                answer = qa_system.get_answer(
                    request.question,
                    request.api_key,
                    request.mode,
                    use_ollama=request.use_ollama,
                    deep_thinking=request.deep_thinking,
                )
            else:
                answer = f"这是对问题「{request.question}」的模拟回答。"

            question.answer = answer
            db.commit()

            return question.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理问题时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{video_id}")
async def get_qa_history(video_id: int, db: Session = Depends(get_db)):
    """获取视频的问答历史"""
    try:
        questions = db.query(Question).filter(Question.video_id == video_id).order_by(Question.created_at.desc()).all()
        return [q.to_dict() for q in questions]
    except Exception as e:
        logger.error(f"获取问答历史时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
