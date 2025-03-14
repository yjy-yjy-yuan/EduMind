from flask import Blueprint, jsonify, request, current_app, Response, stream_with_context
from app.models.qa import Question
from app.models.video import Video
from app.utils.qa_utils import QASystem
from app import db

qa_bp = Blueprint('qa', __name__)

qa_system = QASystem()

@qa_bp.route('/ask', methods=['POST'])
def ask_question():
    """提问并获取答案"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        video_id = data.get('video_id')
        question_content = data.get('question')
        api_key = data.get('api_key')
        mode = data.get('mode', 'video')  # 默认为视频问答模式
        stream_response = data.get('stream', True)  # 默认启用流式响应
        
        if not all([question_content, api_key]):
            return jsonify({'error': '缺少必要参数'}), 400
            
        # 如果是视频问答模式，需要检查视频ID
        if mode == 'video':
            if not video_id:
                return jsonify({'error': '视频问答模式需要提供视频ID'}), 400
                
            # 获取视频信息
            video = Video.query.get_or_404(video_id)
            if not video.subtitle_filepath:
                return jsonify({'error': '该视频尚未生成字幕'}), 400
                
            # 检查字幕文件是否存在
            import os
            if not os.path.exists(video.subtitle_filepath):
                return jsonify({'error': '字幕文件不存在'}), 400
                
            # 读取字幕文件内容
            try:
                with open(video.subtitle_filepath, 'r', encoding='utf-8') as f:
                    subtitle_content = f.read()
                if not subtitle_content.strip():
                    return jsonify({'error': '字幕文件内容为空'}), 400
            except Exception as e:
                current_app.logger.error(f"读取字幕文件时出错: {str(e)}")
                return jsonify({'error': f'读取字幕文件时出错: {str(e)}'}), 500
        
        # 创建问题记录
        question = Question(
            video_id=video_id if mode == 'video' else None,
            content=question_content
        )
        db.session.add(question)
        
        try:
            if mode == 'video':
                # 创建知识库
                try:
                    vectorstore = qa_system.create_knowledge_base(video.subtitle_filepath)
                    if not vectorstore or not qa_system.texts or len(qa_system.texts) == 0:
                        return jsonify({'error': '未找到有效的字幕内容'}), 500
                except Exception as e:
                    current_app.logger.error(f"创建知识库时出错: {str(e)}")
                    return jsonify({'error': f'创建知识库时出错: {str(e)}'}), 500
            
            # 如果请求流式响应
            if stream_response:
                # 使用流式响应
                def generate():
                    full_answer = ""
                    for chunk in qa_system.get_answer_stream(question_content, api_key, mode):
                        full_answer += chunk
                        yield chunk
                    
                    # 更新问题记录
                    question.answer = full_answer
                    db.session.commit()
                
                return Response(stream_with_context(generate()), content_type='text/plain')
            else:
                # 使用非流式响应
                answer = qa_system.get_answer(question_content, api_key, mode)
                
                # 更新问题记录
                question.answer = answer
                db.session.commit()
                
                return jsonify(question.to_dict()), 200
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"处理问题时出错: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        current_app.logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@qa_bp.route('/history/<int:video_id>', methods=['GET'])
def get_qa_history(video_id):
    """获取视频的问答历史"""
    try:
        questions = Question.query.filter_by(video_id=video_id).order_by(Question.created_at.desc()).all()
        return jsonify([q.to_dict() for q in questions]), 200
    except Exception as e:
        current_app.logger.error(f"获取问答历史时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500
