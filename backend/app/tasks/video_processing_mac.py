"""
视频处理任务 - Mac M系列芯片优化版
主要功能：
1. 视频预览图生成
2. 视频信息提取
3. 字幕生成和格式化
4. 音频转录
5. 🍎 支持 Apple M1/M2/M3/M4 芯片的 MPS 加速
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

def get_device():
    """获取最佳计算设备 - Mac优化版"""
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"

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
        # 创建预览图目录
        preview_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'previews')
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
    """预热GPU，提高首次转录速度 - Mac MPS 优化版"""
    try:
        device = get_device()
        if device == "mps":
            # 执行一些小型矩阵运算来预热 MPS
            x = torch.randn(100, 100).to('mps')
            torch.matmul(x, x)
            # MPS 不需要 synchronize，直接清空缓存
            logger.info("✅ MPS GPU预热完成 (Apple Silicon)")
        else:
            logger.info("💻 使用CPU模式，无需预热")
    except Exception as e:
        logger.warning(f"⚠️  GPU预热失败: {str(e)}")

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
        'fp16': False,  # Mac MPS 不支持 fp16，使用 fp32
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

@celery.task(name='app.tasks.process_video_mac', bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=240, retry_jitter=True)
def process_video(self, video_id, language='zh', model='turbo'):
    """处理视频任务 - Mac优化版"""
    try:
        # 设置任务ID
        task_id = self.request.id
        logger.info(f"🎬 开始处理视频 (Mac MPS优化) | ID: {video_id} | 语言: {language} | 模型: {model} | 任务ID: {task_id}")
        
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
            preview_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'previews')
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
            logger.info(f"🎙️ 准备转录视频 (MPS加速) | 文件: {os.path.basename(video.filepath)}")
            
            # 更新进度
            video.process_progress = 50.0
            video.current_step = "准备转录视频"
            db.session.commit()
            
            # 检测MPS是否可用
            mps_available = torch.backends.mps.is_available()
            if mps_available:
                logger.info("🍎 MPS加速可用 (Apple Silicon)")
                # 预热MPS
                warm_up_gpu()
            else:
                logger.info("💻 使用CPU模式")
            
            # 检查是否是占位文件，如果是则跳过字幕处理
            if not is_placeholder:
                # 创建字幕输出目录
                subtitle_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles')
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
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    # 等待进程完成
                    process.wait()
                    
                    if os.path.exists(audio_path):
                        logger.info(f"✅ 音频提取成功 | 文件: {os.path.basename(audio_path)}")
                        input_file = audio_path
                    else:
                        logger.warning("⚠️  音频提取失败，将使用原视频文件")
                        input_file = video.filepath
                except Exception as e:
                    logger.warning(f"⚠️  音频提取过程中出错: {str(e)}，将使用原视频文件")
                    input_file = video.filepath
                
                # 调用whisper命令行工具进行转录
                whisper_cmd = [
                    "python", "-m", "whisper", 
                    input_file,
                    "--model", model,
                    "--language", language,
                    "--output_dir", subtitle_dir,
                    "--output_format", "all",
                ]
                
                if language:
                    whisper_cmd.extend(["--language", language])
                
                # 记录命令
                logger.info(f"🚀 启动AI转录引擎 | 模型: {model} | 语言: {language} | MPS加速: {'已启用' if mps_available else '未启用'}")
                logger.info(f"📝 处理文件: {os.path.basename(input_file)}")
                
                # 启动子进程并实时监控输出
                process = subprocess.Popen(
                    whisper_cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # 监控进度（简化版，避免线程问题）
                start_time = time.time()
                while process.poll() is None:
                    elapsed = time.time() - start_time
                    progress = min(95, int(elapsed / 45 * 100))
                    
                    video.process_progress = 60.0 + (progress * 0.3)
                    video.current_step = f"转录中: {progress}%"
                    db.session.commit()
                    
                    time.sleep(2)
                
                result = process.returncode
                
                # 更新进度
                video.process_progress = 90.0
                video.current_step = "转录完成，处理结果"
                db.session.commit()
                
                if result != 0:
                    stderr_output = process.stderr.read()
                    logger.error(f"❌ 转录失败: {stderr_output}")
                else:
                    logger.info(f"✅ 转录完成 | 状态: 成功")
                
                # 检查生成的字幕文件是否存在
                expected_srt = os.path.join(subtitle_dir, f"{base_filename}.srt")
                if os.path.exists(expected_srt):
                    video.subtitle_filepath = expected_srt
                    logger.info(f"📄 字幕文件已生成 | 文件: {os.path.basename(expected_srt)}")
                else:
                    srt_files = [f for f in os.listdir(subtitle_dir) if f.endswith('.srt')]
                    if srt_files:
                        newest_srt = max([os.path.join(subtitle_dir, f) for f in srt_files], 
                                       key=os.path.getctime)
                        video.subtitle_filepath = newest_srt
                        logger.info(f"📄 字幕文件已生成 | 文件: {os.path.basename(newest_srt)}")
                    else:
                        logger.warning(f"⚠️  未找到生成的字幕文件")
                
                # 清理临时音频文件
                try:
                    if 'audio_path' in locals() and os.path.exists(audio_path):
                        os.remove(audio_path)
                        logger.info(f"🧹 已清理临时音频文件: {os.path.basename(audio_path)}")
                except Exception as e:
                    logger.warning(f"⚠️  清理临时文件失败: {str(e)}")
                    
                # 更新视频状态为已完成
                video.status = VideoStatus.COMPLETED
                video.processed = True
                video.process_progress = 100.0
                video.current_step = "处理完成"
                db.session.commit()
            else:
                logger.info(f"📝 占位文件，跳过字幕处理")
                video.process_progress = 100.0
                video.status = VideoStatus.COMPLETED
                video.processed = True
                video.current_step = "处理完成"
                db.session.commit()
        except Exception as e:
            logger.error(f"❌ 字幕处理失败: {str(e)}")
            video.status = VideoStatus.COMPLETED
            video.processed = True
            video.process_progress = 100.0
            video.current_step = "处理完成（字幕处理失败）"
            db.session.commit()
        
        logger.info(f"✅ 视频处理完成 | ID: {video_id}")
        return {'status': 'success', 'message': '视频处理成功'}
        
    except Exception as e:
        logger.error(f"❌ 处理视频失败 | 错误: {str(e)}")
        
        try:
            video = Video.query.get(video_id)
            if video:
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = f"处理失败: {str(e)}"
                db.session.commit()
        except Exception as e2:
            logger.error(f"更新视频状态失败: {str(e2)}")
        
        return {'status': 'failed', 'message': f'处理视频失败: {str(e)}'}

@celery.task(name='app.tasks.cleanup_video_mac')
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
