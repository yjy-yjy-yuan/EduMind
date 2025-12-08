import io
import json
import logging
import os

import redis
from celery.exceptions import OperationalError
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from flask import send_file

from .. import celery
from .. import db
from ..models import Subtitle
from ..models import Video
from ..tasks.subtitle_tasks import generate_subtitles
from ..utils.semantic_utils import merge_subtitles_by_semantics_ollama
from ..utils.subtitle_utils import convert_to_srt
from ..utils.subtitle_utils import convert_to_txt
from ..utils.subtitle_utils import convert_to_vtt
from ..utils.subtitle_utils import merge_subtitles
from ..utils.subtitle_utils import validate_subtitle_time

subtitle_bp = Blueprint('subtitle', __name__)


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


# 处理字幕的语义合并和标题生成
@subtitle_bp.route('/videos/<int:video_id>/subtitles/semantic-merged', methods=['GET'])
def get_merged_subtitles(video_id):
    """获取语义合并后的字幕"""
    try:
        # 检查是否需要强制刷新
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        # 检查是否请求下载特定格式
        format_type = request.args.get('format')

        # 获取视频信息
        video = Video.query.get_or_404(video_id)

        # 检查字幕文件是否存在
        if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
            return jsonify({"error": "字幕文件不存在"}), 404

        # 构建缓存文件路径
        cache_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cache')
        os.makedirs(cache_dir, exist_ok=True)

        # 使用视频文件名作为缓存文件名，保持与其他字幕格式一致
        video_name = video.filename.rsplit('.', 1)[0] if video.filename else f'video_{video_id}'
        cache_file = os.path.join(cache_dir, f'{video_name}_semantic.json')

        # 获取合并字幕（从缓存或重新生成）
        merged_subtitles = None

        # 如果缓存文件存在且不需要强制刷新，直接返回缓存结果
        if os.path.exists(cache_file) and not force_refresh:
            current_app.logger.info(f"使用缓存的语义合并字幕: {cache_file}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    merged_subtitles = json.load(f)
            except Exception as e:
                current_app.logger.error(f"读取缓存文件时出错: {str(e)}")
                # 如果读取缓存失败，继续执行后续代码重新生成

        # 如果没有从缓存获取到合并字幕，则重新生成
        if merged_subtitles is None:
            # 读取字幕文件
            try:
                with open(video.subtitle_filepath, 'r', encoding='utf-8') as f:
                    subtitle_content = f.read()
            except Exception as e:
                current_app.logger.error(f"读取字幕文件时出错: {str(e)}")
                return jsonify({"error": f"读取字幕文件时出错: {str(e)}"}), 500

            # 解析.srt文件内容
            subtitle_blocks = subtitle_content.strip().split('\n\n')
            current_app.logger.info(f"分割出的字幕块数量: {len(subtitle_blocks)}")

            subtitles = []
            for block in subtitle_blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:  # 确保至少有索引、时间和文本
                    # 解析时间行
                    time_line = lines[1]
                    if '-->' in time_line:
                        start_time_str, end_time_str = time_line.split('-->')

                        # 转换时间格式为秒
                        start_time_parts = start_time_str.strip().split(':')
                        if len(start_time_parts) == 2:  # MM:SS 格式
                            start_minutes = int(start_time_parts[0])
                            start_seconds = float(start_time_parts[1].replace(',', '.'))
                            start_time = start_minutes * 60 + start_seconds
                        else:  # HH:MM:SS 格式
                            start_hours = int(start_time_parts[0])
                            start_minutes = int(start_time_parts[1])
                            start_seconds = float(start_time_parts[2].replace(',', '.'))
                            start_time = start_hours * 3600 + start_minutes * 60 + start_seconds

                        end_time_parts = end_time_str.strip().split(':')
                        if len(end_time_parts) == 2:  # MM:SS 格式
                            end_minutes = int(end_time_parts[0])
                            end_seconds = float(end_time_parts[1].replace(',', '.'))
                            end_time = end_minutes * 60 + end_seconds
                        else:  # HH:MM:SS 格式
                            end_hours = int(end_time_parts[0])
                            end_minutes = int(end_time_parts[1])
                            end_seconds = float(end_time_parts[2].replace(',', '.'))
                            end_time = end_hours * 3600 + end_minutes * 60 + end_seconds

                        # 获取文本（可能有多行）
                        text = '\n'.join(lines[2:])

                        subtitles.append({'start_time': start_time, 'end_time': end_time, 'text': text})

            current_app.logger.info(f"从文件中解析出{len(subtitles)}条字幕")

            if not subtitles:
                current_app.logger.warning("没有解析出有效的字幕")
                return jsonify([]), 200

            # 调用基于Ollama的语义合并和标题生成函数
            merged_subtitles = merge_subtitles_by_semantics_ollama(subtitles)

            current_app.logger.info(f"合并后的字幕数量: {len(merged_subtitles)}")

            # 将结果保存到缓存文件
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(merged_subtitles, f, ensure_ascii=False, indent=2)
                current_app.logger.info(f"语义合并字幕已缓存到: {cache_file}")
            except Exception as e:
                current_app.logger.error(f"保存缓存文件时出错: {str(e)}")
                # 保存缓存失败不影响返回结果

        # 如果请求下载特定格式，则转换并返回
        if format_type:
            if not merged_subtitles or len(merged_subtitles) == 0:
                return jsonify({"error": "没有可用的合并字幕"}), 404

            # 根据请求的格式转换字幕
            if format_type == 'srt':
                content = convert_merged_to_srt(merged_subtitles)
                mimetype = 'text/plain'
            elif format_type == 'vtt':
                content = convert_merged_to_vtt(merged_subtitles)
                mimetype = 'text/vtt'
            elif format_type == 'txt':
                content = convert_merged_to_txt(merged_subtitles)
                mimetype = 'text/plain'
            else:
                return jsonify({"error": f"不支持的格式: {format_type}"}), 400

            # 创建一个内存文件对象
            mem_file = io.BytesIO()
            mem_file.write(content.encode('utf-8'))
            mem_file.seek(0)

            # 获取视频标题用于文件名
            video_title = video.title or f"video_{video_id}"
            filename = f"merged-{video_title}.{format_type}"

            return send_file(mem_file, mimetype=mimetype, as_attachment=True, download_name=filename)

        # 返回合并后的字幕
        return jsonify(merged_subtitles), 200
    except Exception as e:
        current_app.logger.error(f"合并字幕时出错: {str(e)}")
        import traceback

        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "处理字幕时发生错误"}), 500


