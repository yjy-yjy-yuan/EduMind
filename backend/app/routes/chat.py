"""
聊天系统API路由
提供以下功能：
1. 发送问题并获取回答
2. 获取聊天历史
3. 清空聊天历史
4. 支持两种问答模式：基于视频内容的RAG问答和自由问答
"""

import os
import traceback

from flask import Blueprint
from flask import Response
from flask import current_app
from flask import jsonify
from flask import request
from flask import stream_with_context

from ..models import Video  # noqa: F401
from ..utils.chat_system import ChatSystem

# 🍎 使用平台检测工具自动导入适合当前平台的 RAG 系统（Mac MPS / Windows CUDA / CPU）
from ..utils.platform_utils import import_rag_system

# 创建蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# 创建聊天系统实例
chat_system = ChatSystem()

# 创建RAG系统实例（自动适配 Mac M4 MPS / Windows CUDA / CPU）
RAGSystem = import_rag_system()
rag_system = RAGSystem()


@chat_bp.route('/ask', methods=['POST'])
def ask():
    """处理聊天请求"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "无效的请求数据"}), 400

        # 获取消息内容
        message = data.get('message', '')
        if not message:
            return jsonify({"error": "消息不能为空"}), 400

        # 获取对话模式和视频ID
        mode = data.get('mode', 'free')  # 默认为自由问答模式
        video_id = data.get('videoId')

        # 创建聊天系统实例
        chat_system = ChatSystem()

        # 创建RAG系统实例（如果需要）
        rag_system = None
        if mode == 'video':
            rag_system = RAGSystem()

        # 如果是视频问答模式，需要加载字幕文件
        if mode == 'video' and video_id:
            try:
                # 获取视频信息，以获取原始文件名
                video = Video.query.get(video_id)
                if not video:
                    current_app.logger.warning(f"未找到视频: {video_id}")

                    # 使用自由问答模式
                    def generate():
                        for chunk in chat_system.chat(message, mode='free'):
                            yield chunk

                    return Response(stream_with_context(generate()), content_type='text/plain')

                # 获取原始文件名（不包含扩展名）
                original_filename = os.path.splitext(os.path.basename(video.filepath))[0] if video.filepath else None

                # 尝试多种可能的字幕文件路径和格式
                subtitle_paths = []

                # 基于视频ID的路径
                subtitle_paths.extend(
                    [
                        os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles', f"{video_id}.txt"),
                        os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles', f"{video_id}.srt"),
                        os.path.join(current_app.config['UPLOAD_FOLDER'], 'captions', f"{video_id}.txt"),
                        os.path.join(current_app.config['UPLOAD_FOLDER'], 'captions', f"{video_id}.srt"),
                    ]
                )

                # 基于原始文件名的路径
                if original_filename:
                    subtitle_paths.extend(
                        [
                            os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles', f"{original_filename}.txt"),
                            os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles', f"{original_filename}.srt"),
                            os.path.join(current_app.config['UPLOAD_FOLDER'], 'captions', f"{original_filename}.txt"),
                            os.path.join(current_app.config['UPLOAD_FOLDER'], 'captions', f"{original_filename}.srt"),
                        ]
                    )

                # 检查字幕文件是否存在
                subtitle_path = None
                for path in subtitle_paths:
                    if os.path.exists(path):
                        subtitle_path = path
                        current_app.logger.info(f"找到字幕文件: {subtitle_path}")
                        break

                if subtitle_path:
                    try:
                        # 创建并初始化RAG系统
                        rag_system.create_knowledge_base(subtitle_path)

                        # 使用RAG系统进行问答
                        def generate():
                            for chunk in chat_system.chat(message, mode='video', rag_system=rag_system):
                                yield chunk

                        return Response(stream_with_context(generate()), content_type='text/plain')
                    except Exception as e:
                        current_app.logger.error(f"加载字幕文件出错: {str(e)}")
                        current_app.logger.error(f"错误详情: {traceback.format_exc()}")

                        # 使用自由问答模式
                        def generate():
                            for chunk in chat_system.chat(message, mode='free'):
                                yield chunk

                        return Response(stream_with_context(generate()), content_type='text/plain')
                else:
                    current_app.logger.warning(f"未找到字幕文件，尝试过的路径: {subtitle_paths}")

                    # 使用自由问答模式
                    def generate():
                        for chunk in chat_system.chat(message, mode='free'):
                            yield chunk

                    return Response(stream_with_context(generate()), content_type='text/plain')
            except Exception as e:
                current_app.logger.error(f"处理视频问答请求出错: {str(e)}")
                current_app.logger.error(f"错误详情: {traceback.format_exc()}")

                # 使用自由问答模式
                def generate():
                    for chunk in chat_system.chat(message, mode='free'):
                        yield chunk

                return Response(stream_with_context(generate()), content_type='text/plain')
        else:
            # 自由问答模式
            def generate():
                for chunk in chat_system.chat(message, mode='free'):
                    yield chunk

            return Response(stream_with_context(generate()), content_type='text/plain')

    except Exception as e:
        current_app.logger.error(f"处理聊天请求出错: {str(e)}")
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({"error": f"处理请求时出错: {str(e)}"}), 500


@chat_bp.route('/history', methods=['GET'])
def get_history():
    """获取聊天历史记录"""
    try:
        # 获取请求参数
        mode = request.args.get('mode', 'free')  # 默认为自由问答模式

        # 获取对应模式的历史记录
        history = chat_system.get_history(mode=mode)

        # 返回历史记录
        return jsonify({"history": history})
    except Exception as e:
        current_app.logger.error(f"获取历史记录出错: {str(e)}")
        return jsonify({"error": f"获取历史记录出错: {str(e)}"}), 500


@chat_bp.route('/clear', methods=['POST'])
def clear_history():
    """清空聊天历史记录"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "无效的请求数据"}), 400

        # 获取对话模式
        mode = data.get('mode', 'all')  # 默认清空所有历史记录

        # 清空历史记录
        if mode == 'all':
            chat_system.clear_all_history()
        else:
            chat_system.clear_history(mode=mode)

        return jsonify({"message": "历史记录已清空"})
    except Exception as e:
        current_app.logger.error(f"清空历史记录出错: {str(e)}")
        return jsonify({"error": f"清空历史记录出错: {str(e)}"}), 500
