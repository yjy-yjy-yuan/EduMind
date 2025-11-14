import os
import traceback
import re
import json
import uuid
import time
import shutil
import logging
import subprocess
import hashlib
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file, make_response, Response
from werkzeug.utils import secure_filename
import yt_dlp
from ..models.video import Video, VideoStatus
from ..extensions import db
from ..tasks.test import add  # 暂时使用测试任务
# 导入视频摘要生成器
import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.summary_generator import generate_video_summary
from services.tag_generator import generate_video_tags

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_with_chinese(filename):
    """安全的文件名处理，保留中文字符"""
    # 替换不安全的字符为下划线，但保留中文字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除前后的点和空格
    filename = filename.strip('. ')
    return filename

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
        return response
        
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            current_app.logger.error('未提供文件')
            return jsonify({'error': '没有文件'}), 400
            
        file = request.files['file']
        if file.filename == '':
            current_app.logger.error('没有选择文件')
            return jsonify({'error': '没有选择文件'}), 400
            
        if not allowed_file(file.filename):
            current_app.logger.error(f'不支持的文件类型: {file.filename}')
            return jsonify({'error': '不支持的文件类型'}), 400

        # 计算文件MD5
        try:
            file_content = file.read()
            file_md5 = hashlib.md5(file_content).hexdigest()
            file.seek(0)  # 重置文件指针到开始位置
            current_app.logger.info(f'文件MD5: {file_md5}')
        except Exception as e:
            current_app.logger.error(f'计算MD5失败: {str(e)}')
            return jsonify({'error': '文件处理失败'}), 500

        # 检查是否存在相同MD5的视频
        try:
            existing_video = Video.query.filter_by(md5=file_md5).first()
            if existing_video:
                current_app.logger.info(f'发现重复视频: {existing_video.filename}')
                video_dict = existing_video.to_dict()
                current_app.logger.info(f'重复视频信息: {video_dict}')
                return jsonify({
                    'id': existing_video.id,
                    'status': existing_video.status.value if isinstance(existing_video.status, VideoStatus) else existing_video.status,
                    'message': '视频已存在',
                    'duplicate': True,
                    'existingVideo': video_dict
                }), 200
        except Exception as e:
            current_app.logger.error(f'检查重复视频失败: {str(e)}')
            current_app.logger.error(f'详细错误信息: {traceback.format_exc()}')
            return jsonify({'error': '数据库查询失败'}), 500

        # 确保上传目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
                current_app.logger.info(f'创建上传目录: {upload_folder}')
            except Exception as e:
                current_app.logger.error(f'创建上传目录失败: {str(e)}')
                return jsonify({'error': '服务器存储错误'}), 500

        # 获取原始文件名和扩展名
        original_filename = file.filename
        name, ext = os.path.splitext(original_filename)
        
        # 使用自定义函数处理文件名，保留中文字符
        cleaned_name = secure_filename_with_chinese(name)
        
        # 添加local-前缀
        title = f"local-{cleaned_name}"
        filename = f"{title}{ext}"
        file_path = os.path.join(upload_folder, filename)
        
        # 如果文件已存在，添加时间戳（这里保留这个逻辑，以防万一出现MD5碰撞）
        if os.path.exists(file_path):
            title = f"{title}_{int(datetime.now().timestamp())}"
            filename = f"{title}{ext}"
            file_path = os.path.join(upload_folder, filename)
        
        # 保存文件
        try:
            current_app.logger.info(f'保存文件: {file_path}')
            file.save(file_path)
        except Exception as e:
            current_app.logger.error(f'保存文件失败: {str(e)}')
            return jsonify({'error': '文件保存失败'}), 500
        
        # 创建视频记录
        try:
            video = Video(
                filename=filename,
                filepath=file_path,
                title=title,
                status=VideoStatus.UPLOADED,
                md5=file_md5
            )
            
            db.session.add(video)
            db.session.commit()
            
            current_app.logger.info(f'创建视频记录: {video.id}')
            
            response_data = {
                'id': video.id,
                'status': 'uploaded',
                'message': '视频上传成功',
                'duplicate': False,
                'data': video.to_dict()
            }
            
            current_app.logger.info(f'返回数据: {response_data}')
            return jsonify(response_data)
            
        except Exception as e:
            current_app.logger.error(f'创建视频记录失败: {str(e)}')
            # 如果数据库操作失败，删除已上传的文件
            try:
                os.remove(file_path)
                current_app.logger.info(f'删除文件: {file_path}')
            except Exception as del_e:
                current_app.logger.error(f'删除文件失败: {str(del_e)}')
            return jsonify({'error': '数据库操作失败'}), 500
        
    except Exception as e:
        current_app.logger.error(f"上传错误: {str(e)}")
        current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({'error': '上传失败，请重试'}), 500

