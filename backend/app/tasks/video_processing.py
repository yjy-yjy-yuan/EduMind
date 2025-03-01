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

@celery.task(name='app.tasks.process_video')
def process_video(video_id, language='zh', model='base'):
    """处理视频任务"""
    try:
        logger.warning(f'开始处理视频: {video_id}, 语言: {language}, 模型: {model}')
        
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            logger.error(f'视频不存在: {video_id}')
            return {'status': 'failed', 'message': '视频不存在'}
        
        # 更新视频状态
        video.status = VideoStatus.PROCESSING
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
            if create_placeholder_preview(video):
                # 更新视频状态
                video.status = VideoStatus.COMPLETED
                video.processed = True
                video.duration = 0
                video.fps = 0
                video.width = 640
                video.height = 360
                video.frame_count = 0
                db.session.commit()
                
                return {'status': 'success', 'message': '已创建占位文件预览图'}
            else:
                video.status = VideoStatus.FAILED
                db.session.commit()
                return {'status': 'failed', 'message': '创建占位文件预览图失败'}
        
        # 生成预览图
        try:
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
                db.session.commit()
                return {'status': 'failed', 'message': '无法打开视频文件'}
            
            # 读取第一帧
            ret, frame = cap.read()
            if not ret:
                logger.error(f"无法读取视频帧: {video.filepath}")
                cap.release()
                video.status = VideoStatus.FAILED
                db.session.commit()
                return {'status': 'failed', 'message': '无法读取视频帧'}
            
            # 保存预览图
            cv2.imwrite(preview_path, frame)
            cap.release()
            
            # 更新视频记录
            video.preview_filename = preview_filename
            video.preview_filepath = preview_path
        except Exception as e:
            logger.error(f"生成预览图失败: {str(e)}")
            video.status = VideoStatus.FAILED
            db.session.commit()
            return {'status': 'failed', 'message': f'生成预览图失败: {str(e)}'}
        
        # 提取视频信息
        try:
            # 获取视频信息
            video_info = generate_video_info(video.filepath)
            
            if video_info:
                # 更新视频信息
                video.width = video_info['width']
                video.height = video_info['height']
                video.fps = video_info['fps']
                video.frame_count = video_info['frame_count']
                video.duration = video_info['duration']
            else:
                logger.error(f"获取视频信息失败: {video.filepath}")
                video.status = VideoStatus.FAILED
                db.session.commit()
                return {'status': 'failed', 'message': '获取视频信息失败'}
        except Exception as e:
            logger.error(f"提取视频信息失败: {str(e)}")
            video.status = VideoStatus.FAILED
            db.session.commit()
            return {'status': 'failed', 'message': f'提取视频信息失败: {str(e)}'}
        
        # 处理字幕
        try:
            logger.info(f"开始处理视频字幕: {video_id}")
            
            # 检查是否是占位文件，如果是则跳过字幕处理
            if not is_placeholder:
                # 创建字幕输出目录
                subtitle_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'subtitles')
                os.makedirs(subtitle_dir, exist_ok=True)
                
                # 设置输出文件路径
                base_filename = os.path.splitext(os.path.basename(video.filepath))[0]
                srt_filepath = os.path.join(subtitle_dir, f"{base_filename}.srt")
                txt_filepath = os.path.join(subtitle_dir, f"{base_filename}.txt")
                
                # 使用whisper模型转录视频
                logger.info(f"开始转录视频: {video.filepath}")
                
                # 调用whisper命令行工具进行转录
                whisper_cmd = [
                    "whisper", 
                    video.filepath,
                    "--model", model,
                    "--language", language,
                    "--output_dir", subtitle_dir,
                    "--output_format", "all"  # 使用all生成所有格式，包括srt和txt
                ]
                
                logger.info(f"执行命令: {' '.join(whisper_cmd)}")
                result = subprocess.run(whisper_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"转录失败: {result.stderr}")
                    # 不要因为字幕失败而使整个处理失败，继续处理
                else:
                    logger.info(f"转录成功: {result.stdout}")
                    # 更新视频记录 - 注意whisper生成的文件名可能与视频文件名不同
                    # 检查生成的字幕文件是否存在
                    expected_srt = os.path.join(subtitle_dir, f"{base_filename}.srt")
                    if os.path.exists(expected_srt):
                        video.subtitle_filepath = expected_srt
                        logger.info(f"找到字幕文件: {expected_srt}")
                    else:
                        # 尝试查找任何生成的srt文件
                        srt_files = [f for f in os.listdir(subtitle_dir) if f.endswith('.srt')]
                        if srt_files:
                            newest_srt = max([os.path.join(subtitle_dir, f) for f in srt_files], 
                                           key=os.path.getctime)
                            video.subtitle_filepath = newest_srt
                            logger.info(f"使用最新生成的字幕文件: {newest_srt}")
                        else:
                            logger.warning(f"未找到生成的字幕文件")
                    
                    db.session.commit()
            else:
                logger.info(f"占位文件，跳过字幕处理: {video.filepath}")
                
        except Exception as e:
            logger.error(f"处理字幕失败: {str(e)}")
            # 不要因为字幕失败而使整个处理失败，继续处理
        
        # 更新视频状态
        video.status = VideoStatus.COMPLETED
        video.processed = True
        db.session.commit()
        
        return {'status': 'success', 'message': '视频处理成功'}
        
    except Exception as e:
        logger.error(f"处理视频失败: {str(e)}")
        
        # 更新视频状态
        try:
            video = Video.query.get(video_id)
            if video:
                video.status = VideoStatus.FAILED
                db.session.commit()
        except Exception as e2:
            logger.error(f"更新视频状态失败: {str(e2)}")
        
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
