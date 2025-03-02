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
from datetime import datetime
from flask import current_app
from ..extensions import db, celery
from ..models.video import Video, VideoStatus

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

def process_subtitles(video, whisper_model="base", to_simplified=True):
    """处理视频字幕"""
    try:
        # 创建字幕输出目录
        subtitle_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles')
        os.makedirs(subtitle_dir, exist_ok=True)
        
        # 设置输出文件路径
        base_filename = os.path.splitext(video.filename)[0]
        srt_filepath = os.path.join(subtitle_dir, f"{base_filename}.srt")
        txt_filepath = os.path.join(subtitle_dir, f"{base_filename}.txt")
        
        # 初始化视频工具
        video_tools = VideoTools(whisper_model=whisper_model)
        
        # 转录视频
        result = video_tools.transcribe_video(video.filepath)
        if not result:
            raise Exception("视频转录失败")
            
        # 保存字幕文件
        video_tools.save_subtitles(result, txt_filepath, srt_filepath, to_simplified)
        
        # 更新视频记录
        video.subtitle_filepath = srt_filepath
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"处理字幕失败: {str(e)}")
        return False

def create_placeholder_preview(video):
    """为占位文件创建默认预览图"""
    import os  # 确保os模块导入
    try:
        # 确保预览图目录存在
        preview_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'previews')
        os.makedirs(preview_dir, exist_ok=True)
        
        # 设置预览图路径
        preview_filename = f"preview_{video.id}.jpg"
        preview_path = os.path.join(preview_dir, preview_filename)
        
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
        
        # 更新视频记录
        video.preview_filename = preview_filename
        video.preview_filepath = preview_path
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"创建占位文件预览图出错: {str(e)}")
        return False