# 将合并字幕转换为SRT格式
def convert_merged_to_srt(merged_subtitles):
    srt_content = ""
    for i, subtitle in enumerate(merged_subtitles):
        start_time = format_seconds_to_srt_time(subtitle['start_time'])
        end_time = format_seconds_to_srt_time(subtitle['end_time'])
        srt_content += f"{i+1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return srt_content


# 将合并字幕转换为VTT格式
def convert_merged_to_vtt(merged_subtitles):
    vtt_content = "WEBVTT\n\n"
    for i, subtitle in enumerate(merged_subtitles):
        start_time = format_seconds_to_vtt_time(subtitle['start_time'])
        end_time = format_seconds_to_vtt_time(subtitle['end_time'])
        vtt_content += f"{i+1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return vtt_content


# 将合并字幕转换为TXT格式
def convert_merged_to_txt(merged_subtitles):
    txt_content = ""
    for subtitle in merged_subtitles:
        start_time = format_seconds_to_display_time(subtitle['start_time'])
        end_time = format_seconds_to_display_time(subtitle['end_time'])
        title = subtitle.get('title', '无标题')
        txt_content += f"[{start_time} - {end_time}] {title}\n{subtitle['text']}\n\n"
    return txt_content


# 时间格式转换函数
def format_seconds_to_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def format_seconds_to_vtt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def format_seconds_to_display_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


