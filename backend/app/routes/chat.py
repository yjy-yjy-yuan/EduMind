"""
聊天系统路由
"""

from flask import Blueprint, request, jsonify
from app.chat_system import ChatSystem
from app.utils.logger import logger

# 创建蓝图
bp = Blueprint('chat', __name__)

# 创建聊天系统实例
chat_system = ChatSystem()

@bp.route('/api/videos/<int:video_id>/qa', methods=['POST'])
def video_qa(video_id):
    """基于视频内容的问答"""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': '请提供问题'}), 400

        question = data['question']
        logger.info(f"收到视频问答请求: video_id={video_id}, question={question}")

        response = chat_system.chat_with_video(question, video_id)
        return jsonify({'answer': response})

    except Exception as e:
        logger.error(f"视频问答出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/chat', methods=['POST'])
def free_chat():
    """自由问答"""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': '请提供问题'}), 400

        question = data['question']
        response = chat_system.chat_free(question)
        return jsonify({'answer': response})

    except Exception as e:
        logger.error(f"自由问答出错: {str(e)}")
        return jsonify({'error': str(e)}), 500
