from flask import Blueprint, request, jsonify, send_file, current_app
from app.models.note import Note, NoteTimestamp
from app.models.video import Video
from app.extensions import db
from datetime import datetime
import json
from sqlalchemy import or_
import jieba.analyse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import io
import zipfile

note_bp = Blueprint('note', __name__)

# 创建TF-IDF向量化器
tfidf_vectorizer = TfidfVectorizer(max_features=100)

@note_bp.route('/api/notes', methods=['GET'])
def get_notes():
    """获取所有笔记"""
    # 获取查询参数
    video_id = request.args.get('video_id', type=int)
    tag = request.args.get('tag')
    search = request.args.get('search')
    note_type = request.args.get('note_type')
    
    # 构建查询
    query = Note.query
    
    # 根据视频ID筛选
    if video_id:
        query = query.filter(Note.video_id == video_id)
    
    # 根据标签筛选
    if tag:
        query = query.filter(Note.tags.like(f'%{tag}%'))
    
    # 根据笔记类型筛选
    if note_type:
        query = query.filter(Note.note_type == note_type)
    
    # 根据搜索词筛选（标题和内容）
    if search:
        query = query.filter(or_(
            Note.title.like(f'%{search}%'),
            Note.content.like(f'%{search}%'),
            Note.keywords.like(f'%{search}%')
        ))
    
    # 按更新时间排序
    notes = query.order_by(Note.updated_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': [note.to_dict() for note in notes]
    })

@note_bp.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """获取单个笔记"""
    note = Note.query.get_or_404(note_id)
    
    return jsonify({
        'status': 'success',
        'data': note.to_dict()
    })

def extract_keywords(text, top_k=10):
    """提取文本关键词"""
    if not text or len(text) < 10:
        return []
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_k)
    return keywords

def generate_content_vector(text):
    """生成内容向量"""
    if not text or len(text.strip()) == 0:
        # 如果文本为空或只包含空白字符，返回空向量
        return json.dumps([0.0] * 10)  # 返回固定长度的零向量
    
    # 使用所有笔记内容来训练TF-IDF向量化器
    all_notes = Note.query.all()
    all_contents = [note.content for note in all_notes if note.content and len(note.content.strip()) > 0]
    
    # 确保有足够的非空文本进行训练
    if not all_contents:
        # 如果没有其他笔记，使用一些默认文本
        all_contents = ["默认文本示例", text]
    else:
        all_contents.append(text)
    
    try:
        # 拟合向量化器并转换当前文本
        tfidf_vectorizer = TfidfVectorizer(
            max_features=100,  # 限制特征数量
            stop_words=None,   # 不使用停用词
            min_df=1           # 最小文档频率
        )
        tfidf_vectorizer.fit(all_contents)
        vector = tfidf_vectorizer.transform([text]).toarray()[0]
        
        # 转换为JSON字符串存储
        return json.dumps(vector.tolist())
    except ValueError as e:
        # 处理可能的错误，返回空向量
        current_app.logger.error(f"生成内容向量时出错: {str(e)}")
        return json.dumps([0.0] * 10)  # 返回固定长度的零向量

@note_bp.route('/api/notes', methods=['POST'])
def create_note():
    """创建新笔记"""
    data = request.json
    
    # 验证必要字段
    if not data.get('title'):
        return jsonify({
            'status': 'error',
            'message': '标题不能为空'
        }), 400
    
    # 如果提供了视频ID，验证视频是否存在
    video_id = data.get('video_id')
    if video_id:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'status': 'error',
                'message': '视频不存在'
            }), 404
    
    content = data.get('content', '')
    
    # 提取关键词
    keywords = extract_keywords(content)
    keywords_str = ','.join(keywords) if keywords else None
    
    # 生成内容向量
    content_vector = generate_content_vector(content)
    
    # 创建笔记
    note = Note(
        title=data.get('title'),
        content=content,
        content_vector=content_vector,
        note_type=data.get('note_type', 'text'),
        video_id=video_id,
        tags=','.join(data.get('tags', [])) if data.get('tags') else None,
        keywords=keywords_str
    )
    
    # 添加时间戳
    timestamps = data.get('timestamps', [])
    
    db.session.add(note)
    db.session.commit()
    
    # 添加时间戳
    for ts in timestamps:
        timestamp = NoteTimestamp(
            note_id=note.id,
            time_seconds=ts.get('time_seconds'),
            subtitle_text=ts.get('subtitle_text')
        )
        db.session.add(timestamp)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': note.to_dict()
    })

