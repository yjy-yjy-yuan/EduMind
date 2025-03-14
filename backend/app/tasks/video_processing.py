"""
视频处理任务
主要功能：
1. 视频预览图生成
2. 视频信息提取
3. 字幕生成和格式化
4. 音频转录
"""

import os
import cv2
import json
import time
import logging
import subprocess
import numpy as np
import whisper
import torch
from datetime import datetime
from flask import current_app
from ..extensions import db, celery
from ..models.video import Video, VideoStatus
from pydub import AudioSegment
import tempfile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

logger = logging.getLogger(__name__)

def generate_video_info(video_path):
    """生成视频信息"""
    try:
        # 使用OpenCV获取视频信息
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return None
        
        # 获取视频属性
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # 释放视频对象
        cap.release()
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration
        }
        
    except Exception as e:
        logger.error(f"获取视频信息失败: {str(e)}")
        return None

def extract_video_info(video):
    """提取视频信息"""
    try:
        # 检查是否为占位文件
        try:
            with open(video.filepath, 'r', encoding='utf-8') as f:
                content = f.read(100)
                if "慕课视频链接" in content or "无法下载慕课视频" in content:
                    # 返回默认视频信息
                    return {
                        'duration': 0,
                        'fps': 0,
                        'width': 640,
                        'height': 360,
                        'frame_count': 0
                    }
        except UnicodeDecodeError:
            pass  # 不是文本文件，继续正常处理
        
        # 获取视频信息
        video_info = generate_video_info(video.filepath)
        
        if video_info:
            # 更新视频信息
            video.duration = video_info.get('duration')
            video.fps = video_info.get('fps')
            video.width = video_info.get('width')
            video.height = video_info.get('height')
            video.frame_count = video_info.get('frame_count')
            db.session.commit()
            
            return video_info
        else:
            logger.error(f"无法获取视频信息: {video.filepath}")
            return None
    
    except Exception as e:
        logger.error(f"提取视频信息失败: {str(e)}")
        return None