@celery.task(name='app.tasks.process_video', bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=240, retry_jitter=True)
def process_video(self, video_id, language='zh', model='large'):
    """处理视频任务"""
    import os  # 确保os模块导入
    try:
        # 导入faiss相关模块
        import sys
        import importlib
        
        # 记录Python版本和环境信息
        python_version = sys.version
        logger.info(f"🐍 Python版本: {python_version}")
        
        # 尝试导入faiss模块
        try:
            import faiss
            logger.info("🔍 FAISS模块已成功加载")
        except ImportError as e:
            logger.warning(f"⚠️ 未找到FAISS模块，QA功能将受限: {str(e)}")
            
            # 尝试查找可能的faiss安装位置
            try:
                for path in sys.path:
                    if 'site-packages' in path or 'dist-packages' in path:
                        import os
                        packages = os.listdir(path)
                        faiss_related = [p for p in packages if 'faiss' in p.lower()]
                        if faiss_related:
                            logger.info(f"💡 发现可能的FAISS相关包: {faiss_related}")
            except Exception as e:
                logger.error(f"❌ 查找FAISS包时出错: {str(e)}")
        
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
                        audio_path
                    ]
                    
                    # 执行ffmpeg命令
                    subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                    
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
                
                # 根据模型大小调整参数
                model_size_map = {
                    "tiny": {"beam_size": 2, "best_of": 2, "patience": 1.0},
                    "base": {"beam_size": 2, "best_of": 2, "patience": 1.0},
                    "small": {"beam_size": 3, "best_of": 3, "patience": 1.0},
                    "medium": {"beam_size": 3, "best_of": 3, "patience": 1.0},
                    "large": {"beam_size": 3, "best_of": 3, "patience": 1.0},
                    "turbo": {"beam_size": 1, "best_of": 1, "patience": 0.8},  # turbo模型更快，使用更小的参数
                }
                
                # 获取当前模型的参数配置
                model_base = model.split('.')[0] if '.' in model else model  # 处理如small.en这样的模型名
                model_params = model_size_map.get(model_base, {"beam_size": 3, "best_of": 3, "patience": 1.0})
                
                # 只有在CUDA可用时才添加CUDA设备参数
                if cuda_available:
                    whisper_cmd.extend(["--device", "cuda"])
                    # 添加FP16加速参数
                    whisper_cmd.extend(["--fp16", "True"])
                    # 增加线程数，提高CPU部分的处理速度
                    whisper_cmd.extend(["--threads", "8"])
                    # 添加beam_size参数，在保证质量的情况下提高速度
                    whisper_cmd.extend(["--beam_size", str(model_params["beam_size"])])
                    # 添加best_of参数，减少候选数量，加快处理速度
                    whisper_cmd.extend(["--best_of", str(model_params["best_of"])])
                    # 添加patience参数，优化beam search效率
                    whisper_cmd.extend(["--patience", str(model_params["patience"])])
                    # 添加length_penalty参数，优化长文本处理
                    whisper_cmd.extend(["--length_penalty", "0.8"])
                    # 添加temperature参数，使用较低的温度提高准确性和速度
                    whisper_cmd.extend(["--temperature", "0.0"])
                    # 添加no_speech_threshold参数，更好地处理静音段
                    whisper_cmd.extend(["--no_speech_threshold", "0.6"])
                    
                    # 如果是大模型，给出性能提示
                    large_models = ["large", "medium"]
                    if model_base in large_models:
                        logger.info(f"⚠️ 注意: 正在使用较大的模型({model})，即使有CUDA加速，处理也可能需要较长时间")
                else:
                    # 如果CUDA不可用，但模型较大，给出警告
                    large_models = ["large", "medium"]
                    if model_base in large_models:
                        logger.warning(f"⚠️ 注意: 正在使用较大的模型({model})但CUDA未启用，处理可能会很慢")
                    # 即使没有CUDA，也增加线程数提高CPU处理速度
                    whisper_cmd.extend(["--threads", "8"])
                    # 对于CPU处理，使用更小的beam_size和best_of以加快速度
                    whisper_cmd.extend(["--beam_size", "1"])
                    whisper_cmd.extend(["--best_of", "1"])
                    # 添加patience参数，优化beam search效率
                    whisper_cmd.extend(["--patience", "0.8"])
                    # 添加temperature参数，使用较低的温度提高准确性和速度
                    whisper_cmd.extend(["--temperature", "0.0"])
                    # 添加no_speech_threshold参数，更好地处理静音段
                    whisper_cmd.extend(["--no_speech_threshold", "0.6"])
                
                # 格式化日志输出，使其更友好
                cmd_str = ' '.join(whisper_cmd)
                logger.info(f"🚀 启动AI转录引擎 | 模型: {model} | 语言: {language} | CUDA加速: {'已启用' if cuda_available else '未启用'}")
                logger.info(f"📝 处理文件: {os.path.basename(video.filepath)}")
                
                # 更新进度
                video.process_progress = 60.0
                video.current_step = "运行AI转录引擎"
                db.session.commit()
                
                # 启动子进程并实时监控输出
                process = subprocess.Popen(
                    whisper_cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 监控进度
                for line in iter(process.stderr.readline, ''):
                    # 解析进度信息
                    if "%" in line:
                        try:
                            # 尝试从输出中提取进度百分比
                            progress_parts = line.split('%')
                            if len(progress_parts) > 1:
                                progress_text = progress_parts[0].strip().split(' ')[-1]
                                progress_value = float(progress_text)
                                # 将whisper的进度(0-100)映射到整体进度的60%-90%
                                overall_progress = 60.0 + (progress_value * 0.3)
                                video.process_progress = min(90.0, overall_progress)
                                video.current_step = f"转录中: {progress_value:.1f}%"
                                db.session.commit()
                                logger.debug(f"转录进度: {progress_value:.1f}%")
                        except Exception as e:
                            logger.debug(f"解析进度失败: {str(e)}, 行: {line}")
                    
                    # 检查是否包含处理步骤信息
                    step_indicators = {
                        "Detecting language": "检测语言",
                        "Transcribing": "转录音频",
                        "Loading model": "加载模型",
                        "Processing": "处理音频"
                    }
                    
                    for indicator, step_name in step_indicators.items():
                        if indicator in line:
                            video.current_step = step_name
                            db.session.commit()
                            logger.debug(f"当前步骤: {step_name}")
                
                # 等待进程完成
                process.wait()
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
                    
                db.session.commit()
            else:
                logger.info(f"📝 占位文件，跳过字幕处理 | 文件: {os.path.basename(video.filepath)}")
                video.process_progress = 90.0
                db.session.commit()
        except Exception as e:
            logger.error(f"❌ 字幕处理失败: {str(e)}")
            # 不要因为字幕失败而使整个处理失败，继续处理
        
        # 更新视频状态
        video.status = VideoStatus.COMPLETED
        video.processed = True
        video.process_progress = 100.0
        video.current_step = "处理完成"
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