@subtitle_bp.route('/videos/<int:video_id>/subtitles/generate', methods=['POST'])
def generate_video_subtitles(video_id):
    try:
        # 检查Redis连接
        if not check_redis_connection():
            return jsonify({'status': 'error', 'message': 'Redis服务未运行或连接失败，请确保Redis服务器已启动'}), 500

        # 检查Celery连接
        if not check_celery_connection():
            return jsonify({'status': 'error', 'message': 'Celery服务未正确运行，请确保Celery worker已启动'}), 500

        video = Video.query.get(video_id)
        if not video:
            return jsonify({'status': 'error', 'message': f'未找到ID为{video_id}的视频'}), 404

        data = request.get_json() or {}
        language = data.get('language', 'zh')  # 默认使用中文
        model_name = data.get('whisper_model', 'base')  # 默认使用base模型

        # 启动字幕生成任务
        try:
            # 确保参数顺序正确：video_id, language, model_name
            task = generate_subtitles.delay(video_id=video_id, language=language, model_name=model_name)
            return jsonify({'status': 'success', 'message': '字幕生成任务已启动', 'task_id': task.id})
        except Exception as e:
            logging.error(f"启动字幕生成任务时发生错误: {str(e)}")
            return jsonify({'status': 'error', 'message': f'启动字幕生成任务失败: {str(e)}'}), 500

    except OperationalError as e:
        logging.error(f"Celery操作错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Celery任务队列错误: {str(e)}'}), 500
    except Exception as e:
        logging.error(f"处理字幕生成请求时发生未知错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'服务器内部错误: {str(e)}'}), 500


@subtitle_bp.route('/videos/<int:video_id>/subtitles', methods=['GET'])
def get_video_subtitles(video_id):
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'status': 'error', 'message': f'未找到ID为{video_id}的视频'}), 404

        # 获取视频的所有字幕
        subtitles = Subtitle.query.filter_by(video_id=video_id).all()

        # 将字幕数据转换为JSON格式
        subtitle_list = [
            {
                'id': subtitle.id,
                'start_time': subtitle.start_time,
                'end_time': subtitle.end_time,
                'text': subtitle.text,
                'language': subtitle.language,
            }
            for subtitle in subtitles
        ]

        return jsonify(
            {'status': 'success', 'video_id': video_id, 'video_status': video.status, 'subtitles': subtitle_list}
        )

    except Exception as e:
        logging.error(f"获取字幕时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取字幕失败: {str(e)}'}), 500


@subtitle_bp.route('/videos/<int:video_id>/subtitles/export', methods=['GET'])
def export_subtitles(video_id):
    """导出字幕文件"""
    try:
        format_type = request.args.get('format', 'srt')  # 默认为srt格式
        if format_type not in ['srt', 'vtt', 'txt']:
            return jsonify({'status': 'error', 'message': '不支持的字幕格式'}), 400

        # 获取视频的所有字幕
        subtitles = Subtitle.query.filter_by(video_id=video_id).order_by(Subtitle.start_time).all()
        if not subtitles:
            return jsonify({'status': 'error', 'message': '未找到字幕数据'}), 404

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

        # 返回文件，使用safe_filename处理中文文件名
        safe_filename = filename.encode('utf-8').decode('latin-1')
        response = send_file(file_path, mimetype=mime_type, as_attachment=True, download_name=safe_filename)

        # 添加必要的响应头
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'

        return response

    except Exception as e:
        logging.error(f"导出字幕时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'导出字幕失败: {str(e)}'}), 500


@subtitle_bp.route('/videos/<int:video_id>/subtitles/<int:subtitle_id>', methods=['PUT'])
def update_subtitle(video_id, subtitle_id):
    """更新字幕内容"""
    try:
        subtitle = Subtitle.query.filter_by(id=subtitle_id, video_id=video_id).first()
        if not subtitle:
            return jsonify({'status': 'error', 'message': '未找到指定字幕'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '未提供更新数据'}), 400

        # 更新文本
        if 'text' in data:
            subtitle.update_text(data['text'], editor=data.get('editor'))

        # 更新时间戳
        if 'start_time' in data or 'end_time' in data:
            start_time = data.get('start_time', subtitle.start_time)
            end_time = data.get('end_time', subtitle.end_time)

            # 验证时间戳
            video = Video.query.get(video_id)
            is_valid, error_msg = validate_subtitle_time(start_time, end_time, video.duration if video else None)

            if not is_valid:
                return jsonify({'status': 'error', 'message': error_msg}), 400

            subtitle.start_time = start_time
            subtitle.end_time = end_time

        db.session.commit()

        return jsonify({'status': 'success', 'message': '字幕更新成功', 'subtitle': subtitle.to_dict()})

    except Exception as e:
        db.session.rollback()
        logging.error(f"更新字幕时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'更新字幕失败: {str(e)}'}), 500


@subtitle_bp.route('/videos/<int:video_id>/subtitles/merge', methods=['POST'])
def merge_subtitle_segments(video_id):
    """合并字幕片段"""
    try:
        subtitles = Subtitle.query.filter_by(video_id=video_id).order_by(Subtitle.start_time).all()
        if not subtitles:
            return jsonify({'status': 'error', 'message': '未找到字幕数据'}), 404

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
                language=sub['language'],
            )
            db.session.add(new_subtitle)

        db.session.commit()

        return jsonify(
            {
                'status': 'success',
                'message': '字幕合并成功',
                'subtitles': [sub.to_dict() for sub in Subtitle.query.filter_by(video_id=video_id).all()],
            }
        )

    except Exception as e:
        db.session.rollback()
        logging.error(f"合并字幕时发生错误: {str(e)}")
        return jsonify({'status': 'error', 'message': f'合并字幕失败: {str(e)}'}), 500


# 触发字幕的语义合并处理
@subtitle_bp.route('/videos/<int:video_id>/subtitles/semantic-merge', methods=['POST'])
def trigger_semantic_merge(video_id):
    """触发字幕的语义合并处理"""
    try:
        # 获取视频信息
        video = Video.query.get_or_404(video_id)

        # 检查字幕文件是否存在
        if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
            return jsonify({"error": "字幕文件不存在"}), 404

        # 读取字幕文件
        try:
            with open(video.subtitle_filepath, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()
        except Exception as e:
            current_app.logger.error(f"读取字幕文件时出错: {str(e)}")
            return jsonify({"error": f"读取字幕文件时出错: {str(e)}"}), 500

        # 解析.srt文件内容
        subtitle_blocks = subtitle_content.strip().split('\n\n')
        current_app.logger.info(f"分割出的字幕块数量: {len(subtitle_blocks)}")

        subtitles = []
        for block in subtitle_blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:  # 确保至少有索引、时间和文本
                # 解析时间行
                time_line = lines[1]
                if '-->' in time_line:
                    start_time_str, end_time_str = time_line.split('-->')

                    # 转换时间格式为秒
                    start_time_parts = start_time_str.strip().split(':')
                    if len(start_time_parts) == 2:  # MM:SS 格式
                        start_minutes = int(start_time_parts[0])
                        start_seconds = float(start_time_parts[1].replace(',', '.'))
                        start_time = start_minutes * 60 + start_seconds
                    else:  # HH:MM:SS 格式
                        start_hours = int(start_time_parts[0])
                        start_minutes = int(start_time_parts[1])
                        start_seconds = float(start_time_parts[2].replace(',', '.'))
                        start_time = start_hours * 3600 + start_minutes * 60 + start_seconds

                    end_time_parts = end_time_str.strip().split(':')
                    if len(end_time_parts) == 2:  # MM:SS 格式
                        end_minutes = int(end_time_parts[0])
                        end_seconds = float(end_time_parts[1].replace(',', '.'))
                        end_time = end_minutes * 60 + end_seconds
                    else:  # HH:MM:SS 格式
                        end_hours = int(end_time_parts[0])
                        end_minutes = int(end_time_parts[1])
                        end_seconds = float(end_time_parts[2].replace(',', '.'))
                        end_time = end_hours * 3600 + end_minutes * 60 + end_seconds

                    # 获取文本（可能有多行）
                    text = '\n'.join(lines[2:])

                    subtitles.append({'start_time': start_time, 'end_time': end_time, 'text': text})

        current_app.logger.info(f"从文件中解析出{len(subtitles)}条字幕")

        if not subtitles:
            current_app.logger.warning("没有解析出有效的字幕")
            return jsonify({"error": "没有解析出有效的字幕"}), 400

        # 构建缓存文件路径
        cache_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cache')
        os.makedirs(cache_dir, exist_ok=True)

        # 使用视频文件名作为缓存文件名，保持与其他字幕格式一致
        video_name = video.filename.rsplit('.', 1)[0] if video.filename else f'video_{video_id}'
        cache_file = os.path.join(cache_dir, f'{video_name}_semantic.json')

        # 如果缓存文件已存在，先删除它
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                current_app.logger.info(f"已删除现有缓存文件: {cache_file}")
            except Exception as e:
                current_app.logger.error(f"删除现有缓存文件时出错: {str(e)}")

        # 调用基于Ollama的语义合并和标题生成函数
        merged_subtitles = merge_subtitles_by_semantics_ollama(subtitles)

        current_app.logger.info(f"合并后的字幕数量: {len(merged_subtitles)}")

        # 将结果保存到缓存文件
        try:
            # 检查合并后的字幕是否为空
            if not merged_subtitles:
                current_app.logger.warning("合并后的字幕为空，不写入空数组")
                # 如果合并后的字幕为空，返回错误
                return jsonify({"error": "合并字幕失败，结果为空"}), 500
            else:
                # 直接覆盖现有缓存文件，不创建备份
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(merged_subtitles, f, ensure_ascii=False, indent=2)
                current_app.logger.info(f"语义合并字幕已缓存到: {cache_file}")
        except Exception as e:
            current_app.logger.error(f"保存缓存文件时出错: {str(e)}")
            # 保存缓存失败不影响返回结果

        return jsonify({"success": True, "message": "语义合并处理完成", "count": len(merged_subtitles)}), 200
    except Exception as e:
        current_app.logger.error(f"语义合并处理时出错: {str(e)}")
        import traceback

        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "语义合并处理时发生错误"}), 500