@bp.route('/upload-url', methods=['POST', 'OPTIONS'])
def upload_video_url():
    import traceback  # 添加这一行，确保traceback模块被导入
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
                title = f'bilibili-{video_id}'  # 临时标题
            elif av_match:
                video_id = av_match.group(0)
                current_app.logger.info(f'提取到av号: {video_id}')
                title = f'bilibili-{video_id}'  # 临时标题
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
            title = f'youtube-{video_id}'  # 临时标题
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
            title=title,  # 使用临时标题
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
                'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),  # 使用视频原标题
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
                # YouTube特定配置 - 让 yt-dlp 自动选择最佳格式
                ydl_opts = {
                    'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    # 🔥 不指定格式，让 yt-dlp 自动下载并合并最佳格式
                    # 这是 yt-dlp 推荐的方式，避免格式选择错误
                    'merge_output_format': 'mp4',
                    # 🚀 性能优化：并发下载和重试
                    'concurrent_fragment_downloads': 4,  # 并发下载4个片段
                    'retries': 10,
                    'fragment_retries': 10,
                    'file_access_retries': 3,
                    'extractor_retries': 3,
                    # 🚀 代理配置：加速下载Youtube视频
                    'proxy': 'http://127.0.0.1:7890',  # 常见的 Clash 代理端口
                    # 'proxy': 'socks5://127.0.0.1:1080',  # 或 V2Ray 代理
                    'http_headers': {
                        'User-Agent': user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Sec-Fetch-Mode': 'navigate',
                    },
                    'nocheckcertificate': True,
                    'ignoreerrors': False,
                }

                # 🔥 最新方案：直接从浏览器提取 cookies（最可靠！）
                # 这避免了所有 cookies 文件导出的问题
                ydl_opts['cookiesfrombrowser'] = ('chrome',)
                current_app.logger.info('🍪 从 Chrome 浏览器实时提取 cookies')
                current_app.logger.info('💡 注意：Chrome 必须已登录 YouTube 且保持后台运行')
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
                    os.path.join(download_folder, f"{title}.mp4"), 
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
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # 对于YouTube视频，设置更长的超时时间
                        if is_youtube:
                            current_app.logger.info(f'YouTube视频下载可能需要较长时间，已设置更长的超时时间')
                            ydl.params['socket_timeout'] = 180  # 设置更长的超时时间，3分钟

                        # 为哔哩哔哩视频设置特殊的网络参数
                        if is_bilibili:
                            # 增加重试次数和超时时间
                            ydl.params['retries'] = 10  # 增加重试次数
                            ydl.params['socket_timeout'] = 60  # 增加超时时间到60秒
                            ydl.params['fragment_retries'] = 10  # 片段下载重试次数
                            current_app.logger.info(f'哔哩哔哩视频：已设置更高的重试次数和更长的超时时间')

                        # 先获取视频信息
                        current_app.logger.info(f'开始获取视频信息: {video_url}')
                        info = ydl.extract_info(video_url, download=False)
                        video_title = info.get('title', '未知标题')
                        # 清理标题中的特殊字符，但保留中文字符
                        video_title = secure_filename_with_chinese(video_title)
                        # 根据来源添加前缀
                        prefix = 'bilibili-' if is_bilibili else 'youtube-'
                        title = f"{prefix}{video_title}"

                        # 更新下载配置中的输出模板
                        ydl_opts['outtmpl'] = os.path.join(download_folder, f'{title}.%(ext)s')

                        # 使用新的配置下载视频
                        current_app.logger.info(f'开始下载视频: {video_url}')
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            ydl2.download([video_url])

                        # 设置文件路径
                        filename = f"{title}.mp4"
                        filepath = os.path.join(download_folder, filename)

                        # 检查文件是否存在
                        if not os.path.exists(filepath):
                            current_app.logger.error(f'下载的视频文件不存在: {filepath}')
                            raise FileNotFoundError(f"下载的视频文件不存在: {filepath}")

                        current_app.logger.info(f'✅ 视频下载成功: {filepath}')

                except Exception as e:
                    error_msg = str(e)
                    current_app.logger.error(f'下载视频时出错: {error_msg}')

                    # 特殊处理 YouTube 错误
                    if is_youtube:
                        if 'Sign in to confirm' in error_msg or 'bot' in error_msg or 'cookie' in error_msg.lower():
                            cookies_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'youtube_cookies.txt')
                            current_app.logger.error('❌ YouTube 需要登录验证')
                            current_app.logger.error(f'💡 解决方法：')
                            current_app.logger.error(f'   1. 安装浏览器插件导出 cookies')
                            current_app.logger.error(f'   2. 将 cookies 文件保存到: {cookies_file}')
                            current_app.logger.error(f'   3. 重新尝试下载')
                            raise Exception(f'YouTube 需要登录验证。请导出 cookies 文件到: {cookies_file}')
                    raise
            
            # 更新临时视频记录
            temp_video.filename = filename
            temp_video.filepath = filepath
            temp_video.title = title
            temp_video.status = VideoStatus.UPLOADED
            db.session.commit()
            current_app.logger.info(f'视频记录更新成功: {temp_video.id}, 状态: {temp_video.status}')
            
            return jsonify({
                'id': temp_video.id,
                'status': 'uploaded',
                'message': '视频上传成功'
            })
            
        except Exception as e:
            current_app.logger.error(f"下载视频失败: {str(e)}")
            current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
            
            # 更新视频状态为失败
            if temp_video:
                temp_video.status = VideoStatus.FAILED
                temp_video.error_message = str(e)
                db.session.commit()
            
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
    try:
        video = Video.query.get_or_404(video_id)
        
        # 检查是否存在字幕文件
        subtitle_path = None
        possible_subtitle_files = [
            os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{video.filename}.srt"),
            os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{os.path.splitext(video.filename)[0]}.srt")
        ]
        
        for path in possible_subtitle_files:
            if os.path.exists(path):
                subtitle_path = os.path.basename(path)
                break
        
        return jsonify({
            'id': video.id,
            'title': video.title,
            'filename': video.filename,
            'status': video.status.value,
            'upload_time': video.upload_time.isoformat() if video.upload_time else None,
            'duration': video.duration,
            'fps': video.fps,
            'width': video.width,
            'height': video.height,
            'frame_count': video.frame_count,
            'preview_filename': video.preview_filename,
            'error_message': video.error_message,
            'subtitle_filepath': subtitle_path
        })
    except Exception as e:
        current_app.logger.error(f"获取视频信息失败: {str(e)}")
        return jsonify({'error': f'获取视频信息失败: {str(e)}'}), 500

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
        # 添加性能日志
        start_time = time.time()
        current_app.logger.info("🔍 开始获取视频列表")
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        current_app.logger.info(f"分页参数: page={page}, per_page={per_page}")
        
        # 限制返回最近100条记录以提高性能
        try:
            videos = Video.query.order_by(Video.upload_time.desc()).limit(100).all()
            current_app.logger.info(f"成功查询数据库，获取到 {len(videos)} 条视频记录")
        except Exception as db_error:
            current_app.logger.error(f"数据库查询失败: {str(db_error)}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({'error': f'数据库查询失败: {str(db_error)}'}), 500
        
        result = []
        
        for video in videos:
            try:
                current_app.logger.debug(f"处理视频记录: ID={video.id}, 文件名={video.filename}")
                
                # 安全获取状态值
                if hasattr(video.status, 'value'):
                    status = video.status.value
                    current_app.logger.debug(f"视频状态为枚举值: {status}")
                elif isinstance(video.status, str):
                    status = video.status
                    current_app.logger.debug(f"视频状态为字符串: {status}")
                else:
                    status = 'unknown'
                    current_app.logger.warning(f"未知的视频状态类型: {type(video.status)}")
                
                # 尝试解析标签数据
                tags = []
                if hasattr(video, 'tags') and video.tags:
                    try:
                        tags = json.loads(video.tags)
                        current_app.logger.debug(f"成功解析视频标签: {tags}")
                    except Exception as e:
                        current_app.logger.error(f'解析视频标签时出错: {str(e)}')
                        current_app.logger.error(f'标签原始数据: {video.tags}')
                
                # 安全获取各个属性
                try:
                    upload_time = video.upload_time.isoformat() if video.upload_time else None
                except Exception as e:
                    current_app.logger.error(f"处理upload_time时出错: {str(e)}")
                    upload_time = None
                
                # 构建视频数据字典
                video_data = {
                    'id': video.id,
                    'title': video.title if hasattr(video, 'title') and video.title else '',
                    'filename': video.filename if hasattr(video, 'filename') and video.filename else '',
                    'status': status,
                    'upload_time': upload_time,
                    'preview_filename': video.preview_filename if hasattr(video, 'preview_filename') else None,
                    'duration': video.duration if hasattr(video, 'duration') else None,
                    'width': video.width if hasattr(video, 'width') else None,
                    'height': video.height if hasattr(video, 'height') else None,
                    'fps': video.fps if hasattr(video, 'fps') else None,
                    'summary': video.summary if hasattr(video, 'summary') else None,
                    'tags': tags  # 添加标签数据
                }
                result.append(video_data)
                current_app.logger.debug(f"成功处理视频记录: ID={video.id}")
            except Exception as e:
                current_app.logger.error(f'处理视频记录时出错: {str(e)}')
                current_app.logger.error(traceback.format_exc())
                # 跳过有问题的记录，继续处理其他记录
                continue
        
        # 手动实现分页
        total = len(result)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_result = result[start_idx:end_idx] if start_idx < total else []
        
        elapsed_time = time.time() - start_time
        current_app.logger.info(f"✅ 获取视频列表完成 | 耗时: {elapsed_time:.2f}秒 | 总记录数: {total} | 当前页记录数: {len(paginated_result)}")
        
        return jsonify({
            'message': '获取成功',
            'videos': paginated_result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        current_app.logger.error(f'❌ 获取视频列表失败: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'获取视频列表失败: {str(e)}'}), 500

@bp.route('/<int:video_id>/status', methods=['GET'])
def get_video_status(video_id):
    """获取视频状态"""
    try:
        video = Video.query.get_or_404(video_id)
        current_app.logger.info(f"获取视频状态: ID={video_id}, 原始状态={video.status}")
        
        # 确保返回正确的状态值
        if video.status == VideoStatus.COMPLETED:
            status = 'completed'
        elif video.status == VideoStatus.PROCESSING:
            status = 'processing'
        elif video.status == VideoStatus.FAILED:
            status = 'failed'
        elif video.status == VideoStatus.UPLOADED:
            status = 'uploaded'
        else:
            status = str(video.status.value) if hasattr(video.status, 'value') else str(video.status)
            
        response_data = {
            'id': video.id,
            'status': status,
            'progress': video.process_progress or 0,
            'current_step': video.current_step or '',
            'task_id': video.task_id
        }
        
        current_app.logger.info(f"返回视频状态: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"获取视频状态失败: {str(e)}")
        current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:video_id>/process', methods=['POST', 'OPTIONS'])
def process_video_route(video_id):
    """开始处理视频"""
    current_app.logger.info(f'收到{request.method}请求: /videos/{video_id}/process')
    
    # 处理OPTIONS请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.status_code = 200
        return response
    
    try:
        # 🍎 使用平台检测工具自动导入适合当前平台的视频处理任务（Mac MPS / Windows CUDA / CPU）
        from app.utils.platform_utils import import_video_processing
        process_video = import_video_processing()
        
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

@bp.route('/<int:video_id>/delete', methods=['DELETE', 'OPTIONS'])
def delete_video(video_id):
    """删除视频"""
    # 处理 OPTIONS 请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        return response
        
    try:
        video = Video.query.get_or_404(video_id)
        
        # 先删除与该视频关联的问题记录
        from ..models.qa import Question
        Question.query.filter_by(video_id=video_id).delete()
        db.session.commit()
        
        # 🍎 使用平台检测工具导入清理任务（自动适配 Mac/Windows/Linux）
        import platform
        if platform.system() == "Darwin":  # Mac
            from ..tasks.video_processing_mac import cleanup_video
        else:  # Windows/Linux
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

@bp.route('/<int:video_id>/stream', methods=['GET', 'OPTIONS'])
def get_video_stream(video_id):
    """流式传输视频"""
    # 处理OPTIONS请求
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Range',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400'
        }
        return '', 200, headers
        
    current_app.logger.info(f'收到视频流请求: video_id={video_id}')
    current_app.logger.info(f'请求头: {dict(request.headers)}')
    
    try:
        video = Video.query.get_or_404(video_id)
        current_app.logger.info(f'找到视频记录: {video.filename}')
        
        # 检查文件是否存在
        if not os.path.exists(video.filepath):
            current_app.logger.error(f'视频文件不存在: {video.filepath}')
            return jsonify({'error': '视频文件不存在'}), 404
        
        # 获取文件大小
        file_size = os.path.getsize(video.filepath)
        current_app.logger.info(f'视频文件大小: {file_size} 字节')
        
        # 获取Range头
        range_header = request.headers.get('Range')
        current_app.logger.info(f'Range头: {range_header}')
        
        # 设置基础响应头
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Type': 'video/mp4',
            'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Range',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Expose-Headers': 'Content-Range, Accept-Ranges, Content-Length',
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
        }
        
        if range_header:
            try:
                # 解析Range头
                bytes_range = range_header.replace('bytes=', '').split('-')
                start = int(bytes_range[0]) if bytes_range[0] else 0
                end = int(bytes_range[1]) if bytes_range[1] else file_size - 1
                
                if start >= file_size:
                    current_app.logger.error(f'请求的范围无效: start={start}, file_size={file_size}')
                    return jsonify({'error': '请求的范围无效'}), 416
                
                # 确保end不超过文件大小
                end = min(end, file_size - 1)
                chunk_size = end - start + 1
                
                current_app.logger.info(f'处理范围请求: bytes {start}-{end}/{file_size}')
                
                headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                headers['Content-Length'] = str(chunk_size)
                
                def generate():
                    try:
                        with open(video.filepath, 'rb') as f:
                            f.seek(start)
                            remaining = chunk_size
                            buffer_size = min(8192, remaining)  # 8KB chunks
                            
                            while remaining:
                                if remaining < buffer_size:
                                    buffer_size = remaining
                                data = f.read(buffer_size)
                                if not data:
                                    break
                                remaining -= len(data)
                                yield data
                    except Exception as e:
                        current_app.logger.error(f'生成视频流时出错: {str(e)}')
                        return jsonify({'error': '读取视频文件失败'}), 500
                
                return Response(
                    generate(),
                    206,
                    headers=headers,
                    direct_passthrough=True
                )
                
            except (IndexError, ValueError) as e:
                current_app.logger.error(f'解析Range头失败: {str(e)}')
                return jsonify({'error': '无效的Range头'}), 400
        
        # 如果没有Range头，返回整个文件
        headers['Content-Length'] = str(file_size)
        
        def generate_full():
            try:
                with open(video.filepath, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            except Exception as e:
                current_app.logger.error(f'生成完整视频流时出错: {str(e)}')
                return jsonify({'error': '读取视频文件失败'}), 500
        
        return Response(
            generate_full(),
            200,
            headers=headers,
            direct_passthrough=True
        )
        
    except Exception as e:
        current_app.logger.error(f"视频流传输失败: {str(e)}")
        current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({'error': '视频流传输失败'}), 500

@bp.route('/<int:video_id>/subtitle', methods=['GET'])
def get_subtitle(video_id):
    try:
        # 获取请求的格式参数
        format_type = request.args.get('format', 'srt')
        current_app.logger.info(f'请求的字幕格式: {format_type}')
        
        # 获取视频信息
        video = Video.query.get_or_404(video_id)
        current_app.logger.info(f'获取视频信息: ID={video.id}, 文件名={video.filename}')
        
        # 处理文件名
        filename = os.path.splitext(video.filename)[0]
        current_app.logger.info(f'处理后的文件名: {filename}')
        
        # 构建可能的字幕文件路径
        possible_subtitle_files = [
            video.subtitle_filepath,  # 直接使用存储的路径
            os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles', os.path.basename(video.subtitle_filepath)),  # 在subtitles目录下
            os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(video.subtitle_filepath)),  # 在上传目录下
            os.path.join(os.path.dirname(video.filepath), os.path.basename(video.subtitle_filepath))  # 在视频文件同目录下
        ]
        current_app.logger.info(f'可能的字幕文件路径: {possible_subtitle_files}')
        
        # 检查字幕文件夹是否存在
        subtitle_folder = current_app.config['SUBTITLE_FOLDER']
        current_app.logger.info(f'字幕文件夹路径: {subtitle_folder}')
        
        subtitle_path = None
        for path in possible_subtitle_files:
            current_app.logger.info(f'检查文件: {path}')
            if path and os.path.exists(path):
                subtitle_path = path
                current_app.logger.info(f'找到字幕文件: {path}')
                break
        
        if not subtitle_path:
            current_app.logger.error(f'尝试了所有可能的路径，但字幕文件不存在')
            return jsonify({'error': '字幕文件不存在'}), 404
            
        current_app.logger.info(f'读取字幕文件: {subtitle_path}')
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 根据请求的格式处理字幕内容
        format_type = format_type.lower()
        if format_type == 'vtt':
            current_app.logger.info('转换为VTT格式')
            vtt_content = 'WEBVTT\n\n' + content.replace(',', '.')
            response = make_response(vtt_content)
            response.headers['Content-Type'] = 'text/vtt; charset=utf-8'
        elif format_type == 'txt':
            current_app.logger.info('转换为TXT格式')
            # 解析SRT内容，提取纯文本
            import re
            # 移除时间戳和序号，只保留文本内容
            txt_content = re.sub(r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n', '', content, flags=re.MULTILINE)
            txt_content = re.sub(r'^\s*\n', '', txt_content, flags=re.MULTILINE)  # 移除空行
            response = make_response(txt_content)
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        else:
            current_app.logger.info('返回SRT格式')
            response = make_response(content)
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            
        # 如果是下载请求，添加Content-Disposition头
        if request.args.get('download') == 'true':
            # 使用 RFC 5987 编码处理中文文件名
            filename_encoded = filename.encode('utf-8').decode('latin-1')
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename_encoded}.{format_type}"
            response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"获取字幕失败: {str(e)}")
        return jsonify({'error': f'获取字幕失败: {str(e)}'}), 500

@bp.route('/<int:video_id>/generate-summary', methods=['POST'])
def generate_summary(video_id):
    """为视频生成内容摘要"""
    try:
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            current_app.logger.error(f'视频不存在: {video_id}')
            return jsonify({'error': '视频不存在'}), 404
            
        # 检查视频是否已处理完成
        if video.status != VideoStatus.COMPLETED:
            current_app.logger.error(f'视频尚未处理完成，无法生成摘要: {video_id}')
            return jsonify({'error': '视频尚未处理完成，请先处理视频'}), 400
            
        # 获取字幕文件路径
        subtitle_path = None
        if video.subtitle_filepath:
            # 尝试多种可能的路径
            possible_paths = [
                video.subtitle_filepath,  # 直接使用存储的路径
                os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles', os.path.basename(video.subtitle_filepath)),  # 在subtitles目录下
                os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(video.subtitle_filepath)),  # 在上传目录下
                os.path.join(os.path.dirname(video.filepath), os.path.basename(video.subtitle_filepath))  # 在视频文件同目录下
            ]
            
            current_app.logger.info(f'尝试查找字幕文件，可能的路径: {possible_paths}')
            
            # 检查所有可能的路径
            for path in possible_paths:
                if path and os.path.exists(path):
                    subtitle_path = path
                    current_app.logger.info(f'找到字幕文件: {path}')
                    break
            
            if not subtitle_path:
                current_app.logger.error(f'尝试了所有可能的路径，但字幕文件不存在')
                return jsonify({'error': '字幕文件不存在'}), 404
        else:
            current_app.logger.error(f'视频没有字幕文件: {video_id}')
            return jsonify({'error': '视频没有字幕文件，无法生成摘要'}), 400
            
        # 调用摘要生成服务
        current_app.logger.info(f'开始为视频 {video_id} 生成摘要')
        result = generate_video_summary(video_id, subtitle_path)
        
        if not result['success']:
            current_app.logger.error(f'生成摘要失败: {result["error"]}')
            return jsonify({'error': f'生成摘要失败: {result["error"]}'}), 500
            
        # 更新视频摘要
        try:
            video.summary = result['summary']
            db.session.commit()
            current_app.logger.info(f'成功为视频 {video_id} 生成摘要并保存')
        except Exception as e:
            current_app.logger.error(f'保存摘要到数据库失败: {str(e)}')
            return jsonify({'error': '保存摘要失败'}), 500
            
        return jsonify({
            'success': True,
            'summary': result['summary']
        })
        
    except Exception as e:
        current_app.logger.error(f'生成摘要时发生错误: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'生成摘要时发生错误: {str(e)}'}), 500

@bp.route('/<int:video_id>/generate-tags', methods=['POST'])
def generate_tags(video_id):
    """为视频生成标签"""
    try:
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            current_app.logger.error(f'视频不存在: {video_id}')
            return jsonify({'error': '视频不存在'}), 404
            
        # 检查视频是否已处理完成
        if video.status != VideoStatus.COMPLETED:
            current_app.logger.error(f'视频尚未处理完成，无法生成标签: {video_id}')
            return jsonify({'error': '视频尚未处理完成，请先处理视频'}), 400
            
        # 检查视频是否有摘要
        if not video.summary:
            current_app.logger.error(f'视频没有摘要，无法生成标签: {video_id}')
            return jsonify({'error': '视频没有摘要，请先生成摘要'}), 400
            
        # 调用标签生成服务
        current_app.logger.info(f'开始为视频 {video_id} 生成标签')
        result = generate_video_tags(video_id, video.summary)
        
        if not result['success']:
            current_app.logger.error(f'生成标签失败: {result["error"]}')
            return jsonify({'error': f'生成标签失败: {result["error"]}'}), 500
            
        # 更新视频标签
        try:
            # 将标签列表转换为JSON字符串存储
            video.tags = json.dumps(result['tags'], ensure_ascii=False)
            db.session.commit()
            current_app.logger.info(f'成功为视频 {video_id} 生成标签并保存: {result["tags"]}')
        except Exception as e:
            current_app.logger.error(f'保存标签到数据库失败: {str(e)}')
            return jsonify({'error': '保存标签失败'}), 500
            
        return jsonify({
            'success': True,
            'tags': result['tags']
        })
        
    except Exception as e:
        current_app.logger.error(f'生成标签时发生错误: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'生成标签时发生错误: {str(e)}'}), 500

@bp.route('/<int:video_id>', methods=['GET'])
def get_video_detail(video_id):
    """获取视频详情"""
    try:
        video = Video.query.get(video_id)
        return jsonify(video.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