@note_bp.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """更新笔记"""
    note = Note.query.get_or_404(note_id)
    data = request.json
    
    # 验证必要字段
    if not data.get('title'):
        return jsonify({
            'status': 'error',
            'message': '标题不能为空'
        }), 400
    
    # 更新基本信息
    note.title = data.get('title')
    
    # 更新内容并重新生成向量和关键词
    if 'content' in data:
        note.content = data.get('content')
        
        # 提取关键词
        keywords = extract_keywords(note.content)
        note.keywords = ','.join(keywords) if keywords else None
        
        # 生成内容向量
        note.content_vector = generate_content_vector(note.content)
    
    # 更新其他字段
    if 'note_type' in data:
        note.note_type = data.get('note_type')
    
    if 'tags' in data:
        note.tags = ','.join(data.get('tags', [])) if data.get('tags') else None
    
    # 更新时间戳
    if 'timestamps' in data:
        # 删除现有时间戳
        NoteTimestamp.query.filter_by(note_id=note.id).delete()
        
        # 添加新时间戳
        for ts in data.get('timestamps', []):
            timestamp = NoteTimestamp(
                note_id=note.id,
                time_seconds=ts.get('time_seconds'),
                subtitle_text=ts.get('subtitle_text')
            )
            db.session.add(timestamp)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': note.to_dict()
    })

@note_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """删除笔记"""
    note = Note.query.get_or_404(note_id)
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '笔记已删除'
    })

@note_bp.route('/api/notes/<int:note_id>/timestamps', methods=['POST'])
def add_timestamp(note_id):
    """添加时间戳"""
    note = Note.query.get_or_404(note_id)
    data = request.json
    
    # 验证必要字段
    if 'time_seconds' not in data:
        return jsonify({
            'status': 'error',
            'message': '时间点不能为空'
        }), 400
    
    # 创建时间戳
    timestamp = NoteTimestamp(
        note_id=note.id,
        time_seconds=data.get('time_seconds'),
        subtitle_text=data.get('subtitle_text')
    )
    
    db.session.add(timestamp)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'data': timestamp.to_dict()
    })

@note_bp.route('/api/notes/<int:note_id>/timestamps/<int:timestamp_id>', methods=['DELETE'])
def delete_timestamp(note_id, timestamp_id):
    """删除时间戳"""
    timestamp = NoteTimestamp.query.filter_by(id=timestamp_id, note_id=note_id).first_or_404()
    
    db.session.delete(timestamp)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': '时间戳已删除'
    })

@note_bp.route('/api/tags', methods=['GET'])
def get_tags():
    """获取所有标签"""
    # 查询所有笔记的标签
    notes = Note.query.filter(Note.tags.isnot(None)).all()
    
    # 提取并统计标签
    all_tags = {}
    for note in notes:
        if note.tags:
            for tag in note.tags.split(','):
                if tag in all_tags:
                    all_tags[tag] += 1
                else:
                    all_tags[tag] = 1
    
    # 按使用频率排序
    sorted_tags = [{'name': tag, 'count': count} for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)]
    
    return jsonify({
        'status': 'success',
        'data': sorted_tags
    })

@note_bp.route('/api/notes/similar', methods=['POST'])
def get_similar_notes():
    """获取相似笔记"""
    data = request.json
    content = data.get('content', '')
    limit = data.get('limit', 5)
    
    if not content or len(content) < 10:
        return jsonify({
            'status': 'success',
            'data': []
        })
    
    # 1. 提取当前内容的关键词
    keywords = extract_keywords(content)
    
    # 2. 生成当前内容的向量
    query_vector = None
    try:
        # 获取所有笔记内容
        all_notes = Note.query.all()
        all_contents = [note.content for note in all_notes if note.content]
        
        if all_contents:
            all_contents.append(content)
            
            # 拟合向量化器并转换当前文本
            tfidf_vectorizer.fit(all_contents)
            query_vector = tfidf_vectorizer.transform([content]).toarray()[0]
    except Exception as e:
        current_app.logger.error(f"向量生成错误: {str(e)}")
    
    # 3. 基于关键词匹配和向量相似度的混合策略
    similar_notes = []
    
    # 3.1 关键词匹配
    if keywords:
        keyword_query = Note.query
        
        # 构建查询条件
        conditions = []
        for word in keywords[:5]:  # 限制关键词数量
            conditions.append(or_(
                Note.title.like(f'%{word}%'),
                Note.content.like(f'%{word}%'),
                Note.keywords.like(f'%{word}%')
            ))
        
        # 使用OR连接所有条件
        keyword_query = keyword_query.filter(or_(*conditions))
        
        # 获取结果
        keyword_matches = keyword_query.all()
        similar_notes.extend(keyword_matches)
    
    # 3.2 向量相似度匹配（如果向量生成成功）
    if query_vector is not None:
        vector_similar_notes = []
        
        # 获取所有有向量的笔记
        notes_with_vector = Note.query.filter(Note.content_vector.isnot(None)).all()
        
        # 计算相似度
        for note in notes_with_vector:
            try:
                note_vector = json.loads(note.content_vector)
                
                # 确保向量维度匹配
                if len(note_vector) == len(query_vector):
                    similarity = cosine_similarity([note_vector], [query_vector])[0][0]
                    
                    if similarity > 0.3:  # 相似度阈值
                        vector_similar_notes.append((note, similarity))
            except:
                continue
        
        # 按相似度排序并添加到结果中
        vector_similar_notes.sort(key=lambda x: x[1], reverse=True)
        for note, _ in vector_similar_notes[:limit]:
            if note not in similar_notes:
                similar_notes.append(note)
    
    # 去重并限制数量
    unique_notes = []
    note_ids = set()
    for note in similar_notes:
        if note.id not in note_ids and len(unique_notes) < limit:
            note_ids.add(note.id)
            unique_notes.append(note)
    
    return jsonify({
        'status': 'success',
        'data': [note.to_dict() for note in unique_notes]
    })

