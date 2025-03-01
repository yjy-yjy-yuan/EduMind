from flask import Blueprint, jsonify, request, current_app, send_file
from ..models import Video, Subtitle
from ..tasks.subtitle_tasks import generate_subtitles
from .. import db, celery
from celery.exceptions import OperationalError
from ..utils.subtitle_utils import (
    convert_to_srt, convert_to_vtt, convert_to_txt,
    validate_subtitle_time, merge_subtitles
)
import redis
import logging
import io
import os

subtitle_bp = Blueprint('subtitle', __name__, url_prefix='/api')

def check_redis_connection():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except redis.ConnectionError as e:
        logging.error(f"Redis连接错误: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"检查Redis连接时发生未知错误: {str(e)}")
        return False

def check_celery_connection():
    try:
        # 检查Celery是否已正确配置
        if not current_app.extensions.get('celery'):
            logging.error("Celery未在Flask应用中正确配置")
            return False
        
        # 尝试ping Redis broker
        celery.control.ping(timeout=1.0)
        return True
    except Exception as e:
        logging.error(f"Celery连接检查失败: {str(e)}")
        return False

@subtitle_bp.route('/videos/<int:video_id>/subtitles/generate', methods=['POST'])
def generate_video_subtitles(video_id):
    try:
        # 检查Redis连接
        if not check_redis_connection():
            return jsonify({
                'status': 'error',
                'message': 'Redis服务未运行或连接失败，请确保Redis服务器已启动'
            }), 500

        # 检查Celery连接
        if not check_celery_connection():
            return jsonify({
                'status': 'error',
                'message': 'Celery服务未正确运行，请确保Celery worker已启动'
            }), 500

        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{video_id}的视频'
            }), 404

        data = request.get_json() or {}
        language = data.get('language', 'zh')  # 默认使用中文
        model_name = data.get('whisper_model', 'base')  # 默认使用base模型

        # 启动字幕生成任务
        try:
            # 确保参数顺序正确：video_id, language, model_name
            task = generate_subtitles.delay(
                video_id=video_id,
                language=language,
                model_name=model_name
            )
            return jsonify({
                'status': 'success',
                'message': '字幕生成任务已启动',
                'task_id': task.id
            })
        except Exception as e:
            logging.error(f"启动字幕生成任务时发生错误: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'启动字幕生成任务失败: {str(e)}'
            }), 500

    except OperationalError as e:
        logging.error(f"Celery操作错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Celery任务队列错误: {str(e)}'
        }), 500
    except Exception as e:
        logging.error(f"处理字幕生成请求时发生未知错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'服务器内部错误: {str(e)}'
        }), 500

@subtitle_bp.route('/videos/<int:video_id>/subtitles', methods=['GET'])
def get_video_subtitles(video_id):
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{video_id}的视频'
            }), 404

        # 获取视频的所有字幕
        subtitles = Subtitle.query.filter_by(video_id=video_id).all()
        
        # 将字幕数据转换为JSON格式
        subtitle_list = [{
            'id': subtitle.id,
            'start_time': subtitle.start_time,
            'end_time': subtitle.end_time,
            'text': subtitle.text,
            'language': subtitle.language
        } for subtitle in subtitles]

        return jsonify({
            'status': 'success',
            'video_id': video_id,
            'video_status': video.status,
            'subtitles': subtitle_list
        })

    except Exception as e:
        logging.error(f"获取字幕时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取字幕失败: {str(e)}'
        }), 500

@subtitle_bp.route('/videos/<int:video_id>/subtitles/export', methods=['GET'])
def export_subtitles(video_id):
    """导出字幕文件"""
    try:
        format_type = request.args.get('format', 'srt')  # 默认为srt格式
        if format_type not in ['srt', 'vtt', 'txt']:
            return jsonify({
                'status': 'error',
                'message': '不支持的字幕格式'
            }), 400

        # 获取视频的所有字幕
        subtitles = Subtitle.query.filter_by(video_id=video_id).order_by(Subtitle.start_time).all()
        if not subtitles:
            return jsonify({
                'status': 'error',
                'message': '未找到字幕数据'
            }), 404

        # 转换字幕格式
        subtitle_list = [sub.to_dict() for sub in subtitles]
        if format_type == 'srt':
            content = convert_to_srt(subtitle_list)
            mime_type = 'application/x-subrip'
            ext = 'srt'
        elif format_type == 'vtt':
            content = convert_to_vtt(subtitle_list)
            mime_type = 'text/vtt'
            ext = 'vtt'
        else:  # txt
            content = convert_to_txt(subtitle_list)
            mime_type = 'text/plain'
            ext = 'txt'

        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        captions_dir = os.path.join(root_dir, 'captions')
        os.makedirs(captions_dir, exist_ok=True)

        # 创建文件
        video = Video.query.get(video_id)
        filename = f"{video.title}_{video.id}.{ext}"
        file_path = os.path.join(captions_dir, filename)
        
        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 返回文件
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logging.error(f"导出字幕时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'导出字幕失败: {str(e)}'
        }), 500

@subtitle_bp.route('/videos/<int:video_id>/subtitles/<int:subtitle_id>', methods=['PUT'])
def update_subtitle(video_id, subtitle_id):
    """更新字幕内容"""
    try:
        subtitle = Subtitle.query.filter_by(id=subtitle_id, video_id=video_id).first()
        if not subtitle:
            return jsonify({
                'status': 'error',
                'message': '未找到指定字幕'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '未提供更新数据'
            }), 400

        # 更新文本
        if 'text' in data:
            subtitle.update_text(data['text'], editor=data.get('editor'))

        # 更新时间戳
        if 'start_time' in data or 'end_time' in data:
            start_time = data.get('start_time', subtitle.start_time)
            end_time = data.get('end_time', subtitle.end_time)
            
            # 验证时间戳
            video = Video.query.get(video_id)
            is_valid, error_msg = validate_subtitle_time(
                start_time, end_time, video.duration if video else None
            )
            
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), 400
                
            subtitle.start_time = start_time
            subtitle.end_time = end_time

        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '字幕更新成功',
            'subtitle': subtitle.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"更新字幕时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'更新字幕失败: {str(e)}'
        }), 500

@subtitle_bp.route('/videos/<int:video_id>/subtitles/merge', methods=['POST'])
def merge_subtitle_segments(video_id):
    """合并字幕片段"""
    try:
        subtitles = Subtitle.query.filter_by(video_id=video_id).order_by(Subtitle.start_time).all()
        if not subtitles:
            return jsonify({
                'status': 'error',
                'message': '未找到字幕数据'
            }), 404

        # 转换为列表并合并
        subtitle_list = [sub.to_dict() for sub in subtitles]
        merged_subtitles = merge_subtitles(subtitle_list)

        # 更新数据库
        Subtitle.query.filter_by(video_id=video_id).delete()
        for sub in merged_subtitles:
            new_subtitle = Subtitle(
                video_id=video_id,
                start_time=sub['start_time'],
                end_time=sub['end_time'],
                text=sub['text'],
                language=sub['language']
            )
            db.session.add(new_subtitle)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': '字幕合并成功',
            'subtitles': [sub.to_dict() for sub in Subtitle.query.filter_by(video_id=video_id).all()]
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"合并字幕时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'合并字幕失败: {str(e)}'
        }), 500
