"""笔记路由 - FastAPI 版本"""
import io
import json
import zipfile
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
import jieba.analyse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.database import get_db
from app.models.note import Note, NoteTimestamp
from app.models.video import Video
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    TimestampCreate,
    SimilarNotesRequest,
    BatchDeleteRequest,
    TagResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

tfidf_vectorizer = TfidfVectorizer(max_features=100)


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """提取文本关键词"""
    if not text or len(text) < 10:
        return []
    return jieba.analyse.extract_tags(text, topK=top_k)


def generate_content_vector(text: str, all_contents: List[str]) -> str:
    """生成内容向量"""
    if not text or len(text.strip()) == 0:
        return json.dumps([0.0] * 10)

    if not all_contents:
        all_contents = ["默认文本示例", text]
    else:
        all_contents = list(all_contents) + [text]

    try:
        vectorizer = TfidfVectorizer(max_features=100, stop_words=None, min_df=1)
        vectorizer.fit(all_contents)
        vector = vectorizer.transform([text]).toarray()[0]
        return json.dumps(vector.tolist())
    except ValueError as e:
        logger.error(f"生成内容向量时出错: {str(e)}")
        return json.dumps([0.0] * 10)


@router.get("", response_model=NoteListResponse)
async def get_notes(
    video_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    note_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取所有笔记"""
    query = db.query(Note)

    if video_id:
        query = query.filter(Note.video_id == video_id)

    if tag:
        query = query.filter(Note.tags.like(f'%{tag}%'))

    if note_type:
        query = query.filter(Note.note_type == note_type)

    if search:
        query = query.filter(or_(
            Note.title.like(f'%{search}%'),
            Note.content.like(f'%{search}%'),
            Note.keywords.like(f'%{search}%')
        ))

    notes = query.order_by(Note.updated_at.desc()).all()

    return NoteListResponse(data=[NoteResponse.model_validate(note.to_dict()) for note in notes])


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: Session = Depends(get_db)):
    """获取单个笔记"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    return NoteResponse.model_validate(note.to_dict())


@router.post("", response_model=NoteResponse)
async def create_note(request: NoteCreate, db: Session = Depends(get_db)):
    """创建新笔记"""
    if request.video_id:
        video = db.query(Video).filter(Video.id == request.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="视频不存在")

    # 获取所有笔记内容用于向量化
    all_notes = db.query(Note).all()
    all_contents = [note.content for note in all_notes if note.content and len(note.content.strip()) > 0]

    # 提取关键词
    keywords = extract_keywords(request.content)
    keywords_str = ','.join(keywords) if keywords else None

    # 生成内容向量
    content_vector = generate_content_vector(request.content, all_contents)

    note = Note(
        title=request.title,
        content=request.content,
        content_vector=content_vector,
        note_type=request.note_type,
        video_id=request.video_id,
        tags=','.join(request.tags) if request.tags else None,
        keywords=keywords_str
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    # 添加时间戳
    if request.timestamps:
        for ts in request.timestamps:
            timestamp = NoteTimestamp(
                note_id=note.id,
                time_seconds=ts.time_seconds,
                subtitle_text=ts.subtitle_text
            )
            db.add(timestamp)
        db.commit()
        db.refresh(note)

    return NoteResponse.model_validate(note.to_dict())


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, request: NoteUpdate, db: Session = Depends(get_db)):
    """更新笔记"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    note.title = request.title

    if request.content is not None:
        note.content = request.content

        # 提取关键词
        keywords = extract_keywords(note.content)
        note.keywords = ','.join(keywords) if keywords else None

        # 获取所有笔记内容用于向量化
        all_notes = db.query(Note).all()
        all_contents = [n.content for n in all_notes if n.content and len(n.content.strip()) > 0]
        note.content_vector = generate_content_vector(note.content, all_contents)

    if request.note_type is not None:
        note.note_type = request.note_type

    if request.tags is not None:
        note.tags = ','.join(request.tags) if request.tags else None

    # 更新时间戳
    if request.timestamps is not None:
        db.query(NoteTimestamp).filter(NoteTimestamp.note_id == note.id).delete()

        for ts in request.timestamps:
            timestamp = NoteTimestamp(
                note_id=note.id,
                time_seconds=ts.time_seconds,
                subtitle_text=ts.subtitle_text
            )
            db.add(timestamp)

    db.commit()
    db.refresh(note)

    return NoteResponse.model_validate(note.to_dict())


@router.delete("/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """删除笔记"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    db.delete(note)
    db.commit()

    return {"status": "success", "message": "笔记已删除"}


@router.post("/{note_id}/timestamps")
async def add_timestamp(note_id: int, request: TimestampCreate, db: Session = Depends(get_db)):
    """添加时间戳"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    timestamp = NoteTimestamp(
        note_id=note.id,
        time_seconds=request.time_seconds,
        subtitle_text=request.subtitle_text
    )

    db.add(timestamp)
    db.commit()
    db.refresh(timestamp)

    return {"status": "success", "data": timestamp.to_dict()}


@router.delete("/{note_id}/timestamps/{timestamp_id}")
async def delete_timestamp(note_id: int, timestamp_id: int, db: Session = Depends(get_db)):
    """删除时间戳"""
    timestamp = db.query(NoteTimestamp).filter(
        NoteTimestamp.id == timestamp_id,
        NoteTimestamp.note_id == note_id
    ).first()

    if not timestamp:
        raise HTTPException(status_code=404, detail="时间戳不存在")

    db.delete(timestamp)
    db.commit()

    return {"status": "success", "message": "时间戳已删除"}


@router.get("/tags/all", response_model=List[TagResponse])
async def get_tags(db: Session = Depends(get_db)):
    """获取所有标签"""
    notes = db.query(Note).filter(Note.tags.isnot(None)).all()

    all_tags = {}
    for note in notes:
        if note.tags:
            for tag in note.tags.split(','):
                if tag in all_tags:
                    all_tags[tag] += 1
                else:
                    all_tags[tag] = 1

    sorted_tags = [
        TagResponse(name=tag, count=count)
        for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
    ]

    return sorted_tags


@router.post("/similar", response_model=NoteListResponse)
async def get_similar_notes(request: SimilarNotesRequest, db: Session = Depends(get_db)):
    """获取相似笔记"""
    content = request.content
    limit = request.limit

    if not content or len(content) < 10:
        return NoteListResponse(data=[])

    # 提取关键词
    keywords = extract_keywords(content)

    # 生成向量
    all_notes = db.query(Note).all()
    all_contents = [note.content for note in all_notes if note.content]

    query_vector = None
    if all_contents:
        all_contents.append(content)
        try:
            tfidf_vectorizer.fit(all_contents)
            query_vector = tfidf_vectorizer.transform([content]).toarray()[0]
        except Exception as e:
            logger.error(f"向量生成错误: {str(e)}")

    similar_notes = []

    # 关键词匹配
    if keywords:
        conditions = []
        for word in keywords[:5]:
            conditions.append(or_(
                Note.title.like(f'%{word}%'),
                Note.content.like(f'%{word}%'),
                Note.keywords.like(f'%{word}%')
            ))

        keyword_matches = db.query(Note).filter(or_(*conditions)).all()
        similar_notes.extend(keyword_matches)

    # 向量相似度匹配
    if query_vector is not None:
        notes_with_vector = db.query(Note).filter(Note.content_vector.isnot(None)).all()

        for note in notes_with_vector:
            try:
                note_vector = json.loads(note.content_vector)
                if len(note_vector) == len(query_vector):
                    similarity = cosine_similarity([note_vector], [query_vector])[0][0]
                    if similarity > 0.3:
                        if note not in similar_notes:
                            similar_notes.append(note)
            except Exception:
                continue

    # 去重并限制数量
    unique_notes = []
    note_ids = set()
    for note in similar_notes:
        if note.id not in note_ids and len(unique_notes) < limit:
            note_ids.add(note.id)
            unique_notes.append(note)

    return NoteListResponse(data=[NoteResponse.model_validate(note.to_dict()) for note in unique_notes])


@router.post("/batch-delete")
async def batch_delete_notes(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除笔记"""
    note_ids = request.note_ids

    if not note_ids:
        raise HTTPException(status_code=400, detail="未提供笔记ID")

    notes = db.query(Note).filter(Note.id.in_(note_ids)).all()

    for note in notes:
        db.delete(note)

    db.commit()

    return {
        "status": "success",
        "message": f"成功删除 {len(notes)} 条笔记",
        "deleted_count": len(notes)
    }


@router.post("/batch-export")
async def batch_export_notes(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量导出笔记"""
    note_ids = request.note_ids

    if not note_ids:
        raise HTTPException(status_code=400, detail="未提供笔记ID")

    notes = db.query(Note).filter(Note.id.in_(note_ids)).all()

    if not notes:
        raise HTTPException(status_code=404, detail="未找到指定的笔记")

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for note in notes:
            md_content = f"# {note.title}\n\n"
            md_content += f"创建时间: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            md_content += f"更新时间: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if note.tags:
                md_content += f"标签: {note.tags}\n"

            md_content += "\n---\n\n"
            md_content += note.content

            safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in note.title])
            zf.writestr(f"{safe_title}.md", md_content.encode('utf-8'))

    memory_file.seek(0)

    return StreamingResponse(
        memory_file,
        media_type='application/zip',
        headers={'Content-Disposition': 'attachment; filename=notes_export.zip'}
    )


@router.get("/{note_id}/export")
async def export_single_note(note_id: int, db: Session = Depends(get_db)):
    """导出单个笔记"""
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(status_code=404, detail="未找到指定的笔记")

    md_content = f"# {note.title}\n\n"
    md_content += f"创建时间: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    md_content += f"更新时间: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if note.tags:
        md_content += f"标签: {note.tags}\n"

    md_content += "\n---\n\n"
    md_content += note.content

    safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in note.title])
    filename = f"{safe_title}.md"

    return Response(
        content=md_content,
        media_type='text/markdown',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.post("/tags/sync")
async def sync_tags(db: Session = Depends(get_db)):
    """同步标签数据"""
    notes = db.query(Note).all()

    valid_tags = set()
    for note in notes:
        if note.tags:
            for tag in note.tags.split(','):
                if tag.strip():
                    valid_tags.add(tag.strip())

    for note in notes:
        if note.tags:
            tags = note.tags.split(',')
            filtered_tags = [tag for tag in tags if tag.strip() in valid_tags]
            note.tags = ','.join(filtered_tags) if filtered_tags else None

    db.commit()

    return {
        "status": "success",
        "message": "标签数据已同步",
        "valid_tags": list(valid_tags)
    }
