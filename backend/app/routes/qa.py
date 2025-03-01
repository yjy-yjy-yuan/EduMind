from flask import Blueprint, jsonify, request, current_app
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
        
        # 创建问题记录
        question = Question(
            video_id=video_id if mode == 'video' else None,
            content=question_content
        )
        db.session.add(question)
        
        try:
            if mode == 'video':
                # 创建知识库
                vectorstore = qa_system.create_knowledge_base(video.subtitle_filepath)
            
            # 获取答案
            answer = qa_system.get_answer(question_content, vectorstore if mode == 'video' else None, api_key, mode)
            
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
