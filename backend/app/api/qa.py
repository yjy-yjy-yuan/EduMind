"""问答路由 - FastAPI 版本"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.qa import Question
from app.models.video import Video
from app.schemas.qa import QuestionCreate, QuestionResponse, QAHistoryResponse
from app.utils.qa_utils import QASystem, check_ollama_service

logger = logging.getLogger(__name__)

router = APIRouter()

qa_system = QASystem()


@router.post("/ask")
async def ask_question(request: QuestionCreate, db: Session = Depends(get_db)):
    """提问并获取答案"""
    video_id = request.video_id
    question_content = request.question
    api_key = request.api_key
    mode = request.mode
    stream_response = request.stream
    use_ollama = request.use_ollama
    deep_thinking = request.deep_thinking

    logger.info(f"请求参数: question={question_content}, mode={mode}, use_ollama={use_ollama}, deep_thinking={deep_thinking}")

    # 检查Ollama服务
    if use_ollama:
        if not check_ollama_service():
            raise HTTPException(status_code=503, detail="Ollama服务不可用，请检查服务是否运行")
    else:
        if not api_key:
            raise HTTPException(status_code=400, detail="在线模式需要提供API密钥")

    if not question_content:
        raise HTTPException(status_code=400, detail="缺少问题内容")

    # 如果是视频问答模式
    if mode == 'video':
        if not video_id:
            raise HTTPException(status_code=400, detail="视频问答模式需要提供视频ID")

        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")

        if not video.subtitle_filepath:
            raise HTTPException(status_code=400, detail="该视频尚未生成字幕")

        if not os.path.exists(video.subtitle_filepath):
            raise HTTPException(status_code=400, detail="字幕文件不存在")

        with open(video.subtitle_filepath, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()

        if not subtitle_content.strip():
            raise HTTPException(status_code=400, detail="字幕文件内容为空")

    # 创建问题记录
    question = Question(
        video_id=video_id if mode == 'video' else None,
        content=question_content
    )
    db.add(question)
    db.commit()

    try:
        if mode == 'video':
            vectorstore = qa_system.create_knowledge_base(video.subtitle_filepath)
            if not vectorstore or len(qa_system.subtitles) == 0:
                raise HTTPException(status_code=500, detail="未找到有效的字幕内容")

        # 流式响应
        if stream_response:
            def generate():
                full_answer = ""
                try:
                    logger.info(f"开始流式响应，use_ollama={use_ollama}, deep_thinking={deep_thinking}")

                    for chunk in qa_system.get_answer_stream(
                        question_content, api_key, mode,
                        use_ollama=use_ollama, deep_thinking=deep_thinking
                    ):
                        full_answer += chunk
                        yield chunk

                    # 更新问题记录
                    question.answer = full_answer
                    db.commit()
                    logger.info(f"流式响应完成，答案长度={len(full_answer)}")
                except Exception as e:
                    logger.error(f"流式响应出错: {str(e)}")
                    yield f"回答生成出错: {str(e)}"

            return StreamingResponse(generate(), media_type='text/plain')
        else:
            # 非流式响应
            answer = qa_system.get_answer(
                question_content, api_key, mode,
                use_ollama=use_ollama, deep_thinking=deep_thinking
            )

            question.answer = answer
            db.commit()
            db.refresh(question)

            return QuestionResponse.model_validate(question.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"处理问题时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{video_id}")
async def get_qa_history(video_id: int, db: Session = Depends(get_db)):
    """获取视频的问答历史"""
    questions = db.query(Question).filter(
        Question.video_id == video_id
    ).order_by(Question.created_at.desc()).all()

    return [QuestionResponse.model_validate(q.to_dict()) for q in questions]
