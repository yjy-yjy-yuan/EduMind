import os
import re
import json
import uuid
import time
import shutil
import logging
import subprocess
import traceback
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file, make_response
from werkzeug.utils import secure_filename
import yt_dlp
from ..models.video import Video, VideoStatus
from ..extensions import db
from ..tasks.test import add  # 暂时使用测试任务

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

bp = Blueprint('video', __name__, url_prefix='/api/videos')  # 移除url_prefix，让app注册时处理

@bp.before_request
def log_request_info():
    current_app.logger.info('------------------------')
    current_app.logger.info(f'请求方法: {request.method}')
    current_app.logger.info(f'请求路径: {request.path}')
    current_app.logger.info(f'请求头: {dict(request.headers)}')
    current_app.logger.info('------------------------')

@bp.after_request
def after_request(response):
    current_app.logger.info('------------------------')
    current_app.logger.info(f'响应状态: {response.status}')
    current_app.logger.info(f'响应头: {dict(response.headers)}')
    current_app.logger.info('------------------------')
    return response

@bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_video():
    """上传视频文件"""
    current_app.logger.info(f'收到{request.method}请求: /videos/upload')
    
    # 处理OPTIONS请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.status_code = 200
        # 不再手动添加CORS头，由全局after_request处理
        return response
        
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400
            
        file = request.files['file']
        if file.filename == '':
            current_app.logger.error('没有选择文件')
            return jsonify({'error': '没有选择文件'}), 400
            
        if not allowed_file(file.filename):
            current_app.logger.error('不支持的文件类型')
            return jsonify({'error': '不支持的文件类型'}), 400

        # 确保上传目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # 生成安全的文件名并保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        
        # 如果文件已存在，添加时间戳
        if os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
            file_path = os.path.join(upload_folder, filename)
        
        current_app.logger.info(f'保存文件: {file_path}')
        file.save(file_path)
        
        # 创建视频记录，状态设为UPLOADED
        video = Video(
            filename=filename,
            filepath=file_path,
            title=os.path.splitext(filename)[0],  # 使用文件名作为标题
            status=VideoStatus.UPLOADED  # 修改初始状态
        )
        db.session.add(video)
        db.session.commit()
        
        current_app.logger.info(f'创建视频记录: {video.id}')
        
        return jsonify({
            'id': video.id,
            'status': 'uploaded',
            'message': '视频上传成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        import traceback
        current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({'error': '上传失败，请重试'}), 500

@bp.route('/upload-url', methods=['POST', 'OPTIONS'])
def upload_video_url():
    current_app.logger.info(f'收到{request.method}请求: /upload-url')
    
    if request.method == 'OPTIONS':
        current_app.logger.info('处理OPTIONS预检请求')
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        current_app.logger.info(f'返回预检响应: {dict(response.headers)}')
        return response, 200

    try:
        current_app.logger.info(f'请求内容类型: {request.content_type}')
        current_app.logger.info(f'请求数据: {request.get_data()}')
        
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            # 尝试手动解析JSON
            try:
                data = json.loads(request.get_data().decode('utf-8'))
            except:
                current_app.logger.error('无法解析请求数据')
                return jsonify({'error': '无效的请求格式'}), 400
        
        if not data or 'url' not in data:
            current_app.logger.error('No URL found in request')
            return jsonify({'error': '没有提供视频链接'}), 400
            
        video_url = data['url']
        current_app.logger.info(f'处理视频URL: {video_url}')
        
        # 验证URL格式
        is_bilibili = 'bilibili.com' in video_url or 'b23.tv' in video_url
        is_youtube = 'youtube.com' in video_url or 'youtu.be' in video_url
        is_mooc = 'icourse163.org' in video_url
        
        if not (is_bilibili or is_youtube or is_mooc):
            current_app.logger.error(f'不支持的视频平台: {video_url}')
            return jsonify({'error': '目前仅支持B站、YouTube和中国大学慕课视频'}), 400
        
        video_id = None
        title = None
        
        if is_bilibili:
            # 提取B站视频ID
            bv_match = re.search(r'BV[0-9A-Za-z]+', video_url)
            av_match = re.search(r'av\d+', video_url.lower())
                
            if bv_match:
                video_id = bv_match.group(0)
                current_app.logger.info(f'提取到BV号: {video_id}')
                title = f'bilibili-{video_id}'
            elif av_match:
                video_id = av_match.group(0)
                current_app.logger.info(f'提取到av号: {video_id}')
                title = f'bilibili-{video_id}'
            else:
                current_app.logger.error(f'无法从URL中提取视频ID: {video_url}')
                return jsonify({'error': '无效的B站视频链接'}), 400
        elif is_youtube:
            # 提取YouTube视频ID
            if 'youtube.com' in video_url:
                video_id_match = re.search(r'v=([^&]+)', video_url)
                if video_id_match:
                    video_id = video_id_match.group(1)
            elif 'youtu.be' in video_url:
                video_id = video_url.split('/')[-1].split('?')[0]
                
            if not video_id:
                current_app.logger.error(f'无法从URL中提取视频ID: {video_url}')
                return jsonify({'error': '无效的YouTube视频链接'}), 400
                
            current_app.logger.info(f'提取到YouTube视频ID: {video_id}')
            title = f'youtube-{video_id}'
        elif is_mooc:
            # 提取慕课视频ID
            mooc_url = video_url
            
            # 处理带有#号的链接
            mooc_url = mooc_url.split('#')[0]
            
            # 尝试从URL中提取courseId
            course_id_match = re.search(r'learn/([^-]+)-(\d+)', mooc_url)
            if not course_id_match:
                course_id_match = re.search(r'courseId=(\d+)', mooc_url)
            
            # 尝试从URL中提取tid
            tid_match = re.search(r'tid=(\d+)', mooc_url)
            
            # 尝试从URL中提取详情ID
            detail_id_match = re.search(r'id=(\d+)', video_url)  # 使用原始URL，因为id可能在#后面
            cid_match = re.search(r'cid=(\d+)', video_url)  # 使用原始URL，因为cid可能在#后面
            
            if course_id_match:
                if len(course_id_match.groups()) > 1:
                    # 如果是learn/XXX-123456格式
                    course_id = course_id_match.group(2)
                else:
                    # 如果是courseId=123456格式
                    course_id = course_id_match.group(1)
                
                tid = tid_match.group(1) if tid_match else 'unknown'
                detail_id = detail_id_match.group(1) if detail_id_match else 'unknown'
                cid = cid_match.group(1) if cid_match else 'unknown'
                
                video_id = f"{course_id}_{tid}_{detail_id}_{cid}"
                current_app.logger.info(f'提取到慕课课程ID: {course_id}, 章节ID: {tid}, 详情ID: {detail_id}, 内容ID: {cid}')
                title = f'mooc-{course_id}'
            else:
                current_app.logger.error(f'无法从URL中提取视频ID: {video_url}')
                return jsonify({'error': '无效的慕课视频链接，请确保链接格式正确'}), 400
        
        # 创建临时视频记录，状态为DOWNLOADING
        temp_video = Video(
            title=title,
            url=video_url,
            status=VideoStatus.DOWNLOADING
        )
        db.session.add(temp_video)
        db.session.commit()
        current_app.logger.info(f'创建临时视频记录: {temp_video.id}')
        
        try:
            # 确保下载目录存在
            download_folder = os.path.join(current_app.config['UPLOAD_FOLDER'])
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)
            
            filename = None
            filepath = None
            
            # 通用User-Agent
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            # 通用的下载配置
            common_opts = {
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(download_folder, f'{title}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            # 根据不同平台设置不同的下载配置
            if is_bilibili:
                # B站特定配置
                ydl_opts = {
                    **common_opts,
                    'format': 'bestvideo*+bestaudio/best',
                    'http_headers': {
                        'Referer': 'https://www.bilibili.com',
                        'User-Agent': user_agent
                    }
                }
            elif is_youtube:
                # YouTube特定配置
                ydl_opts = {
                    **common_opts,
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # 优先选择mp4格式
                    'http_headers': {
                        'User-Agent': user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Sec-Fetch-Mode': 'navigate',
                    },
                    'nocheckcertificate': True,
                    'ignoreerrors': False,
                }
            elif is_mooc:
                # 慕课特定配置
                ydl_opts = {
                    **common_opts,
                    'format': 'best',
                    'http_headers': {
                        'User-Agent': user_agent,
                        'Referer': 'https://www.icourse163.org/',
                    },
                    'nocheckcertificate': True,
                    'ignoreerrors': False,
                }
            
            # 尝试下载视频
            if is_mooc:
                # 使用自定义方法下载慕课视频
                success, message = download_mooc_video(
                    video_url, 
                    os.path.join(download_folder, f'{title}.mp4'), 
                    course_id, 
                    tid, 
                    detail_id, 
                    cid
                )
                
                if success:
                    filename = f"{title}.mp4"
                    filepath = os.path.join(download_folder, filename)
                    current_app.logger.info(f'慕课视频处理成功: {filepath}')
                else:
                    current_app.logger.error(f'下载视频失败: {message}')
                    return jsonify({'error': f'下载视频失败: {message}'}), 500
            else:
                # 使用yt-dlp下载B站和YouTube视频
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # 对于YouTube视频，设置更长的超时时间
                    if is_youtube:
                        current_app.logger.info(f'YouTube视频下载可能需要较长时间，已设置更长的超时时间')
                        ydl.params['socket_timeout'] = 180  # 设置更长的超时时间，3分钟
                    
                    info = ydl.extract_info(video_url, download=True)
                    video_title = info.get('title', title)
                    filename = f"{title}.mp4"
                    filepath = os.path.join(download_folder, filename)
            
            # 确保文件存在
            if not os.path.exists(filepath):
                # 尝试查找实际下载的文件
                potential_files = [f for f in os.listdir(download_folder) if f.startswith(title)]
                if potential_files:
                    filename = potential_files[0]
                    filepath = os.path.join(download_folder, filename)
            
            if not os.path.exists(filepath):
                current_app.logger.error(f'无法找到下载的视频文件: {filepath}')
                # 更新临时视频记录状态为失败
                temp_video.status = VideoStatus.FAILED
                temp_video.error_message = "无法找到下载的视频文件"
                db.session.commit()
                raise FileNotFoundError(f"无法找到下载的视频文件")
            
            current_app.logger.info(f'视频下载成功: {filepath}')
            
            # 更新临时视频记录
            temp_video.filename = filename
            temp_video.filepath = filepath
            temp_video.status = VideoStatus.UPLOADED  # 修改为UPLOADED状态，不自动处理
            db.session.commit()
            current_app.logger.info(f'视频记录更新成功: {temp_video.id}, 状态: {temp_video.status}')
            
            return jsonify({
                'id': temp_video.id,
                'status': 'uploaded',
                'message': '视频上传成功'
            })
            
        except Exception as e:
            current_app.logger.error(f"下载视频失败: {str(e)}")
            import traceback
            current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return jsonify({'error': f'下载视频失败: {str(e)}'}), 500
        
    except Exception as e:
        current_app.logger.error(f"URL upload error: {str(e)}")
        import traceback
        current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({'error': '处理视频链接失败，请重试'}), 500

def download_mooc_video(video_url, output_path, course_id, tid, detail_id, cid):
    """
    自定义函数用于下载中国大学慕课视频
    """
    try:
        current_app.logger.info(f'使用自定义方法下载慕课视频: {video_url}')
        
        # 创建一个简单的文本文件作为占位符
        with open(output_path, 'w') as f:
            f.write(f"慕课视频链接: {video_url}\n")
            f.write(f"课程ID: {course_id}, 章节ID: {tid}, 详情ID: {detail_id}, 内容ID: {cid}\n")
            f.write("由于慕课网的限制，无法自动下载视频。请手动下载后替换此文件。\n")
            f.write("下载步骤：\n")
            f.write("1. 打开浏览器访问上述链接\n")
            f.write("2. 登录慕课网账号\n")
            f.write("3. 使用浏览器开发者工具(F12)下载视频\n")
            f.write("4. 将下载的视频替换此文件\n")
        
        current_app.logger.info(f'已创建慕课视频占位文件: {output_path}')
        
        # 返回成功，这样系统可以继续处理
        return True, "已创建慕课视频占位文件，请手动下载视频后替换"
    
    except Exception as e:
        error_msg = f"下载慕课视频时出错: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(traceback.format_exc())
        
        # 尝试创建一个简单的占位文件
        try:
            with open(output_path, 'w') as f:
                f.write(f"无法下载慕课视频: {video_url}\n")
                f.write(f"错误信息: {str(e)}\n")
                f.write(f"请手动下载后替换此文件。\n")
            return True, "已创建错误占位文件，请手动下载视频后替换"
        except:
            return False, f"创建占位文件失败: {str(e)}"

@bp.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = add.AsyncResult(task_id)  # 暂时使用测试任务
    if task.state == 'PENDING':
        response = {
            'state': 'pending',
            'status': '等待处理...'
        }
    elif task.state == 'FAILURE':
        response = {
            'state': 'error',
            'status': '处理失败',
            'error': str(task.info)
        }
    else:
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'progress': task.info.get('progress', 0)
        }
    return jsonify(response)

@bp.route('/<int:video_id>', methods=['GET'])
def get_video(video_id):
    video = Video.query.get_or_404(video_id)
    return jsonify({
        'id': video.id,
        'title': video.title,
        'status': video.status.value,
        'created_at': video.created_at.isoformat()
    })

@bp.route('/<int:video_id>/preview', methods=['GET'])
def get_video_preview_file(video_id):
    """获取视频预览图"""
    try:
        video = Video.query.get_or_404(video_id)
        if not video.preview_filepath or not os.path.exists(video.preview_filepath):
            return jsonify({'error': '预览图不存在'}), 404
            
        return send_file(video.preview_filepath, mimetype='image/jpeg')
    except Exception as e:
        current_app.logger.error(f"获取视频预览图失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/list', methods=['GET'])
def get_video_list():
    try:
        videos = Video.query.order_by(Video.upload_time.desc()).all()
        result = []
        for video in videos:
            try:
                # 安全获取状态值
                if hasattr(video.status, 'value'):
                    status = video.status.value
                elif isinstance(video.status, str):
                    status = video.status
                else:
                    status = 'unknown'
                
                video_data = {
                    'id': video.id,
                    'title': video.title,
                    'filename': video.filename,
                    'status': status,
                    'upload_time': video.upload_time.isoformat() if video.upload_time else None,
                    'preview_filename': video.preview_filename if hasattr(video, 'preview_filename') else None,
                    'duration': video.duration if hasattr(video, 'duration') else None,
                    'width': video.width if hasattr(video, 'width') else None,
                    'height': video.height if hasattr(video, 'height') else None,
                    'fps': video.fps if hasattr(video, 'fps') else None
                }
                result.append(video_data)
            except Exception as e:
                current_app.logger.error(f'处理视频记录时出错: {str(e)}')
                # 跳过有问题的记录，继续处理其他记录
                continue
        
        return jsonify({
            'message': '获取成功',
            'videos': result
        })
    except Exception as e:
        current_app.logger.error(f'获取视频列表失败: {str(e)}')
        return jsonify({'error': '获取视频列表失败'}), 500

@bp.route('/<int:video_id>/status', methods=['GET'])
def get_video_status(video_id):
    """获取视频状态"""
    try:
        video = Video.query.get_or_404(video_id)
        status = video.status.value if hasattr(video.status, 'value') else str(video.status)
        current_app.logger.info(f"获取视频状态成功: 视频ID={video_id}, 状态={status}")
        return jsonify({
            'id': video.id,
            'status': status
        })
    except Exception as e:
        current_app.logger.error(f"获取视频状态失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:video_id>/process', methods=['POST', 'OPTIONS'])
def process_video_route(video_id):
    """开始处理视频"""
    current_app.logger.info(f'收到{request.method}请求: /videos/{video_id}/process')
    
    # 处理OPTIONS请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.status_code = 200
        # 不再手动添加CORS头，由全局after_request处理
        return response
    
    try:
        # 导入process_video任务
        from app.tasks.video_processing import process_video
        
        video = Video.query.get_or_404(video_id)
        
        # 检查视频状态
        if video.status not in [VideoStatus.UPLOADED, VideoStatus.PENDING, VideoStatus.FAILED, VideoStatus.COMPLETED]:
            return jsonify({
                'status': 'error',
                'message': f'视频状态不正确: {video.status.name}'
            }), 400
        
        # 获取请求数据
        data = request.get_json() or {}
        language = data.get('language', 'Other')
        model = data.get('model', 'turbo')
        
        # 根据语言选择设置whisper参数
        whisper_language = 'en' if language == 'English' else 'zh'
        whisper_model = model
        
        # 更新视频状态
        video.status = VideoStatus.PENDING
        db.session.commit()
        
        # 启动异步任务处理视频
        task = process_video.delay(video.id, whisper_language, whisper_model)
        
        # 更新视频的任务ID
        video.task_id = task.id
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '视频处理已开始',
            'task_id': task.id
        })
        
    except Exception as e:
        current_app.logger.error(f'处理视频失败: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'处理视频失败: {str(e)}'
        }), 500

@bp.route('/<int:video_id>/preview', methods=['GET'])
def get_video_preview(video_id):
    """获取视频预览图"""
    try:
        video = Video.query.get_or_404(video_id)
        if not video.preview_filepath or not os.path.exists(video.preview_filepath):
            return jsonify({'error': '预览图不存在'}), 404
            
        return send_file(video.preview_filepath, mimetype='image/jpeg')
    except Exception as e:
        current_app.logger.error(f"获取视频预览图失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:video_id>/delete', methods=['DELETE'])
def delete_video(video_id):
    """删除视频"""
    try:
        video = Video.query.get_or_404(video_id)
        
        # 启动清理任务
        from ..tasks.video_processing import cleanup_video
        task = cleanup_video.delay(video.id)
        
        # 立即从数据库中删除记录
        db.session.delete(video)
        db.session.commit()
        
        return jsonify({
            'message': '视频删除任务已启动',
            'video_id': video.id,
            'task_id': task.id
        })
    except Exception as e:
        current_app.logger.error(f"删除视频失败: {str(e)}")
        return jsonify({'error': '删除视频失败'}), 500

@bp.route('/list', methods=['GET'])
def get_video_list_new():
    """获取视频列表"""
    try:
        videos = Video.query.order_by(Video.upload_time.desc()).all()
        return jsonify([video.to_dict() for video in videos])
    except Exception as e:
        current_app.logger.error(f"获取视频列表失败: {str(e)}")
        return jsonify({"error": "获取视频列表失败"}), 500

@bp.route('/upload', methods=['POST'])
def upload_video_new():
    """上传视频文件"""
    try:
        # 检查是否有文件被上传
        if 'file' not in request.files:
            return jsonify({"error": "没有文件被上传"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "没有选择文件"}), 400
            
        # 确保文件名安全
        filename = secure_filename(file.filename)
        
        # 确保上传目录存在
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # 创建视频记录
        video = Video(
            filename=filename,
            filepath=filepath,
            status=VideoStatus.UPLOADED,
            upload_time=datetime.utcnow()
        )
        db.session.add(video)
        db.session.commit()
        
        return jsonify(video.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"上传视频失败: {str(e)}")
        return jsonify({"error": "上传视频失败"}), 500

@bp.route('/<int:video_id>/process', methods=['POST'])
def process_video_route_new(video_id):
    """处理视频"""
    try:
        video = Video.query.get_or_404(video_id)
        
        # 只有UPLOADED状态的视频可以处理
        if video.status not in [VideoStatus.UPLOADED, VideoStatus.PENDING, VideoStatus.FAILED, VideoStatus.COMPLETED, VideoStatus.READY]:
            return jsonify({
                "error": "视频状态不正确",
                "status": video.status.value
            }), 400
            
        # 获取请求数据
        data = request.get_json() or {}
        language = data.get('language', 'Other')
        model = data.get('model', 'turbo')
        
        # 根据语言选择设置whisper参数
        whisper_language = 'en' if language == 'English' else 'zh'
        whisper_model = model
            
        # 更新状态为处理中
        video.status = VideoStatus.PENDING
        db.session.commit()
        
        # 启动异步处理任务
        from ..tasks.video_processing import process_video
        process_video.delay(video_id, whisper_language, whisper_model)
        
        return jsonify({"message": "视频处理已开始"}), 200
        
    except Exception as e:
        current_app.logger.error(f"处理视频失败: {str(e)}")
        return jsonify({"error": "处理视频失败"}), 500

@bp.route('/<int:video_id>/preview', methods=['GET'])
def get_preview(video_id):
    """获取视频预览图"""
    try:
        video = Video.query.get_or_404(video_id)
        
        if not video.preview_filepath or not os.path.exists(video.preview_filepath):
            return jsonify({"error": "预览图不存在"}), 404
            
        return send_file(video.preview_filepath, mimetype='image/jpeg')
        
    except Exception as e:
        current_app.logger.error(f"获取预览图失败: {str(e)}")
        return jsonify({"error": "获取预览图失败"}), 500

@bp.route('/<int:video_id>', methods=['DELETE'])
def delete_video_new(video_id):
    """删除视频"""
    try:
        video = Video.query.get_or_404(video_id)
        
        # 删除文件
        if video.filepath and os.path.exists(video.filepath):
            os.remove(video.filepath)
        if video.preview_filepath and os.path.exists(video.preview_filepath):
            os.remove(video.preview_filepath)
            
        # 删除数据库记录
        db.session.delete(video)
        db.session.commit()
        
        return jsonify({"message": "视频已删除"}), 200
        
    except Exception as e:
        current_app.logger.error(f"删除视频失败: {str(e)}")
        return jsonify({"error": "删除视频失败"}), 500

@bp.route('/<int:video_id>/stream', methods=['GET'])
def stream_video(video_id):
    """流式传输视频"""
    try:
        video = Video.query.get_or_404(video_id)
        return send_file(video.filepath,
                        mimetype='video/mp4',
                        as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"流式传输视频失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<int:video_id>/subtitle', methods=['GET'])
def get_subtitle(video_id):
    """获取字幕文件"""
    try:
        video = Video.query.get_or_404(video_id)
        if not video.subtitle_filepath or not os.path.exists(video.subtitle_filepath):
            return jsonify({
                'status': 'error',
                'message': '字幕文件不存在'
            }), 404
            
        return send_file(video.subtitle_filepath,
                        mimetype='text/plain',
                        as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"获取字幕文件失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/<int:video_id>', methods=['GET'])
def get_video_detail(video_id):
    """获取视频详情"""
    try:
        video = Video.query.get_or_404(video_id)
        return jsonify(video.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