def generate_preview(video_path):
    """生成视频预览图"""
    import os  # 确保os模块导入
    import cv2
    import numpy as np
    try:
        # 使用应用配置中定义的预览图目录
        preview_dir = current_app.config['PREVIEW_FOLDER']
        os.makedirs(preview_dir, exist_ok=True)
        
        # 设置预览图路径
        preview_filename = f"preview_{os.path.basename(video_path)}.jpg"
        preview_path = os.path.join(preview_dir, preview_filename)
        
        # 检查是否为占位文件
        try:
            with open(video_path, 'r', encoding='utf-8') as f:
                content = f.read(100)
                if "慕课视频链接" in content or "无法下载慕课视频" in content:
                    # 创建一个简单的预览图
                    img = np.zeros((360, 640, 3), dtype=np.uint8)
                    # 设置背景颜色为深蓝色
                    img[:, :] = (25, 55, 125)
                    
                    # 添加文字
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(img, '慕课视频占位图', (160, 180), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(img, '请手动下载替换', (160, 220), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    
                    # 保存图片
                    cv2.imwrite(preview_path, img)
                    return preview_path
        except UnicodeDecodeError:
            pass  # 不是文本文件，继续正常处理
        
        # 使用OpenCV生成预览图
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return None
        
        # 读取第一帧
        ret, frame = cap.read()
        if not ret:
            logger.error(f"无法读取视频帧: {video_path}")
            cap.release()
            return None
        
        # 保存预览图
        cv2.imwrite(preview_path, frame)
        cap.release()
        
        return preview_path
    
    except Exception as e:
        logger.error(f"生成预览图失败: {str(e)}")
        return None

def warm_up_gpu():
    """预热GPU，提高首次转录速度"""
    try:
        if torch.cuda.is_available():
            # 执行一些小型矩阵运算来预热 GPU
            x = torch.randn(100, 100).cuda()
            torch.matmul(x, x)
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            logger.info("GPU预热完成")
    except Exception as e:
        logger.warning(f"GPU预热失败: {str(e)}")

def process_long_audio(audio_path, chunk_duration=600):
    """处理长音频文件，将其分成小块并行处理"""
    try:
        audio = AudioSegment.from_wav(audio_path)
        total_duration = len(audio)
        chunks = []
        
        # 如果音频小于10分钟，直接返回原文件
        if total_duration <= chunk_duration * 1000:
            return [audio_path]
            
        # 分割音频
        logger.info(f"分割长音频文件: {os.path.basename(audio_path)}")
        for i in tqdm(range(0, total_duration, chunk_duration * 1000), 
                     desc="分割音频", unit="块", ncols=100):
            chunk = audio[i:i + chunk_duration * 1000]
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                chunk.export(temp_file.name, format='wav')
                chunks.append(temp_file.name)
        
        return chunks
    except Exception as e:
        logger.error(f"音频分块失败: {str(e)}")
        return [audio_path]

def get_whisper_params(model_name, language='zh'):
    """获取针对不同模型优化的转录参数"""
    # 语言代码映射
    language_map = {
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'en': 'English',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'ru': 'Russian',
        'it': 'Italian',
        'pt': 'Portuguese',
        'nl': 'Dutch',
        'pl': 'Polish',
        'tr': 'Turkish',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'th': 'Thai',
        'vi': 'Vietnamese'
    }
    
    # 获取完整的语言名称，如果不在映射表中，则使用原始代码
    target_language = language_map.get(language.lower(), language)
    
    # 基础参数配置
    base_params = {
        'language': target_language,
        'task': 'transcribe',
        'temperature': 0.0,  # 使用确定性输出
        'no_speech_threshold': 0.6,
        'condition_on_previous_text': True,
        'fp16': True,  # 使用半精度加速
        'verbose': False
    }
    
    # 为不同语言设置初始提示
    prompts = {
        'Chinese': '这是一个教育视频。',
        'Japanese': 'これは教育ビデオです。',
        'Korean': '이것은 교육 비디오입니다。',
        'English': 'This is an educational video.',
    }
    base_params['initial_prompt'] = prompts.get(target_language, '')
    
    # 根据模型大小优化参数
    if model_name in ['tiny', 'tiny.en', 'base', 'base.en', 'turbo']:
        base_params.update({
            'beam_size': 1,
            'best_of': 1,
            'patience': 1,
            'compression_ratio_threshold': 2.4,
            'logprob_threshold': -1.0,
            'no_speech_threshold': 0.6
        })
    elif model_name in ['small', 'small.en']:
        base_params.update({
            'beam_size': 2,
            'best_of': 2,
            'patience': 1,
            'compression_ratio_threshold': 2.4,
            'logprob_threshold': -1.0
        })
    else:  # medium, large
        base_params.update({
            'beam_size': 5,
            'best_of': 5,
            'patience': 1,
            'compression_ratio_threshold': 2.4,
            'logprob_threshold': -1.0
        })
    
    return base_params

def transcribe_audio(audio_path, model_name="base", language="zh"):
    """使用Whisper API转录音频"""
    try:
        # 加载模型
        logger.info(f"加载Whisper模型: {model_name}")
        model = whisper.load_model(model_name)
        
        # 转录音频
        logger.info(f"开始转录音频: {os.path.basename(audio_path)}")
        result = model.transcribe(audio_path, language=language, verbose=False)
        
        return result
    except Exception as e:
        logger.error(f"转录音频失败: {str(e)}")
        return None

def merge_transcriptions(chunks_results):
    """合并多个转录结果"""
    merged_result = {
        'text': '',
        'segments': []
    }
    
    time_offset = 0
    for result in chunks_results:
        if not result:
            continue
            
        merged_result['text'] += result['text'] + '\n'
        
        # 调整时间戳
        for segment in result['segments']:
            segment['start'] += time_offset
            segment['end'] += time_offset
            merged_result['segments'].append(segment)
        
        # 更新时间偏移
        if result['segments']:
            time_offset = result['segments'][-1]['end']
    
    return merged_result

@celery.task(name='app.tasks.process_video', bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=240, retry_jitter=True)
def process_video(self, video_id, language='zh', model='turbo'):
    """处理视频任务"""
    try:
        # 设置任务ID
        task_id = self.request.id
        logger.info(f"🎬 开始处理视频 | ID: {video_id} | 语言: {language} | 模型: {model} | 任务ID: {task_id}")
        
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            logger.error(f'❌ 视频不存在 | ID: {video_id}')
            return {'status': 'failed', 'message': '视频不存在'}
        
        # 更新视频状态和进度
        video.status = VideoStatus.PROCESSING
        video.process_progress = 0.0
        video.current_step = "初始化处理"
        video.task_id = self.request.id
        db.session.commit()
        
        # 检查文件是否为占位文件（文本文件）
        is_placeholder = False
        try:
            with open(video.filepath, 'r', encoding='utf-8') as f:
                content = f.read(100)  # 读取前100个字符
                if "慕课视频链接" in content or "无法下载慕课视频" in content:
                    is_placeholder = True
                    logger.warning(f'检测到占位文件: {video.filepath}')
        except UnicodeDecodeError:
            # 如果不是文本文件，则不是占位文件
            pass
        except Exception as e:
            logger.error(f'检查占位文件时出错: {str(e)}')
            # 继续处理，假设不是占位文件
        
        # 如果是占位文件，创建一个默认预览图
        if is_placeholder:
            logger.warning(f'为占位文件创建默认预览图')
            video.process_progress = 20.0
            video.current_step = "处理占位文件"
            db.session.commit()
            
            if create_placeholder_preview(video):
                # 更新视频状态
                video.status = VideoStatus.COMPLETED
                video.processed = True
                video.duration = 0
                video.fps = 0
                video.width = 640
                video.height = 360
                video.frame_count = 0
                video.process_progress = 100.0
                video.current_step = "完成"
                db.session.commit()
                
                return {'status': 'success', 'message': '已创建占位文件预览图'}
            else:
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = "处理失败"
                db.session.commit()
                return {'status': 'failed', 'message': '创建占位文件预览图失败'}
        
        # 生成预览图
        try:
            # 更新进度
            video.process_progress = 10.0
            video.current_step = "生成预览图"
            db.session.commit()
            
            # 确保预览图目录存在
            preview_dir = current_app.config['PREVIEW_FOLDER']
            os.makedirs(preview_dir, exist_ok=True)
            
            # 设置预览图路径
            preview_filename = f"preview_{video.id}.jpg"
            preview_path = os.path.join(preview_dir, preview_filename)
            
            # 使用OpenCV生成预览图
            cap = cv2.VideoCapture(video.filepath)
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video.filepath}")
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = "无法打开视频文件"
                db.session.commit()
                return {'status': 'failed', 'message': '无法打开视频文件'}
            
            # 读取第一帧
            ret, frame = cap.read()
            if not ret:
                logger.error(f"无法读取视频帧: {video.filepath}")
                cap.release()
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = "无法读取视频帧"
                db.session.commit()
                return {'status': 'failed', 'message': '无法读取视频帧'}
            
            # 保存预览图
            cv2.imwrite(preview_path, frame)
            cap.release()
            
            # 更新视频记录
            video.preview_filename = preview_filename
            video.preview_filepath = preview_path
            video.process_progress = 20.0
            db.session.commit()
        except Exception as e:
            logger.error(f"生成预览图失败: {str(e)}")
            video.status = VideoStatus.FAILED
            video.process_progress = 0.0
            video.current_step = f"生成预览图失败: {str(e)}"
            db.session.commit()
            return {'status': 'failed', 'message': f'生成预览图失败: {str(e)}'}
        
        # 提取视频信息
        try:
            # 更新进度
            video.process_progress = 30.0
            video.current_step = "提取视频信息"
            db.session.commit()
            
            # 获取视频信息
            video_info = generate_video_info(video.filepath)
            
            if video_info:
                # 更新视频信息
                video.width = video_info['width']
                video.height = video_info['height']
                video.fps = video_info['fps']
                video.frame_count = video_info['frame_count']
                video.duration = video_info['duration']
                video.process_progress = 40.0
                db.session.commit()
            else:
                logger.error(f"获取视频信息失败: {video.filepath}")
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = "获取视频信息失败"
                db.session.commit()
                return {'status': 'failed', 'message': '获取视频信息失败'}
        except Exception as e:
            logger.error(f"提取视频信息失败: {str(e)}")
            video.status = VideoStatus.FAILED
            video.process_progress = 0.0
            video.current_step = f"提取视频信息失败: {str(e)}"
            db.session.commit()
            return {'status': 'failed', 'message': f'提取视频信息失败: {str(e)}'}
        
        # 处理字幕
        try:
            logger.info(f"🎙️ 准备转录视频 | 文件: {os.path.basename(video.filepath)}")
            
            # 更新进度
            video.process_progress = 50.0
            video.current_step = "准备转录视频"
            db.session.commit()
            
            # 检测CUDA是否可用
            cuda_available = False
            try:
                # 尝试执行一个简单的命令来检测CUDA是否可用
                check_cmd = ["python", "-c", "import torch; print(torch.cuda.is_available())"]
                result = subprocess.run(check_cmd, capture_output=True, text=True)
                cuda_available = "True" in result.stdout
                logger.info(f"CUDA检测结果: {cuda_available}")
                
                # 如果CUDA可用，尝试预热GPU
                if cuda_available:
                    logger.info("🔥 预热GPU以提高处理速度...")
                    warm_cmd = ["python", "-c", "import torch; torch.cuda.init(); torch.cuda.empty_cache(); print('GPU预热完成')"]
                    subprocess.run(warm_cmd, capture_output=True, text=True)
            except Exception as e:
                logger.warning(f"CUDA检测失败: {str(e)}")
                cuda_available = False
            
            # 检查是否是占位文件，如果是则跳过字幕处理
            if not is_placeholder:
                # 创建字幕输出目录
                subtitle_dir = current_app.config['SUBTITLE_FOLDER']
                os.makedirs(subtitle_dir, exist_ok=True)
                
                # 设置输出文件路径
                base_filename = os.path.splitext(os.path.basename(video.filepath))[0]
                srt_filepath = os.path.join(subtitle_dir, f"{base_filename}.srt")
                txt_filepath = os.path.join(subtitle_dir, f"{base_filename}.txt")
                
                # 预处理视频，提取音频以加快处理速度
                try:
                    logger.info("🔊 提取音频以加快处理速度...")
                    audio_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio_temp')
                    os.makedirs(audio_dir, exist_ok=True)
                    audio_path = os.path.join(audio_dir, f"{base_filename}.wav")
                    
                    # 使用ffmpeg提取音频（单声道，16kHz采样率，优化为语音识别）
                    ffmpeg_cmd = [
                        "ffmpeg", "-y", "-i", video.filepath, 
                        "-vn", "-acodec", "pcm_s16le", 
                        "-ar", "16000", "-ac", "1", 
                        "-threads", "8",  # 使用8个线程
                        "-benchmark",  # 启用基准测试模式
                        audio_path
                    ]
                    
                    # 执行ffmpeg命令
                    logger.info(f"执行音频提取命令: {' '.join(ffmpeg_cmd)}")
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        encoding='utf-8',  # 显式指定使用UTF-8编码
                        errors='replace'   # 遇到无法解码的字符时替换而不是报错
                    )
                    
                    # 等待进程完成，不显示进度条
                    process.wait()
                    
                    if os.path.exists(audio_path):
                        logger.info(f"✅ 音频提取成功 | 文件: {os.path.basename(audio_path)}")
                        # 使用提取的音频文件替代原视频文件进行转录
                        input_file = audio_path
                    else:
                        logger.warning("⚠️ 音频提取失败，将使用原视频文件")
                        input_file = video.filepath
                except Exception as e:
                    logger.warning(f"⚠️ 音频提取过程中出错: {str(e)}，将使用原视频文件")
                    input_file = video.filepath
                
                # 调用whisper命令行工具进行转录
                whisper_cmd = [
                    "python", "-m", "whisper", 
                    input_file,  # 使用提取的音频文件或原视频文件
                    "--model", model,
                    "--language", language,
                    "--output_dir", subtitle_dir,
                    "--output_format", "all",  # 使用all生成所有格式，包括srt和txt
                ]
                
                if language:
                    whisper_cmd.extend(["--language", language])
                
                # 记录命令
                logger.info(f"🚀 启动AI转录引擎 | 模型: {model} | 语言: {language} | CUDA加速: {'已启用' if torch.cuda.is_available() else '未启用'}")
                logger.info(f"📝 处理文件: {os.path.basename(input_file)}")
                
                # 启动子进程并实时监控输出
                process = subprocess.Popen(
                    whisper_cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',  # 显式指定使用UTF-8编码
                    errors='replace'   # 遇到无法解码的字符时替换而不是报错
                )
                
                # 监控进度
                with tqdm(total=100, desc="转录进度", unit="%", ncols=100) as pbar:
                    # 设置一个计时器，用于估算进度
                    start_time = time.time()
                    estimated_total_time = 45  # 估计的总处理时间（秒）
                    
                    # 创建一个线程安全的队列用于更新进度
                    import queue
                    progress_queue = queue.Queue()
                    
                    # 创建一个变量来跟踪实际的转录进度
                    actual_progress = 0
                    
                    # 创建一个线程来更新进度条
                    def update_progress():
                        nonlocal actual_progress
                        last_progress = 0
                        while process.poll() is None:  # 当进程仍在运行时
                            # 使用实际进度（如果有）或基于时间的估算
                            if actual_progress > 0:
                                current_progress = actual_progress
                            else:
                                # 计算经过的时间和估计的进度
                                elapsed_time = time.time() - start_time
                                current_progress = min(95, int(elapsed_time / estimated_total_time * 100))
                            
                            # 只有当当前进度大于上次更新的进度时才更新
                            if current_progress > last_progress:
                                # 更新进度条
                                pbar.update(current_progress - last_progress)
                                last_progress = current_progress
                                
                                # 将进度信息放入队列，而不是直接更新数据库
                                progress_queue.put({
                                    'progress': 60.0 + (current_progress * 0.3),
                                    'step': f"转录中: {current_progress}%"
                                })
                            
                            # 每秒更新一次
                            time.sleep(1)
                    
                    # 启动进度更新线程
                    import threading
                    progress_thread = threading.Thread(target=update_progress)
                    progress_thread.daemon = True  # 设置为守护线程，这样主线程结束时它也会结束
                    progress_thread.start()
                    
                    # 在主线程中处理进度队列，因为主线程有应用上下文
                    last_queue_check = time.time()
                    queue_check_interval = 0.5  # 每0.5秒检查一次队列
                    
                    # 读取进程的输出（不阻塞主线程）
                    for line in iter(lambda: process.stdout.readline() or process.stderr.readline(), ''):
                        logger.debug(f"Whisper输出: {line.strip()}")
                        
                        # 尝试从输出中提取实际进度信息
                        try:
                            # 检查是否包含进度信息
                            if "%" in line:
                                # 尝试提取百分比
                                percent_parts = line.split('%')
                                if len(percent_parts) > 0:
                                    # 提取百分比前面的数字
                                    percent_text = percent_parts[0].strip().split(' ')[-1]
                                    try:
                                        # 转换为数字
                                        percent_value = float(percent_text)
                                        # 更新实际进度
                                        actual_progress = int(percent_value)
                                        logger.debug(f"检测到实际进度: {actual_progress}%")
                                    except (ValueError, IndexError):
                                        pass
                            
                            # 检查是否包含特定的处理阶段信息
                            progress_markers = {
                                "Detecting language": 5,
                                "Language detected": 10,
                                "Loading model": 15,
                                "Transcribing": 20,
                                "Processing": 30,
                                "Transcription complete": 100
                            }
                            
                            for marker, progress in progress_markers.items():
                                if marker in line and progress > actual_progress:
                                    actual_progress = progress
                                    logger.debug(f"检测到处理阶段: {marker}, 设置进度为 {progress}%")
                        except Exception as e:
                            logger.debug(f"解析进度信息出错: {str(e)}")
                        
                        # 定期检查进度队列并更新数据库
                        current_time = time.time()
                        if current_time - last_queue_check >= queue_check_interval:
                            last_queue_check = current_time
                            
                            # 处理队列中的所有进度更新
                            try:
                                while not progress_queue.empty():
                                    progress_info = progress_queue.get_nowait()
                                    # 在主线程中更新数据库
                                    video.process_progress = progress_info['progress']
                                    video.current_step = progress_info['step']
                                    db.session.commit()
                            except Exception as e:
                                logger.warning(f"更新进度时出错: {str(e)}")
                    
                    # 等待进程完成
                    process.wait()
                    # 等待进度线程结束
                    progress_thread.join(timeout=1)
                    
                    # 处理队列中剩余的进度更新
                    try:
                        while not progress_queue.empty():
                            progress_info = progress_queue.get_nowait()
                            video.process_progress = progress_info['progress']
                            video.current_step = progress_info['step']
                            db.session.commit()
                    except Exception as e:
                        logger.warning(f"处理剩余进度更新时出错: {str(e)}")
                    
                    # 完成后更新到100%
                    if pbar.n < 100:
                        pbar.update(100 - pbar.n)
                        video.process_progress = 90.0
                        video.current_step = "转录完成"
                        db.session.commit()
                
                result = process.returncode
                
                # 更新进度
                video.process_progress = 90.0
                video.current_step = "转录完成，处理结果"
                db.session.commit()
                
                if result != 0:
                    stderr_output = process.stderr.read()
                    logger.error(f"❌ 转录失败: {stderr_output}")
                    # 不要因为字幕失败而使整个处理失败，继续处理
                else:
                    logger.info(f"✅ 转录完成 | 状态: 成功")
                    
                # 检查生成的字幕文件是否存在
                expected_srt = os.path.join(subtitle_dir, f"{base_filename}.srt")
                if os.path.exists(expected_srt):
                    video.subtitle_filepath = expected_srt
                    logger.info(f"📄 字幕文件已生成 | 文件: {os.path.basename(expected_srt)}")
                else:
                    # 尝试查找任何生成的srt文件
                    srt_files = [f for f in os.listdir(subtitle_dir) if f.endswith('.srt')]
                    if srt_files:
                        newest_srt = max([os.path.join(subtitle_dir, f) for f in srt_files], 
                                       key=os.path.getctime)
                        video.subtitle_filepath = newest_srt
                        logger.info(f"📄 字幕文件已生成 | 文件: {os.path.basename(newest_srt)}")
                    else:
                        logger.warning(f"⚠️ 未找到生成的字幕文件")
                
                # 清理临时音频文件
                try:
                    if 'audio_path' in locals() and os.path.exists(audio_path):
                        os.remove(audio_path)
                        logger.info(f"🧹 已清理临时音频文件: {os.path.basename(audio_path)}")
                except Exception as e:
                    logger.warning(f"⚠️ 清理临时文件失败: {str(e)}")
                    
                # 立即更新视频状态为已完成
                video.status = VideoStatus.COMPLETED
                video.processed = True
                video.process_progress = 100.0
                video.current_step = "处理完成"
                db.session.commit()
                
                # 确保所有数据库更改已提交
                try:
                    db.session.commit()
                except Exception as e:
                    logger.error(f"提交数据库更改时出错: {str(e)}")
                    db.session.rollback()
                    # 再次尝试提交
                    video.status = VideoStatus.COMPLETED
                    video.processed = True
                    video.process_progress = 100.0
                    video.current_step = "处理完成"
                    db.session.commit()
            else:
                logger.info(f"📝 占位文件，跳过字幕处理 | 文件: {os.path.basename(video.filepath)}")
                video.process_progress = 100.0
                video.status = VideoStatus.COMPLETED
                video.processed = True
                video.current_step = "处理完成"
                db.session.commit()
        except Exception as e:
            logger.error(f"❌ 字幕处理失败: {str(e)}")
            # 即使字幕处理失败，也将视频标记为已完成
            video.status = VideoStatus.COMPLETED
            video.processed = True
            video.process_progress = 100.0
            video.current_step = "处理完成（字幕处理失败）"
            db.session.commit()
        
        logger.info(f"✅ 视频处理完成 | ID: {video_id}")
        return {'status': 'success', 'message': '视频处理成功'}
        
    except Exception as e:
        logger.error(f"❌ 处理视频失败 | 错误: {str(e)}")
        
        # 更新视频状态
        try:
            video = Video.query.get(video_id)
            if video:
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = f"处理失败: {str(e)}"
                db.session.commit()
        except Exception as e2:
            logger.error(f"更新视频状态失败: {str(e2)}")
        
        # 尝试重试任务
        try:
            # 如果是超时或特定错误，尝试重试
            retry = False
            if "timed out" in str(e).lower() or "memory" in str(e).lower() or "cuda" in str(e).lower():
                retry = True
            
            if retry and self.request.retries < self.max_retries:
                logger.warning(f"⚠️ 任务失败，准备重试 | 尝试: {self.request.retries + 1}/{self.max_retries} | ID: {video_id}")
                # 指数退避策略：每次重试等待时间翻倍
                countdown = 60 * (2 ** self.request.retries)  # 60秒, 120秒, 240秒
                raise self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error(f"❌ 达到最大重试次数，任务失败 | ID: {video_id}")
        
        return {'status': 'failed', 'message': f'处理视频失败: {str(e)}'}

