from celery import shared_task
from ..models.video import Video, VideoStatus
from ..extensions import db
import yt_dlp
import os
import requests
import time
from flask import current_app
import json
import csv

@shared_task(bind=True)
def process_video(self, video_id, filepath=None):
    """处理视频文件，包括转码和生成字幕"""
    try:
        with create_app().app_context():
            video = Video.query.get(video_id)
            if not video:
                return
                
            current_app.logger.info(f"开始处理视频: {video.filename}")
            
            # 更新状态为处理中
            video.status = VideoStatus.PROCESSING
            db.session.commit()
            
            try:
                # 获取视频信息
                video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video.filename)
                if not os.path.exists(video_path):
                    raise Exception(f"视频文件不存在: {video_path}")
                    
                # 生成字幕文件
                subtitle_filename = os.path.splitext(video.filename)[0]
                subtitle_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{subtitle_filename}.srt")
                
                # 使用whisper生成字幕
                try:
                    current_app.logger.info(f"开始生成字幕: {video_path}")
                    result = model.transcribe(
                        video_path,
                        language="zh",
                        task="transcribe",
                        beam_size=5,
                        best_of=5,
                        temperature=0.0,
                        patience=2.0,
                        length_penalty=0.8,
                        no_speech_threshold=0.5,
                        condition_on_previous_text=True,
                        initial_prompt="这是一个中文视频，请用中文字幕。",
                        word_timestamps=True
                    )
                    
                    # 保存不同格式的字幕文件
                    current_app.logger.info("保存字幕文件")
                    
                    # 保存SRT格式
                    with open(subtitle_path, "w", encoding="utf-8") as f:
                        write_srt(result["segments"], file=f)
                        
                    # 保存VTT格式
                    vtt_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{subtitle_filename}.vtt")
                    with open(vtt_path, "w", encoding="utf-8") as f:
                        write_vtt(result["segments"], file=f)
                        
                    # 保存JSON格式（包含详细信息）
                    json_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{subtitle_filename}.json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                        
                    # 保存TSV格式
                    tsv_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{subtitle_filename}.tsv")
                    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f, delimiter="\t")
                        writer.writerow(["start", "end", "text"])
                        for segment in result["segments"]:
                            writer.writerow([
                                format_timestamp(segment["start"]),
                                format_timestamp(segment["end"]),
                                segment["text"].strip()
                            ])
                            
                    # 保存纯文本格式
                    txt_path = os.path.join(current_app.config['SUBTITLE_FOLDER'], f"{subtitle_filename}.txt")
                    with open(txt_path, "w", encoding="utf-8") as f:
                        for segment in result["segments"]:
                            f.write(segment["text"].strip() + "\n")
                            
                    # 更新数据库中的字幕文件路径
                    video.subtitle_filepath = subtitle_path
                    db.session.commit()
                    
                    current_app.logger.info("字幕生成完成")
                    
                except Exception as e:
                    current_app.logger.error(f"生成字幕失败: {str(e)}")
                    raise
                    
                # 更新状态为完成
                video.status = VideoStatus.READY
                db.session.commit()
                
                current_app.logger.info(f"视频处理完成: {video.filename}")
                
            except Exception as e:
                current_app.logger.error(f"处理视频失败: {str(e)}")
                video.status = VideoStatus.ERROR
                db.session.commit()
                raise
                
    except Exception as e:
        current_app.logger.error(f"处理视频任务失败: {str(e)}")
        raise

@shared_task(bind=True)
def process_video_url(self, video_id, video_url):
    """处理视频链接"""
    try:
        video = Video.query.get(video_id)
        if not video:
            return {'status': 'error', 'message': '视频不存在'}
            
        video.status = VideoStatus.PROCESSING
        db.session.commit()
        
        self.update_state(state='PROGRESS', meta={
            'status': '正在获取视频信息...',
            'progress': 20
        })
        
        # 根据不同平台处理视频
        if 'bilibili.com' in video_url:
            # 处理B站视频
            # TODO: 实现B站视频下载
            pass
            
        elif 'youtube.com' in video_url or 'youtu.be' in video_url:
            # 处理YouTube视频
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'uploads/%(title)s.%(ext)s',
                'progress_hooks': [lambda d: self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': '正在下载视频...',
                        'progress': 20 + int(d['downloaded_bytes'] * 60 / d['total_bytes']) if d.get('total_bytes') else 50
                    }
                ) if d['status'] == 'downloading' else None]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url)
                video.title = info.get('title', '')
                video.file_path = os.path.join('uploads', f"{info['title']}.{info['ext']}")
                
        self.update_state(state='PROGRESS', meta={
            'status': '正在生成预览...',
            'progress': 80
        })
        
        # TODO: 生成预览视频
        time.sleep(1)  # 模拟处理时间
        
        video.status = VideoStatus.READY
        db.session.commit()
        
        return {
            'status': '处理完成',
            'progress': 100,
            'video_id': video_id
        }
        
    except Exception as e:
        video.status = VideoStatus.ERROR
        db.session.commit()
        raise Exception(f'视频处理失败: {str(e)}')