@note_bp.route('/api/notes/batch-delete', methods=['POST'])
def batch_delete_notes():
    """批量删除笔记"""
    data = request.json
    note_ids = data.get('note_ids', [])
    
    if not note_ids:
        return jsonify({
            'status': 'error',
            'message': '未提供笔记ID'
        }), 400
    
    try:
        # 查找所有指定ID的笔记
        notes = Note.query.filter(Note.id.in_(note_ids)).all()
        
        # 删除找到的笔记
        for note in notes:
            db.session.delete(note)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'成功删除 {len(notes)} 条笔记',
            'deleted_count': len(notes)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量删除笔记失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'批量删除笔记失败: {str(e)}'
        }), 500

@note_bp.route('/api/notes/batch-export', methods=['POST'])
def batch_export_notes():
    """批量导出笔记"""
    data = request.json
    note_ids = data.get('note_ids', [])
    
    if not note_ids:
        return jsonify({
            'status': 'error',
            'message': '未提供笔记ID'
        }), 400
    
    try:
        # 查找所有指定ID的笔记
        notes = Note.query.filter(Note.id.in_(note_ids)).all()
        
        if not notes:
            return jsonify({
                'status': 'error',
                'message': '未找到指定的笔记'
            }), 404
        
        # 创建内存中的ZIP文件
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for note in notes:
                # 创建Markdown文件内容
                md_content = f"# {note.title}\n\n"
                md_content += f"创建时间: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                md_content += f"更新时间: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                if note.tags:
                    md_content += f"标签: {', '.join(note.tags)}\n"
                
                md_content += "\n---\n\n"
                md_content += note.content
                
                # 将笔记添加到ZIP文件中
                safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in note.title])
                zf.writestr(f"{safe_title}.md", md_content)
        
        # 设置文件指针到开始位置
        memory_file.seek(0)
        
        # 返回ZIP文件
        return current_app.response_class(
            memory_file,
            mimetype='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename=notes_export.zip'
            }
        )
    except Exception as e:
        current_app.logger.error(f"批量导出笔记失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'批量导出笔记失败: {str(e)}'
        }), 500

@note_bp.route('/api/notes/<int:note_id>/export', methods=['GET'])
def export_single_note(note_id):
    """导出单个笔记"""
    try:
        # 查找指定ID的笔记
        note = Note.query.get(note_id)
        
        if not note:
            return jsonify({
                'status': 'error',
                'message': '未找到指定的笔记'
            }), 404
        
        # 创建Markdown文件内容
        md_content = f"# {note.title}\n\n"
        md_content += f"创建时间: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_content += f"更新时间: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if note.tags:
            md_content += f"标签: {', '.join(note.tags)}\n"
        
        md_content += "\n---\n\n"
        md_content += note.content
        
        # 设置安全的文件名
        safe_title = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in note.title])
        filename = f"{safe_title}.md"
        
        # 返回Markdown文件
        response = current_app.response_class(
            md_content,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
        return response
    except Exception as e:
        current_app.logger.error(f"导出笔记失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'导出笔记失败: {str(e)}'
        }), 500

@note_bp.route('/api/tags/sync', methods=['POST'])
def sync_tags():
    """同步标签数据，清除不存在于任何笔记中的标签"""
    try:
        # 获取所有笔记
        notes = Note.query.all()
        
        # 收集所有实际存在的标签
        valid_tags = set()
        for note in notes:
            if note.tags:
                tags = note.tags.split(',')
                for tag in tags:
                    if tag.strip():  # 确保标签不为空
                        valid_tags.add(tag.strip())
        
        # 输出调试信息
        print(f"有效标签: {valid_tags}")
        
        # 更新所有笔记的标签，确保只包含有效标签
        for note in notes:
            if note.tags:
                tags = note.tags.split(',')
                filtered_tags = [tag for tag in tags if tag.strip() in valid_tags]
                note.tags = ','.join(filtered_tags) if filtered_tags else None
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '标签数据已同步',
            'valid_tags': list(valid_tags)
        })
    except Exception as e:
        db.session.rollback()
        print(f"同步标签时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'同步标签失败: {str(e)}'
        }), 500