@celery.task(name='app.tasks.cleanup_video')
def cleanup_video(video_id):
    """清理视频文件"""
    try:
        video = Video.query.get(video_id)
        if not video:
            logger.error(f"未找到ID为{video_id}的视频")
            return {
                'status': 'error',
                'message': f'未找到ID为{video_id}的视频'
            }
            
        # 先删除与该视频关联的问题记录
        from ..models.qa import Question
        Question.query.filter_by(video_id=video_id).delete()
        db.session.commit()
            
        # 删除原始视频文件
        if video.filepath and os.path.exists(video.filepath):
            os.remove(video.filepath)
            
        # 删除处理后的视频文件
        if video.processed_filepath and os.path.exists(video.processed_filepath):
            os.remove(video.processed_filepath)
            
        # 删除预览图
        if video.preview_filepath and os.path.exists(video.preview_filepath):
            os.remove(video.preview_filepath)
            
        # 删除字幕文件
        if video.subtitle_filepath and os.path.exists(video.subtitle_filepath):
            os.remove(video.subtitle_filepath)
            
        # 删除数据库记录
        db.session.delete(video)
        db.session.commit()
            
        return {
            'status': 'success',
            'message': '视频文件清理完成'
        }
    except Exception as e:
        logger.error(f"清理视频文件时出错: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
